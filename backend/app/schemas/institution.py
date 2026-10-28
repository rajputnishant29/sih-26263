from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class ProgrammeSummary(BaseModel):
    id: int
    programme_code: str
    programme_name: str
    degree_level: str
    department: str
    duration_years: int

    class Config:
        from_attributes = True


class ApprovalIntakeSummary(BaseModel):
    id: int
    programme_id: int
    programme_name: Optional[str] = None
    academic_year_id: int
    academic_year: Optional[str] = None
    base_approved_intake: int
    supernumerary_seats: int
    effective_intake_limit: int
    calculated_enrolment: Optional[int] = 0
    utilization_rate: Optional[float] = 0.0
    rule_version: str
    source_reference: Optional[str] = None

    class Config:
        from_attributes = True


class InstitutionDetail(BaseModel):
    id: int
    code: str
    name: str
    state: str
    district: Optional[str] = None
    institution_type: str
    address: Optional[str] = None
    contact_email: Optional[str] = None
    programmes_count: int = 0
    total_approved_intake: int = 0
    total_actual_enrolment: int = 0
    open_issues_count: int = 0
    programmes: List[ProgrammeSummary] = []

    class Config:
        from_attributes = True


class AcademicYearResponse(BaseModel):
    id: int
    year_code: str
    is_current: bool

    class Config:
        from_attributes = True


class SourceDocumentResponse(BaseModel):
    id: int
    institution_id: int
    institution_name: Optional[str] = None
    academic_year_id: int
    academic_year: Optional[str] = None
    document_type: str
    reference_number: str
    document_url: Optional[str] = None
    publication_date: Optional[datetime] = None
    extraction_status: str
    extraction_confidence: float
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
