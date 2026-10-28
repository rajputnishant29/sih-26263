from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database import get_db
from backend.app.models.institution import Institution, Programme, AcademicYear, ApprovalIntake
from backend.app.models.student import StudentEnrolment, EnrolmentStatus
from backend.app.models.validation import ValidationIssue, DuplicateCandidateGroup, IssueStatus, IssueSeverity
from backend.app.models.user import User, UserRole
from backend.app.core.rbac import get_current_user, enforce_institution_scope
from backend.app.core.sse import sse_manager
from backend.app.schemas.dashboard import (
    DashboardSummaryResponse,
    ProgrammeReconciliationItem,
    CategoryDistributionItem,
    AcademicYearTrendItem,
    ExceptionDistributionItem,
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    academic_year_id: Optional[int] = Query(None),
    institution_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Computes dashboard KPIs and visualizations directly from persisted database models.
    Enforces institutional scope so institution users only see their own metrics.
    """
    scoped_inst_id = enforce_institution_scope(current_user, institution_id)

    # 1. Base counts
    inst_query = db.query(Institution).filter(Institution.is_active == True)
    if scoped_inst_id:
        inst_query = inst_query.filter(Institution.id == scoped_inst_id)
    institutions_count = inst_query.count()

    prog_query = db.query(Programme)
    if scoped_inst_id:
        prog_query = prog_query.filter(Programme.institution_id == scoped_inst_id)
    programmes_count = prog_query.count()

    # 2. Approved Intake Total
    approval_query = db.query(
        func.sum(ApprovalIntake.base_approved_intake),
        func.sum(ApprovalIntake.supernumerary_seats),
        func.sum(ApprovalIntake.effective_intake_limit),
    ).filter(ApprovalIntake.is_active == True)

    if scoped_inst_id:
        approval_query = approval_query.filter(ApprovalIntake.institution_id == scoped_inst_id)
    if academic_year_id:
        approval_query = approval_query.filter(ApprovalIntake.academic_year_id == academic_year_id)

    base_intake_sum, supernumerary_seats_sum, effective_limit_sum = approval_query.first()
    approved_intake_total = base_intake_sum or 0
    supernumerary_seats_total = supernumerary_seats_sum or 0
    effective_limit_total = effective_limit_sum or (approved_intake_total + supernumerary_seats_total)

    # 3. Actual Enrolment Total (Only ACTIVE eligible records count)
    enrolment_query = db.query(func.count(StudentEnrolment.id)).filter(
        StudentEnrolment.enrolment_status == EnrolmentStatus.ACTIVE,
        StudentEnrolment.is_eligible_enrolment == True,
    )
    if scoped_inst_id:
        enrolment_query = enrolment_query.filter(StudentEnrolment.institution_id == scoped_inst_id)
    if academic_year_id:
        enrolment_query = enrolment_query.filter(StudentEnrolment.academic_year_id == academic_year_id)

    actual_enrolment_total = enrolment_query.scalar() or 0

    # 4. Supernumerary Enrolled Count
    supernumerary_enrolled_query = db.query(func.count(StudentEnrolment.id)).filter(
        StudentEnrolment.enrolment_status == EnrolmentStatus.ACTIVE,
        StudentEnrolment.is_supernumerary == True,
    )
    if scoped_inst_id:
        supernumerary_enrolled_query = supernumerary_enrolled_query.filter(StudentEnrolment.institution_id == scoped_inst_id)
    if academic_year_id:
        supernumerary_enrolled_query = supernumerary_enrolled_query.filter(StudentEnrolment.academic_year_id == academic_year_id)

    supernumerary_enrolled_total = supernumerary_enrolled_query.scalar() or 0

    # Remaining capacity & utilization
    remaining_capacity_total = max(0, effective_limit_total - actual_enrolment_total)
    intake_utilization_rate = (
        round((actual_enrolment_total / effective_limit_total * 100), 2)
        if effective_limit_total > 0
        else 0.0
    )

    # 5. Unresolved issues
    issue_query = db.query(ValidationIssue).filter(
        ValidationIssue.status.in_([IssueStatus.OPEN, IssueStatus.ASSIGNED, IssueStatus.CORRECTION_REQUESTED])
    )
    if scoped_inst_id:
        issue_query = issue_query.filter(ValidationIssue.institution_id == scoped_inst_id)
    if academic_year_id:
        issue_query = issue_query.filter(ValidationIssue.academic_year_id == academic_year_id)

    unresolved_issues_count = issue_query.count()
    critical_issues_count = issue_query.filter(ValidationIssue.severity == IssueSeverity.CRITICAL).count()

    # 6. Duplicate candidates awaiting review
    dup_query = db.query(DuplicateCandidateGroup).filter(
        DuplicateCandidateGroup.status == "PENDING_REVIEW"
    )
    duplicate_candidates_count = dup_query.count()

    # 7. Programme reconciliations
    prog_reconciliations = []
    approvals_list_query = (
        db.query(ApprovalIntake)
        .join(Institution)
        .join(Programme)
        .join(AcademicYear)
        .filter(ApprovalIntake.is_active == True)
    )
    if scoped_inst_id:
        approvals_list_query = approvals_list_query.filter(ApprovalIntake.institution_id == scoped_inst_id)
    if academic_year_id:
        approvals_list_query = approvals_list_query.filter(ApprovalIntake.academic_year_id == academic_year_id)

    for app in approvals_list_query.all():
        active_count = (
            db.query(func.count(StudentEnrolment.id))
            .filter(
                StudentEnrolment.institution_id == app.institution_id,
                StudentEnrolment.programme_id == app.programme_id,
                StudentEnrolment.academic_year_id == app.academic_year_id,
                StudentEnrolment.enrolment_status == EnrolmentStatus.ACTIVE,
                StudentEnrolment.is_eligible_enrolment == True,
            )
            .scalar()
            or 0
        )
        super_count = (
            db.query(func.count(StudentEnrolment.id))
            .filter(
                StudentEnrolment.institution_id == app.institution_id,
                StudentEnrolment.programme_id == app.programme_id,
                StudentEnrolment.academic_year_id == app.academic_year_id,
                StudentEnrolment.is_supernumerary == True,
            )
            .scalar()
            or 0
        )
        limit = app.effective_intake_limit
        prog_reconciliations.append(
            ProgrammeReconciliationItem(
                institution_id=app.institution_id,
                institution_name=app.institution.name,
                programme_id=app.programme_id,
                programme_name=app.programme.programme_name,
                programme_code=app.programme.programme_code,
                academic_year=app.academic_year.year_code,
                base_approved_intake=app.base_approved_intake,
                supernumerary_sanctioned=app.supernumerary_seats,
                effective_limit=limit,
                calculated_enrolment=active_count,
                supernumerary_enrolled=super_count,
                variance=active_count - limit,
                utilization_rate=round((active_count / limit * 100), 1) if limit > 0 else 0.0,
                is_exceeded=active_count > limit,
                source_eoa_reference=app.source_document.reference_number if app.source_document else "MANUAL",
                rule_version=app.rule_version,
            )
        )

    # 8. Category distributions
    cat_query = db.query(
        StudentEnrolment.seat_category, func.count(StudentEnrolment.id)
    ).filter(StudentEnrolment.enrolment_status == EnrolmentStatus.ACTIVE)
    if scoped_inst_id:
        cat_query = cat_query.filter(StudentEnrolment.institution_id == scoped_inst_id)
    if academic_year_id:
        cat_query = cat_query.filter(StudentEnrolment.academic_year_id == academic_year_id)

    cat_counts = cat_query.group_by(StudentEnrolment.seat_category).all()
    total_cats = sum(c[1] for c in cat_counts) or 1
    category_distributions = [
        CategoryDistributionItem(
            category=c[0],
            count=c[1],
            percentage=round((c[1] / total_cats * 100), 1),
        )
        for c in cat_counts
    ]

    # 9. Academic year trends
    ay_list = db.query(AcademicYear).order_by(AcademicYear.start_date).all()
    academic_year_trends = []
    for ay in ay_list:
        ay_intake = (
            db.query(func.sum(ApprovalIntake.effective_intake_limit))
            .filter(ApprovalIntake.academic_year_id == ay.id)
            .scalar()
            or 0
        )
        ay_enrolment = (
            db.query(func.count(StudentEnrolment.id))
            .filter(
                StudentEnrolment.academic_year_id == ay.id,
                StudentEnrolment.enrolment_status == EnrolmentStatus.ACTIVE,
            )
            .scalar()
            or 0
        )
        rate = round((ay_enrolment / ay_intake * 100), 1) if ay_intake > 0 else 0.0
        academic_year_trends.append(
            AcademicYearTrendItem(
                academic_year=ay.year_code,
                approved_intake=ay_intake,
                actual_enrolment=ay_enrolment,
                utilization_rate=rate,
            )
        )

    # 10. Exception distributions
    exc_query = db.query(
        ValidationIssue.rule_code, ValidationIssue.severity, func.count(ValidationIssue.id)
    )
    if scoped_inst_id:
        exc_query = exc_query.filter(ValidationIssue.institution_id == scoped_inst_id)
    if academic_year_id:
        exc_query = exc_query.filter(ValidationIssue.academic_year_id == academic_year_id)

    exc_counts = exc_query.group_by(ValidationIssue.rule_code, ValidationIssue.severity).all()
    exception_distributions = [
        ExceptionDistributionItem(rule_code=e[0], severity=e[1], count=e[2])
        for e in exc_counts
    ]

    return DashboardSummaryResponse(
        institutions_count=institutions_count,
        programmes_count=programmes_count,
        approved_intake_total=approved_intake_total,
        actual_enrolment_total=actual_enrolment_total,
        supernumerary_seats_total=supernumerary_seats_total,
        supernumerary_enrolled_total=supernumerary_enrolled_total,
        remaining_capacity_total=remaining_capacity_total,
        intake_utilization_rate=intake_utilization_rate,
        unresolved_issues_count=unresolved_issues_count,
        critical_issues_count=critical_issues_count,
        duplicate_candidates_count=duplicate_candidates_count,
        programme_reconciliations=prog_reconciliations,
        category_distributions=category_distributions,
        academic_year_trends=academic_year_trends,
        exception_distributions=exception_distributions,
        is_synthetic_data=True,
    )


@router.get("/events")
async def sse_dashboard_events(request: Request):
    """
    Server-Sent Events endpoint streaming real-time dashboard events.
    """
    return sse_manager.as_response(request)
