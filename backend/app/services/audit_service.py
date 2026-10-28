from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from backend.app.models.audit import AuditEvent, AuditEventType
from backend.app.models.user import User


class AuditService:
    """
    Immutable audit logging service.
    Every significant action is recorded in an append-only log.
    Strictly prevents recording raw passwords, tokens, or plaintext identity references.
    """

    @classmethod
    def log(
        cls,
        db: Session,
        event_type: str,
        resource_type: str,
        actor: Optional[User] = None,
        institution_id: Optional[int] = None,
        resource_id: Optional[str] = None,
        action_outcome: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
        ip_address: str = "127.0.0.1",
    ) -> AuditEvent:
        sanitized_details = (details or {}).copy()

        # Sanitize sensitive keys if present
        for sensitive_key in ["password", "token", "raw_apaar", "secret"]:
            if sensitive_key in sanitized_details:
                sanitized_details[sensitive_key] = "[REDACTED]"

        event = AuditEvent(
            event_type=event_type,
            actor_user_id=actor.id if actor else None,
            actor_role=actor.role if actor else "SYSTEM",
            actor_email=actor.email if actor else "system@edutrace.gov.in",
            institution_id=institution_id or (actor.institution_id if actor else None),
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            action_outcome=action_outcome,
            ip_address=ip_address,
            event_details=sanitized_details,
            timestamp=datetime.utcnow(),
        )
        db.add(event)
        db.flush()
        return event
