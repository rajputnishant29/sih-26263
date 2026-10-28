from typing import List, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.user import User, UserRole
from backend.app.core.security import decode_access_token

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Resolves the authenticated user from the bearer token.
    Enforces that every API call is authenticated and validated against the database.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated or does not exist",
        )

    return user


class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Role '{current_user.role}' lacks required permissions for this resource",
            )
        return current_user


# Convenience dependency shortcuts
require_aicte_admin = RoleChecker([UserRole.AICTE_ADMIN])
require_institution_access = RoleChecker([
    UserRole.AICTE_ADMIN,
    UserRole.INSTITUTION_ADMIN,
    UserRole.INSTITUTION_DATA_OPERATOR,
])
require_reviewer = RoleChecker([
    UserRole.AICTE_ADMIN,
    UserRole.AUTHORIZED_REVIEWER,
])
require_institution_admin_or_aicte = RoleChecker([
    UserRole.AICTE_ADMIN,
    UserRole.INSTITUTION_ADMIN,
])
require_any_authenticated = RoleChecker([
    UserRole.AICTE_ADMIN,
    UserRole.INSTITUTION_ADMIN,
    UserRole.INSTITUTION_DATA_OPERATOR,
    UserRole.AUTHORIZED_REVIEWER,
    UserRole.EXTERNAL_VERIFIER,
])


def enforce_institution_scope(current_user: User, institution_id: Optional[int]) -> Optional[int]:
    """
    Institutional data isolation rule:
    AICTE Admin, Reviewers, and External Verifiers (with purpose-bound access) can query across institutions.
    Institution-scoped users (INSTITUTION_ADMIN, INSTITUTION_DATA_OPERATOR) CANNOT read or write another institution's data.
    """
    if current_user.role in [UserRole.AICTE_ADMIN, UserRole.AUTHORIZED_REVIEWER]:
        return institution_id  # Allowed to query all or specific institution

    if current_user.role in [UserRole.INSTITUTION_ADMIN, UserRole.INSTITUTION_DATA_OPERATOR]:
        if institution_id is not None and institution_id != current_user.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security Violation: You are not authorized to view or mutate records belonging to other institutions",
            )
        return current_user.institution_id

    return institution_id
