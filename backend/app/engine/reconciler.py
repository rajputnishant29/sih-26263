from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.institution import ApprovalIntake, Programme, SourceDocument
from backend.app.models.student import StudentEnrolment, EnrolmentStatus
from backend.app.models.validation import IssueSeverity


class AdmissionReconciler:
    """
    Reconciles student-level admissions against versioned, sourced AICTE approval intake.
    Maintains traceable association:
    Approval value -> source document -> academic year -> programme -> applicable rule version -> reconciliation result.
    """

    @classmethod
    def reconcile_programme(
        cls,
        db: Session,
        institution_id: int,
        programme_id: int,
        academic_year_id: int,
        prospective_new_active_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Reconciles programme intake and enrolment.
        """
        # 1. Fetch official approval intake metadata
        approval = (
            db.query(ApprovalIntake)
            .filter(
                ApprovalIntake.institution_id == institution_id,
                ApprovalIntake.programme_id == programme_id,
                ApprovalIntake.academic_year_id == academic_year_id,
                ApprovalIntake.is_active == True,
            )
            .first()
        )

        # 2. Query current eligible active student enrolments
        # Explicit counting semantics: Only ACTIVE, non-withdrawn, non-cancelled records count
        current_active_count = (
            db.query(func.count(StudentEnrolment.id))
            .filter(
                StudentEnrolment.institution_id == institution_id,
                StudentEnrolment.programme_id == programme_id,
                StudentEnrolment.academic_year_id == academic_year_id,
                StudentEnrolment.enrolment_status == EnrolmentStatus.ACTIVE,
                StudentEnrolment.is_eligible_enrolment == True,
            )
            .scalar()
            or 0
        )

        # Count supernumerary enrolments
        supernumerary_enrolled = (
            db.query(func.count(StudentEnrolment.id))
            .filter(
                StudentEnrolment.institution_id == institution_id,
                StudentEnrolment.programme_id == programme_id,
                StudentEnrolment.academic_year_id == academic_year_id,
                StudentEnrolment.enrolment_status == EnrolmentStatus.ACTIVE,
                StudentEnrolment.is_supernumerary == True,
            )
            .scalar()
            or 0
        )

        total_calculated_enrolment = current_active_count + prospective_new_active_count

        if not approval:
            # Missing approval intake metadata
            return {
                "has_approval_record": False,
                "base_approved_intake": 0,
                "supernumerary_seats": 0,
                "effective_limit": 0,
                "calculated_enrolment": total_calculated_enrolment,
                "supernumerary_enrolled": supernumerary_enrolled,
                "variance": total_calculated_enrolment,
                "is_exceeded": False,
                "excess_count": 0,
                "source_eoa_reference": "NO_SOURCE_REGISTERED",
                "rule_version": "AICTE_APH_2026_DEFAULT",
                "source_confirmed": False,
                "findings": [{
                    "rule_code": "MISSING_INTAKE_APPROVAL",
                    "severity": IssueSeverity.HIGH,
                    "title": "Missing AICTE Approval Record",
                    "message": "No sanctioned approved intake record found for this programme and academic year.",
                }],
            }

        effective_limit = approval.effective_intake_limit
        is_exceeded = total_calculated_enrolment > effective_limit
        excess_count = max(0, total_calculated_enrolment - effective_limit)
        remaining_capacity = max(0, effective_limit - total_calculated_enrolment)
        utilization_rate = round((total_calculated_enrolment / effective_limit * 100), 2) if effective_limit > 0 else 0.0

        source_doc = approval.source_document
        source_ref = source_doc.reference_number if source_doc else "MANUAL_REGISTERED"
        source_confirmed = source_doc.extraction_status == "CONFIRMED" if source_doc else True

        findings = []
        if is_exceeded:
            findings.append({
                "rule_code": "INTAKE_CAPACITY_EXCEEDED",
                "severity": IssueSeverity.CRITICAL,
                "title": f"Intake Capacity Exceeded by {excess_count}",
                "message": (
                    f"Calculated enrolment ({total_calculated_enrolment}) exceeds effective approved intake "
                    f"limit ({effective_limit}) by {excess_count} students under rule {approval.rule_version}."
                ),
                "evidence": {
                    "base_approved_intake": approval.base_approved_intake,
                    "supernumerary_seats": approval.supernumerary_seats,
                    "effective_limit": effective_limit,
                    "calculated_enrolment": total_calculated_enrolment,
                    "excess_count": excess_count,
                    "rule_version": approval.rule_version,
                    "source_eoa_reference": source_ref,
                },
            })

        return {
            "has_approval_record": True,
            "base_approved_intake": approval.base_approved_intake,
            "supernumerary_seats": approval.supernumerary_seats,
            "effective_limit": effective_limit,
            "calculated_enrolment": total_calculated_enrolment,
            "supernumerary_enrolled": supernumerary_enrolled,
            "remaining_capacity": remaining_capacity,
            "utilization_rate": utilization_rate,
            "variance": total_calculated_enrolment - effective_limit,
            "is_exceeded": is_exceeded,
            "excess_count": excess_count,
            "source_eoa_reference": source_ref,
            "rule_version": approval.rule_version,
            "source_confirmed": source_confirmed,
            "findings": findings,
        }

    @classmethod
    def reconcile_upload_declaration(
        cls,
        declared_total: int,
        rows_received: int,
        accepted_rows: int,
        rejected_rows: int,
        excluded_duplicate_rows: int,
        eligible_enrolment: int,
    ) -> Dict[str, Any]:
        """
        Reconciliation of declared totals vs parsed and accepted records.
        """
        variance = declared_total - rows_received
        has_mismatch = (declared_total > 0 and declared_total != rows_received)

        findings = []
        if has_mismatch:
            findings.append({
                "rule_code": "DECLARED_TOTAL_MISMATCH",
                "severity": IssueSeverity.MEDIUM,
                "title": f"Declared Total Mismatch (Variance: {variance})",
                "message": (
                    f"Institution declared {declared_total} admissions, but upload file contained "
                    f"{rows_received} rows ({accepted_rows} valid/staged, {rejected_rows} rejected). "
                    f"Variance of {abs(variance)} requires operational confirmation."
                ),
                "evidence": {
                    "declared_total": declared_total,
                    "rows_received": rows_received,
                    "accepted_rows": accepted_rows,
                    "rejected_rows": rejected_rows,
                    "excluded_duplicates": excluded_duplicate_rows,
                    "variance": variance,
                },
            })

        return {
            "declared_total": declared_total,
            "rows_received": rows_received,
            "accepted_rows": accepted_rows,
            "rejected_rows": rejected_rows,
            "excluded_duplicates": excluded_duplicate_rows,
            "eligible_enrolment": eligible_enrolment,
            "variance": variance,
            "has_mismatch": has_mismatch,
            "findings": findings,
        }
