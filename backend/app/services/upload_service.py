import hashlib
import io
import time
from typing import Dict, Any, List, Optional
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from backend.app.models.institution import Institution, Programme, AcademicYear, ApprovalIntake
from backend.app.models.student import (
    StudentIdentity,
    StudentEnrolment,
    IdentityVerificationEvidence,
    EnrolmentStatus,
)
from backend.app.models.upload import (
    UploadBatch,
    UploadStagingRow,
    ValidationRun,
    UploadStatus,
)
from backend.app.models.validation import (
    ValidationIssue,
    VersionedRule,
    IssueSeverity,
    IssueStatus,
)
from backend.app.models.user import User
from backend.app.models.audit import AuditEventType
from backend.app.engine.validator import DeterministicValidator
from backend.app.engine.reconciler import AdmissionReconciler
from backend.app.engine.duplicate_detector import DuplicateDetector
from backend.app.services.audit_service import AuditService
from backend.app.core.sse import sse_manager


class UploadService:
    """
    Secure file ingestion, staging, dry-run validation, and atomic commit service.
    Enforces that invalid rows do not disappear silently and repeated submissions
    do not inflate counts.
    """

    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
    MAX_ROWS_LIMIT = 5000

    EXPECTED_COLUMNS_MAP = {
        "apaar_id": ["apaar_id", "apaar", "apaar_no", "identity_ref", "student_apaar"],
        "student_id": ["student_id", "roll_no", "roll_number", "registration_no", "enrolment_id"],
        "student_name": ["student_name", "name", "candidate_name", "full_name"],
        "dob": ["dob", "date_of_birth", "birth_date"],
        "gender": ["gender", "sex"],
        "admission_date": ["admission_date", "adm_date", "date_of_admission"],
        "enrolment_status": ["enrolment_status", "status", "admission_status"],
        "seat_category": ["seat_category", "category", "quota"],
        "programme_code": ["programme_code", "course_code", "programme", "branch"],
        "is_nri": ["is_nri", "nri"],
        "is_oci": ["is_oci", "oci"],
        "is_fn": ["is_fn", "foreign_national", "fn"],
        "is_supernumerary": ["is_supernumerary", "supernumerary"],
        "supernumerary_type": ["supernumerary_type", "supernumerary_quota"],
    }

    @classmethod
    def map_dataframe_columns(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalizes varying CSV/Excel column headers to standard schema names.
        """
        rename_map = {}
        for col in df.columns:
            clean_col = str(col).strip().lower().replace(" ", "_").replace("-", "_")
            for canonical, aliases in cls.EXPECTED_COLUMNS_MAP.items():
                if clean_col == canonical or clean_col in aliases:
                    rename_map[col] = canonical
                    break
        return df.rename(columns=rename_map)

    @classmethod
    def stage_file(
        cls,
        db: Session,
        current_user: User,
        institution_id: int,
        academic_year_id: int,
        programme_id: Optional[int],
        file_bytes: bytes,
        filename: str,
        declared_count: int = 0,
    ) -> UploadBatch:
        """
        Validates format, checks file hash idempotency, and stages records.
        """
        if len(file_bytes) > cls.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Upload file exceeds maximum permitted size of {cls.MAX_FILE_SIZE_BYTES / (1024*1024)} MB",
            )

        # Compute SHA-256 hash
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        # Check for duplicate file submission
        existing_batch = (
            db.query(UploadBatch)
            .filter(
                UploadBatch.file_hash == file_hash,
                UploadBatch.institution_id == institution_id,
                UploadBatch.academic_year_id == academic_year_id,
                UploadBatch.status == UploadStatus.COMMITTED,
            )
            .first()
        )
        if existing_batch:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Safe duplicate submission: File hash already committed in Batch #{existing_batch.id} on {existing_batch.committed_at.strftime('%Y-%m-%d %H:%M')}",
            )

        # Parse CSV or Excel
        try:
            if filename.lower().endswith(".csv"):
                df = pd.read_csv(io.BytesIO(file_bytes), dtype=str, keep_default_na=False)
            elif filename.lower().endswith((".xlsx", ".xls")):
                df = pd.read_excel(io.BytesIO(file_bytes), dtype=str, keep_default_na=False)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported file format. Please upload a valid CSV or XLSX spreadsheet.",
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse spreadsheet file: {str(e)}",
            )

        if len(df) > cls.MAX_ROWS_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Row count ({len(df)}) exceeds maximum permitted batch limit ({cls.MAX_ROWS_LIMIT})",
            )

        # Normalize columns
        df = cls.map_dataframe_columns(df)

        # Create UploadBatch record
        batch = UploadBatch(
            institution_id=institution_id,
            programme_id=programme_id,
            academic_year_id=academic_year_id,
            file_name=filename,
            file_size=len(file_bytes),
            file_hash=file_hash,
            row_count=len(df),
            declared_count=declared_count if declared_count > 0 else len(df),
            status=UploadStatus.STAGED,
            uploaded_by_user_id=current_user.id,
        )
        db.add(batch)
        db.flush()

        # Stage each row
        staging_rows = []
        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            staging = UploadStagingRow(
                upload_batch_id=batch.id,
                row_number=idx + 1,
                raw_data=row_dict,
                validation_status="STAGED",
                validation_messages=[],
                is_accepted=False,
            )
            staging_rows.append(staging)

        db.bulk_save_objects(staging_rows)
        db.commit()
        db.refresh(batch)

        AuditService.log(
            db=db,
            event_type=AuditEventType.FILE_UPLOAD_STAGED,
            resource_type="UPLOAD_BATCH",
            resource_id=str(batch.id),
            actor=current_user,
            institution_id=institution_id,
            details={"file_name": filename, "row_count": len(df), "declared_count": declared_count},
        )

        return batch

    @classmethod
    def validate_batch(cls, db: Session, batch_id: int) -> Dict[str, Any]:
        """
        Runs deterministic validation dry run on staged rows.
        Does NOT persist student records yet.
        """
        batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Upload batch not found")

        start_time = time.time()
        staging_rows = (
            db.query(UploadStagingRow)
            .filter(UploadStagingRow.upload_batch_id == batch.id)
            .order_by(UploadStagingRow.row_number)
            .all()
        )

        # Fetch existing student IDs and fingerprints in institution to detect clashes
        existing_student_ids = set(
            s[0]
            for s in db.query(StudentEnrolment.institution_student_id)
            .filter(
                StudentEnrolment.institution_id == batch.institution_id,
                StudentEnrolment.academic_year_id == batch.academic_year_id,
            )
            .all()
        )

        existing_fingerprints = set(
            f[0]
            for f in db.query(StudentIdentity.protected_identity_fingerprint).all()
        )

        seen_apaar_in_file: Dict[str, int] = {}
        seen_student_ids_in_file: Dict[str, int] = {}

        valid_count = 0
        warning_count = 0
        error_count = 0
        row_results = []
        prospective_active_by_programme: Dict[int, int] = {}

        # Resolve programme for prospective count
        prog_id = batch.programme_id
        if not prog_id:
            first_prog = db.query(Programme).filter(Programme.institution_id == batch.institution_id).first()
            prog_id = first_prog.id if first_prog else 1

        for row in staging_rows:
            v_status, messages, normalized = DeterministicValidator.validate_row(
                row_number=row.row_number,
                data=row.raw_data,
                seen_apaar_in_file=seen_apaar_in_file,
                seen_student_ids_in_file=seen_student_ids_in_file,
                existing_institution_student_ids=existing_student_ids,
                existing_identity_fingerprints=existing_fingerprints,
            )

            row.validation_status = v_status
            row.validation_messages = messages
            row.normalized_data = normalized
            row.is_accepted = (v_status in ["VALID", "WARNING"])

            if v_status == "VALID":
                valid_count += 1
            elif v_status == "WARNING":
                warning_count += 1
            else:
                error_count += 1

            if row.is_accepted and normalized.get("is_eligible_enrolment"):
                prospective_active_by_programme[prog_id] = prospective_active_by_programme.get(prog_id, 0) + 1

            row_results.append({
                "row_number": row.row_number,
                "status": v_status,
                "messages": messages,
                "student_id": normalized.get("student_id"),
                "student_name": normalized.get("student_name"),
                "masked_apaar": normalized.get("masked_apaar"),
                "is_accepted": row.is_accepted,
            })

        duration_ms = round((time.time() - start_time) * 1000, 2)

        # Intake reconciliation check
        prospective_count = prospective_active_by_programme.get(prog_id, 0)
        intake_reconciliation = AdmissionReconciler.reconcile_programme(
            db=db,
            institution_id=batch.institution_id,
            programme_id=prog_id,
            academic_year_id=batch.academic_year_id,
            prospective_new_active_count=prospective_count,
        )

        # Declared total reconciliation
        declaration_reconciliation = AdmissionReconciler.reconcile_upload_declaration(
            declared_total=batch.declared_count,
            rows_received=len(staging_rows),
            accepted_rows=valid_count + warning_count,
            rejected_rows=error_count,
            excluded_duplicate_rows=0,
            eligible_enrolment=prospective_count,
        )

        # Update batch summary counts
        batch.accepted_count = valid_count + warning_count
        batch.rejected_count = error_count
        batch.warning_count = warning_count
        batch.status = UploadStatus.VALIDATED

        # Record validation run
        v_run = ValidationRun(
            upload_batch_id=batch.id,
            run_type="DRY_RUN",
            total_checked=len(staging_rows),
            issues_count=len([m for r in row_results for m in r["messages"]]),
            run_duration_ms=duration_ms,
            summary_metrics={
                "valid_count": valid_count,
                "warning_count": warning_count,
                "error_count": error_count,
                "intake_exceeded": intake_reconciliation.get("is_exceeded", False),
                "declaration_mismatch": declaration_reconciliation.get("has_mismatch", False),
            },
        )
        db.add(v_run)
        db.commit()

        AuditService.log(
            db=db,
            event_type=AuditEventType.FILE_VALIDATION_RUN,
            resource_type="UPLOAD_BATCH",
            resource_id=str(batch.id),
            actor=batch.uploaded_by,
            institution_id=batch.institution_id,
            details={
                "valid": valid_count,
                "warnings": warning_count,
                "errors": error_count,
                "duration_ms": duration_ms,
            },
        )

        return {
            "batch_id": batch.id,
            "filename": batch.file_name,
            "status": batch.status,
            "total_rows": len(staging_rows),
            "valid_count": valid_count,
            "warning_count": warning_count,
            "error_count": error_count,
            "duration_ms": duration_ms,
            "intake_reconciliation": intake_reconciliation,
            "declaration_reconciliation": declaration_reconciliation,
            "row_previews": row_results[:50],  # Limit preview in payload for responsiveness
        }

    @classmethod
    def commit_batch(cls, db: Session, batch_id: int, current_user: User) -> Dict[str, Any]:
        """
        Atomically commits valid and warning staged rows into real student records.
        Creates reviewable ValidationIssue records and checks for cross-institution duplicate candidates.
        """
        batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Upload batch not found")

        if batch.status == UploadStatus.COMMITTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch #{batch.id} has already been committed.",
            )

        # Resolve programme
        programme = None
        if batch.programme_id:
            programme = db.query(Programme).filter(Programme.id == batch.programme_id).first()
        if not programme:
            programme = db.query(Programme).filter(Programme.institution_id == batch.institution_id).first()

        staging_rows = (
            db.query(UploadStagingRow)
            .filter(
                UploadStagingRow.upload_batch_id == batch.id,
                UploadStagingRow.is_accepted == True,
            )
            .all()
        )

        committed_enrolments = []
        new_issues = []
        duplicate_candidate_findings = []

        try:
            for row in staging_rows:
                norm = row.normalized_data
                fingerprint = norm.get("fingerprint") or f"NO_FINGERPRINT_ROW_{row.id}"
                masked_apaar = norm.get("masked_apaar") or "APAAR-MISSING"

                # 1. Deduplicate or create StudentIdentity
                identity = None
                if norm.get("fingerprint"):
                    identity = (
                        db.query(StudentIdentity)
                        .filter(StudentIdentity.protected_identity_fingerprint == norm["fingerprint"])
                        .first()
                    )

                if not identity:
                    identity = StudentIdentity(
                        protected_identity_fingerprint=fingerprint,
                        masked_apaar_id=masked_apaar,
                        legal_name=norm.get("student_name", "Unknown"),
                        dob=norm.get("dob"),
                        gender=norm.get("gender"),
                    )
                    db.add(identity)
                    db.flush()

                # 2. Create StudentEnrolment
                enrolment = StudentEnrolment(
                    student_identity_id=identity.id,
                    institution_id=batch.institution_id,
                    programme_id=programme.id if programme else 1,
                    academic_year_id=batch.academic_year_id,
                    institution_student_id=norm.get("student_id"),
                    admission_date=norm.get("admission_date"),
                    enrolment_status=norm.get("enrolment_status", EnrolmentStatus.ACTIVE),
                    seat_category=norm.get("seat_category", "OPEN"),
                    is_nri=norm.get("is_nri", False),
                    is_oci=norm.get("is_oci", False),
                    is_fn=norm.get("is_fn", False),
                    is_supernumerary=norm.get("is_supernumerary", False),
                    supernumerary_type=norm.get("supernumerary_type"),
                    source_upload_batch_id=batch.id,
                    is_eligible_enrolment=norm.get("is_eligible_enrolment", True),
                )
                db.add(enrolment)
                db.flush()
                committed_enrolments.append(enrolment)

                # 3. Create ValidationIssues for warnings/messages on this row
                for msg in row.validation_messages:
                    issue = ValidationIssue(
                        upload_batch_id=batch.id,
                        rule_code=msg.get("rule_code", "GENERAL_VALIDATION_FINDING"),
                        severity=msg.get("severity", IssueSeverity.HIGH),
                        institution_id=batch.institution_id,
                        programme_id=programme.id if programme else 1,
                        academic_year_id=batch.academic_year_id,
                        affected_student_enrolment_id=enrolment.id,
                        affected_staging_row_id=row.id,
                        title=msg.get("title", "Validation Finding"),
                        description=msg.get("message", "Validation finding detected during batch ingestion."),
                        evidence_details={
                            "row_number": row.row_number,
                            "student_id": norm.get("student_id"),
                            "masked_apaar": masked_apaar,
                            "rule_code": msg.get("rule_code"),
                        },
                        status=IssueStatus.OPEN,
                    )
                    db.add(issue)
                    new_issues.append(issue)

                # 4. Check for cross-institution duplicate candidates
                if norm.get("fingerprint"):
                    dup_findings = DuplicateDetector.scan_for_cross_institution_duplicates(
                        db=db,
                        current_identity_id=identity.id,
                        fingerprint=norm["fingerprint"],
                        institution_id=batch.institution_id,
                        student_enrolment_id=enrolment.id,
                        academic_year_id=batch.academic_year_id,
                        student_name=norm.get("student_name", ""),
                        masked_apaar=masked_apaar,
                    )
                    for df_item in dup_findings:
                        issue = ValidationIssue(
                            upload_batch_id=batch.id,
                            rule_code=df_item["rule_code"],
                            severity=df_item["severity"],
                            institution_id=batch.institution_id,
                            programme_id=programme.id if programme else 1,
                            academic_year_id=batch.academic_year_id,
                            affected_student_enrolment_id=enrolment.id,
                            title=df_item["title"],
                            description=df_item["description"],
                            evidence_details=df_item["evidence_details"],
                            status=IssueStatus.OPEN,
                        )
                        db.add(issue)
                        new_issues.append(issue)
                        duplicate_candidate_findings.append(df_item)

            # 5. Check post-commit intake reconciliation
            if programme:
                post_reconciliation = AdmissionReconciler.reconcile_programme(
                    db=db,
                    institution_id=batch.institution_id,
                    programme_id=programme.id,
                    academic_year_id=batch.academic_year_id,
                )
                for finding in post_reconciliation.get("findings", []):
                    issue = ValidationIssue(
                        upload_batch_id=batch.id,
                        rule_code=finding["rule_code"],
                        severity=finding["severity"],
                        institution_id=batch.institution_id,
                        programme_id=programme.id,
                        academic_year_id=batch.academic_year_id,
                        title=finding["title"],
                        description=finding["message"],
                        evidence_details=finding.get("evidence", {}),
                        status=IssueStatus.OPEN,
                    )
                    db.add(issue)
                    new_issues.append(issue)

            # Mark batch as committed
            batch.status = UploadStatus.COMMITTED
            batch.committed_by_user_id = current_user.id
            batch.committed_at = func.now()

            db.commit()

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Atomic batch commit failed: {str(e)}",
            )

        # Audit log
        AuditService.log(
            db=db,
            event_type=AuditEventType.RECORDS_COMMITTED,
            resource_type="UPLOAD_BATCH",
            resource_id=str(batch.id),
            actor=current_user,
            institution_id=batch.institution_id,
            details={
                "committed_enrolments": len(committed_enrolments),
                "issues_created": len(new_issues),
                "cross_institution_duplicates": len(duplicate_candidate_findings),
            },
        )

        # Broadcast real-time update to all connected dashboard clients
        sse_manager.broadcast(
            event="batch_committed",
            payload={
                "batch_id": batch.id,
                "institution_id": batch.institution_id,
                "committed_count": len(committed_enrolments),
                "issues_count": len(new_issues),
            },
        )

        return {
            "batch_id": batch.id,
            "status": "COMMITTED",
            "committed_enrolments_count": len(committed_enrolments),
            "issues_generated_count": len(new_issues),
            "duplicate_candidates_flagged": len(duplicate_candidate_findings),
            "message": f"Successfully persisted {len(committed_enrolments)} student records. Generated {len(new_issues)} reviewable issues.",
        }
