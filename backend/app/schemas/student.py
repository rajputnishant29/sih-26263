from typing import Optional, List, Any, Dict
from datetime import date, datetime
from pydantic import BaseModel


class CorrectionHistoryItem(BaseModel):
    id: int
    field_name: str
    original_value: Optional[str]
    corrected_value: Optional[str]
    actor_email: Optional[str]
    reason: str
    timestamp: datetime


class StudentEnrolmentListItem(BaseModel):
    id: int
    institution_id: int
    institution_name: str
    programme_id: int
    programme_name: str
    programme_code: str
    academic_year: str
    institution_student_id: str
    masked_apaar_id: str
    student_name: str
    admission_date: date
    enrolment_status: str
    seat_category: str
    is_nri: bool
    is_oci: bool
    is_fn: bool
    is_supernumerary: bool
    is_eligible_enrolment: bool
    has_validation_issue: bool = False

    class Config:
        from_attributes = True


class StudentEnrolmentDetail(BaseModel):
    id: int
    institution_id: int
    institution_name: str
    institution_code: str
    programme_id: int
    programme_name: str
    programme_code: str
    academic_year: str
    institution_student_id: str
    masked_apaar_id: str
    student_name: str
    dob: Optional[date] = None
    gender: Optional[str] = None
    admission_date: date
    enrolment_status: str
    seat_category: str
    is_nri: bool
    is_oci: bool
    is_fn: bool
    is_supernumerary: bool
    supernumerary_type: Optional[str] = None
    is_eligible_enrolment: bool
    source_upload_batch_id: Optional[int] = None
    correction_history: List[CorrectionHistoryItem] = []
    active_issues: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True


class EnrolmentCorrectionRequest(BaseModel):
    field_name: str
    new_value: Any
    reason: str
    source_reference: Optional[str] = None
