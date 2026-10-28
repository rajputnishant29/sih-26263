# EDUTrace — Feature Specification & Implementation Flows

**Problem Statement:** SIH26263  
**Project:** APAAR ID-Based Student Data Management and Verification Platform  
**Target Organization:** AICTE (All India Council for Technical Education)  
**Document Version:** 1.0.0 (High-Level Implementation & Pseudocode Reference)

---

## 1. Operational Overview & Six-Stage Lifecycle

EDUTrace executes an end-to-end governance lifecycle spanning six distinct operational phases:

$$\text{INGEST} \longrightarrow \text{VALIDATE} \longrightarrow \text{RECONCILE} \longrightarrow \text{REVIEW} \longrightarrow \text{RESOLVE} \longrightarrow \text{MONITOR}$$

1. **INGEST:** Institution uploads student admissions via CSV/Excel or structured API, providing institution, academic year, and programme scope.
2. **VALIDATE:** Schema verification, 12-digit APAAR format readiness checks, required fields, and in-file duplicate detection.
3. **RECONCILE:** Active enrolments are compared against approved intake limits (Base Approved Intake + Supernumerary) and declared counts.
4. **REVIEW:** Issues, duplicates, and over-capacity warnings are presented in an actionable review queue with exact evidence and rule citations.
5. **RESOLVE:** Authorized reviewers and institutional administrators record decisions, request corrections, or resolve issues with immutable action logs.
6. **MONITOR:** Aggregated metrics, institutional compliance cards, audit trails, and reports update in real time via Server-Sent Events.

---

## 2. Role-Based Feature Access Matrix

| Feature Module | AICTE Admin | Institution Admin | Data Operator | Authorized Reviewer | External Verifier |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **National Command Dashboard** | Full Access | Scoped to Inst | Scoped to Inst | View Only | ❌ |
| **Institution Profiles** | All Institutions | Own Institution | Own Institution | View Only | ❌ |
| **Programme & EoA Management** | Full Access | View Only | View Only | View Only | ❌ |
| **Upload Staging Wizard** | ❌ | Full Access | Full Access | ❌ | ❌ |
| **Student Records Repository** | All Records | Own Records | Own Records | All Records | ❌ |
| **Exceptions & Review Queue** | Full Access | Respond Only | View Only | Full Decision Power | ❌ |
| **Record Corrections** | Authorized | Submit Request | ❌ | Approve/Reject | ❌ |
| **Purpose-Bound Verification** | View Results | View Results | ❌ | View Results | Full Access |
| **Verifiable Certificate Preview** | Full Access | Full Access | ❌ | Full Access | Verification Only |
| **Sanitized Report CSV Export** | National Scope | Institution Scope | ❌ | View Only | ❌ |
| **Tamper-Evident Audit Trail** | Full Access | Institution Scope | ❌ | View Only | ❌ |

---

## 3. High-Level Feature Specifications & Pseudocode

---

### Feature 1: Authentication & Demo Persona Quick-Switching
- **User Intent:** Secure login with role-based access; provides one-click persona switching for hackathon evaluation and demonstration.
- **Client UX:** Government-branded login screen featuring 5 quick-login persona cards with role descriptions and credentials pre-filled, plus a visible synthetic data warning.

#### Frontend Pseudocode
```
FUNCTION onQuickLoginClick(personaRole, userEmail):
    SET credentials = { email: userEmail, password: "Demo@2026" }
    CALL api.login(credentials)
        ON SUCCESS (response):
            SAVE response.access_token IN localStorage
            UPDATE AuthContext with response.user (role, institution_id)
            REDIRECT to Dashboard ("/")
        ON FAILURE (error):
            DISPLAY error notification banner
```

#### Backend Pseudocode
```
FUNCTION handle_login(request: LoginRequest, db: DatabaseSession):
    FIND user BY email IN database
    IF user NOT FOUND OR NOT verify_password(request.password, user.hashed_password):
        THROW 401 Unauthorized ("Invalid credentials")
    IF user.is_active IS FALSE:
        THROW 401 Unauthorized ("Account deactivated")

    CREATE jwt_token WITH payload { sub: user.id, role: user.role, email: user.email }
    LOG_AUDIT_EVENT(event_type="AUTH_LOGIN", actor=user, outcome="SUCCESS")
    RETURN { access_token: jwt_token, user: user.summary }
```

---

### Feature 2: AICTE Command & National Regulatory Dashboard
- **User Intent:** Holistic, real-time national oversight over approved intake vs actual enrolments, supernumerary quotas, and unresolved exceptions.
- **Client UX:** Top KPI cards (Institutions, Programmes, Approved Intake, Actual Enrolment, Supernumerary Seats, Unresolved Issues, Duplicate Candidates), comparative bar charts, category distribution pies, and a live intake reconciliation table with warning highlights.

#### Frontend Pseudocode
```
FUNCTION DashboardComponent():
    SUBSCRIBE to Server-Sent Events stream ("/api/dashboard/live-stream")
        ON "records_committed" OR "issue_resolved":
            TRIGGER React Query refetch for "dashboard-summary"

    FETCH summary FROM api.getDashboardSummary(selectedAcademicYear, selectedInstitution)
    RENDER MetricCard("Institutions Onboarded", summary.total_institutions)
    RENDER MetricCard("Approved Intake", summary.total_approved_intake)
    RENDER MetricCard("Actual Enrolment", summary.total_actual_enrolment)
    RENDER MetricCard("Intake Utilization", summary.intake_utilization_rate + "%")
    
    RENDER ReconciliationTable(summary.reconciliation_summaries)
        HIGHLIGHT row RED IF row.is_exceeded IS TRUE (Variance > 0)
    RENDER RechartsBarChart(summary.academic_year_trends)
    RENDER RechartsPieChart(summary.category_distributions)
```

#### Backend Pseudocode
```
FUNCTION get_dashboard_summary(academic_year_id, institution_id, user, db):
    ENFORCE_INSTITUTION_SCOPE(user, institution_id)
    AGGREGATE total_institutions, total_programmes FROM database
    COMPUTE total_approved_intake = SUM(approval_intakes.effective_limit)
    COMPUTE total_enrolled = COUNT(active eligible student_enrolments)
    COMPUTE unresolved_issues = COUNT(validation_issues WHERE status != 'RESOLVED')
    COMPUTE duplicate_candidates = COUNT(duplicate_candidate_groups)

    FOREACH programme IN approval_intakes:
        actual = COUNT(active enrolments for this programme)
        is_exceeded = actual > programme.effective_limit
        BUILD reconciliation_summary_row(programme, actual, is_exceeded)

    RETURN aggregated_summary_payload WITH synthetic_disclaimer
```

---

### Feature 3: Institutional Profiles & Multi-Campus Management
- **User Intent:** Detailed institutional views showing sanctioned programmes, intake history, upload logs, and compliance scorecards.
- **Client UX:** Filterable directory of technical universities with search by name/code, leading to an institution profile page with tabs for Programmes, Admissions, Exceptions, and Upload History.

#### Implementation Pseudocode
```
FRONTEND:
    FETCH institutions FROM api.getInstitutions(searchQuery)
    RENDER Table with columns: Institution Name, Code, State, Total Programmes, Enrolment, Status
    ON CLICK institution:
        NAVIGATE to "/institutions/:id"
        RENDER Tabs: [Programmes & Intake, Enrolment Summary, Open Findings, Upload History]

BACKEND:
    FUNCTION get_institution_detail(institution_id, user, db):
        ENFORCE_INSTITUTION_SCOPE(user, institution_id)
        RETRIEVE institution, its programmes, approval_intakes, and active enrolment counts
        RETURN structured institution_profile WITH recent audit events
```

---

### Feature 4: Programme Approval & EoA Document Parser Workflow
- **User Intent:** Register official Extension of Approval (EoA) documents, extract approved intake metadata via automated heuristics, and preserve human confirmation provenance.
- **Client UX:** Upload dropzone for AICTE EoA approval letters, displaying extracted text, confidence score, sanctioned programmes, and a confirmation button that converts extracted intake into authoritative baseline metadata.

#### Implementation Pseudocode
```
FRONTEND:
    ON fileDrop(eoa_file):
        UPLOAD file via FormData to api.parseEoA(formData)
        DISPLAY ExtractedPreview:
            Reference Number: eoa_response.reference_number
            Academic Year: eoa_response.academic_year
            Programmes Found: eoa_response.extracted_programmes (Code, Base Intake)
            Extraction Confidence: eoa_response.confidence_score
        RENDER Button "Confirm & Apply to Official Metadata"
            ON CLICK: CALL api.confirmEoA(payload) -> REFRESH approval baseline

BACKEND:
    FUNCTION parse_eoa_document(file_bytes):
        EXTRACT raw_text USING pypdf / regex pattern matching
        MATCH regex for EoA Letter Reference: r"F\.No\.\s+([A-Za-z]+)/1-(\d+)/(\d{4})/EOA"
        MATCH tabular blocks for Programme Name and Approved Intake digits
        RETURN { reference_number, academic_year, extracted_programmes, status: "MACHINE_EXTRACTED" }

    FUNCTION confirm_eoa_document(confirmed_data, user, db):
        SAVE source_document WITH status = "CONFIRMED", confirmed_by = user.id
        UPSERT approval_intakes FOR each programme WITH base_intake AND effective_limit
        LOG_AUDIT_EVENT("EOA_DOCUMENT_CONFIRMED", resource_id=source_document.id)
```

---

### Feature 5: Guided Student Data Upload Staging Wizard
- **User Intent:** Safe, multi-step onboarding of student admission spreadsheets with dry-run validation before committing data to the database.
- **Client UX:** 4-step wizard:
  1. Scope Selection (Institution, Academic Year, Programme, Declared Total).
  2. File Upload & Column Mapping.
  3. Dry-Run Validation Inspection (view valid rows, errors, intake impact).
  4. Final Atomic Commit with persistent results.

#### Implementation Pseudocode
```
FRONTEND:
    STEP 1: User selects Institution, Academic Year, Programme, inputs Declared Count (e.g. 10)
    STEP 2: User selects CSV file -> CALL api.stageUpload(formData)
            RECEIVE batch_id and staging row count
    STEP 3: User clicks "Run Dry-Run Validation" -> CALL api.validateUpload(batch_id)
            DISPLAY ValidationSummary:
                Valid Rows: validation.valid_count
                Errors: validation.error_count
                Warnings: validation.warning_count
                Intake Capacity Impact: validation.intake_reconciliation.is_exceeded
                Declared Count Variance: validation.declaration_reconciliation.variance
            RENDER Table of row previews with error badges
    STEP 4: User clicks "Confirm & Commit Records" -> CALL api.commitUpload(batch_id)
            DISPLAY Success Screen with committed count and generated issues count
            BROADCAST SSE event to update dashboard

BACKEND:
    FUNCTION stage_file(file, institution_id, academic_year_id, declared_count):
        PARSE CSV into memory using pandas
        CREATE upload_batch RECORD in state 'STAGED'
        INSERT parsed rows into upload_staging_rows table (raw JSON)
        RETURN batch_summary

    FUNCTION validate_upload(batch_id):
        RETRIEVE staging rows for batch_id
        FOREACH row IN staging_rows:
            RUN DeterministicValidator(row) -> check APAAR format, duplicates, required fields
        RUN AdmissionReconciler(staged_valid_count + existing_enrolments vs effective_limit)
        RUN DeclarationReconciler(declared_count vs staged_rows_count)
        RETURN dry_run_summary (NO records permanently written yet)

    FUNCTION commit_upload(batch_id, user, db):
        BEGIN DATABASE TRANSACTION:
            LOCK upload_batch FOR UPDATE
            FOREACH valid staging row:
                HMAC_FINGERPRINT = compute_hmac(row.apaar_id, row.name)
                UPSERT student_identity WITH fingerprint AND masked_apaar
                INSERT student_enrolment linked to identity, institution, and programme
            SAVE any generated validation_issues
            UPDATE upload_batch status to 'COMMITTED'
            LOG_AUDIT_EVENT("RECORDS_COMMITTED", batch_id)
        COMMIT TRANSACTION
        EMIT_SSE_EVENT("records_committed", { batch_id: batch_id })
```

---

### Feature 6: Student Records Repository & Masked APAAR Explorer
- **User Intent:** Search, filter, and inspect enrolled students with complete privacy safeguards (masked identity identifiers).
- **Client UX:** Paginated, responsive data table with server-side filters for Institution, Programme, Academic Year, and Enrolment Status. APAAR IDs are masked by default (`APAAR-****-****-0501`) with a copy-masked action.

#### Implementation Pseudocode
```
FRONTEND:
    FETCH enrolments FROM api.getEnrolments({ page, limit, search, institution_id, programme_id })
    RENDER Table columns:
        Student ID, Masked APAAR ID, Legal Name, Programme, Category, Supernumerary Tag, Status
    ON CLICK row:
        OPEN EnrolmentDetailDrawer showing:
            Personal Metadata (DoB, Gender, State)
            Admission Source & Provenance
            Associated Validation Findings
            Record Correction History
            Button "Generate Certificate Preview"

BACKEND:
    FUNCTION list_enrolments(page, limit, search, institution_id, user, db):
        ENFORCE_INSTITUTION_SCOPE(user, institution_id)
        QUERY student_enrolments JOIN student_identities
        APPLY filters (programme_id, academic_year_id, status)
        IF search query present:
            FILTER BY student_enrolments.institution_student_id ILIKE search OR student_identities.legal_name ILIKE search
        ORDER BY admission_date DESC
        PAGINATE and RETURN items WITH total_count
```

---

### Feature 7: Validation Exceptions Queue & Anomaly Review
- **User Intent:** Comprehensive review center listing all automated findings categorized by severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) and status (`OPEN`, `ASSIGNED`, `CORRECTION_REQUESTED`, `RESOLVED`).
- **Client UX:** Filterable issue cards displaying triggering rule, rule version, affected institution, detection timestamp, and severity badge. Clicking an issue opens the evidence drawer.

#### Implementation Pseudocode
```
FRONTEND:
    FETCH issues FROM api.getIssues({ severity, status, institution_id })
    RENDER IssueList:
        DISPLAY IssueTitle, TriggeringRule, SeverityBadge, InstitutionName, DetectionDate
    ON CLICK issue:
        OPEN IssueEvidenceDrawer:
            RENDER Triggering Rule Description & Citing Standard (e.g. AICTE_APH_2026_V1)
            RENDER Evidence JSON Block (e.g. Effective Limit: 138, Calculated: 140, Excess: 2)
            RENDER Action Form: Action Type, Reason, Reviewer Notes, Submit Button
```

---

### Feature 8: Human Review Decision Workflow & Record Correction Tracking
- **User Intent:** Authorized reviewers record binding decisions (`REQUEST_CORRECTION`, `RESOLVE`, `MARK_FALSE_POSITIVE`, `ASSIGN`) with full accountability; institution users submit field corrections.
- **Client UX:** Interactive decision action box in the issue drawer. Submitting an action updates the issue status and appends a permanent entry in the decision history tab.

#### Implementation Pseudocode
```
FRONTEND:
    FUNCTION onRecordDecision(issueId, actionType, reasonText, notes):
        CALL api.recordDecision(issueId, { action: actionType, reason: reasonText, notes: notes })
        UPDATE issue status in UI state
        DISPLAY Success Toast: "Decision recorded successfully"

BACKEND:
    FUNCTION record_issue_decision(issue_id, payload, user, db):
        REQUIRE_ROLE(user, [AUTHORIZED_REVIEWER, AICTE_ADMIN])
        FIND issue BY issue_id
        INSERT review_decision RECORD:
            issue_id = issue.id, reviewer_id = user.id, action = payload.action,
            reason = payload.reason, notes = payload.notes, timestamp = NOW()
        UPDATE issue.status:
            IF payload.action == 'REQUEST_CORRECTION' -> 'CORRECTION_REQUESTED'
            IF payload.action == 'RESOLVE'            -> 'RESOLVED'
            IF payload.action == 'MARK_FALSE_POSITIVE' -> 'RESOLVED'
        LOG_AUDIT_EVENT("ISSUE_STATUS_CHANGED", issue_id, outcome="SUCCESS")
        RETURN { status: "SUCCESS", new_status: issue.status }
```

---

### Feature 9: Purpose-Bound External Verification Portal
- **User Intent:** Employers and higher-ed regulators verify student enrolment credentials with a mandatory legal purpose and consent proof reference.
- **Client UX:** Purpose-bound query form requiring: Student Identifier, Requester Organization, Purpose (e.g. `EMPLOYMENT_BACKGROUND_CHECK`), and Consent Proof Reference. Submitting returns permitted claims with a synthetic provider disclaimer.

#### Implementation Pseudocode
```
FRONTEND:
    SUBMIT VerificationForm with { query_identifier, requester_organization, purpose, consent_proof_ref }
    CALL api.submitVerification(formValues)
    RENDER ResultCard:
        Status: response.verification_status ("VERIFIED_LOCAL" or "RECORD_NOT_FOUND")
        Student Name: response.student_name
        Masked APAAR: response.masked_apaar_id
        Institution: response.institution_name
        Programme: response.programme_name
        Verification Reference: response.verification_reference
        RENDER Disclaimer Alert: "Verified against synthetic EDUTrace prototype repository."

BACKEND:
    FUNCTION process_verification(request: VerificationRequestPayload, user, db):
        REQUIRE_ROLE(user, [EXTERNAL_VERIFIER, AICTE_ADMIN])
        FIND enrolment BY institution_student_id == request.query_identifier
        IF NOT FOUND:
            RECORD verification_request IN audit WITH status = 'RECORD_NOT_FOUND'
            RETURN { verification_status: "RECORD_NOT_FOUND", message: "No matching record." }

        GENERATE verification_ref = "EDUTRACE-VERIF-" + random_hex()
        SAVE verification_request IN db WITH purpose, requester, consent_ref, verification_ref
        LOG_AUDIT_EVENT("VERIFICATION_REQUESTED", resource_id=verification_ref)
        RETURN {
            verification_status: "VERIFIED_LOCAL",
            verification_provider: "SIMULATED_LOCAL_REPOSITORY",
            student_name: enrolment.student_identity.legal_name,
            student_id: enrolment.institution_student_id,
            masked_apaar_id: enrolment.student_identity.masked_apaar_id,
            institution_name: enrolment.institution.name,
            programme_name: enrolment.programme.name,
            verification_reference: verification_ref,
            disclaimer: "Verified against synthetic EDUTrace prototype repository."
        }
```

---

### Feature 10: Verifiable Degree Credential Preview & QR Route
- **User Intent:** Printable student credential preview displaying the APAAR ID directly alongside the student ID, degree-awarding body, and a working prototype QR verification route.
- **Client UX:** Formal certificate card styled with national emblems, student details, degree-awarding university, a prominent watermark (`NOT AN OFFICIAL CERTIFICATE — SYNTHETIC DEMO CREDENTIAL`), and a QR code linking to `/verify/:slug`.

#### Implementation Pseudocode
```
FRONTEND:
    FETCH credential FROM api.getCertificatePreview(enrolmentId)
    RENDER CertificateLayout:
        Title: credential.degree_awarding_body
        Award Text: "Bachelor of Technology in " + credential.degree_name
        Recipient: credential.student_name
        Side-by-Side Identity:
            Student Roll No : credential.student_id
            APAAR Identifier: credential.masked_apaar_id
        Watermark: credential.watermark_text
        QRCode: pointing to window.location.origin + credential.qr_verification_url
    RENDER Button "Print / Export PDF" (triggers window.print() with print-only styles)

BACKEND (QR Verification Route):
    FUNCTION verify_qr_slug(slug, db):
        FIND credential BY qr_verification_slug == slug
        IF NOT FOUND OR credential.is_revoked IS TRUE:
            THROW 404 ("Invalid or revoked credential")
        RETURN {
            is_valid: True,
            status: "VALID_PROTOTYPE_RECORD",
            student_name: credential.student_enrolment.student_identity.legal_name,
            student_id: credential.student_enrolment.institution_student_id,
            masked_apaar_id: credential.student_enrolment.student_identity.masked_apaar_id,
            degree_awarding_body: credential.degree_awarding_body,
            programme_name: credential.degree_name
        }
```

---

### Feature 11: Regulatory Reports & Sanitized CSV Export
- **User Intent:** Filterable intake reconciliation reports with CSV export protected against spreadsheet formula injection.
- **Client UX:** Filter bar for Academic Year and Institution, aggregated summary cards, and a button "Export Filtered CSV" which downloads a sanitized spreadsheet.

#### Implementation Pseudocode
```
FRONTEND:
    ON CLICK "Export Filtered CSV":
        DOWNLOAD file FROM "/api/reports/reconciliation/export-csv?academic_year_id=...&institution_id=..."

BACKEND:
    FUNCTION export_reconciliation_csv(academic_year_id, institution_id, user, db):
        ENFORCE_INSTITUTION_SCOPE(user, institution_id)
        ROWS = compute_reconciliation_report(academic_year_id, institution_id, db)
        
        CSV_BUFFER = StringIO()
        FOREACH row IN ROWS:
            # Formula Injection Defense
            FOREACH field, value IN row:
                IF string value starts with ('=', '+', '-', '@', '\t', '\r'):
                    value = "'" + value   # Prepend single quote
            WRITE sanitized row to CSV_BUFFER
            
        LOG_AUDIT_EVENT("REPORT_EXPORTED", resource_id="RECONCILIATION_CSV")
        RETURN CSVResponse(CSV_BUFFER.getvalue(), filename="edutrace_reconciliation_report.csv")
```

---

### Feature 12: Tamper-Evident Append-Only Audit Trail Viewer
- **User Intent:** Transparent, immutable accountability for every critical action (logins, uploads, dry-runs, commits, reviewer decisions, verifications).
- **Client UX:** Audit log table with filter by Event Type, Actor, and Date Range. Shows Actor Email, Role Code, Resource Type, Action Outcome, and IP Address.

#### Implementation Pseudocode
```
FRONTEND:
    FETCH logs FROM api.getAuditLogs({ event_type, page, limit })
    RENDER AuditTable:
        Columns: Timestamp, Actor, Role, Institution, Event Type, Resource, Outcome, IP Address
    ROW click: view raw sanitized event details JSON

BACKEND:
    FUNCTION log_audit_event(event_type, resource_type, resource_id, actor, outcome, details, db):
        SANATIZE details -> REMOVE any raw passwords, tokens, or plaintext APAARs
        INSERT INTO audit_events:
            event_type = event_type, actor_id = actor.id, actor_email = actor.email,
            actor_role = actor.role, resource_type = resource_type,
            resource_id = str(resource_id), action_outcome = outcome,
            event_details = details, timestamp = UTC_NOW()
        # Note: audit_events table has NO update or delete API endpoints (Append-Only)
```

---

### Feature 13: Versioned Rule Registry & Integration Health Status
- **User Intent:** Inspect versioned validation rules (e.g. `AICTE_APH_2026_V1`), active thresholds, and adapter status across local simulation and production roadmap APIs.
- **Client UX:** Dual tab interface:
  - **Rule Definitions:** Displays Rule Code, Version, Category, Default Severity, and Description.
  - **Integration Status:** Clear cards showing whether APAAR/DigiLocker, AICTE Approval Portal, and State DTE adapters are `SIMULATED_LOCAL` or `PRODUCTION_PENDING`.

#### Implementation Pseudocode
```
FRONTEND:
    FETCH rules FROM api.getRules()
    FETCH integrations FROM api.getIntegrationStatus()
    RENDER RulesTable(rules)
    RENDER IntegrationCards(integrations):
        DISPLAY Badge "SIMULATED LOCAL" for DigiLocker APAAR Adapter
        DISPLAY Badge "SIMULATED LOCAL" for AICTE EoA OCR Pipeline
        DISPLAY Disclaimer: "Mock integrations never represent live government endpoints."

BACKEND:
    FUNCTION get_integration_status():
        RETURN [
            { name: "APAAR / DigiLocker Registry", mode: "SIMULATED_LOCAL", is_production: False },
            { name: "AICTE EoA Document Parser", mode: "HEURISTIC_PARSER", is_production: False },
            { name: "State Admission Authority Feed", mode: "PLANNED_PHASE_2", is_production: False }
        ]
```

---

### Feature 14: Requirements Traceability Matrix View
- **User Intent:** In-application compliance inspection matching every SIH26263 requirement to backend modules, APIs, test suites, and empirical evaluation results.
- **Client UX:** Table displaying Requirement ID, Description, Implementing Files, Test Suites, and Verification Status (`100% Implemented & Tested`).
