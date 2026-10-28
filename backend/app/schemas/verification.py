from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class VerificationSubmitRequest(BaseModel):
    query_identifier: str  # Student ID or APAAR ID reference
    requester_organization: str
    purpose: str
    consent_proof_ref: str


class VerificationResultResponse(BaseModel):
    verification_status: str
    verification_provider: str
    student_name: Optional[str] = None
    student_id: Optional[str] = None
    masked_apaar_id: Optional[str] = None
    institution_name: Optional[str] = None
    institution_code: Optional[str] = None
    programme_name: Optional[str] = None
    programme_code: Optional[str] = None
    academic_year: Optional[str] = None
    enrolment_status: Optional[str] = None
    admission_date: Optional[str] = None
    is_eligible_enrolment: Optional[bool] = None
    verification_reference: Optional[str] = None
    timestamp: str
    disclaimer: Optional[str] = None
    message: Optional[str] = None


class CertificatePreviewResponse(BaseModel):
    certificate_number: str
    degree_awarding_body: str
    institution_name: str
    institution_code: str
    student_name: str
    student_id: str
    masked_apaar_id: str
    degree_name: str
    grade_or_division: str
    academic_year: str
    issue_date: str
    qr_verification_slug: str
    qr_verification_url: str
    is_revoked: bool
    watermark_text: str
    disclaimer: str
