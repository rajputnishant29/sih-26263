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
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


class UploadStatus:
    STAGED = "STAGED"
    VALIDATED = "VALIDATED"
    COMMITTED = "COMMITTED"
    REJECTED = "REJECTED"


class UploadBatch(Base):
    __tablename__ = "upload_batches"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False, index=True)
    programme_id = Column(Integer, ForeignKey("programmes.id", ondelete="SET NULL"), nullable=True, index=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)

    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256 to prevent duplicate upload submissions
    row_count = Column(Integer, default=0, nullable=False)
    declared_count = Column(Integer, default=0, nullable=False)  # Declared total submitted by institution
    accepted_count = Column(Integer, default=0, nullable=False)
    rejected_count = Column(Integer, default=0, nullable=False)
    warning_count = Column(Integer, default=0, nullable=False)

    status = Column(String(50), default=UploadStatus.STAGED, nullable=False, index=True)

    uploaded_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    committed_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    committed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    institution = relationship("Institution", back_populates="upload_batches")
    programme = relationship("Programme")
    academic_year = relationship("AcademicYear")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_user_id])
    committed_by = relationship("User", foreign_keys=[committed_by_user_id])

    staging_rows = relationship("UploadStagingRow", back_populates="upload_batch", cascade="all, delete-orphan")
    validation_runs = relationship("ValidationRun", back_populates="upload_batch", cascade="all, delete-orphan")
    issues = relationship("ValidationIssue", back_populates="upload_batch")


class UploadStagingRow(Base):
    __tablename__ = "upload_staging_rows"

    id = Column(Integer, primary_key=True, index=True)
    upload_batch_id = Column(Integer, ForeignKey("upload_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    raw_data = Column(JSON, nullable=False)
    normalized_data = Column(JSON, nullable=True)
    validation_status = Column(String(30), default="VALID", nullable=False)  # VALID, WARNING, ERROR
    validation_messages = Column(JSON, default=list, nullable=False)
    is_accepted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    upload_batch = relationship("UploadBatch", back_populates="staging_rows")


class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id = Column(Integer, primary_key=True, index=True)
    upload_batch_id = Column(Integer, ForeignKey("upload_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    run_type = Column(String(50), default="DRY_RUN", nullable=False)  # DRY_RUN, COMMIT_RUN
    total_checked = Column(Integer, default=0, nullable=False)
    issues_count = Column(Integer, default=0, nullable=False)
    run_duration_ms = Column(Float, default=0.0, nullable=False)
    summary_metrics = Column(JSON, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    upload_batch = relationship("UploadBatch", back_populates="validation_runs")
    issues = relationship("ValidationIssue", back_populates="validation_run")
