from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.audit import AuditEvent
from backend.app.models.user import User, UserRole
from backend.app.core.rbac import get_current_user, enforce_institution_scope
from backend.app.schemas.audit import AuditEventListItem

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Trail"])


@router.get("", response_model=List[AuditEventListItem])
def list_audit_logs(
    event_type: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    institution_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Searchable, append-only audit trail.
    Enforces that institutional actors can only inspect events in their scope.
    """
    scoped_inst_id = enforce_institution_scope(current_user, institution_id)

    query = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc())

    if scoped_inst_id:
        query = query.filter(AuditEvent.institution_id == scoped_inst_id)
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)
    if resource_type:
        query = query.filter(AuditEvent.resource_type == resource_type)

    events = query.limit(limit).all()
    results = []

    for ev in events:
        inst_name = ev.institution.name if ev.institution else None
        results.append(
            AuditEventListItem(
                id=ev.id,
                event_type=ev.event_type,
                actor_email=ev.actor_email,
                actor_role=ev.actor_role,
                institution_name=inst_name,
                resource_type=ev.resource_type,
                resource_id=ev.resource_id,
                action_outcome=ev.action_outcome,
                ip_address=ev.ip_address,
                event_details=ev.event_details,
                timestamp=ev.timestamp,
            )
        )

    return results
