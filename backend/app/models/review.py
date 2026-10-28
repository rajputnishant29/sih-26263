from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id = Column(Integer, primary_key=True, index=True)
    validation_issue_id = Column(Integer, ForeignKey("validation_issues.id", ondelete="CASCADE"), nullable=True, index=True)
    duplicate_group_id = Column(Integer, ForeignKey("duplicate_candidate_groups.id", ondelete="CASCADE"), nullable=True, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    action = Column(String(50), nullable=False)  # ASSIGN, REQUEST_CORRECTION, CONFIRM_FINDING, MARK_FALSE_POSITIVE, RESOLVE, REOPEN
    previous_status = Column(String(50), nullable=False)
    new_status = Column(String(50), nullable=False)
    reason = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    action_metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    validation_issue = relationship("ValidationIssue", back_populates="review_decisions")
    duplicate_group = relationship("DuplicateCandidateGroup", back_populates="review_decisions")
    actor = relationship("User")


class RecordCorrectionHistory(Base):
    __tablename__ = "record_correction_histories"

    id = Column(Integer, primary_key=True, index=True)
    student_enrolment_id = Column(Integer, ForeignKey("student_enrolments.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    original_value = Column(Text, nullable=True)
    corrected_value = Column(Text, nullable=True)
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reason = Column(Text, nullable=False)
    source_reference = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    student_enrolment = relationship("StudentEnrolment", back_populates="correction_histories")
    actor = relationship("User")
