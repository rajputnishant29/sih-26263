from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


class EnrolmentStatus:
    ACTIVE = "ACTIVE"
    WITHDRAWN = "WITHDRAWN"
    CANCELLED = "CANCELLED"
    TRANSFERRED = "TRANSFERRED"


class SeatCategory:
    OPEN = "OPEN"
    OBC = "OBC"
    SC = "SC"
    ST = "ST"
    EWS = "EWS"
    TFW = "TFW"  # Tuition Fee Waiver
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class StudentIdentity(Base):
    """
    Separates student's academic identity from individual enrolment records.
    Stores protected identity fingerprint (keyed HMAC-SHA256) and masked APAAR reference.
    Raw student identifiers are never stored or logged in plain text.
    """
    __tablename__ = "student_identities"

    id = Column(Integer, primary_key=True, index=True)
    # Deterministic keyed HMAC-SHA256 fingerprint for safe deduplication across records
    protected_identity_fingerprint = Column(String(64), unique=True, index=True, nullable=False)
    # Masked presentation e.g. "APAAR-****-****-9482"
    masked_apaar_id = Column(String(30), nullable=False)
    # Encrypted envelope for authorized recovery (simulated)
    encrypted_identity_payload = Column(String(500), nullable=True)

    legal_name = Column(String(255), nullable=False, index=True)
    dob = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    primary_state = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    enrolments = relationship("StudentEnrolment", back_populates="student_identity")
    verification_evidence = relationship("IdentityVerificationEvidence", back_populates="student_identity")


class StudentEnrolment(Base):
    """
    Individual enrolment record at an institution and programme.
    A student may legitimately have multiple enrolment records over time (transfer, new degree, etc.).
    """
    __tablename__ = "student_enrolments"

    id = Column(Integer, primary_key=True, index=True)
    student_identity_id = Column(Integer, ForeignKey("student_identities.id", ondelete="CASCADE"), nullable=False, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    programme_id = Column(Integer, ForeignKey("programmes.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)

    institution_student_id = Column(String(100), nullable=False, index=True)  # e.g. "COEP-2026-CSE-012"
    admission_date = Column(Date, nullable=False)
    enrolment_status = Column(String(30), default=EnrolmentStatus.ACTIVE, nullable=False, index=True)

    seat_category = Column(String(50), default=SeatCategory.OPEN, nullable=False)
    is_nri = Column(Boolean, default=False, nullable=False)
    is_oci = Column(Boolean, default=False, nullable=False)
    is_fn = Column(Boolean, default=False, nullable=False)  # Foreign National

    is_supernumerary = Column(Boolean, default=False, nullable=False)
    supernumerary_type = Column(String(50), nullable=True)  # "TFW", "EWS", "PIO_FN_OCI"

    source_upload_batch_id = Column(Integer, ForeignKey("upload_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    # Explicit counting semantics: only eligible active records count toward reconciled enrolment
    is_eligible_enrolment = Column(Boolean, default=True, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    student_identity = relationship("StudentIdentity", back_populates="enrolments")
    institution = relationship("Institution", back_populates="enrolments")
    programme = relationship("Programme", back_populates="enrolments")
    academic_year = relationship("AcademicYear", back_populates="enrolments")
    upload_batch = relationship("UploadBatch")
    certificate_credentials = relationship("CertificateCredential", back_populates="student_enrolment")
    correction_histories = relationship("RecordCorrectionHistory", back_populates="student_enrolment")

    __table_args__ = (
        # Within an institution, the institution_student_id must be unique for an academic year
        UniqueConstraint("institution_id", "academic_year_id", "institution_student_id", name="uq_inst_ay_student_id"),
    )


class IdentityVerificationEvidence(Base):
    """
    Evidence of verification by external or simulated identity provider.
    """
    __tablename__ = "identity_verification_evidence"

    id = Column(Integer, primary_key=True, index=True)
    student_identity_id = Column(Integer, ForeignKey("student_identities.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(100), default="SIMULATED_APAAR_GATEWAY", nullable=False)
    verification_status = Column(String(50), default="VERIFIED_LOCAL", nullable=False)  # VERIFIED_LOCAL, NOT_FOUND, FURTHER_REVIEW
    verification_reference = Column(String(100), nullable=False, index=True)
    consent_reference = Column(String(100), nullable=True)
    verified_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata_payload = Column(JSON, nullable=True)

    student_identity = relationship("StudentIdentity", back_populates="verification_evidence")
