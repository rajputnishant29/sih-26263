from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.validation import (
    ValidationIssue,
    DuplicateCandidateGroup,
    DuplicateCandidateMember,
    IssueStatus,
    IssueSeverity,
)
from backend.app.models.student import StudentEnrolment
from backend.app.models.user import User
from backend.app.core.rbac import get_current_user, enforce_institution_scope, require_reviewer
from backend.app.services.review_service import ReviewService
from backend.app.schemas.validation import (
    ValidationIssueListItem,
    ValidationIssueDetail,
    IssueDecisionRequest,
    DuplicateCandidateGroupItem,
)

router = APIRouter(prefix="/api/issues", tags=["Validation & Review Queue"])


@router.get("", response_model=List[ValidationIssueListItem])
def list_issues(
    rule_code: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    institution_id: Optional[int] = Query(None),
    academic_year_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scoped_inst_id = enforce_institution_scope(current_user, institution_id)

    query = db.query(ValidationIssue).order_by(ValidationIssue.id.desc())

    if scoped_inst_id:
        query = query.filter(ValidationIssue.institution_id == scoped_inst_id)
    if rule_code:
        query = query.filter(ValidationIssue.rule_code == rule_code)
    if severity:
        query = query.filter(ValidationIssue.severity == severity)
    if status:
        query = query.filter(ValidationIssue.status == status)
    if academic_year_id:
        query = query.filter(ValidationIssue.academic_year_id == academic_year_id)

    issues = query.all()
    results = []

    for iss in issues:
        assigned_email = iss.assigned_to.email if iss.assigned_to else None
        prog_name = iss.programme.programme_name if iss.programme else "All Programmes"
        inst_name = iss.institution.name if iss.institution else ""

        results.append(
            ValidationIssueListItem(
                id=iss.id,
                rule_code=iss.rule_code,
                rule_version=iss.rule_version,
                severity=iss.severity,
                institution_id=iss.institution_id,
                institution_name=inst_name,
                programme_name=prog_name,
                academic_year=iss.academic_year.year_code if iss.academic_year else "2026-27",
                title=iss.title,
                status=iss.status,
                assigned_to_email=assigned_email,
                detected_at=iss.detected_at,
                resolved_at=iss.resolved_at,
            )
        )

    return results


@router.get("/{issue_id}", response_model=ValidationIssueDetail)
def get_issue(
    issue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    iss = db.query(ValidationIssue).filter(ValidationIssue.id == issue_id).first()
    if not iss:
        raise HTTPException(status_code=404, detail="Validation issue not found")

    enforce_institution_scope(current_user, iss.institution_id)

    affected_student_id = None
    affected_name = None
    affected_apaar = None
    if iss.affected_enrolment:
        affected_student_id = iss.affected_enrolment.institution_student_id
        if iss.affected_enrolment.student_identity:
            affected_name = iss.affected_enrolment.student_identity.legal_name
            affected_apaar = iss.affected_enrolment.student_identity.masked_apaar_id

    decisions = [
        {
            "id": d.id,
            "action": d.action,
            "actor_email": d.actor.email if d.actor else "System",
            "previous_status": d.previous_status,
            "new_status": d.new_status,
            "reason": d.reason,
            "notes": d.notes,
            "timestamp": d.timestamp.isoformat(),
        }
        for d in iss.review_decisions
    ]

    return ValidationIssueDetail(
        id=iss.id,
        rule_code=iss.rule_code,
        rule_version=iss.rule_version,
        severity=iss.severity,
        institution_id=iss.institution_id,
        institution_name=iss.institution.name if iss.institution else "",
        programme_id=iss.programme_id,
        programme_name=iss.programme.programme_name if iss.programme else None,
        academic_year_id=iss.academic_year_id,
        academic_year=iss.academic_year.year_code if iss.academic_year else "2026-27",
        affected_student_enrolment_id=iss.affected_student_enrolment_id,
        affected_student_id=affected_student_id,
        affected_student_name=affected_name,
        affected_masked_apaar=affected_apaar,
        title=iss.title,
        description=iss.description,
        evidence_details=iss.evidence_details,
        status=iss.status,
        assigned_to_user_id=iss.assigned_to_user_id,
        assigned_to_email=iss.assigned_to.email if iss.assigned_to else None,
        reviewer_notes=iss.reviewer_notes,
        resolution_reason=iss.resolution_reason,
        detected_at=iss.detected_at,
        resolved_at=iss.resolved_at,
        decision_history=decisions,
    )


@router.post("/{issue_id}/decision")
def record_issue_decision(
    issue_id: int,
    req: IssueDecisionRequest,
    current_user: User = Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    issue = ReviewService.record_decision(
        db=db,
        issue_id=issue_id,
        actor=current_user,
        action=req.action,
        reason=req.reason,
        notes=req.notes,
        assigned_to_user_id=req.assigned_to_user_id,
    )
    return {
        "status": "SUCCESS",
        "issue_id": issue.id,
        "new_status": issue.status,
        "action": req.action,
        "message": f"Review decision '{req.action}' recorded successfully.",
    }


@router.get("/duplicate-candidates/list", response_model=List[DuplicateCandidateGroupItem])
def list_duplicate_candidate_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    groups = (
        db.query(DuplicateCandidateGroup)
        .order_by(DuplicateCandidateGroup.id.desc())
        .all()
    )
    results = []

    for g in groups:
        members_data = []
        for m in g.members:
            ident = m.student_identity
            enrol = m.student_enrolment
            members_data.append({
                "member_id": m.id,
                "institution_id": m.institution_id,
                "institution_name": m.institution.name if m.institution else "",
                "student_id": enrol.institution_student_id if enrol else "",
                "student_name": ident.legal_name if ident else "",
                "masked_apaar_id": ident.masked_apaar_id if ident else "",
                "programme": enrol.programme.programme_name if enrol and enrol.programme else "",
                "admission_date": enrol.admission_date.isoformat() if enrol and enrol.admission_date else None,
                "match_confidence": m.match_confidence,
            })

        results.append(
            DuplicateCandidateGroupItem(
                id=g.id,
                rule_code=g.rule_code,
                match_type=g.match_type,
                status=g.status,
                review_notes=g.review_notes,
                created_at=g.created_at,
                members=members_data,
            )
        )

    return results
