import pytest
from fastapi import HTTPException
from backend.app.database import SessionLocal
from backend.app.models.user import User, UserRole
from backend.app.core.rbac import enforce_institution_scope


@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()


def test_aicte_admin_can_access_any_institution(db_session):
    aicte_user = db_session.query(User).filter(User.role == UserRole.AICTE_ADMIN).first()
    # Can query any institution id or None
    assert enforce_institution_scope(aicte_user, 1) == 1
    assert enforce_institution_scope(aicte_user, 2) == 2
    assert enforce_institution_scope(aicte_user, None) is None


def test_institution_user_cannot_access_foreign_institution(db_session):
    coep_user = db_session.query(User).filter(User.email == "inst.admin@coep.ac.in").first()
    assert coep_user.institution_id is not None

    # Allowed to access own institution
    assert enforce_institution_scope(coep_user, coep_user.institution_id) == coep_user.institution_id

    # Accessing another institution must raise 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        enforce_institution_scope(coep_user, 999)  # Foreign institution ID
    assert exc_info.value.status_code == 403
    assert "Security Violation" in exc_info.value.detail


def test_security_zero_raw_apaar_leakage_in_audit(db_session):
    from backend.app.services.audit_service import AuditService
    from backend.app.models.audit import AuditEvent

    admin_user = db_session.query(User).filter(User.role == UserRole.AICTE_ADMIN).first()

    event = AuditService.log(
        db=db_session,
        event_type="TEST_EVENT",
        resource_type="STUDENT",
        actor=admin_user,
        details={"raw_apaar": "900012345678", "password": "SuperSecretPassword123", "normal_field": "val"},
    )
    db_session.commit()

    saved_event = db_session.query(AuditEvent).filter(AuditEvent.id == event.id).first()
    assert saved_event.event_details["raw_apaar"] == "[REDACTED]"
    assert saved_event.event_details["password"] == "[REDACTED]"
    assert saved_event.event_details["normal_field"] == "val"
