from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.app.models.validation import ValidationIssue, IssueStatus, DuplicateCandidateGroup
from backend.app.models.student import StudentEnrolment
from backend.app.models.review import ReviewDecision, RecordCorrectionHistory
from backend.app.models.user import User
from backend.app.models.audit import AuditEventType
from backend.app.services.audit_service import AuditService
from backend.app.core.sse import sse_manager


class ReviewService:
    """
    Actionable review queue and issue resolution service.
    Enforces human review before consequential decisions.
    Preserves original values, corrected values, actor, timestamp, reason, and complete decision history.
    """

    @classmethod
    def record_decision(
        cls,
        db: Session,
        issue_id: int,
        actor: User,
        action: str,  # "ASSIGN", "REQUEST_CORRECTION", "CONFIRM_FINDING", "MARK_FALSE_POSITIVE", "RESOLVE", "REOPEN"
        reason: str,
        notes: Optional[str] = None,
        assigned_to_user_id: Optional[int] = None,
    ) -> ValidationIssue:
        issue = db.query(ValidationIssue).filter(ValidationIssue.id == issue_id).first()
        if not issue:
            raise HTTPException(status_code=404, detail="Validation issue not found")

        prev_status = issue.status
        new_status = prev_status

        if action == "ASSIGN":
            new_status = IssueStatus.ASSIGNED
            issue.assigned_to_user_id = assigned_to_user_id or actor.id
        elif action == "REQUEST_CORRECTION":
            new_status = IssueStatus.CORRECTION_REQUESTED
        elif action == "CONFIRM_FINDING":
            new_status = "CONFIRMED"
        elif action == "MARK_FALSE_POSITIVE":
            new_status = IssueStatus.FALSE_POSITIVE
            issue.resolved_at = datetime.utcnow()
        elif action == "RESOLVE":
            new_status = IssueStatus.RESOLVED
            issue.resolved_at = datetime.utcnow()
        elif action == "REOPEN":
            new_status = IssueStatus.OPEN
            issue.resolved_at = None
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported review action '{action}'.",
            )

        issue.status = new_status
        issue.reviewer_notes = notes or issue.reviewer_notes
        issue.resolution_reason = reason

        # Log immutable ReviewDecision
        decision = ReviewDecision(
            validation_issue_id=issue.id,
            actor_user_id=actor.id,
            action=action,
            previous_status=prev_status,
            new_status=new_status,
            reason=reason,
            notes=notes,
            action_metadata={"actor_email": actor.email, "actor_role": actor.role},
            timestamp=datetime.utcnow(),
        )
        db.add(decision)
        db.commit()
        db.refresh(issue)

        AuditService.log(
            db=db,
            event_type=AuditEventType.ISSUE_STATUS_CHANGED,
            resource_type="VALIDATION_ISSUE",
            resource_id=str(issue.id),
            actor=actor,
            institution_id=issue.institution_id,
            details={"action": action, "prev_status": prev_status, "new_status": new_status, "reason": reason},
        )

        # Notify real-time clients
        sse_manager.broadcast(
            event="issue_updated",
            payload={"issue_id": issue.id, "new_status": new_status, "action": action},
        )

        return issue

    @classmethod
    def correct_student_record(
        cls,
        db: Session,
        enrolment_id: int,
        field_name: str,
        new_value: Any,
        reason: str,
        actor: User,
        source_reference: Optional[str] = None,
    ) -> StudentEnrolment:
        """
        Allows authorized users to correct permitted student enrolment fields.
        Preserves original values, actor, timestamp, reason, and source reference.
        """
        enrolment = db.query(StudentEnrolment).filter(StudentEnrolment.id == enrolment_id).first()
        if not enrolment:
            raise HTTPException(status_code=404, detail="Student enrolment record not found")

        # Check permission: AICTE Admin or belonging institution user
        if actor.role not in ["AICTE_ADMIN"] and enrolment.institution_id != actor.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security violation: You cannot correct records for another institution.",
            )

        if not hasattr(enrolment, field_name):
            raise HTTPException(status_code=400, detail=f"Field '{field_name}' does not exist on student enrolment")

        original_value = str(getattr(enrolment, field_name))

        # Update field
        setattr(enrolment, field_name, new_value)
        enrolment.updated_at = datetime.utcnow()

        # Record immutable correction history
        history = RecordCorrectionHistory(
            student_enrolment_id=enrolment.id,
            field_name=field_name,
            original_value=original_value,
            corrected_value=str(new_value),
            actor_user_id=actor.id,
            reason=reason,
            source_reference=source_reference or "MANUAL_REVIEW_CORRECTION",
            timestamp=datetime.utcnow(),
        )
        db.add(history)
        db.commit()
        db.refresh(enrolment)

        AuditService.log(
            db=db,
            event_type=AuditEventType.ENROLMENT_CORRECTED,
            resource_type="STUDENT_ENROLMENT",
            resource_id=str(enrolment.id),
            actor=actor,
            institution_id=enrolment.institution_id,
            details={
                "field": field_name,
                "original": original_value,
                "corrected": str(new_value),
                "reason": reason,
            },
        )

        sse_manager.broadcast(
            event="record_corrected",
            payload={"enrolment_id": enrolment.id, "field": field_name},
        )

        return enrolment
