from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database import get_db
from backend.app.models.institution import Institution, Programme, AcademicYear, ApprovalIntake, SourceDocument
from backend.app.models.student import StudentEnrolment, EnrolmentStatus
from backend.app.models.user import User
from backend.app.models.audit import AuditEventType
from backend.app.core.rbac import get_current_user, enforce_institution_scope, require_reviewer
from backend.app.engine.eoa_parser import EoAParserService
from backend.app.services.audit_service import AuditService
from backend.app.schemas.institution import ApprovalIntakeSummary, AcademicYearResponse

router = APIRouter(prefix="/api/programmes", tags=["Programmes & Approvals"])


@router.get("/academic-years", response_model=List[AcademicYearResponse])
def list_academic_years(db: Session = Depends(get_db)):
    years = db.query(AcademicYear).order_by(AcademicYear.start_date.desc()).all()
    return [AcademicYearResponse(id=y.id, year_code=y.year_code, is_current=y.is_current) for y in years]


@router.get("", response_model=List[ApprovalIntakeSummary])
def list_programmes(
    institution_id: Optional[int] = Query(None),
    academic_year_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scoped_inst_id = enforce_institution_scope(current_user, institution_id)

    query = (
        db.query(ApprovalIntake)
        .join(Programme)
        .join(AcademicYear)
        .filter(ApprovalIntake.is_active == True)
    )

    if scoped_inst_id:
        query = query.filter(ApprovalIntake.institution_id == scoped_inst_id)
    if academic_year_id:
        query = query.filter(ApprovalIntake.academic_year_id == academic_year_id)

    approvals = query.all()
    results = []

    for app in approvals:
        enrolled = (
            db.query(func.count(StudentEnrolment.id))
            .filter(
                StudentEnrolment.institution_id == app.institution_id,
                StudentEnrolment.programme_id == app.programme_id,
                StudentEnrolment.academic_year_id == app.academic_year_id,
                StudentEnrolment.enrolment_status == EnrolmentStatus.ACTIVE,
            )
            .scalar()
            or 0
        )
        util = round((enrolled / app.effective_intake_limit * 100), 1) if app.effective_intake_limit > 0 else 0.0
        src_ref = app.source_document.reference_number if app.source_document else "MANUAL"

        results.append(
            ApprovalIntakeSummary(
                id=app.id,
                programme_id=app.programme_id,
                programme_name=app.programme.programme_name,
                academic_year_id=app.academic_year_id,
                academic_year=app.academic_year.year_code,
                base_approved_intake=app.base_approved_intake,
                supernumerary_seats=app.supernumerary_seats,
                effective_intake_limit=app.effective_intake_limit,
                calculated_enrolment=enrolled,
                utilization_rate=util,
                rule_version=app.rule_version,
                source_reference=src_ref,
            )
        )

    return results


@router.post("/eoa-parse")
async def parse_eoa_document(
    file: Optional[UploadFile] = File(None),
    sample_text: Optional[str] = Form(None),
    current_user: User = Depends(require_reviewer),
):
    """
    EoA ingestion service: extracts potential institution, academic year, and approved intake.
    Flagged as PENDING_CONFIRMATION with confidence score.
    """
    if file:
        content = await file.read()
        if file.filename.lower().endswith(".pdf"):
            result = EoAParserService.parse_pdf_bytes(content, file.filename)
        else:
            text_str = content.decode("utf-8", errors="ignore")
            result = EoAParserService.parse_eoa_text(text_str, file.filename)
    elif sample_text:
        result = EoAParserService.parse_eoa_text(sample_text, "Manual_EoA_Text_Input.txt")
    else:
        raise HTTPException(status_code=400, detail="Please provide a PDF file or text snippet.")

    return result


@router.post("/eoa-confirm")
def confirm_eoa_intake(
    payload: Dict[str, Any],
    current_user: User = Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    """
    Human confirmation of machine-extracted EoA values.
    Transforms pending extracted data into authoritative approval intake.
    """
    institution_id = payload.get("institution_id")
    academic_year_id = payload.get("academic_year_id")
    ref_number = payload.get("reference_number", "AICTE-CONFIRMED-EOA")
    programmes_data = payload.get("programmes", [])

    if not institution_id or not academic_year_id:
        raise HTTPException(status_code=400, detail="institution_id and academic_year_id are required")

    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    # Create confirmed SourceDocument
    source_doc = SourceDocument(
        institution_id=institution_id,
        academic_year_id=academic_year_id,
        document_type="AICTE_EOA_PDF",
        reference_number=ref_number,
        extraction_status="CONFIRMED",
        extraction_confidence=1.0,
        confirmed_by=current_user.email,
        confirmed_at=func.now(),
    )
    db.add(source_doc)
    db.flush()

    confirmed_intakes = []
    for p in programmes_data:
        p_name = p.get("programme_name")
        base_intake = int(p.get("base_approved_intake", 60))
        supernumerary = int(p.get("supernumerary_seats", int(base_intake * 0.15)))
        effective = base_intake + supernumerary

        # Find or create programme
        prog = (
            db.query(Programme)
            .filter(Programme.institution_id == institution_id, Programme.programme_name.ilike(p_name))
            .first()
        )
        if not prog:
            prog = Programme(
                institution_id=institution_id,
                programme_code=p.get("programme_code", p_name[:4].upper()),
                programme_name=p_name,
                department=p.get("department", "Engineering"),
            )
            db.add(prog)
            db.flush()

        # Update or create ApprovalIntake
        app = (
            db.query(ApprovalIntake)
            .filter(
                ApprovalIntake.institution_id == institution_id,
                ApprovalIntake.programme_id == prog.id,
                ApprovalIntake.academic_year_id == academic_year_id,
            )
            .first()
        )
        if not app:
            app = ApprovalIntake(
                institution_id=institution_id,
                programme_id=prog.id,
                academic_year_id=academic_year_id,
                source_document_id=source_doc.id,
                base_approved_intake=base_intake,
                supernumerary_seats=supernumerary,
                effective_intake_limit=effective,
                rule_version="AICTE_APH_2026_V1",
            )
            db.add(app)
        else:
            app.source_document_id = source_doc.id
            app.base_approved_intake = base_intake
            app.supernumerary_seats = supernumerary
            app.effective_intake_limit = effective
            app.rule_version = "AICTE_APH_2026_V1"

        confirmed_intakes.append(prog.programme_name)

    db.commit()

    AuditService.log(
        db=db,
        event_type=AuditEventType.EOA_DOCUMENT_CONFIRMED,
        resource_type="SOURCE_DOCUMENT",
        resource_id=str(source_doc.id),
        actor=current_user,
        institution_id=institution_id,
        details={"reference_number": ref_number, "programmes_confirmed": confirmed_intakes},
    )

    return {
        "status": "CONFIRMED",
        "source_document_id": source_doc.id,
        "reference_number": ref_number,
        "programmes_updated": len(confirmed_intakes),
        "message": f"Successfully confirmed official intake approvals for {len(confirmed_intakes)} programmes.",
    }
