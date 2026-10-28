from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class AuditEventListItem(BaseModel):
    id: int
    event_type: str
    actor_email: Optional[str]
    actor_role: str
    institution_name: Optional[str] = None
    resource_type: str
    resource_id: Optional[str]
    action_outcome: str
    ip_address: str
    event_details: Dict[str, Any]
    timestamp: datetime

    class Config:
        from_attributes = True
