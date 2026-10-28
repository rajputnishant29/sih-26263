import random
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal, engine, Base
import backend.app.models
from backend.app.models.user import User, UserRole
from backend.app.models.institution import (
    Institution,
    Programme,
    AcademicYear,
    SourceDocument,
    ApprovalIntake,
)
from backend.app.models.student import (
    StudentIdentity,
    StudentEnrolment,
    IdentityVerificationEvidence,
    EnrolmentStatus,
    SeatCategory,
)
from backend.app.models.upload import (
    UploadBatch,
    UploadStagingRow,
    ValidationRun,
    UploadStatus,
)
from backend.app.models.validation import (
    VersionedRule,
    ValidationIssue,
    DuplicateCandidateGroup,
    DuplicateCandidateMember,
    IssueSeverity,
    IssueStatus,
)
from backend.app.models.review import ReviewDecision, RecordCorrectionHistory
from backend.app.models.verification import CertificateCredential
from backend.app.models.audit import AuditEvent, AuditEventType
from backend.app.core.security import (
    get_password_hash,
    compute_identity_fingerprint,
    mask_apaar_id,
)


def seed_database():
    db: Session = SessionLocal()
    try:
        print("--- Clearing existing database data ---")
        # Clean in reverse dependency order
        db.query(AuditEvent).delete()
        db.query(CertificateCredential).delete()
        db.query(RecordCorrectionHistory).delete()
        db.query(ReviewDecision).delete()
        db.query(DuplicateCandidateMember).delete()
        db.query(DuplicateCandidateGroup).delete()
        db.query(ValidationIssue).delete()
        db.query(ValidationRun).delete()
        db.query(UploadStagingRow).delete()
        db.query(UploadBatch).delete()
        db.query(IdentityVerificationEvidence).delete()
        db.query(StudentEnrolment).delete()
        db.query(StudentIdentity).delete()
        db.query(ApprovalIntake).delete()
        db.query(SourceDocument).delete()
        db.query(Programme).delete()
        db.query(AcademicYear).delete()
        db.query(User).delete()
        db.query(Institution).delete()
        db.query(VersionedRule).delete()
        db.commit()

        print("--- 1. Seeding Versioned Rules ---")
        rules = [
            VersionedRule(
                rule_code="APAAR_PRESENCE_CHECK",
                rule_version="v2026.1",
                rule_name="Mandatory APAAR Identity Reference Presence",
                description="Verifies that an APAAR identity reference is provided for student records.",
                severity=IssueSeverity.HIGH,
                config_payload={"mandatory": True, "allow_conditional_onboarding": True},
            ),
            VersionedRule(
                rule_code="APAAR_FORMAT_READINESS",
                rule_version="v2026.1",
                rule_name="12-Digit Numeric Identity Readiness Check",
                description="Checks that the supplied identifier satisfies structural 12-digit numeric readiness standards.",
                severity=IssueSeverity.HIGH,
                config_payload={"expected_length": 12, "numeric_only": True},
            ),
            VersionedRule(
                rule_code="INTAKE_CAPACITY_EXCEEDED",
                rule_version="v2026.1",
                rule_name="Approved Intake & Supernumerary Capacity Reconciler",
                description="Detects student admissions exceeding base approved intake plus authorized supernumerary allocation.",
                severity=IssueSeverity.CRITICAL,
                config_payload={"supernumerary_ceiling_percent": 15},
            ),
            VersionedRule(
                rule_code="CROSS_INSTITUTION_DUPLICATE_CANDIDATE",
                rule_version="v2026.1",
                rule_name="Cross-Institution Duplicate Enrolment Detector",
                description="Flags concurrent active enrolment of the same student identity across multiple institutions.",
                severity=IssueSeverity.HIGH,
                config_payload={"requires_human_investigation": True, "auto_consequence": False},
            ),
            VersionedRule(
                rule_code="FILE_DUPLICATE_ROW",
                rule_version="v2026.1",
                rule_name="In-File Duplicate Row Check",
                description="Flags multiple rows with duplicate Student ID or APAAR reference within an upload file.",
                severity=IssueSeverity.CRITICAL,
                config_payload={"scope": "FILE"},
            ),
            VersionedRule(
                rule_code="INSTITUTION_DUPLICATE_CHECK",
                rule_version="v2026.1",
                rule_name="Institutional Student ID Collision",
                description="Detects repeated student IDs within the same institution and academic year.",
                severity=IssueSeverity.HIGH,
                config_payload={"scope": "INSTITUTION"},
            ),
            VersionedRule(
                rule_code="DECLARED_TOTAL_MISMATCH",
                rule_version="v2026.1",
                rule_name="Declared vs Calculated Admission Variance",
                description="Compares declared institution total admissions with parsed accepted rows.",
                severity=IssueSeverity.MEDIUM,
                config_payload={"variance_tolerance": 0},
            ),
            VersionedRule(
                rule_code="CATEGORY_INCONSISTENCY",
                rule_version="v2026.1",
                rule_name="International vs Reserved Quota Inconsistency",
                description="Checks for conflicting category declarations such as NRI/OCI students holding domestic SC/ST quota.",
                severity=IssueSeverity.MEDIUM,
                config_payload={},
            ),
            VersionedRule(
                rule_code="HISTORICAL_UTILIZATION_ANOMALY",
                rule_version="v2026.1",
                rule_name="Historical Utilization Anomaly Signal (AI Secondary Signal)",
                description="Identifies statistically significant deviations in intake utilization against 3-year historical baseline.",
                severity=IssueSeverity.MEDIUM,
                config_payload={"algorithm": "IsolationForest", "contamination": 0.1},
            ),
        ]
        db.bulk_save_objects(rules)
        db.commit()

        print("--- 2. Seeding Academic Years ---")
        ay_2026 = AcademicYear(
            year_code="2026-27",
            start_date=datetime(2026, 7, 1),
            end_date=datetime(2027, 6, 30),
            is_current=True,
        )
        ay_2025 = AcademicYear(
            year_code="2025-26",
            start_date=datetime(2025, 7, 1),
            end_date=datetime(2026, 6, 30),
            is_current=False,
        )
        ay_2024 = AcademicYear(
            year_code="2024-25",
            start_date=datetime(2024, 7, 1),
            end_date=datetime(2025, 6, 30),
            is_current=False,
        )
        db.add_all([ay_2026, ay_2025, ay_2024])
        db.commit()

        print("--- 3. Seeding Institutions ---")
        inst_coep = Institution(
            code="1-10023841",
            name="COEP Technological University (Unitary Public University)",
            state="Maharashtra",
            district="Pune",
            institution_type="Government / Autonomous University",
            address="Wellesley Rd, Shivajinagar, Pune, Maharashtra 411005",
            contact_email="registrar@coep.ac.in",
            is_active=True,
        )
        inst_anna = Institution(
            code="1-20045612",
            name="College of Engineering Guindy, Anna University",
            state="Tamil Nadu",
            district="Chennai",
            institution_type="State University Autonomous College",
            address="12, Sardar Patel Rd, Guindy, Chennai, Tamil Nadu 600025",
            contact_email="dean@ceg.annauniv.edu",
            is_active=True,
        )
        inst_vjti = Institution(
            code="1-30078923",
            name="Veermata Jijabai Technological Institute (VJTI)",
            state="Maharashtra",
            district="Mumbai",
            institution_type="Government Autonomous Institute",
            address="H.R. Mahajani Rd, Matunga, Mumbai, Maharashtra 400019",
            contact_email="principal@vjti.ac.in",
            is_active=True,
        )
        db.add_all([inst_coep, inst_anna, inst_vjti])
        db.commit()

        print("--- 4. Seeding Programmes ---")
        prog_coep_cse = Programme(
            institution_id=inst_coep.id,
            programme_code="CSE",
            programme_name="Computer Science and Engineering",
            degree_level="UG",
            department="Computer Science & Engineering",
            duration_years=4,
        )
        prog_coep_ece = Programme(
            institution_id=inst_coep.id,
            programme_code="ECE",
            programme_name="Electronics and Telecommunication Engineering",
            degree_level="UG",
            department="Electronics & Telecommunication",
            duration_years=4,
        )
        prog_coep_mech = Programme(
            institution_id=inst_coep.id,
            programme_code="MECH",
            programme_name="Mechanical Engineering",
            degree_level="UG",
            department="Mechanical Engineering",
            duration_years=4,
        )
        prog_anna_cse = Programme(
            institution_id=inst_anna.id,
            programme_code="CSE",
            programme_name="Computer Science and Engineering",
            degree_level="UG",
            department="Computer Science & Engineering",
            duration_years=4,
        )
        prog_vjti_cse = Programme(
            institution_id=inst_vjti.id,
            programme_code="CSE",
            programme_name="Computer Science and Engineering",
            degree_level="UG",
            department="Computer Science & Engineering",
            duration_years=4,
        )
        db.add_all([prog_coep_cse, prog_coep_ece, prog_coep_mech, prog_anna_cse, prog_vjti_cse])
        db.commit()

        print("--- 5. Seeding Sourced EoA Approval Documents & Intake Records ---")
        eoa_coep_2026 = SourceDocument(
            institution_id=inst_coep.id,
            academic_year_id=ay_2026.id,
            document_type="AICTE_EOA_PDF",
            reference_number="F.No. Western/1-10023841/2026/EOA",
            document_url="https://facilities.aicte-india.org/dashboard/pages/angulardashboard.php#!/approved",
            publication_date=datetime(2026, 4, 30),
            extraction_status="CONFIRMED",
            extraction_confidence=1.0,
            confirmed_by="aicte.admin@edutrace.gov.in",
            confirmed_at=datetime(2026, 5, 2),
        )
        eoa_anna_2026 = SourceDocument(
            institution_id=inst_anna.id,
            academic_year_id=ay_2026.id,
            document_type="AICTE_EOA_PDF",
            reference_number="F.No. Southern/1-20045612/2026/EOA",
            document_url="https://facilities.aicte-india.org/dashboard/pages/angulardashboard.php#!/approved",
            publication_date=datetime(2026, 5, 1),
            extraction_status="CONFIRMED",
            extraction_confidence=1.0,
            confirmed_by="aicte.admin@edutrace.gov.in",
            confirmed_at=datetime(2026, 5, 3),
        )
        eoa_vjti_2026 = SourceDocument(
            institution_id=inst_vjti.id,
            academic_year_id=ay_2026.id,
            document_type="AICTE_EOA_PDF",
            reference_number="F.No. Western/1-30078923/2026/EOA",
            document_url="https://facilities.aicte-india.org/dashboard/pages/angulardashboard.php#!/approved",
            publication_date=datetime(2026, 4, 28),
            extraction_status="CONFIRMED",
            extraction_confidence=1.0,
            confirmed_by="aicte.admin@edutrace.gov.in",
            confirmed_at=datetime(2026, 5, 2),
        )
        db.add_all([eoa_coep_2026, eoa_anna_2026, eoa_vjti_2026])
        db.commit()

        # Approval Intakes for 2026-27
        # Program 1 (COEP CSE): 120 base + 18 supernumerary = 138 limit
        app_coep_cse = ApprovalIntake(
            institution_id=inst_coep.id,
            programme_id=prog_coep_cse.id,
            academic_year_id=ay_2026.id,
            source_document_id=eoa_coep_2026.id,
            base_approved_intake=120,
            supernumerary_seats=18,
            effective_intake_limit=138,
            rule_version="AICTE_APH_2026_V1",
        )
        # Program 2 (COEP ECE): 60 base + 9 supernumerary = 69 limit
        app_coep_ece = ApprovalIntake(
            institution_id=inst_coep.id,
            programme_id=prog_coep_ece.id,
            academic_year_id=ay_2026.id,
            source_document_id=eoa_coep_2026.id,
            base_approved_intake=60,
            supernumerary_seats=9,
            effective_intake_limit=69,
            rule_version="AICTE_APH_2026_V1",
        )
        # Program 3 (COEP MECH): 120 base + 18 supernumerary = 138 limit
        app_coep_mech = ApprovalIntake(
            institution_id=inst_coep.id,
            programme_id=prog_coep_mech.id,
            academic_year_id=ay_2026.id,
            source_document_id=eoa_coep_2026.id,
            base_approved_intake=120,
            supernumerary_seats=18,
            effective_intake_limit=138,
            rule_version="AICTE_APH_2026_V1",
        )
        # Program 4 (Anna Univ CSE): 120 base + 18 supernumerary = 138 limit
        app_anna_cse = ApprovalIntake(
            institution_id=inst_anna.id,
            programme_id=prog_anna_cse.id,
            academic_year_id=ay_2026.id,
            source_document_id=eoa_anna_2026.id,
            base_approved_intake=120,
            supernumerary_seats=18,
            effective_intake_limit=138,
            rule_version="AICTE_APH_2026_V1",
        )
        # Program 5 (VJTI CSE): 60 base + 9 supernumerary = 69 limit
        app_vjti_cse = ApprovalIntake(
            institution_id=inst_vjti.id,
            programme_id=prog_vjti_cse.id,
            academic_year_id=ay_2026.id,
            source_document_id=eoa_vjti_2026.id,
            base_approved_intake=60,
            supernumerary_seats=9,
            effective_intake_limit=69,
            rule_version="AICTE_APH_2026_V1",
        )
        db.add_all([app_coep_cse, app_coep_ece, app_coep_mech, app_anna_cse, app_vjti_cse])

        # Prior years approvals for trend calculations
        for ay, factor in [(ay_2025, 0.95), (ay_2024, 0.90)]:
            db.add_all([
                ApprovalIntake(institution_id=inst_coep.id, programme_id=prog_coep_cse.id, academic_year_id=ay.id, base_approved_intake=120, supernumerary_seats=18, effective_intake_limit=138, rule_version="AICTE_APH_PREV"),
                ApprovalIntake(institution_id=inst_coep.id, programme_id=prog_coep_ece.id, academic_year_id=ay.id, base_approved_intake=60, supernumerary_seats=9, effective_intake_limit=69, rule_version="AICTE_APH_PREV"),
                ApprovalIntake(institution_id=inst_anna.id, programme_id=prog_anna_cse.id, academic_year_id=ay.id, base_approved_intake=120, supernumerary_seats=18, effective_intake_limit=138, rule_version="AICTE_APH_PREV"),
                ApprovalIntake(institution_id=inst_vjti.id, programme_id=prog_vjti_cse.id, academic_year_id=ay.id, base_approved_intake=60, supernumerary_seats=9, effective_intake_limit=69, rule_version="AICTE_APH_PREV"),
            ])
        db.commit()

        print("--- 6. Seeding Demo User Accounts ---")
        hashed_pw = get_password_hash("Demo@2026")
        demo_users = [
            User(
                email="aicte.admin@edutrace.gov.in",
                hashed_password=hashed_pw,
                full_name="Dr. Rajiv Sharma (AICTE Admin)",
                role=UserRole.AICTE_ADMIN,
                institution_id=None,
                is_active=True,
            ),
            User(
                email="inst.admin@coep.ac.in",
                hashed_password=hashed_pw,
                full_name="Prof. Sunita Deshmukh (COEP Admin)",
                role=UserRole.INSTITUTION_ADMIN,
                institution_id=inst_coep.id,
                is_active=True,
            ),
            User(
                email="data.operator@coep.ac.in",
                hashed_password=hashed_pw,
                full_name="Ramesh Joshi (COEP Data Operator)",
                role=UserRole.INSTITUTION_DATA_OPERATOR,
                institution_id=inst_coep.id,
                is_active=True,
            ),
            User(
                email="reviewer@aicte.gov.in",
                hashed_password=hashed_pw,
                full_name="Meera Sundaram (Authorized Reviewer)",
                role=UserRole.AUTHORIZED_REVIEWER,
                institution_id=None,
                is_active=True,
            ),
            User(
                email="verifier.tcs@tcs.com",
                hashed_password=hashed_pw,
                full_name="Anand Kulkarni (TCS Campus Hiring Verification)",
                role=UserRole.EXTERNAL_VERIFIER,
                institution_id=None,
                is_active=True,
            ),
            User(
                email="inst.admin@annauniv.edu",
                hashed_password=hashed_pw,
                full_name="Dr. V. Natarajan (Anna Univ Admin)",
                role=UserRole.INSTITUTION_ADMIN,
                institution_id=inst_anna.id,
                is_active=True,
            ),
            User(
                email="inst.admin@vjti.ac.in",
                hashed_password=hashed_pw,
                full_name="Dr. Farhan Shaikh (VJTI Admin)",
                role=UserRole.INSTITUTION_ADMIN,
                institution_id=inst_vjti.id,
                is_active=True,
            ),
        ]
        db.add_all(demo_users)
        db.commit()

        print("--- 7. Seeding 500 Fictional Student Enrolment Records ---")
        first_names = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan", "Krishna", "Ishaan",
                       "Diya", "Saanvi", "Ananya", "Aadhya", "Pari", "Chiara", "Riya", "Myra", "Isha", "Kavya",
                       "Rohan", "Siddharth", "Manish", "Pooja", "Neha", "Rahul", "Priya", "Amit", "Sneha", "Vikram"]
        last_names = ["Patel", "Sharma", "Mehta", "Joshi", "Deshmukh", "Nair", "Iyer", "Rao", "Reddy", "Kulkarni",
                      "Verma", "Gupta", "Bose", "Chatterjee", "Mishra", "Pandey", "Chauhan", "Singh", "Yadav", "Kumar"]

        categories = [SeatCategory.OPEN, SeatCategory.OBC, SeatCategory.SC, SeatCategory.ST, SeatCategory.EWS, SeatCategory.TFW]
        cat_weights = [0.45, 0.25, 0.12, 0.08, 0.05, 0.05]

        # Generate 500 records distributed across the 5 programmes:
        # COEP CSE: 130 records (Intake 138)
        # COEP ECE: 65 records (Intake 69)
        # COEP MECH: 142 records (Intake 138 -> INTENTIONALLY EXCEEDED by 4!)
        # Anna Univ CSE: 110 records (Intake 138)
        # VJTI CSE: 53 records (Intake 69)
        # Total = 130 + 65 + 142 + 110 + 53 = 500 records!

        prog_distributions = [
            (inst_coep, prog_coep_cse, 130, "COEP-2026-CSE"),
            (inst_coep, prog_coep_ece, 65, "COEP-2026-ECE"),
            (inst_coep, prog_coep_mech, 142, "COEP-2026-MECH"),
            (inst_anna, prog_anna_cse, 110, "CEG-2026-CSE"),
            (inst_vjti, prog_vjti_cse, 53, "VJTI-2026-CSE"),
        ]

        # Create seeded upload batches for provenance
        batch_coep = UploadBatch(
            institution_id=inst_coep.id,
            academic_year_id=ay_2026.id,
            file_name="COEP_Admissions_Batch_2026_Final.csv",
            file_size=1024 * 65,
            file_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            row_count=337,
            declared_count=337,
            accepted_count=335,
            rejected_count=2,
            warning_count=6,
            status=UploadStatus.COMMITTED,
            uploaded_by_user_id=demo_users[2].id,
            committed_by_user_id=demo_users[1].id,
            committed_at=datetime(2026, 7, 20, 14, 30),
        )
        batch_anna = UploadBatch(
            institution_id=inst_anna.id,
            academic_year_id=ay_2026.id,
            file_name="AnnaUniv_CEG_CSE_2026.csv",
            file_size=1024 * 28,
            file_hash="5f4dcc3b5aa765d61d8327deb882cf992b9699b9ca495991b7852b855aa11223",
            row_count=110,
            declared_count=110,
            accepted_count=110,
            rejected_count=0,
            warning_count=1,
            status=UploadStatus.COMMITTED,
            uploaded_by_user_id=demo_users[5].id,
            committed_by_user_id=demo_users[5].id,
            committed_at=datetime(2026, 7, 21, 11, 15),
        )
        batch_vjti = UploadBatch(
            institution_id=inst_vjti.id,
            academic_year_id=ay_2026.id,
            file_name="VJTI_Degree_Admissions_2026.xlsx",
            file_size=1024 * 22,
            file_hash="6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b",
            row_count=53,
            declared_count=53,
            accepted_count=53,
            rejected_count=0,
            warning_count=2,
            status=UploadStatus.COMMITTED,
            uploaded_by_user_id=demo_users[6].id,
            committed_by_user_id=demo_users[6].id,
            committed_at=datetime(2026, 7, 22, 16, 45),
        )
        db.add_all([batch_coep, batch_anna, batch_vjti])
        db.commit()

        enrolment_seq = 1
        all_created_enrolments = []

        random.seed(42)  # Deterministic seed for reproducible testing!

        for inst, prog, count, prefix in prog_distributions:
            assigned_batch = batch_coep if inst.id == inst_coep.id else (batch_anna if inst.id == inst_anna.id else batch_vjti)
            for i in range(1, count + 1):
                # Unique synthetic APAAR 12-digit number (e.g. 900000000001 -> 900000000500)
                synthetic_apaar = f"9000{enrolment_seq:08d}"

                # Intentionally leave 2 records with missing APAAR to satisfy seeded issue requirement
                is_missing_apaar = (enrolment_seq in [15, 145])
                is_invalid_apaar_format = (enrolment_seq == 88)  # 10 digits only
                if is_missing_apaar:
                    synthetic_apaar = ""
                elif is_invalid_apaar_format:
                    synthetic_apaar = "9000000888"  # 10 digits only!

                clean_apaar = synthetic_apaar
                fingerprint = compute_identity_fingerprint(clean_apaar) if clean_apaar else f"NO_APAAR_SEQ_{enrolment_seq}"
                masked_apaar = mask_apaar_id(clean_apaar)

                fname = random.choice(first_names)
                lname = random.choice(last_names)
                full_name = f"{fname} {lname}"

                b_year = random.randint(2004, 2006)
                b_month = random.randint(1, 12)
                b_day = random.randint(1, 28)
                dob = date(b_year, b_month, b_day)

                adm_day = random.randint(1, 25)
                adm_date = date(2026, 7, adm_day)

                cat = random.choices(categories, weights=cat_weights)[0]
                is_super = (cat == SeatCategory.TFW or random.random() < 0.05)
                is_nri = (random.random() < 0.03)
                is_oci = (random.random() < 0.01)
                is_fn = (random.random() < 0.01)

                # Special seeded condition: Enrolment 42 has NRI=True but category SC (seeded category inconsistency)
                if enrolment_seq == 42:
                    is_nri = True
                    cat = SeatCategory.SC

                student_ident = StudentIdentity(
                    protected_identity_fingerprint=fingerprint,
                    masked_apaar_id=masked_apaar,
                    legal_name=full_name,
                    dob=dob,
                    gender="MALE" if fname in first_names[:10] + first_names[20:25] else "FEMALE",
                    primary_state=inst.state,
                )
                db.add(student_ident)
                db.flush()

                st_id = f"{prefix}-{i:03d}"
                enrol = StudentEnrolment(
                    student_identity_id=student_ident.id,
                    institution_id=inst.id,
                    programme_id=prog.id,
                    academic_year_id=ay_2026.id,
                    institution_student_id=st_id,
                    admission_date=adm_date,
                    enrolment_status=EnrolmentStatus.ACTIVE,
                    seat_category=cat,
                    is_nri=is_nri,
                    is_oci=is_oci,
                    is_fn=is_fn,
                    is_supernumerary=is_super,
                    supernumerary_type="TFW" if cat == SeatCategory.TFW else ("PIO_FN_OCI" if (is_fn or is_oci) else None),
                    source_upload_batch_id=assigned_batch.id,
                    is_eligible_enrolment=True,
                )
                db.add(enrol)
                all_created_enrolments.append((student_ident, enrol, inst, prog))
                enrolment_seq += 1

        db.commit()
        print(f"Persisted {len(all_created_enrolments)} student enrolment records.")

        print("--- 8. Seeding Cross-Institution Duplicate Candidates (4 candidates in 2 groups) ---")
        # Duplicate Candidate Group 1: Exact APAAR collision between COEP CSE student #10 and Anna Univ CSE
        ident_1, enrol_1, inst_1, prog_1 = all_created_enrolments[9]   # COEP CSE #10
        ident_2, enrol_2, inst_2, prog_2 = all_created_enrolments[340] # Anna Univ CSE #5

        # Both enrolments share the same student identity record
        enrol_2.student_identity_id = ident_1.id
        db.commit()

        dup_group_1 = DuplicateCandidateGroup(
            rule_code="CROSS_INSTITUTION_DUPLICATE_CANDIDATE",
            match_type="EXACT_FINGERPRINT",
            status="PENDING_REVIEW",
            review_notes="Candidate match: identical APAAR reference active at COEP and Anna University. Transfer investigation needed.",
        )
        db.add(dup_group_1)
        db.flush()

        db.add(DuplicateCandidateMember(duplicate_group_id=dup_group_1.id, student_identity_id=ident_1.id, student_enrolment_id=enrol_1.id, institution_id=inst_1.id, match_confidence=1.0))
        db.add(DuplicateCandidateMember(duplicate_group_id=dup_group_1.id, student_identity_id=ident_1.id, student_enrolment_id=enrol_2.id, institution_id=inst_2.id, match_confidence=1.0))

        # Duplicate Candidate Group 2: Name + DOB match across COEP ECE student #25 and VJTI CSE #12
        ident_3, enrol_3, inst_3, prog_3 = all_created_enrolments[154] # COEP ECE #25
        ident_4, enrol_4, inst_4, prog_4 = all_created_enrolments[458] # VJTI CSE #12
        ident_4.legal_name = ident_3.legal_name
        ident_4.dob = ident_3.dob
        db.commit()

        dup_group_2 = DuplicateCandidateGroup(
            rule_code="CROSS_INSTITUTION_DUPLICATE_CANDIDATE",
            match_type="CROSS_INSTITUTION_NAME_DOB",
            status="PENDING_REVIEW",
            review_notes="Candidate match: identical candidate legal name and date of birth across distinct institutes.",
        )
        db.add(dup_group_2)
        db.flush()

        db.add(DuplicateCandidateMember(duplicate_group_id=dup_group_2.id, student_identity_id=ident_3.id, student_enrolment_id=enrol_3.id, institution_id=inst_3.id, match_confidence=0.88))
        db.add(DuplicateCandidateMember(duplicate_group_id=dup_group_2.id, student_identity_id=ident_4.id, student_enrolment_id=enrol_4.id, institution_id=inst_4.id, match_confidence=0.88))
        db.commit()

        print("--- 9. Seeding the 12 Documented Validation Issues (Exact Presentation Alignment) ---")
        seeded_issues = [
            # Issue 1: Missing ID reference (MECH)
            ValidationIssue(
                upload_batch_id=batch_coep.id,
                rule_code="APAAR_PRESENCE_CHECK",
                rule_version="v2026.1",
                severity=IssueSeverity.HIGH,
                institution_id=inst_coep.id,
                programme_id=prog_coep_mech.id,
                academic_year_id=ay_2026.id,
                affected_student_enrolment_id=all_created_enrolments[144][1].id,
                title="Missing APAAR Identifier in Mechanical Engineering",
                description="Student record for Roll No COEP-2026-MECH-015 lacks an APAAR identity reference.",
                evidence_details={"student_id": "COEP-2026-MECH-015", "missing_field": "apaar_id", "rule": "APAAR_PRESENCE_CHECK"},
                status=IssueStatus.OPEN,
                detected_at=datetime(2026, 7, 20, 14, 32),
            ),
            # Issue 2: Missing ID reference (ECE)
            ValidationIssue(
                upload_batch_id=batch_coep.id,
                rule_code="APAAR_PRESENCE_CHECK",
                rule_version="v2026.1",
                severity=IssueSeverity.HIGH,
                institution_id=inst_coep.id,
                programme_id=prog_coep_ece.id,
                academic_year_id=ay_2026.id,
                affected_student_enrolment_id=all_created_enrolments[14][1].id,
                title="Missing APAAR Identifier in Electronics Engineering",
                description="Student record for Roll No COEP-2026-ECE-015 lacks an APAAR identity reference.",
                evidence_details={"student_id": "COEP-2026-ECE-015", "missing_field": "apaar_id", "rule": "APAAR_PRESENCE_CHECK"},
                status=IssueStatus.CORRECTION_REQUESTED,
                assigned_to_user_id=demo_users[3].id,
                reviewer_notes="Requested institution data operator to furnish APAAR enrollment slip or reference.",
                detected_at=datetime(2026, 7, 20, 14, 32),
            ),
            # Issue 3: Declared Count Mismatch
            ValidationIssue(
                upload_batch_id=batch_coep.id,
                rule_code="DECLARED_TOTAL_MISMATCH",
                rule_version="v2026.1",
                severity=IssueSeverity.MEDIUM,
                institution_id=inst_coep.id,
                programme_id=prog_coep_cse.id,
                academic_year_id=ay_2026.id,
                title="Declared Admission Count Mismatch (Variance: 4)",
                description="Institution declared 200 admissions in preliminary declaration, but 196 eligible rows were parsed.",
                evidence_details={"declared_count": 200, "rows_received": 196, "variance": 4, "rule": "DECLARED_TOTAL_MISMATCH"},
                status=IssueStatus.OPEN,
                detected_at=datetime(2026, 7, 20, 14, 33),
            ),
            # Issue 4: Intake Capacity Exceeded in Mechanical Engineering (142 enrolled vs 138 limit)
            ValidationIssue(
                upload_batch_id=batch_coep.id,
                rule_code="INTAKE_CAPACITY_EXCEEDED",
                rule_version="v2026.1",
                severity=IssueSeverity.CRITICAL,
                institution_id=inst_coep.id,
                programme_id=prog_coep_mech.id,
                academic_year_id=ay_2026.id,
                title="Approved Intake Capacity Exceeded by 4 in Mechanical Engineering",
                description="Calculated enrolment (142) exceeds effective approved intake limit (138) under AICTE_APH_2026_V1 by 4 students.",
                evidence_details={"base_intake": 120, "supernumerary": 18, "effective_limit": 138, "calculated_enrolment": 142, "excess": 4, "source_eoa": "F.No. Western/1-10023841/2026/EOA"},
                status=IssueStatus.OPEN,
                detected_at=datetime(2026, 7, 20, 14, 35),
            ),
            # Issue 5: International Status vs Domestic Quota Inconsistency
            ValidationIssue(
                upload_batch_id=batch_coep.id,
                rule_code="CATEGORY_INCONSISTENCY",
                rule_version="v2026.1",
                severity=IssueSeverity.MEDIUM,
                institution_id=inst_coep.id,
                programme_id=prog_coep_cse.id,
                academic_year_id=ay_2026.id,
                affected_student_enrolment_id=all_created_enrolments[41][1].id,
                title="NRI Status Conflict with Reserved SC Quota",
                description="Student COEP-2026-CSE-042 is designated as NRI but recorded under domestic SC quota.",
                evidence_details={"student_id": "COEP-2026-CSE-042", "is_nri": True, "seat_category": "SC", "rule": "CATEGORY_INCONSISTENCY"},
                status=IssueStatus.OPEN,
                detected_at=datetime(2026, 7, 20, 14, 36),
            ),
            # Issue 6: Cross-Institution Duplicate Candidate #1
            ValidationIssue(
                upload_batch_id=batch_coep.id,
                rule_code="CROSS_INSTITUTION_DUPLICATE_CANDIDATE",
                rule_version="v2026.1",
                severity=IssueSeverity.HIGH,
                institution_id=inst_coep.id,
                programme_id=prog_coep_cse.id,
                academic_year_id=ay_2026.id,
                affected_student_enrolment_id=enrol_1.id,
                title=f"Potential Concurrent Enrolment: COEP & Anna University ({ident_1.masked_apaar_id})",
                description="Identical APAAR fingerprint detected in concurrent active enrolments at COEP CSE and CEG Anna Univ CSE.",
                evidence_details={"masked_apaar_id": ident_1.masked_apaar_id, "student_1": enrol_1.institution_student_id, "student_2": enrol_2.institution_student_id, "group_id": dup_group_1.id},
                status=IssueStatus.OPEN,
                detected_at=datetime(2026, 7, 21, 12, 00),
            ),
            # Issue 7: Cross-Institution Duplicate Candidate #2
            ValidationIssue(
                upload_batch_id=batch_vjti.id,
                rule_code="CROSS_INSTITUTION_DUPLICATE_CANDIDATE",
                rule_version="v2026.1",
                severity=IssueSeverity.HIGH,
                institution_id=inst_vjti.id,
                programme_id=prog_vjti_cse.id,
                academic_year_id=ay_2026.id,
                affected_student_enrolment_id=enrol_4.id,
                title=f"Name & DOB Duplicate Candidate: VJTI & COEP ({ident_4.legal_name})",
                description="Matching full legal name and birthdate detected across distinct institutions (COEP ECE & VJTI CSE).",
                evidence_details={"student_name": ident_4.legal_name, "dob": ident_4.dob.isoformat(), "group_id": dup_group_2.id},
                status=IssueStatus.OPEN,
                detected_at=datetime(2026, 7, 22, 17, 00),
            ),
            # Issue 8: Format readiness check failure (10-digit APAAR)
            ValidationIssue(
                upload_batch_id=batch_coep.id,
                rule_code="APAAR_FORMAT_READINESS",
                rule_version="v2026.1",
                severity=IssueSeverity.HIGH,
                institution_id=inst_coep.id,
                programme_id=prog_coep_cse.id,
                academic_year_id=ay_2026.id,
                affected_student_enrolment_id=all_created_enrolments[87][1].id,
                title="APAAR Format Readiness Failed (10 Digits Instead of 12)",
                description="Identifier failed structural check: expected 12 numeric digits, received 10 digits.",
                evidence_details={"student_id": "COEP-2026-CSE-088", "received_len": 10, "rule": "APAAR_FORMAT_READINESS"},
                status=IssueStatus.OPEN,
                detected_at=datetime(2026, 7, 20, 14, 38),
            ),
            # Issue 9: In-File Duplicate Row
            ValidationIssue(
                upload_batch_id=batch_coep.id,
                rule_code="FILE_DUPLICATE_ROW",
                rule_version="v2026.1",
                severity=IssueSeverity.CRITICAL,
                institution_id=inst_coep.id,
                programme_id=prog_coep_cse.id,
                academic_year_id=ay_2026.id,
                title="Duplicate Student Row Detected in Upload Staging",
                description="Upload row 198 duplicates student identifier of row 44 within the same batch file.",
                evidence_details={"row_number": 198, "duplicate_of_row": 44, "student_id": "COEP-2026-CSE-044"},
                status=IssueStatus.OPEN,
                detected_at=datetime(2026, 7, 20, 14, 39),
            ),
            # Issue 10: Institutional Student ID Clash
            ValidationIssue(
                upload_batch_id=batch_coep.id,
                rule_code="INSTITUTION_DUPLICATE_CHECK",
                rule_version="v2026.1",
                severity=IssueSeverity.HIGH,
                institution_id=inst_coep.id,
                programme_id=prog_coep_ece.id,
                academic_year_id=ay_2026.id,
                title="Repeated Student Roll Number Conflict",
                description="Roll number COEP-2026-ECE-033 clashes with an existing registered enrolment record.",
                evidence_details={"student_id": "COEP-2026-ECE-033", "scope": "INSTITUTION"},
                status=IssueStatus.ASSIGNED,
                assigned_to_user_id=demo_users[3].id,
                reviewer_notes="Assigned to Dr. Rajiv for checking registration registrar ledger.",
                detected_at=datetime(2026, 7, 20, 14, 40),
            ),
            # Issue 11: AI Secondary Anomaly Signal (Sudden Utilization Shift in VJTI)
            ValidationIssue(
                upload_batch_id=batch_vjti.id,
                rule_code="HISTORICAL_UTILIZATION_ANOMALY",
                rule_version="v2026.1",
                severity=IssueSeverity.MEDIUM,
                institution_id=inst_vjti.id,
                programme_id=prog_vjti_cse.id,
                academic_year_id=ay_2026.id,
                title="AI Anomaly Signal: Sharp Enrolment Spike vs 3-Year Baseline",
                description="Machine-learning secondary anomaly detector observed a +38% intake utilization deviation against historical mean.",
                evidence_details={"algorithm": "IsolationForest", "historical_mean": 64.2, "current_utilization": 88.3, "delta": 24.1, "is_secondary_signal": True},
                status=IssueStatus.OPEN,
                detected_at=datetime(2026, 7, 22, 17, 10),
            ),
            # Issue 12: Category Unrecognized / Mapped to Unknown
            ValidationIssue(
                upload_batch_id=batch_anna.id,
                rule_code="CATEGORY_CONSISTENCY",
                rule_version="v2026.1",
                severity=IssueSeverity.LOW,
                institution_id=inst_anna.id,
                programme_id=prog_anna_cse.id,
                academic_year_id=ay_2026.id,
                title="Unsupported Category Value 'SPECIAL_SPORTS' Mapped to UNKNOWN",
                description="Institution provided non-standard admission category 'SPECIAL_SPORTS'. Normalized to UNKNOWN pending AICTE verification.",
                evidence_details={"raw_category": "SPECIAL_SPORTS", "normalized_to": "UNKNOWN"},
                status=IssueStatus.RESOLVED,
                assigned_to_user_id=demo_users[3].id,
                reviewer_notes="Resolved: mapped as state autonomous sports quota under OPEN category.",
                resolution_reason="Confirmed valid autonomous sports quota reservation under state guidelines.",
                detected_at=datetime(2026, 7, 21, 11, 20),
                resolved_at=datetime(2026, 7, 23, 10, 00),
            ),
        ]
        db.add_all(seeded_issues)
        db.commit()

        # Seed review decisions for issue #2 and #12
        db.add(
            ReviewDecision(
                validation_issue_id=seeded_issues[1].id,
                actor_user_id=demo_users[3].id,
                action="REQUEST_CORRECTION",
                previous_status=IssueStatus.OPEN,
                new_status=IssueStatus.CORRECTION_REQUESTED,
                reason="Mandatory APAAR reference missing from submission",
                notes="Institution data operator requested to upload APAAR registration proof.",
                timestamp=datetime(2026, 7, 21, 14, 0),
            )
        )
        db.add(
            ReviewDecision(
                validation_issue_id=seeded_issues[11].id,
                actor_user_id=demo_users[3].id,
                action="RESOLVE",
                previous_status=IssueStatus.OPEN,
                new_status=IssueStatus.RESOLVED,
                reason="State sports quota reservation documented",
                notes="Documentation checked against Tamil Nadu state sports quota annexure.",
                timestamp=datetime(2026, 7, 23, 10, 0),
            )
        )
        db.commit()

        print("--- 10. Seeding Sample Certificate Credentials ---")
        # Generate degree certificate for student 1
        ident_sample = all_created_enrolments[0][0]
        enrol_sample = all_created_enrolments[0][1]
        cert_sample = CertificateCredential(
            student_enrolment_id=enrol_sample.id,
            certificate_number="CERT-2026-COEP-0001",
            degree_awarding_body="COEP Technological University (Unitary Public University)",
            degree_name="Bachelor of Technology in Computer Science and Engineering",
            grade_or_division="First Class with Distinction",
            issue_date=datetime(2026, 7, 25),
            masked_apaar_id=ident_sample.masked_apaar_id,
            student_id_ref=enrol_sample.institution_student_id,
            qr_verification_slug="coep-cse-2026-0001",
            is_revoked=False,
        )
        db.add(cert_sample)
        db.commit()

        print("--- 11. Seeding Audit Events ---")
        events = [
            AuditEvent(
                event_type=AuditEventType.AUTH_LOGIN,
                actor_user_id=demo_users[0].id,
                actor_role=UserRole.AICTE_ADMIN,
                actor_email=demo_users[0].email,
                resource_type="SYSTEM",
                action_outcome="SUCCESS",
                event_details={"action": "AICTE Admin login from secure subnet"},
                timestamp=datetime(2026, 7, 20, 9, 0),
            ),
            AuditEvent(
                event_type=AuditEventType.EOA_DOCUMENT_CONFIRMED,
                actor_user_id=demo_users[0].id,
                actor_role=UserRole.AICTE_ADMIN,
                actor_email=demo_users[0].email,
                institution_id=inst_coep.id,
                resource_type="SOURCE_DOCUMENT",
                resource_id=str(eoa_coep_2026.id),
                action_outcome="SUCCESS",
                event_details={"reference_number": eoa_coep_2026.reference_number, "status": "CONFIRMED"},
                timestamp=datetime(2026, 7, 20, 9, 30),
            ),
            AuditEvent(
                event_type=AuditEventType.RECORDS_COMMITTED,
                actor_user_id=demo_users[1].id,
                actor_role=UserRole.INSTITUTION_ADMIN,
                actor_email=demo_users[1].email,
                institution_id=inst_coep.id,
                resource_type="UPLOAD_BATCH",
                resource_id=str(batch_coep.id),
                action_outcome="SUCCESS",
                event_details={"batch_id": batch_coep.id, "records_committed": 335, "issues_generated": 8},
                timestamp=datetime(2026, 7, 20, 14, 30),
            ),
            AuditEvent(
                event_type=AuditEventType.ISSUE_STATUS_CHANGED,
                actor_user_id=demo_users[3].id,
                actor_role=UserRole.AUTHORIZED_REVIEWER,
                actor_email=demo_users[3].email,
                institution_id=inst_coep.id,
                resource_type="VALIDATION_ISSUE",
                resource_id=str(seeded_issues[1].id),
                action_outcome="SUCCESS",
                event_details={"action": "REQUEST_CORRECTION", "issue_id": seeded_issues[1].id},
                timestamp=datetime(2026, 7, 21, 14, 0),
            ),
        ]
        db.add_all(events)
        db.commit()

        print("=== Database Seeding Complete! ===")
        print(f"Institutions: {db.query(Institution).count()}")
        print(f"Programmes: {db.query(Programme).count()}")
        print(f"Approval Intakes: {db.query(ApprovalIntake).count()}")
        print(f"Student Enrolments: {db.query(StudentEnrolment).count()}")
        print(f"Validation Issues: {db.query(ValidationIssue).count()}")
        print(f"Duplicate Candidate Groups: {db.query(DuplicateCandidateGroup).count()}")
        print(f"Audit Events: {db.query(AuditEvent).count()}")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
