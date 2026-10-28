import pytest
from backend.app.database import SessionLocal
from backend.app.engine.reconciler import AdmissionReconciler
from backend.app.models.institution import Institution, Programme, AcademicYear


@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()


def test_reconciliation_within_limit(db_session):
    # COEP ECE has 65 enrolled vs 69 limit
    inst = db_session.query(Institution).filter(Institution.code == "1-10023841").first()
    prog = db_session.query(Programme).filter(Programme.institution_id == inst.id, Programme.programme_code == "ECE").first()
    ay = db_session.query(AcademicYear).filter(AcademicYear.year_code == "2026-27").first()

    rec = AdmissionReconciler.reconcile_programme(
        db=db_session,
        institution_id=inst.id,
        programme_id=prog.id,
        academic_year_id=ay.id,
    )
    assert rec["has_approval_record"] is True
    assert rec["effective_limit"] == 69
    assert rec["is_exceeded"] is False
    assert rec["remaining_capacity"] > 0
    assert len(rec["findings"]) == 0


def test_reconciliation_exceeded_limit(db_session):
    # COEP MECH has 142 enrolled vs 138 limit
    inst = db_session.query(Institution).filter(Institution.code == "1-10023841").first()
    prog = db_session.query(Programme).filter(Programme.institution_id == inst.id, Programme.programme_code == "MECH").first()
    ay = db_session.query(AcademicYear).filter(AcademicYear.year_code == "2026-27").first()

    rec = AdmissionReconciler.reconcile_programme(
        db=db_session,
        institution_id=inst.id,
        programme_id=prog.id,
        academic_year_id=ay.id,
    )
    assert rec["has_approval_record"] is True
    assert rec["effective_limit"] == 138
    assert rec["is_exceeded"] is True
    assert rec["excess_count"] == 4
    assert len(rec["findings"]) == 1
    assert rec["findings"][0]["rule_code"] == "INTAKE_CAPACITY_EXCEEDED"


def test_declared_total_reconciliation():
    rec = AdmissionReconciler.reconcile_upload_declaration(
        declared_total=200,
        rows_received=196,
        accepted_rows=196,
        rejected_rows=0,
        excluded_duplicate_rows=0,
        eligible_enrolment=196,
    )
    assert rec["has_mismatch"] is True
    assert rec["variance"] == 4
    assert len(rec["findings"]) == 1
    assert rec["findings"][0]["rule_code"] == "DECLARED_TOTAL_MISMATCH"
