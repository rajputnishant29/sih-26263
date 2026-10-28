from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship
from backend.app.database import Base


class AuditEventType:
    AUTH_LOGIN = "AUTH_LOGIN"
    AUTH_LOGOUT = "AUTH_LOGOUT"
    FILE_UPLOAD_STAGED = "FILE_UPLOAD_STAGED"
    FILE_VALIDATION_RUN = "FILE_VALIDATION_RUN"
    RECORDS_COMMITTED = "RECORDS_COMMITTED"
    ENROLMENT_CORRECTED = "ENROLMENT_CORRECTED"
    ISSUE_STATUS_CHANGED = "ISSUE_STATUS_CHANGED"
    ISSUE_ASSIGNED = "ISSUE_ASSIGNED"
    VERIFICATION_REQUESTED = "VERIFICATION_REQUESTED"
    CERTIFICATE_GENERATED = "CERTIFICATE_GENERATED"
    REPORT_EXPORTED = "REPORT_EXPORTED"
    EOA_DOCUMENT_CONFIRMED = "EOA_DOCUMENT_CONFIRMED"
    PERMISSION_CHANGED = "PERMISSION_CHANGED"


class AuditEvent(Base):
    """
    Append-only immutable audit trail.
    Does NOT store raw passwords, tokens, or plaintext identity references.
    """
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_role = Column(String(50), nullable=False)
    actor_email = Column(String(255), nullable=True)
    institution_id = Column(Integer, ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True, index=True)

    resource_type = Column(String(50), nullable=False, index=True)  # "UPLOAD_BATCH", "STUDENT_ENROLMENT", "VALIDATION_ISSUE", etc.
    resource_id = Column(String(100), nullable=True)
    action_outcome = Column(String(20), default="SUCCESS", nullable=False)  # SUCCESS, FAILURE, DENIED
    ip_address = Column(String(45), default="127.0.0.1", nullable=False)
    event_details = Column(JSON, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    actor = relationship("User")
    institution = relationship("Institution")
