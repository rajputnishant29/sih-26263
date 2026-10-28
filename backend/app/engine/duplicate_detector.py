from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models.student import StudentIdentity, StudentEnrolment, EnrolmentStatus
from backend.app.models.validation import (
    DuplicateCandidateGroup,
    DuplicateCandidateMember,
    ValidationIssue,
    IssueSeverity,
    IssueStatus,
)


class DuplicateDetector:
    """
    Identifies duplicate candidates across institutions and uploads.
    Separates findings requiring investigation from proof of wrongdoing.
    Never automatically merges student identities or imposes adverse consequences.
    """

    @classmethod
    def scan_for_cross_institution_duplicates(
        cls,
        db: Session,
        current_identity_id: int,
        fingerprint: str,
        institution_id: int,
        student_enrolment_id: int,
        academic_year_id: int,
        student_name: str,
        masked_apaar: str,
    ) -> List[Dict[str, Any]]:
        """
        Scans for existing enrolments of the same student identity across other institutions.
        """
        if not fingerprint:
            return []

        # Find other active enrolments associated with the same student identity in the same academic year
        other_enrolments = (
            db.query(StudentEnrolment)
            .join(StudentIdentity)
            .filter(
                StudentIdentity.protected_identity_fingerprint == fingerprint,
                StudentEnrolment.academic_year_id == academic_year_id,
                StudentEnrolment.institution_id != institution_id,
                StudentEnrolment.enrolment_status == EnrolmentStatus.ACTIVE,
            )
            .all()
        )

        findings = []
        if other_enrolments:
            # Create or link duplicate candidate group
            group = DuplicateCandidateGroup(
                rule_code="CROSS_INSTITUTION_DUPLICATE_CANDIDATE",
                match_type="EXACT_FINGERPRINT",
                status="PENDING_REVIEW",
                review_notes="Automated finding: multiple simultaneous active enrolments detected across distinct institutions.",
            )
            db.add(group)
            db.flush()

            # Add current student enrolment member
            db.add(
                DuplicateCandidateMember(
                    duplicate_group_id=group.id,
                    student_identity_id=current_identity_id,
                    student_enrolment_id=student_enrolment_id,
                    institution_id=institution_id,
                    match_confidence=1.0,
                )
            )

            matched_institutions = []
            for oe in other_enrolments:
                db.add(
                    DuplicateCandidateMember(
                        duplicate_group_id=group.id,
                        student_identity_id=oe.student_identity_id,
                        student_enrolment_id=oe.id,
                        institution_id=oe.institution_id,
                        match_confidence=1.0,
                    )
                )
                inst_name = oe.institution.name if oe.institution else f"Institution #{oe.institution_id}"
                matched_institutions.append({
                    "institution_id": oe.institution_id,
                    "institution_name": inst_name,
                    "enrolment_id": oe.id,
                    "student_id": oe.institution_student_id,
                    "admission_date": oe.admission_date.isoformat() if oe.admission_date else None,
                    "programme": oe.programme.programme_name if oe.programme else "Unknown",
                })

            db.commit()

            evidence = {
                "candidate_group_id": group.id,
                "masked_apaar_id": masked_apaar,
                "current_institution_id": institution_id,
                "matched_institutions": matched_institutions,
                "academic_year_id": academic_year_id,
                "rule_note": "A potential duplicate is a finding requiring investigation, not proof of wrongdoing.",
            }

            findings.append({
                "rule_code": "CROSS_INSTITUTION_DUPLICATE_CANDIDATE",
                "severity": IssueSeverity.HIGH,
                "title": f"Potential Concurrent Cross-Institution Enrolment ({masked_apaar})",
                "description": (
                    f"Student ({masked_apaar}) is actively enrolled in another institution for the same academic year. "
                    "Requires human review to verify transfer clearance or concurrent registration."
                ),
                "evidence_details": evidence,
                "duplicate_group_id": group.id,
            })

        return findings
