import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.app.models.student import StudentEnrolment, StudentIdentity
from backend.app.models.verification import VerificationRequest
from backend.app.models.user import User
from backend.app.models.audit import AuditEventType
from backend.app.services.audit_service import AuditService
from backend.app.core.security import compute_identity_fingerprint, mask_apaar_id, normalize_apaar_id


class VerificationService:
    """
    Authorized, purpose-bound verification service.
    Enforces purpose limitation, consent references, and returns permitted claims only.
    Clearly labels results as verified against the synthetic local prototype repository.
    """

    @classmethod
    def verify_student_record(
        cls,
        db: Session,
        actor: User,
        requester_organization: str,
        query_identifier: str,  # Student ID or raw/masked APAAR ID
        purpose: str,
        consent_proof_ref: str,
    ) -> Dict[str, Any]:
        if not consent_proof_ref or len(consent_proof_ref.strip()) < 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valid consent or authorization reference is mandatory for verification requests.",
            )

        if not purpose or len(purpose.strip()) < 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Specific lawful purpose is mandatory for identity verification (Purpose Limitation).",
            )

        clean_query = str(query_identifier).strip()
        normalized_apaar = normalize_apaar_id(clean_query)
        fingerprint = compute_identity_fingerprint(normalized_apaar) if normalized_apaar else ""

        # Search by student ID or by identity fingerprint
        enrolment = None
        if fingerprint:
            enrolment = (
                db.query(StudentEnrolment)
                .join(StudentIdentity)
                .filter(StudentIdentity.protected_identity_fingerprint == fingerprint)
                .first()
            )

        if not enrolment:
            enrolment = (
                db.query(StudentEnrolment)
                .filter(StudentEnrolment.institution_student_id.ilike(clean_query))
                .first()
            )

        verification_ref = f"EDUTRACE-VERIF-{uuid.uuid4().hex[:12].upper()}"

        if not enrolment:
            v_status = "RECORD_NOT_FOUND"
            permitted_claims = {
                "verification_status": v_status,
                "verification_provider": "SIMULATED_LOCAL_REPOSITORY",
                "message": "No matching enrolment record found in prototype repository for provided reference.",
                "query_reference": clean_query,
                "timestamp": datetime.utcnow().isoformat(),
            }
        else:
            identity = enrolment.student_identity
            v_status = "VERIFIED_LOCAL"
            permitted_claims = {
                "verification_status": v_status,
                "verification_provider": "SIMULATED_LOCAL_REPOSITORY",
                "disclaimer": "Verified against synthetic EDUTrace prototype repository. Not an official UIDAI/DigiLocker certificate.",
                "student_name": identity.legal_name if identity else "Confidential",
                "student_id": enrolment.institution_student_id,
                "masked_apaar_id": identity.masked_apaar_id if identity else mask_apaar_id(clean_query),
                "institution_name": enrolment.institution.name if enrolment.institution else "Unknown Institution",
                "institution_code": enrolment.institution.code if enrolment.institution else "",
                "programme_name": enrolment.programme.programme_name if enrolment.programme else "Unknown Programme",
                "programme_code": enrolment.programme.programme_code if enrolment.programme else "",
                "academic_year": enrolment.academic_year.year_code if enrolment.academic_year else "2026-27",
                "enrolment_status": enrolment.enrolment_status,
                "admission_date": enrolment.admission_date.isoformat() if enrolment.admission_date else None,
                "is_eligible_enrolment": enrolment.is_eligible_enrolment,
                "verification_reference": verification_ref,
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Persist VerificationRequest audit
        v_req = VerificationRequest(
            requester_user_id=actor.id,
            requester_organization=requester_organization,
            verification_type="STUDENT_ENROLMENT_RECORD",
            target_identity_ref=mask_apaar_id(clean_query) if len(clean_query) >= 10 else clean_query,
            purpose=purpose,
            consent_proof_reference=consent_proof_ref,
            authorization_status="AUTHORIZED",
            verification_status=v_status,
            result_payload=permitted_claims,
            requested_at=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=30),
        )
        db.add(v_req)
        db.commit()

        AuditService.log(
            db=db,
            event_type=AuditEventType.VERIFICATION_REQUESTED,
            resource_type="VERIFICATION_REQUEST",
            resource_id=verification_ref,
            actor=actor,
            institution_id=enrolment.institution_id if enrolment else None,
            details={
                "purpose": purpose,
                "organization": requester_organization,
                "status": v_status,
                "consent_ref": consent_proof_ref,
            },
        )

        return permitted_claims
