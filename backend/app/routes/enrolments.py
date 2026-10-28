from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.student import StudentEnrolment, StudentIdentity
from backend.app.models.validation import ValidationIssue, IssueStatus
from backend.app.models.user import User, UserRole
from backend.app.core.rbac import get_current_user, enforce_institution_scope
from backend.app.services.review_service import ReviewService
from backend.app.schemas.student import (
    StudentEnrolmentListItem,
    StudentEnrolmentDetail,
    EnrolmentCorrectionRequest,
    CorrectionHistoryItem,
)

router = APIRouter(prefix="/api/enrolments", tags=["Student Enrolments"])


@router.get("", response_model=Dict[str, Any])
def list_enrolments(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    institution_id: Optional[int] = Query(None),
    programme_id: Optional[int] = Query(None),
    academic_year_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    seat_category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scoped_inst_id = enforce_institution_scope(current_user, institution_id)

    query = (
        db.query(StudentEnrolment)
        .join(StudentIdentity)
    )

    if scoped_inst_id:
        query = query.filter(StudentEnrolment.institution_id == scoped_inst_id)
    if programme_id:
        query = query.filter(StudentEnrolment.programme_id == programme_id)
    if academic_year_id:
        query = query.filter(StudentEnrolment.academic_year_id == academic_year_id)
    if status:
        query = query.filter(StudentEnrolment.enrolment_status == status)
    if seat_category:
        query = query.filter(StudentEnrolment.seat_category == seat_category)
    if search:
        s = f"%{search}%"
        query = query.filter(
            (StudentEnrolment.institution_student_id.ilike(s)) |
            (StudentIdentity.legal_name.ilike(s))
        )

    total_count = query.count()
    enrolments = (
        query.order_by(StudentEnrolment.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    items = []
    for e in enrolments:
        ident = e.student_identity
        has_issue = (
            db.query(ValidationIssue)
            .filter(
                ValidationIssue.affected_student_enrolment_id == e.id,
                ValidationIssue.status.in_([IssueStatus.OPEN, IssueStatus.ASSIGNED, IssueStatus.CORRECTION_REQUESTED]),
            )
            .first()
            is not None
        )

        items.append(
            StudentEnrolmentListItem(
                id=e.id,
                institution_id=e.institution_id,
                institution_name=e.institution.name if e.institution else "",
                programme_id=e.programme_id,
                programme_name=e.programme.programme_name if e.programme else "",
                programme_code=e.programme.programme_code if e.programme else "",
                academic_year=e.academic_year.year_code if e.academic_year else "",
                institution_student_id=e.institution_student_id,
                masked_apaar_id=ident.masked_apaar_id if ident else "APAAR-MISSING",
                student_name=ident.legal_name if ident else "Student",
                admission_date=e.admission_date,
                enrolment_status=e.enrolment_status,
                seat_category=e.seat_category,
                is_nri=e.is_nri,
                is_oci=e.is_oci,
                is_fn=e.is_fn,
                is_supernumerary=e.is_supernumerary,
                is_eligible_enrolment=e.is_eligible_enrolment,
                has_validation_issue=has_issue,
            )
        )

    return {
        "items": items,
        "total": total_count,
        "page": page,
        "limit": limit,
        "pages": (total_count + limit - 1) // limit,
    }


@router.get("/{enrolment_id}", response_model=StudentEnrolmentDetail)
def get_enrolment(
    enrolment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    e = db.query(StudentEnrolment).filter(StudentEnrolment.id == enrolment_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Student enrolment record not found")

    enforce_institution_scope(current_user, e.institution_id)

    ident = e.student_identity

    # Fetch correction history
    corrections = [
        CorrectionHistoryItem(
            id=c.id,
            field_name=c.field_name,
            original_value=c.original_value,
            corrected_value=c.corrected_value,
            actor_email=c.actor.email if c.actor else None,
            reason=c.reason,
            timestamp=c.timestamp,
        )
        for c in e.correction_histories
    ]

    # Fetch active issues
    issues = (
        db.query(ValidationIssue)
        .filter(ValidationIssue.affected_student_enrolment_id == e.id)
        .all()
    )
    issues_data = [
        {
            "id": iss.id,
            "rule_code": iss.rule_code,
            "title": iss.title,
            "severity": iss.severity,
            "status": iss.status,
            "description": iss.description,
            "detected_at": iss.detected_at.isoformat(),
        }
        for iss in issues
    ]

    return StudentEnrolmentDetail(
        id=e.id,
        institution_id=e.institution_id,
        institution_name=e.institution.name,
        institution_code=e.institution.code,
        programme_id=e.programme_id,
        programme_name=e.programme.programme_name,
        programme_code=e.programme.programme_code,
        academic_year=e.academic_year.year_code,
        institution_student_id=e.institution_student_id,
        masked_apaar_id=ident.masked_apaar_id if ident else "APAAR-MISSING",
        student_name=ident.legal_name if ident else "Student",
        dob=ident.dob if ident else None,
        gender=ident.gender if ident else None,
        admission_date=e.admission_date,
        enrolment_status=e.enrolment_status,
        seat_category=e.seat_category,
        is_nri=e.is_nri,
        is_oci=e.is_oci,
        is_fn=e.is_fn,
        is_supernumerary=e.is_supernumerary,
        supernumerary_type=e.supernumerary_type,
        is_eligible_enrolment=e.is_eligible_enrolment,
        source_upload_batch_id=e.source_upload_batch_id,
        correction_history=corrections,
        active_issues=issues_data,
    )


@router.post("/{enrolment_id}/correct")
def correct_enrolment_record(
    enrolment_id: int,
    req: EnrolmentCorrectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enrolment = ReviewService.correct_student_record(
        db=db,
        enrolment_id=enrolment_id,
        field_name=req.field_name,
        new_value=req.new_value,
        reason=req.reason,
        actor=current_user,
        source_reference=req.source_reference,
    )
    return {
        "status": "SUCCESS",
        "enrolment_id": enrolment.id,
        "field_name": req.field_name,
        "new_value": req.new_value,
        "message": f"Field '{req.field_name}' successfully corrected with full audit record.",
    }
