from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ProgrammeReconciliationItem(BaseModel):
    institution_id: int
    institution_name: str
    programme_id: int
    programme_name: str
    programme_code: str
    academic_year: str
    base_approved_intake: int
    supernumerary_sanctioned: int
    effective_limit: int
    calculated_enrolment: int
    supernumerary_enrolled: int
    variance: int
    utilization_rate: float
    is_exceeded: bool
    source_eoa_reference: str
    rule_version: str


class CategoryDistributionItem(BaseModel):
    category: str
    count: int
    percentage: float


class AcademicYearTrendItem(BaseModel):
    academic_year: str
    approved_intake: int
    actual_enrolment: int
    utilization_rate: float


class ExceptionDistributionItem(BaseModel):
    rule_code: str
    severity: str
    count: int


class DashboardSummaryResponse(BaseModel):
    institutions_count: int
    programmes_count: int
    approved_intake_total: int
    actual_enrolment_total: int
    supernumerary_seats_total: int
    supernumerary_enrolled_total: int
    remaining_capacity_total: int
    intake_utilization_rate: float
    unresolved_issues_count: int
    critical_issues_count: int
    duplicate_candidates_count: int

    programme_reconciliations: List[ProgrammeReconciliationItem]
    category_distributions: List[CategoryDistributionItem]
    academic_year_trends: List[AcademicYearTrendItem]
    exception_distributions: List[ExceptionDistributionItem]

    is_synthetic_data: bool = True
    disclaimer: str = (
        "Illustrative synthetic prototype data. These figures are not official AICTE statistics. "
        "Official APAAR verification and institutional integrations are not enabled unless explicitly demonstrated."
    )
