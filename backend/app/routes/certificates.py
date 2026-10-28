from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.core.rbac import get_current_user
from backend.app.services.certificate_service import CertificateService
from backend.app.schemas.verification import CertificatePreviewResponse

router = APIRouter(prefix="/api/certificates", tags=["Degree Credential & Certificate Preview"])


@router.get("/preview/{enrolment_id}", response_model=CertificatePreviewResponse)
def get_certificate_preview(
    enrolment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cert = CertificateService.get_or_create_certificate(
        db=db,
        enrolment_id=enrolment_id,
        actor=current_user,
    )
    return CertificatePreviewResponse(**cert)


@router.get("/verify-qr/{slug}")
def verify_qr_certificate(
    slug: str,
    db: Session = Depends(get_db),
):
    """
    Public working prototype verification route accessible via QR code.
    Demonstrates instant proof of credential validity without disclosing excessive personal data.
    """
    result = CertificateService.verify_by_slug(db=db, slug=slug)
    return result
