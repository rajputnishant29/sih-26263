from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.validation import ValidationIssue
from backend.app.core.rbac import get_current_user, enforce_institution_scope
from backend.app.services.report_service import ReportService
from backend.app.services.audit_service import AuditService
from backend.app.models.audit import AuditEventType

router = APIRouter(prefix="/api/reports", tags=["Reports & Analytics"])


@router.get("/reconciliation")
def get_reconciliation_report(
    academic_year_id: Optional[int] = Query(None),
    institution_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scoped_inst_id = enforce_institution_scope(current_user, institution_id)
    rows = ReportService.get_enrolment_reconciliation_report(
        db=db,
        academic_year_id=academic_year_id,
        institution_id=scoped_inst_id,
    )
    return {"rows": rows, "count": len(rows)}


@router.get("/reconciliation/export-csv")
def export_reconciliation_csv(
    academic_year_id: Optional[int] = Query(None),
    institution_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scoped_inst_id = enforce_institution_scope(current_user, institution_id)
    rows = ReportService.get_enrolment_reconciliation_report(
        db=db,
        academic_year_id=academic_year_id,
        institution_id=scoped_inst_id,
    )
    csv_text = ReportService.generate_reconciliation_csv(rows)

    AuditService.log(
        db=db,
        event_type=AuditEventType.REPORT_EXPORTED,
        resource_type="REPORT",
        resource_id="ENROLMENT_RECONCILIATION_CSV",
        actor=current_user,
        institution_id=scoped_inst_id,
        details={"rows_exported": len(rows)},
    )

    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=edutrace_reconciliation_report.csv"},
    )


@router.get("/data-quality")
def get_data_quality_report(
    institution_id: Optional[int] = Query(None),
    academic_year_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scoped_inst_id = enforce_institution_scope(current_user, institution_id)

    query = db.query(
        ValidationIssue.rule_code,
        ValidationIssue.severity,
        ValidationIssue.status,
        func.count(ValidationIssue.id),
    )
    if scoped_inst_id:
        query = query.filter(ValidationIssue.institution_id == scoped_inst_id)
    if academic_year_id:
        query = query.filter(ValidationIssue.academic_year_id == academic_year_id)

    counts = query.group_by(
        ValidationIssue.rule_code,
        ValidationIssue.severity,
        ValidationIssue.status,
    ).all()

    return {
        "breakdown": [
            {
                "rule_code": c[0],
                "severity": c[1],
                "status": c[2],
                "count": c[3],
            }
            for c in counts
        ],
        "disclaimer": "Derived from persisted validation issue store. Illustrative synthetic demonstration metrics.",
    }
