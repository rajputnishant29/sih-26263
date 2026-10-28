from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class ValidationIssueListItem(BaseModel):
    id: int
    rule_code: str
    rule_version: str
    severity: str
    institution_id: int
    institution_name: str
    programme_name: Optional[str] = None
    academic_year: str
    title: str
    status: str
    assigned_to_email: Optional[str] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ValidationIssueDetail(BaseModel):
    id: int
    rule_code: str
    rule_version: str
    severity: str
    institution_id: int
    institution_name: str
    programme_id: Optional[int] = None
    programme_name: Optional[str] = None
    academic_year_id: int
    academic_year: str
    affected_student_enrolment_id: Optional[int] = None
    affected_student_id: Optional[str] = None
    affected_student_name: Optional[str] = None
    affected_masked_apaar: Optional[str] = None
    title: str
    description: str
    evidence_details: Dict[str, Any]
    status: str
    assigned_to_user_id: Optional[int] = None
    assigned_to_email: Optional[str] = None
    reviewer_notes: Optional[str] = None
    resolution_reason: Optional[str] = None
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    decision_history: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True


class IssueDecisionRequest(BaseModel):
    action: str  # ASSIGN, REQUEST_CORRECTION, CONFIRM_FINDING, MARK_FALSE_POSITIVE, RESOLVE, REOPEN
    reason: str
    notes: Optional[str] = None
    assigned_to_user_id: Optional[int] = None


class DuplicateCandidateGroupItem(BaseModel):
    id: int
    rule_code: str
    match_type: str
    status: str
    review_notes: Optional[str]
    created_at: datetime
    members: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True
