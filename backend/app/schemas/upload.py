from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class UploadBatchSummary(BaseModel):
    id: int
    institution_id: int
    institution_name: Optional[str] = None
    programme_id: Optional[int] = None
    programme_name: Optional[str] = None
    academic_year: str
    file_name: str
    file_size: int
    row_count: int
    declared_count: int
    accepted_count: int
    rejected_count: int
    warning_count: int
    status: str
    uploaded_by_email: Optional[str] = None
    committed_by_email: Optional[str] = None
    committed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ValidationDryRunResponse(BaseModel):
    batch_id: int
    filename: str
    status: str
    total_rows: int
    valid_count: int
    warning_count: int
    error_count: int
    duration_ms: float
    intake_reconciliation: Dict[str, Any]
    declaration_reconciliation: Dict[str, Any]
    row_previews: List[Dict[str, Any]]


class CommitBatchResponse(BaseModel):
    batch_id: int
    status: str
    committed_enrolments_count: int
    issues_generated_count: int
    duplicate_candidates_flagged: int
    message: str
