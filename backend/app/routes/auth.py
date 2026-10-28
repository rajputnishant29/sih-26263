from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.config import settings
from backend.app.models.user import User, UserRole
from backend.app.models.institution import Institution
from backend.app.models.audit import AuditEventType
from backend.app.core.security import verify_password, create_access_token
from backend.app.core.rbac import get_current_user
from backend.app.services.audit_service import AuditService
from backend.app.schemas.auth import LoginRequest, Token, UserSummary, DemoRoleSwitchRequest

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated",
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role, "email": user.email}
    )

    inst_name = user.institution.name if user.institution else None

    AuditService.log(
        db=db,
        event_type=AuditEventType.AUTH_LOGIN,
        resource_type="USER",
        resource_id=str(user.id),
        actor=user,
        institution_id=user.institution_id,
        details={"email": user.email, "role": user.role},
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserSummary(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            institution_id=user.institution_id,
            institution_name=inst_name,
        ),
    )


@router.get("/me", response_model=UserSummary)
def get_me(current_user: User = Depends(get_current_user)):
    inst_name = current_user.institution.name if current_user.institution else None
    return UserSummary(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        institution_id=current_user.institution_id,
        institution_name=inst_name,
    )


@router.post("/demo-switch", response_model=Token)
def demo_switch_role(
    request: DemoRoleSwitchRequest,
    db: Session = Depends(get_db),
):
    """
    Demo evaluation role switcher for hackathon judges.
    Strictly disabled if ALLOW_DEMO_ROLE_SWITCHER is false in production configuration.
    """
    if not settings.ALLOW_DEMO_ROLE_SWITCHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo role switcher is disabled in production environment.",
        )

    # Find or use the primary seed demo account for the target role
    target_role = request.target_role.upper()
    valid_roles = [
        UserRole.AICTE_ADMIN,
        UserRole.INSTITUTION_ADMIN,
        UserRole.INSTITUTION_DATA_OPERATOR,
        UserRole.AUTHORIZED_REVIEWER,
        UserRole.EXTERNAL_VERIFIER,
    ]
    if target_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid target role: {target_role}")

    query = db.query(User).filter(User.role == target_role)
    if request.institution_id and target_role in [UserRole.INSTITUTION_ADMIN, UserRole.INSTITUTION_DATA_OPERATOR]:
        query = query.filter(User.institution_id == request.institution_id)

    user = query.first()
    if not user:
        # Fallback to any user with that role
        user = db.query(User).filter(User.role == target_role).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"No demo user found for role {target_role}")

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role, "email": user.email}
    )

    inst_name = user.institution.name if user.institution else None

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserSummary(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            institution_id=user.institution_id,
            institution_name=inst_name,
        ),
    )
