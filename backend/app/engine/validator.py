from typing import List, Dict, Any, Tuple
from datetime import datetime
from backend.app.core.security import (
    compute_identity_fingerprint,
    mask_apaar_id,
    check_apaar_format_readiness,
    normalize_apaar_id,
)
from backend.app.models.student import EnrolmentStatus, SeatCategory
from backend.app.models.validation import IssueSeverity


class DeterministicValidator:
    """
    Deterministic admission and student-data validation engine.
    Backend is the sole source of truth for validation rules.
    """

    VALID_ENROLMENT_STATUSES = {
        EnrolmentStatus.ACTIVE,
        EnrolmentStatus.WITHDRAWN,
        EnrolmentStatus.CANCELLED,
        EnrolmentStatus.TRANSFERRED,
    }

    VALID_SEAT_CATEGORIES = {
        SeatCategory.OPEN,
        SeatCategory.OBC,
        SeatCategory.SC,
        SeatCategory.ST,
        SeatCategory.EWS,
        SeatCategory.TFW,
        SeatCategory.UNKNOWN,
        SeatCategory.NOT_APPLICABLE,
    }

    @classmethod
    def validate_row(
        cls,
        row_number: int,
        data: Dict[str, Any],
        seen_apaar_in_file: Dict[str, int],
        seen_student_ids_in_file: Dict[str, int],
        existing_institution_student_ids: set,
        existing_identity_fingerprints: set,
    ) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Validates an individual staging row.
        Returns:
            validation_status: 'VALID', 'WARNING', or 'ERROR'
            messages: list of detected issue dicts
            normalized: cleansed normalized data dictionary
        """
        messages = []
        is_error = False
        is_warning = False

        # 1. Field extraction & normalization
        raw_apaar = str(data.get("apaar_id") or data.get("apaar") or "").strip()
        student_id = str(data.get("student_id") or data.get("roll_no") or "").strip()
        student_name = str(data.get("name") or data.get("student_name") or "").strip()
        dob_raw = str(data.get("dob") or data.get("date_of_birth") or "").strip()
        gender = str(data.get("gender") or "UNKNOWN").strip().upper()
        admission_date_raw = str(data.get("admission_date") or "").strip()
        enrolment_status = str(data.get("enrolment_status") or "ACTIVE").strip().upper()
        seat_category = str(data.get("seat_category") or data.get("category") or "OPEN").strip().upper()
        programme_code = str(data.get("programme_code") or "").strip()

        # Flags
        is_nri = str(data.get("is_nri") or "").strip().lower() in ["true", "1", "yes", "y"]
        is_oci = str(data.get("is_oci") or "").strip().lower() in ["true", "1", "yes", "y"]
        is_fn = str(data.get("is_fn") or "").strip().lower() in ["true", "1", "yes", "y"]
        is_supernumerary = str(data.get("is_supernumerary") or "").strip().lower() in ["true", "1", "yes", "y"]
        supernumerary_type = str(data.get("supernumerary_type") or "").strip()

        # 2. Required Fields Check
        if not student_id:
            messages.append({
                "rule_code": "REQUIRED_FIELD_CHECK",
                "severity": IssueSeverity.CRITICAL,
                "title": "Missing Student ID",
                "message": f"Row {row_number}: Institution student ID / roll number is required.",
            })
            is_error = True

        if not student_name:
            messages.append({
                "rule_code": "REQUIRED_FIELD_CHECK",
                "severity": IssueSeverity.HIGH,
                "title": "Missing Student Name",
                "message": f"Row {row_number}: Student legal name is required.",
            })
            is_error = True

        # Parse admission date
        admission_date = None
        if admission_date_raw:
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]:
                try:
                    admission_date = datetime.strptime(admission_date_raw, fmt).date()
                    break
                except ValueError:
                    pass
        if not admission_date:
            messages.append({
                "rule_code": "DATE_FORMAT_INVALID",
                "severity": IssueSeverity.HIGH,
                "title": "Invalid Admission Date",
                "message": f"Row {row_number}: Admission date '{admission_date_raw}' is missing or does not match expected formats (YYYY-MM-DD or DD/MM/YYYY).",
            })
            is_error = True

        # Parse DOB if present
        dob = None
        if dob_raw:
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"]:
                try:
                    dob = datetime.strptime(dob_raw, fmt).date()
                    break
                except ValueError:
                    pass

        # 3. APAAR Identity Presence & Format Readiness
        apaar_check = check_apaar_format_readiness(raw_apaar)
        clean_apaar = normalize_apaar_id(raw_apaar)
        fingerprint = compute_identity_fingerprint(clean_apaar) if clean_apaar else ""
        masked_apaar = mask_apaar_id(clean_apaar)

        if not apaar_check["is_present"]:
            messages.append({
                "rule_code": "APAAR_PRESENCE_CHECK",
                "severity": IssueSeverity.HIGH,
                "title": "Missing APAAR Reference",
                "message": f"Row {row_number}: Student record does not contain an APAAR identity reference.",
            })
            is_warning = True  # Allowed to stage as exception for onboarding, flagged for review
        elif not apaar_check["is_format_ready"]:
            messages.append({
                "rule_code": "APAAR_FORMAT_READINESS",
                "severity": IssueSeverity.HIGH,
                "title": "APAAR Format Readiness Failed",
                "message": f"Row {row_number}: {apaar_check['message']}.",
            })
            is_warning = True

        # 4. In-file Duplicates Check
        if student_id:
            if student_id in seen_student_ids_in_file:
                first_row = seen_student_ids_in_file[student_id]
                messages.append({
                    "rule_code": "FILE_DUPLICATE_ROW",
                    "severity": IssueSeverity.CRITICAL,
                    "title": "Duplicate Student ID in File",
                    "message": f"Row {row_number}: Student ID '{student_id}' is duplicated with row {first_row}.",
                })
                is_error = True
            else:
                seen_student_ids_in_file[student_id] = row_number

        if clean_apaar:
            if clean_apaar in seen_apaar_in_file:
                first_row = seen_apaar_in_file[clean_apaar]
                messages.append({
                    "rule_code": "FILE_DUPLICATE_APAAR",
                    "severity": IssueSeverity.CRITICAL,
                    "title": "Duplicate APAAR in File",
                    "message": f"Row {row_number}: Identity reference '{masked_apaar}' appears multiple times in upload (first seen on row {first_row}).",
                })
                is_error = True
            else:
                seen_apaar_in_file[clean_apaar] = row_number

        # 5. Existing Institutional Record Duplication
        if student_id in existing_institution_student_ids:
            messages.append({
                "rule_code": "INSTITUTION_DUPLICATE_CHECK",
                "severity": IssueSeverity.HIGH,
                "title": "Student ID Already Exists in Institution",
                "message": f"Row {row_number}: Student ID '{student_id}' is already registered in this institution for the selected academic year.",
            })
            is_error = True

        # 6. Status and Category Consistency
        if enrolment_status not in cls.VALID_ENROLMENT_STATUSES:
            messages.append({
                "rule_code": "STATUS_SANITY_CHECK",
                "severity": IssueSeverity.MEDIUM,
                "title": "Unsupported Enrolment Status",
                "message": f"Row {row_number}: Enrolment status '{enrolment_status}' is invalid. Expected one of {list(cls.VALID_ENROLMENT_STATUSES)}.",
            })
            is_warning = True
            enrolment_status = EnrolmentStatus.ACTIVE

        if seat_category not in cls.VALID_SEAT_CATEGORIES:
            messages.append({
                "rule_code": "CATEGORY_CONSISTENCY",
                "severity": IssueSeverity.MEDIUM,
                "title": "Unsupported Seat Category",
                "message": f"Row {row_number}: Category '{seat_category}' is unrecognized; mapped to 'UNKNOWN'.",
            })
            is_warning = True
            seat_category = SeatCategory.UNKNOWN

        # NRI/OCI/FN category consistency
        if (is_nri or is_oci or is_fn) and seat_category in [SeatCategory.SC, SeatCategory.ST, SeatCategory.OBC]:
            messages.append({
                "rule_code": "CATEGORY_INCONSISTENCY",
                "severity": IssueSeverity.MEDIUM,
                "title": "International Status vs Reserved Category Mismatch",
                "message": f"Row {row_number}: Student marked as NRI/OCI/FN cannot hold domestic reserved quota '{seat_category}'.",
            })
            is_warning = True

        # Determine overall status
        status = "VALID"
        if is_error:
            status = "ERROR"
        elif is_warning:
            status = "WARNING"

        normalized = {
            "row_number": row_number,
            "raw_apaar": raw_apaar,
            "clean_apaar": clean_apaar,
            "masked_apaar": masked_apaar,
            "fingerprint": fingerprint,
            "student_id": student_id,
            "student_name": student_name,
            "dob": dob.isoformat() if dob else None,
            "gender": gender,
            "admission_date": admission_date.isoformat() if admission_date else None,
            "enrolment_status": enrolment_status,
            "seat_category": seat_category,
            "programme_code": programme_code,
            "is_nri": is_nri,
            "is_oci": is_oci,
            "is_fn": is_fn,
            "is_supernumerary": is_supernumerary,
            "supernumerary_type": supernumerary_type,
            "is_eligible_enrolment": enrolment_status == EnrolmentStatus.ACTIVE,
        }

        return status, messages, normalized
