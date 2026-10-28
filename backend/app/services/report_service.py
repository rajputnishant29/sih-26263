import csv
import io
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.institution import Institution, Programme, AcademicYear, ApprovalIntake
from backend.app.models.student import StudentEnrolment, EnrolmentStatus
from backend.app.models.validation import ValidationIssue, IssueStatus


class ReportService:
    """
    Regulatory reporting and analytics export service.
    Implements formula-injection defense for spreadsheet exports.
    Derives aggregate metrics through documented backend queries.
    """

    @classmethod
    def sanitize_for_csv(cls, value: Any) -> str:
        """
        Prevents Spreadsheet Formula Injection (CSV Injection).
        If cell starts with =, +, -, @, \t, \r, prefixes with a single quote.
        """
        s = str(value) if value is not None else ""
        if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
            return f"'{s}"
        return s

    @classmethod
    def get_enrolment_reconciliation_report(
        cls,
        db: Session,
        academic_year_id: Optional[int] = None,
        institution_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns programme-level intake and enrolment reconciliation rows.
        """
        query = (
            db.query(ApprovalIntake)
            .join(Institution, ApprovalIntake.institution_id == Institution.id)
            .join(Programme, ApprovalIntake.programme_id == Programme.id)
            .join(AcademicYear, ApprovalIntake.academic_year_id == AcademicYear.id)
        )

        if academic_year_id:
            query = query.filter(ApprovalIntake.academic_year_id == academic_year_id)
        if institution_id:
            query = query.filter(ApprovalIntake.institution_id == institution_id)

        approvals = query.all()
        rows = []

        for app in approvals:
            active_count = (
                db.query(func.count(StudentEnrolment.id))
                .filter(
                    StudentEnrolment.institution_id == app.institution_id,
                    StudentEnrolment.programme_id == app.programme_id,
                    StudentEnrolment.academic_year_id == app.academic_year_id,
                    StudentEnrolment.enrolment_status == EnrolmentStatus.ACTIVE,
                    StudentEnrolment.is_eligible_enrolment == True,
                )
                .scalar()
                or 0
            )

            supernumerary_count = (
                db.query(func.count(StudentEnrolment.id))
                .filter(
                    StudentEnrolment.institution_id == app.institution_id,
                    StudentEnrolment.programme_id == app.programme_id,
                    StudentEnrolment.academic_year_id == app.academic_year_id,
                    StudentEnrolment.is_supernumerary == True,
                )
                .scalar()
                or 0
            )

            nri_count = (
                db.query(func.count(StudentEnrolment.id))
                .filter(
                    StudentEnrolment.institution_id == app.institution_id,
                    StudentEnrolment.programme_id == app.programme_id,
                    StudentEnrolment.academic_year_id == app.academic_year_id,
                    StudentEnrolment.is_nri == True,
                )
                .scalar()
                or 0
            )

            fn_oci_count = (
                db.query(func.count(StudentEnrolment.id))
                .filter(
                    StudentEnrolment.institution_id == app.institution_id,
                    StudentEnrolment.programme_id == app.programme_id,
                    StudentEnrolment.academic_year_id == app.academic_year_id,
                    (StudentEnrolment.is_fn == True) | (StudentEnrolment.is_oci == True),
                )
                .scalar()
                or 0
            )

            limit = app.effective_intake_limit
            variance = active_count - limit
            utilization = round((active_count / limit * 100), 1) if limit > 0 else 0.0

            rows.append({
                "institution_code": app.institution.code,
                "institution_name": app.institution.name,
                "programme_code": app.programme.programme_code,
                "programme_name": app.programme.programme_name,
                "academic_year": app.academic_year.year_code,
                "base_approved_intake": app.base_approved_intake,
                "supernumerary_sanctioned": app.supernumerary_seats,
                "effective_limit": limit,
                "calculated_enrolment": active_count,
                "supernumerary_enrolled": supernumerary_count,
                "nri_enrolled": nri_count,
                "fn_oci_enrolled": fn_oci_count,
                "variance": variance,
                "utilization_rate": utilization,
                "is_exceeded": active_count > limit,
                "rule_version": app.rule_version,
                "source_eoa_reference": app.source_document.reference_number if app.source_document else "MANUAL",
            })

        return rows

    @classmethod
    def generate_reconciliation_csv(cls, rows: List[Dict[str, Any]]) -> str:
        """
        Exports reconciliation dataset as sanitized CSV string.
        """
        output = io.StringIO()
        fieldnames = [
            "institution_code",
            "institution_name",
            "programme_code",
            "programme_name",
            "academic_year",
            "base_approved_intake",
            "supernumerary_sanctioned",
            "effective_limit",
            "calculated_enrolment",
            "supernumerary_enrolled",
            "nri_enrolled",
            "fn_oci_enrolled",
            "variance",
            "utilization_rate",
            "is_exceeded",
            "rule_version",
            "source_eoa_reference",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            sanitized = {k: cls.sanitize_for_csv(v) for k, v in r.items()}
            writer.writerow(sanitized)
        return output.getvalue()
