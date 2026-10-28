from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.upload import UploadBatch, UploadStagingRow
from backend.app.models.user import User
from backend.app.core.rbac import get_current_user, enforce_institution_scope, require_institution_access
from backend.app.services.upload_service import UploadService
from backend.app.schemas.upload import UploadBatchSummary, ValidationDryRunResponse, CommitBatchResponse

router = APIRouter(prefix="/api/uploads", tags=["Uploads & Ingestion"])


@router.get("/template/csv")
def download_csv_template():
    """
    Standard downloadable CSV template for institution student data onboarding.
    """
    csv_content = (
        "student_id,apaar_id,name,dob,gender,admission_date,enrolment_status,seat_category,programme_code,is_nri,is_oci,is_fn,is_supernumerary,supernumerary_type\n"
        "COEP-2026-CSE-101,123456789012,Aarav Patel,2005-04-12,MALE,2026-07-15,ACTIVE,OPEN,CSE,FALSE,FALSE,FALSE,FALSE,\n"
        "COEP-2026-CSE-102,987654321098,Diya Sharma,2005-08-23,FEMALE,2026-07-15,ACTIVE,OBC,CSE,FALSE,FALSE,FALSE,TRUE,TFW\n"
        "COEP-2026-CSE-103,456789123456,Rohan Mehta,2004-11-05,MALE,2026-07-16,ACTIVE,OPEN,CSE,TRUE,FALSE,FALSE,FALSE,\n"
    )
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=edutrace_student_upload_template.csv"},
    )


@router.post("/stage", response_model=UploadBatchSummary)
async def stage_upload(
    institution_id: int = Form(...),
    academic_year_id: int = Form(...),
    programme_id: Optional[int] = Form(None),
    declared_count: int = Form(0),
    file: UploadFile = File(...),
    current_user: User = Depends(require_institution_access),
    db: Session = Depends(get_db),
):
    enforce_institution_scope(current_user, institution_id)

    content = await file.read()
    batch = UploadService.stage_file(
        db=db,
        current_user=current_user,
        institution_id=institution_id,
        academic_year_id=academic_year_id,
        programme_id=programme_id,
        file_bytes=content,
        filename=file.filename,
        declared_count=declared_count,
    )

    return UploadBatchSummary(
        id=batch.id,
        institution_id=batch.institution_id,
        institution_name=batch.institution.name if batch.institution else "",
        programme_id=batch.programme_id,
        programme_name=batch.programme.programme_name if batch.programme else "All Programmes",
        academic_year=batch.academic_year.year_code if batch.academic_year else "2026-27",
        file_name=batch.file_name,
        file_size=batch.file_size,
        row_count=batch.row_count,
        declared_count=batch.declared_count,
        accepted_count=batch.accepted_count,
        rejected_count=batch.rejected_count,
        warning_count=batch.warning_count,
        status=batch.status,
        uploaded_by_email=current_user.email,
        created_at=batch.created_at,
    )


@router.post("/{batch_id}/validate", response_model=ValidationDryRunResponse)
def validate_staged_upload(
    batch_id: int,
    current_user: User = Depends(require_institution_access),
    db: Session = Depends(get_db),
):
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Upload batch not found")

    enforce_institution_scope(current_user, batch.institution_id)

    outcome = UploadService.validate_batch(db=db, batch_id=batch_id)
    return ValidationDryRunResponse(**outcome)


@router.post("/{batch_id}/commit", response_model=CommitBatchResponse)
def commit_upload_batch(
    batch_id: int,
    current_user: User = Depends(require_institution_access),
    db: Session = Depends(get_db),
):
    batch = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Upload batch not found")

    enforce_institution_scope(current_user, batch.institution_id)

    result = UploadService.commit_batch(db=db, batch_id=batch_id, current_user=current_user)
    return CommitBatchResponse(**result)


@router.get("", response_model=List[UploadBatchSummary])
def list_upload_batches(
    institution_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scoped_inst_id = enforce_institution_scope(current_user, institution_id)

    query = db.query(UploadBatch).order_by(UploadBatch.id.desc())
    if scoped_inst_id:
        query = query.filter(UploadBatch.institution_id == scoped_inst_id)

    batches = query.all()
    return [
        UploadBatchSummary(
            id=b.id,
            institution_id=b.institution_id,
            institution_name=b.institution.name if b.institution else "",
            programme_id=b.programme_id,
            programme_name=b.programme.programme_name if b.programme else "All Programmes",
            academic_year=b.academic_year.year_code if b.academic_year else "2026-27",
            file_name=b.file_name,
            file_size=b.file_size,
            row_count=b.row_count,
            declared_count=b.declared_count,
            accepted_count=b.accepted_count,
            rejected_count=b.rejected_count,
            warning_count=b.warning_count,
            status=b.status,
            uploaded_by_email=b.uploaded_by.email if b.uploaded_by else None,
            committed_by_email=b.committed_by.email if b.committed_by else None,
            committed_at=b.committed_at,
            created_at=b.created_at,
        )
        for b in batches
    ]


@router.get("/{batch_id}")
def get_upload_batch(
    batch_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    b = db.query(UploadBatch).filter(UploadBatch.id == batch_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Upload batch not found")

    enforce_institution_scope(current_user, b.institution_id)

    rows = (
        db.query(UploadStagingRow)
        .filter(UploadStagingRow.upload_batch_id == b.id)
        .order_by(UploadStagingRow.row_number)
        .limit(100)
        .all()
    )

    return {
        "id": b.id,
        "file_name": b.file_name,
        "status": b.status,
        "row_count": b.row_count,
        "declared_count": b.declared_count,
        "accepted_count": b.accepted_count,
        "rejected_count": b.rejected_count,
        "warning_count": b.warning_count,
        "created_at": b.created_at.isoformat(),
        "rows": [
            {
                "row_number": r.row_number,
                "raw_data": r.raw_data,
                "validation_status": r.validation_status,
                "validation_messages": r.validation_messages,
                "is_accepted": r.is_accepted,
            }
            for r in rows
        ],
    }
