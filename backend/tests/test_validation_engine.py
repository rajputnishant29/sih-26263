import pytest
from backend.app.engine.validator import DeterministicValidator
from backend.app.core.security import compute_identity_fingerprint, mask_apaar_id, check_apaar_format_readiness


def test_apaar_format_readiness_valid():
    check = check_apaar_format_readiness("900012345678")
    assert check["is_present"] is True
    assert check["is_format_ready"] is True


def test_apaar_format_readiness_missing():
    check = check_apaar_format_readiness("")
    assert check["is_present"] is False
    assert check["is_format_ready"] is False


def test_apaar_format_readiness_wrong_length():
    check = check_apaar_format_readiness("123456789")  # 9 digits
    assert check["is_present"] is True
    assert check["is_format_ready"] is False
    assert "expected 12 digits" in check["message"]


def test_apaar_hmac_fingerprint_deterministic():
    fp1 = compute_identity_fingerprint("900012345678")
    fp2 = compute_identity_fingerprint("9000-1234-5678")  # With dashes
    assert fp1 != ""
    assert fp1 == fp2  # Canonicalization handles hyphens


def test_apaar_masking():
    masked = mask_apaar_id("900012345678")
    assert masked == "APAAR-****-****-5678"
    assert "1234" not in masked


def test_row_validation_clean():
    row_data = {
        "student_id": "COEP-2026-CSE-999",
        "apaar_id": "900099998888",
        "name": "Tanvi Joshi",
        "admission_date": "2026-07-20",
        "seat_category": "OPEN",
        "enrolment_status": "ACTIVE",
    }
    status, messages, norm = DeterministicValidator.validate_row(
        row_number=1,
        data=row_data,
        seen_apaar_in_file={},
        seen_student_ids_in_file={},
        existing_institution_student_ids=set(),
        existing_identity_fingerprints=set(),
    )
    assert status == "VALID"
    assert len(messages) == 0
    assert norm["student_name"] == "Tanvi Joshi"
    assert norm["is_eligible_enrolment"] is True


def test_row_validation_missing_student_id():
    row_data = {
        "student_id": "",
        "apaar_id": "900099998888",
        "name": "Tanvi Joshi",
        "admission_date": "2026-07-20",
    }
    status, messages, norm = DeterministicValidator.validate_row(
        row_number=1,
        data=row_data,
        seen_apaar_in_file={},
        seen_student_ids_in_file={},
        existing_institution_student_ids=set(),
        existing_identity_fingerprints=set(),
    )
    assert status == "ERROR"
    assert any(m["rule_code"] == "REQUIRED_FIELD_CHECK" for m in messages)


def test_row_validation_duplicate_in_file():
    seen_ids = {"COEP-2026-CSE-101": 1}
    row_data = {
        "student_id": "COEP-2026-CSE-101",
        "apaar_id": "900011112222",
        "name": "Duplicate Student",
        "admission_date": "2026-07-20",
    }
    status, messages, norm = DeterministicValidator.validate_row(
        row_number=2,
        data=row_data,
        seen_apaar_in_file={},
        seen_student_ids_in_file=seen_ids,
        existing_institution_student_ids=set(),
        existing_identity_fingerprints=set(),
    )
    assert status == "ERROR"
    assert any(m["rule_code"] == "FILE_DUPLICATE_ROW" for m in messages)


def test_row_validation_category_inconsistency():
    row_data = {
        "student_id": "COEP-2026-CSE-888",
        "apaar_id": "900088887777",
        "name": "NRI Candidate",
        "admission_date": "2026-07-20",
        "seat_category": "SC",
        "is_nri": "TRUE",
    }
    status, messages, norm = DeterministicValidator.validate_row(
        row_number=1,
        data=row_data,
        seen_apaar_in_file={},
        seen_student_ids_in_file={},
        existing_institution_student_ids=set(),
        existing_identity_fingerprints=set(),
    )
    assert status == "WARNING"
    assert any(m["rule_code"] == "CATEGORY_INCONSISTENCY" for m in messages)
