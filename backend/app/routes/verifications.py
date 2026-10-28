from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.core.rbac import get_current_user
from backend.app.services.verification_service import VerificationService
from backend.app.schemas.verification import VerificationSubmitRequest, VerificationResultResponse

router = APIRouter(prefix="/api/verifications", tags=["Authorized Verification"])


@router.post("", response_model=VerificationResultResponse)
def submit_verification(
    req: VerificationSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Authorized verification portal endpoint.
    Enforces lawful purpose and consent references.
    Returns permitted claims only.
    Clearly labels simulated provider.
    """
    result = VerificationService.verify_student_record(
        db=db,
        actor=current_user,
        requester_organization=req.requester_organization,
        query_identifier=req.query_identifier,
        purpose=req.purpose,
        consent_proof_ref=req.consent_proof_ref,
    )
    return VerificationResultResponse(**result)
