from datetime import datetime, timedelta
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base


class VerificationRequest(Base):
    """
    Purpose-bound verification request submitted by authorized institutions, employers, or regulators.
    Maintains consent reference, purpose limitation, authorization checks, and audit history.
    """
    __tablename__ = "verification_requests"

    id = Column(Integer, primary_key=True, index=True)
    requester_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    requester_organization = Column(String(255), nullable=False)
    verification_type = Column(String(50), default="STUDENT_ENROLMENT_RECORD", nullable=False)  # STUDENT_ENROLMENT_RECORD, CERTIFICATE_CREDENTIAL
    target_identity_ref = Column(String(100), nullable=False)  # Student ID or verification query ref
    purpose = Column(String(255), nullable=False)  # e.g., "Employment Background Verification", "Regulatory Audit"
    consent_proof_reference = Column(String(255), nullable=False)  # e.g., "CANDIDATE-CONSENT-REF-2026-X89"

    authorization_status = Column(String(50), default="AUTHORIZED", nullable=False)  # AUTHORIZED, UNAUTHORIZED, EXPIRED
    verification_status = Column(String(50), default="VERIFIED_LOCAL", nullable=False)  # VERIFIED_LOCAL, RECORD_NOT_FOUND, FURTHER_REVIEW_REQUIRED
    result_payload = Column(JSON, nullable=False)  # Permitted claims only (institution, programme, academic year, status)

    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_until = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=30), nullable=False)

    requester = relationship("User")


class CertificateCredential(Base):
    """
    Verifiable student record and degree certificate credentials.
    Explicitly represents degree-awarding body, student ID, and APAAR ID side-by-side.
    """
    __tablename__ = "certificate_credentials"

    id = Column(Integer, primary_key=True, index=True)
    student_enrolment_id = Column(Integer, ForeignKey("student_enrolments.id", ondelete="CASCADE"), nullable=False, index=True)
    certificate_number = Column(String(100), unique=True, index=True, nullable=False)
    degree_awarding_body = Column(String(255), nullable=False)  # e.g. "Savitribai Phule Pune University" or "Anna University"
    degree_name = Column(String(255), nullable=False)  # e.g. "Bachelor of Technology in Computer Science and Engineering"
    grade_or_division = Column(String(50), default="First Class with Distinction", nullable=False)
    issue_date = Column(DateTime, nullable=False)

    masked_apaar_id = Column(String(30), nullable=False)
    student_id_ref = Column(String(100), nullable=False)
    qr_verification_slug = Column(String(64), unique=True, index=True, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    student_enrolment = relationship("StudentEnrolment", back_populates="certificate_credentials")
