from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)  # AICTE permanent institute ID
    name = Column(String(255), nullable=False)
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=True)
    institution_type = Column(String(100), default="Government / Autonomous", nullable=False)
    address = Column(Text, nullable=True)
    contact_email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    users = relationship("User", back_populates="institution")
    programmes = relationship("Programme", back_populates="institution", cascade="all, delete-orphan")
    source_documents = relationship("SourceDocument", back_populates="institution")
    approval_intakes = relationship("ApprovalIntake", back_populates="institution")
    enrolments = relationship("StudentEnrolment", back_populates="institution")
    upload_batches = relationship("UploadBatch", back_populates="institution")


class Programme(Base):
    __tablename__ = "programmes"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    programme_code = Column(String(50), nullable=False)
    programme_name = Column(String(255), nullable=False)
    degree_level = Column(String(50), default="UG", nullable=False)  # UG, PG, Diploma
    department = Column(String(100), nullable=False)
    duration_years = Column(Integer, default=4, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    institution = relationship("Institution", back_populates="programmes")
    approval_intakes = relationship("ApprovalIntake", back_populates="programme")
    enrolments = relationship("StudentEnrolment", back_populates="programme")

    __table_args__ = (
        UniqueConstraint("institution_id", "programme_code", name="uq_institution_programme_code"),
    )


class AcademicYear(Base):
    __tablename__ = "academic_years"

    id = Column(Integer, primary_key=True, index=True)
    year_code = Column(String(20), unique=True, index=True, nullable=False)  # e.g., "2026-27"
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_current = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    approval_intakes = relationship("ApprovalIntake", back_populates="academic_year")
    enrolments = relationship("StudentEnrolment", back_populates="academic_year")


class SourceDocument(Base):
    __tablename__ = "source_documents"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    document_type = Column(String(50), default="AICTE_EOA_PDF", nullable=False)  # AICTE_EOA_PDF, INSTITUTION_CSV, MANUAL_REGISTRATION
    reference_number = Column(String(100), nullable=False, index=True)  # Official Letter / EoA Ref No
    document_url = Column(String(500), nullable=True)
    publication_date = Column(DateTime, nullable=True)
    extraction_status = Column(String(50), default="CONFIRMED", nullable=False)  # PENDING_CONFIRMATION, CONFIRMED, REJECTED
    extraction_confidence = Column(Float, default=1.0, nullable=False)
    raw_extracted_data = Column(JSON, nullable=True)
    confirmed_by = Column(String(100), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    institution = relationship("Institution", back_populates="source_documents")
    academic_year = relationship("AcademicYear")
    approval_intakes = relationship("ApprovalIntake", back_populates="source_document")


class ApprovalIntake(Base):
    """
    Approved intake associated with institution, programme, and academic year.
    Stored as programme-level approval metadata, not as a repeated value in student records.
    """
    __tablename__ = "approval_intakes"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    programme_id = Column(Integer, ForeignKey("programmes.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    source_document_id = Column(Integer, ForeignKey("source_documents.id", ondelete="SET NULL"), nullable=True, index=True)

    base_approved_intake = Column(Integer, nullable=False)  # Base EoA sanctioned intake (e.g. 120)
    supernumerary_seats = Column(Integer, default=0, nullable=False)  # Authorized supernumerary (TFW, EWS, PIO/FN)
    nri_quota = Column(Integer, default=0, nullable=False)  # NRI allocation
    fn_quota = Column(Integer, default=0, nullable=False)   # Foreign National allocation
    oci_quota = Column(Integer, default=0, nullable=False)  # OCI allocation
    effective_intake_limit = Column(Integer, nullable=False)  # Calculated effective limit under cited rule

    rule_version = Column(String(50), default="AICTE_APH_2026_V1", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    institution = relationship("Institution", back_populates="approval_intakes")
    programme = relationship("Programme", back_populates="approval_intakes")
    academic_year = relationship("AcademicYear", back_populates="approval_intakes")
    source_document = relationship("SourceDocument", back_populates="approval_intakes")

    __table_args__ = (
        UniqueConstraint("institution_id", "programme_id", "academic_year_id", name="uq_inst_prog_ay_intake"),
    )
