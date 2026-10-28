import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from backend.app.models.student import StudentEnrolment
from backend.app.models.verification import CertificateCredential
from backend.app.models.user import User
from backend.app.models.audit import AuditEventType
from backend.app.services.audit_service import AuditService


class CertificateService:
    """
    Service for issuing and rendering verifiable student credentials and degree certificate previews.
    Explicitly represents the degree-awarding body and displays APAAR ID alongside Student ID.
    Always includes visible watermark 'NOT AN OFFICIAL CERTIFICATE — SYNTHETIC DEMO CREDENTIAL'.
    """

    @classmethod
    def get_or_create_certificate(
        cls,
        db: Session,
        enrolment_id: int,
        actor: Optional[User] = None,
    ) -> Dict[str, Any]:
        enrolment = db.query(StudentEnrolment).filter(StudentEnrolment.id == enrolment_id).first()
        if not enrolment:
            raise HTTPException(status_code=404, detail="Student enrolment record not found")

        identity = enrolment.student_identity
        cert = (
            db.query(CertificateCredential)
            .filter(CertificateCredential.student_enrolment_id == enrolment.id)
            .first()
        )

        if not cert:
            cert_no = f"CERT-{enrolment.academic_year.year_code[:4]}-{enrolment.id:05d}"
            slug = uuid.uuid4().hex[:16]

            # Resolve degree awarding body based on institution
            degree_awarding_body = "State Board of Technical Education & University"
            if "COEP" in enrolment.institution.name:
                degree_awarding_body = "COEP Technological University (Unitary Public University)"
            elif "Anna" in enrolment.institution.name or "Guindy" in enrolment.institution.name:
                degree_awarding_body = "Anna University, Chennai"
            elif "VJTI" in enrolment.institution.name:
                degree_awarding_body = "University of Mumbai (VJTI Autonomous)"

            degree_name = f"Bachelor of Technology in {enrolment.programme.programme_name}"

            cert = CertificateCredential(
                student_enrolment_id=enrolment.id,
                certificate_number=cert_no,
                degree_awarding_body=degree_awarding_body,
                degree_name=degree_name,
                grade_or_division="First Class with Distinction",
                issue_date=datetime.utcnow(),
                masked_apaar_id=identity.masked_apaar_id if identity else "APAAR-****-****-0000",
                student_id_ref=enrolment.institution_student_id,
                qr_verification_slug=slug,
            )
            db.add(cert)
            db.commit()
            db.refresh(cert)

            if actor:
                AuditService.log(
                    db=db,
                    event_type=AuditEventType.CERTIFICATE_GENERATED,
                    resource_type="CERTIFICATE_CREDENTIAL",
                    resource_id=cert.certificate_number,
                    actor=actor,
                    institution_id=enrolment.institution_id,
                    details={"certificate_number": cert.certificate_number, "slug": slug},
                )

        return {
            "certificate_number": cert.certificate_number,
            "degree_awarding_body": cert.degree_awarding_body,
            "institution_name": enrolment.institution.name,
            "institution_code": enrolment.institution.code,
            "student_name": identity.legal_name if identity else "Student Name",
            "student_id": cert.student_id_ref,
            "masked_apaar_id": cert.masked_apaar_id,
            "degree_name": cert.degree_name,
            "grade_or_division": cert.grade_or_division,
            "academic_year": enrolment.academic_year.year_code,
            "issue_date": cert.issue_date.strftime("%B %d, %Y"),
            "qr_verification_slug": cert.qr_verification_slug,
            "qr_verification_url": f"/verify/{cert.qr_verification_slug}",
            "is_revoked": cert.is_revoked,
            "watermark_text": "NOT AN OFFICIAL CERTIFICATE — SYNTHETIC DEMO CREDENTIAL",
            "disclaimer": "This preview demonstrates the EDUTrace verifiable student credential workflow for SIH 2026. Not a government-issued degree certificate.",
        }

    @classmethod
    def verify_by_slug(cls, db: Session, slug: str) -> Dict[str, Any]:
        """
        Public verification route resolved from QR code.
        """
        cert = (
            db.query(CertificateCredential)
            .filter(CertificateCredential.qr_verification_slug == slug)
            .first()
        )
        if not cert:
            return {
                "is_valid": False,
                "status": "CREDENTIAL_NOT_FOUND",
                "message": "Certificate reference not recognized in prototype repository.",
            }

        enrolment = cert.student_enrolment
        identity = enrolment.student_identity if enrolment else None

        return {
            "is_valid": not cert.is_revoked,
            "status": "VALID_PROTOTYPE_RECORD" if not cert.is_revoked else "REVOKED",
            "certificate_number": cert.certificate_number,
            "degree_awarding_body": cert.degree_awarding_body,
            "institution_name": enrolment.institution.name if enrolment else "",
            "student_name": identity.legal_name if identity else "",
            "student_id": cert.student_id_ref,
            "masked_apaar_id": cert.masked_apaar_id,
            "programme_name": cert.degree_name,
            "academic_year": enrolment.academic_year.year_code if enrolment else "",
            "issue_date": cert.issue_date.strftime("%Y-%m-%d"),
            "verification_provider": "EDUTrace Prototype Verifiable Registry",
        }
