from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database import get_db
from backend.app.models.institution import Institution, Programme, ApprovalIntake
from backend.app.models.student import StudentEnrolment, EnrolmentStatus
from backend.app.models.validation import ValidationIssue, IssueStatus
from backend.app.models.user import User, UserRole
from backend.app.core.rbac import get_current_user, enforce_institution_scope
from backend.app.schemas.institution import InstitutionDetail, ProgrammeSummary

router = APIRouter(prefix="/api/institutions", tags=["Institutions"])


@router.get("", response_model=List[InstitutionDetail])
def list_institutions(
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Institution).filter(Institution.is_active == True)

    # Institutional isolation
    if current_user.role in [UserRole.INSTITUTION_ADMIN, UserRole.INSTITUTION_DATA_OPERATOR]:
        query = query.filter(Institution.id == current_user.institution_id)

    if search:
        s = f"%{search}%"
        query = query.filter((Institution.name.ilike(s)) | (Institution.code.ilike(s)) | (Institution.state.ilike(s)))

    institutions = query.order_by(Institution.name).all()
    results = []

    for inst in institutions:
        prog_count = db.query(Programme).filter(Programme.institution_id == inst.id).count()
        total_intake = (
            db.query(func.sum(ApprovalIntake.effective_intake_limit))
            .filter(ApprovalIntake.institution_id == inst.id)
            .scalar()
            or 0
        )
        total_enrolled = (
            db.query(func.count(StudentEnrolment.id))
            .filter(
                StudentEnrolment.institution_id == inst.id,
                StudentEnrolment.enrolment_status == EnrolmentStatus.ACTIVE,
            )
            .scalar()
            or 0
        )
        open_issues = (
            db.query(func.count(ValidationIssue.id))
            .filter(
                ValidationIssue.institution_id == inst.id,
                ValidationIssue.status.in_([IssueStatus.OPEN, IssueStatus.ASSIGNED, IssueStatus.CORRECTION_REQUESTED]),
            )
            .scalar()
            or 0
        )

        programmes = [
            ProgrammeSummary(
                id=p.id,
                programme_code=p.programme_code,
                programme_name=p.programme_name,
                degree_level=p.degree_level,
                department=p.department,
                duration_years=p.duration_years,
            )
            for p in inst.programmes
        ]

        results.append(
            InstitutionDetail(
                id=inst.id,
                code=inst.code,
                name=inst.name,
                state=inst.state,
                district=inst.district,
                institution_type=inst.institution_type,
                address=inst.address,
                contact_email=inst.contact_email,
                programmes_count=prog_count,
                total_approved_intake=total_intake,
                total_actual_enrolment=total_enrolled,
                open_issues_count=open_issues,
                programmes=programmes,
            )
        )

    return results


@router.get("/{institution_id}", response_model=InstitutionDetail)
def get_institution(
    institution_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_institution_scope(current_user, institution_id)
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    prog_count = db.query(Programme).filter(Programme.institution_id == inst.id).count()
    total_intake = (
        db.query(func.sum(ApprovalIntake.effective_intake_limit))
        .filter(ApprovalIntake.institution_id == inst.id)
        .scalar()
        or 0
    )
    total_enrolled = (
        db.query(func.count(StudentEnrolment.id))
        .filter(
            StudentEnrolment.institution_id == inst.id,
            StudentEnrolment.enrolment_status == EnrolmentStatus.ACTIVE,
        )
        .scalar()
        or 0
    )
    open_issues = (
        db.query(func.count(ValidationIssue.id))
        .filter(
            ValidationIssue.institution_id == inst.id,
            ValidationIssue.status.in_([IssueStatus.OPEN, IssueStatus.ASSIGNED, IssueStatus.CORRECTION_REQUESTED]),
        )
        .scalar()
        or 0
    )

    programmes = [
        ProgrammeSummary(
            id=p.id,
            programme_code=p.programme_code,
            programme_name=p.programme_name,
            degree_level=p.degree_level,
            department=p.department,
            duration_years=p.duration_years,
        )
        for p in inst.programmes
    ]

    return InstitutionDetail(
        id=inst.id,
        code=inst.code,
        name=inst.name,
        state=inst.state,
        district=inst.district,
        institution_type=inst.institution_type,
        address=inst.address,
        contact_email=inst.contact_email,
        programmes_count=prog_count,
        total_approved_intake=total_intake,
        total_actual_enrolment=total_enrolled,
        open_issues_count=open_issues,
        programmes=programmes,
    )
