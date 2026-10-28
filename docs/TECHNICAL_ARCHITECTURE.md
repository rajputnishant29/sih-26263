# EDUTrace — Technical Architecture & Implementation Documentation

**Problem Statement:** SIH26263  
**Project:** APAAR ID-Based Student Data Management and Verification Platform  
**Target Organization:** AICTE (All India Council for Technical Education)  
**System Architecture:** Modular Monolith (FastAPI + PostgreSQL 16 + React 19 / TypeScript)  
**Document Version:** 1.0.0 (SIH 2026 Production-Grade Prototype)

---

## 1. System Architecture & High-Level Design

EDUTrace is engineered as a high-performance **modular monolith** with clear boundary separation between domain models, computational engines, security filters, data persistence layers, and client-facing interfaces.

```
                              ┌──────────────────────────────────────────────┐
                              │    React 19 + TypeScript + Tailwind v4 UI    │
                              └──────────────────────┬───────────────────────┘
                                                     │ HTTP / JSON / SSE
                                                     ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       FastAPI Backend Application                                      │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  REST API Routing & Dependency Injection:                                                             │
│    • /api/auth          • /api/dashboard      • /api/institutions    • /api/programmes                │
│    • /api/enrolments    • /api/uploads        • /api/issues          • /api/verifications             │
│    • /api/certificates  • /api/reports        • /api/audit-logs      • /api/rules                     │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  Security & Middleware Filter Pipeline:                                                               │
│    • JWT Bearer Authentication (`get_current_user`)                                                   │
│    • Institutional Tenant Isolation Filter (`enforce_institution_scope`)                              │
│    • Starlette Native SSE Live Notification Broker (`EventBroker`)                                    │
│    • CORS & Global Exception Guard (Sanitized production error responses)                             │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  Core Computational Engines:                                                                           │
│    1. DeterministicValidator    : 12-digit format readiness, duplicate checks, required fields        │
│    2. AdmissionReconciler       : Approved intake + supernumerary quotas vs calculated enrolment       │
│    3. DuplicateDetector         : Cross-institutional student collision identification (HMAC link)   │
│    4. AnomalyDetector           : scikit-learn IsolationForest secondary historical anomaly alerts    │
│    5. EoAParserService          : Regex & structural extraction of official AICTE EoA approval letters │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  Service & Business Layer:                                                                             │
│    • UploadService (Staging, dry-run, atomic commit)     • AuditService (Append-only event logger)    │
│    • ReviewService (Issue decisions & record history)   • VerificationService (Purpose-bound checks)  │
│    • CertificateService (Credential preview & QR slugs) • ReportService (Formula-injection defense)   │
└────────────────────────────────────────────────────┬───────────────────────────────────────────────────┘
                                                     │ SQLAlchemy ORM (SessionPool)
                                                     ▼
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                PostgreSQL 16 Relational Database Engine                                │
│  21 Tables: student_identities, student_enrolments, approval_intakes, source_documents,               │
│             upload_batches, upload_staging_rows, validation_issues, review_decisions,                   │
│             duplicate_candidate_groups, verification_requests, audit_events, users, etc.              │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Architecture & Relational Schema Modeling

To comply with Section 23.A and strict regulatory accounting practices, EDUTrace enforces key structural invariants:

### 2.1 Separation of Student Identity from Institutional Enrolments
Rather than conflating a student with their institutional admission record, the database splits them into two distinct relational entities:
- `student_identities`: Represents the canonical human citizen. Stores the immutable `protected_identity_fingerprint` (HMAC-SHA256), the display-safe `masked_apaar_id`, legal name, date of birth, and gender.
- `student_enrolments`: Represents a specific enrolment event at an AICTE-approved institution. Stores foreign keys to `institution_id`, `programme_id`, `academic_year_id`, and `student_identity_id`, along with the institution-assigned `institution_student_id`, admission date, category, and status.

**Why this matters:** A student can legitimately hold multiple historical enrolments (e.g. Diploma followed by Degree, branch transfer, dual degrees). Uniqueness constraints are enforced on the institution-level student ID (`(institution_id, institution_student_id)`) and the identity fingerprint, preventing duplicate enrolments within the same programme year while allowing cross-institutional collision analysis.

### 2.2 Approval Intake as Programme-Level Metadata
Approved intake is **never** duplicated across student records. It is modeled in `approval_intakes`:
- `institution_id`, `programme_id`, `academic_year_id`
- `base_approved_intake` (sanctioned capacity from AICTE EoA letter)
- `supernumerary_quota` (sum of TFW, EWS, J&K, PMSSS, Foreign National approved quotas)
- `effective_limit` = `base_approved_intake` + `supernumerary_quota`
- `source_document_id` (foreign key to the official Extension of Approval letter)
- `rule_version` (e.g. `AICTE_APH_2026_V1`)

Actual enrolment is dynamically aggregated from valid, active `student_enrolments` rows.

### 2.3 Comprehensive Entity Relational Map

```
  ┌──────────────────┐         1:N         ┌──────────────────┐
  │   institutions   │◄────────────────────┤    programmes    │
  └────────┬─────────┘                     └─────────┬────────┘
           │ 1:N                                     │ 1:N
           ▼                                         ▼
  ┌───────────────────────────────────────────────────────────┐
  │                      approval_intakes                     │
  │  (base_approved_intake, supernumerary, effective_limit)   │
  └────────────────────────┬──────────────────────────────────┘
                           │ 1:N (intake limit rule)
                           ▼
  ┌────────────────────────┴──────────────────────────────────┐
  │                     student_enrolments                    │
  │  (institution_student_id, category, status, adm_date)    │
  └────────────────────────┬──────────────────────────────────┘
                           │ N:1
                           ▼
  ┌───────────────────────────────────────────────────────────┐
  │                     student_identities                    │
  │  (protected_identity_fingerprint, masked_apaar_id, name)  │
  └────────┬──────────────────────────────────────────────────┘
           │ 1:N
           ▼
  ┌───────────────────────────────────────────────────────────┐
  │                duplicate_candidate_members                │
  │        (links candidate identities for human review)       │
  └───────────────────────────────────────────────────────────┘
```

---

## 3. Cryptographic Identity Protection (Zero-PII Invariant)

To comply with the DPDP Act 2023 and the project's non-negotiable security mandates:

### 3.1 Deterministic Keyed HMAC-SHA256 Fingerprinting
Raw 12-digit APAAR identifiers are never stored directly in raw table columns. Instead, all cross-record identity comparisons use a deterministic keyed HMAC:

$$\text{Canonical String} = \text{"APAAR:"} \mathbin{\Vert} \text{raw\_apaar.strip()} \mathbin{\Vert} \text{":NAME:"} \mathbin{\Vert} \text{clean\_legal\_name}$$

$$\text{Fingerprint} = \text{HMAC-SHA256}(\text{HMAC\_SECRET\_KEY}, \text{Canonical String})$$

- **Collision Resistance:** Prevents dictionary and rainbow-table attacks that exploit simple SHA-256 hashes.
- **Key Isolation:** The cryptographic key resides in external environment configuration (`HMAC_SECRET_KEY`), never in client-accessible code.

### 3.2 Display Masking
Whenever an identity reference is exposed to authorized users (in dashboard tables, detail views, verification responses, and certificates), it is dynamically masked to show only the last 4 digits:
$$\text{"APAAR-****-****-0501"}$$

### 3.3 Zero-PII Audit Invariant
Application loggers, exception handlers, and the `audit_events` table are barred from recording raw APAAR numbers or plain student identifiers. Only UUIDs, masked strings, and resource identifiers are recorded.

---

## 4. Core Computational Engines

### 4.1 Deterministic Validation Engine (`DeterministicValidator`)
Located in `backend/app/engine/validator.py`, this engine runs pure, explainable, deterministic checks against incoming staging records:
1. **APAAR Presence (`APAAR_PRESENCE_CHECK`):** Checks if the identity field exists. Missing values trigger a `HIGH` severity finding.
2. **APAAR Format Readiness (`APAAR_FORMAT_READINESS`):** Checks that the reference consists of exactly 12 numeric digits without illegal characters or placeholder sequences (`000000000000`, `111111111111`).
3. **In-File Duplicate Detection (`FILE_DUPLICATE_ROW`):** Identifies rows within the same upload batch that share identical student IDs or identity references.
4. **Institutional Collision Check (`INSTITUTION_DUPLICATE_CHECK`):** Queries existing persisted enrolments in the same institution to prevent assigning the same `institution_student_id` twice.
5. **Category Consistency (`CATEGORY_INCONSISTENCY`):** Validates that students flagged as `is_supernumerary=True` declare an authorized supernumerary category (e.g. `TFW`, `EWS`, `J&K`, `PMSSS`), and that category allocations align with admission quotas.

### 4.2 Admission Reconciliation Engine (`AdmissionReconciler`)
Located in `backend/app/engine/reconciler.py`, this engine computes intake compliance for every institution, programme, and academic year:
1. **Capacity Equation:**
   $$\text{Calculated Enrolment} = \sum \text{Active Eligible Enrolments}$$
   $$\text{Effective Limit} = \text{Base Approved Intake} + \text{Sanctioned Supernumerary}$$
   $$\text{Variance} = \text{Calculated Enrolment} - \text{Effective Limit}$$
2. **Over-Capacity Trigger:** If $\text{Variance} > 0$, the engine generates an `INTAKE_CAPACITY_EXCEEDED` (`CRITICAL` severity) validation issue with exact evidence citing the AICTE Approval Process Handbook rule version and EoA source reference.
3. **Declaration Reconciliation:** Compares institution-declared admission totals with file rows parsed, staging rows accepted, rows rejected, and active enrolments persisted. Mismatches trigger `DECLARED_TOTAL_MISMATCH` (`MEDIUM` severity).

### 4.3 Cross-Institution Duplicate Candidate Detector (`DuplicateDetector`)
Located in `backend/app/engine/duplicate_detector.py`:
- Scans `student_identities` whose `protected_identity_fingerprint` is associated with active enrolments across two or more distinct institutions in the same academic year.
- Automatically clusters them into a `DuplicateCandidateGroup`.
- **Non-Punitive Design:** Flags the group as `CANDIDATE_MATCH` for human review. It **never** cancels an admission or alters student records automatically.

### 4.4 Secondary Anomaly Detection Engine (`AnomalyDetector`)
Located in `backend/app/engine/anomaly_detector.py`:
- Implements an unsupervised machine-learning secondary pipeline using **scikit-learn `IsolationForest`**.
- Evaluates multi-year historical intake utilization rates and category distribution shifts.
- If an institution's intake spikes anomalously (e.g. jump from 40% to 110% utilization without sanctioned expansion), it emits a `HISTORICAL_UTILIZATION_ANOMALY` (`MEDIUM` severity) advisory finding.
- Displays historical baselines, standard deviations, and isolation scores in the issue drawer.

### 4.5 AICTE EoA Parser Service (`EoAParserService`)
Located in `backend/app/engine/eoa_parser.py`:
- Parses AICTE Extension of Approval (EoA) documents (PDF / structured text).
- Extracts official Letter Reference Numbers (`F.No. Western/1-10023841/2026/EOA`), Academic Year, Programme Names, and Sanctioned Intake.
- Flags each record with a confidence score and human confirmation status (`MACHINE_EXTRACTED` vs `CONFIRMED`), preventing unverified values from altering intake limits.

---

## 5. Security & Multi-Tenant Data Isolation

### 5.1 Role-Based Access Control (RBAC)
FastAPI dependency injection enforces role authorization across 5 distinct system roles:
- `AICTE_ADMIN`: Unrestricted national access, cross-institution anomaly review, system-wide exports.
- `INSTITUTION_ADMIN`: Scoped strictly to their own institution. Can commit staged data, respond to exception findings, and view institutional analytics.
- `INSTITUTION_DATA_OPERATOR`: Can stage uploads, map columns, and run dry-run validations.
- `AUTHORIZED_REVIEWER`: Dedicated oversight role. Can assign issues, review supporting evidence, request institutional corrections, and record resolution decisions.
- `EXTERNAL_VERIFIER`: Restricted to purpose-bound credential verification; receives only permitted verification claims.

### 5.2 Institutional Tenant Isolation
The security helper `enforce_institution_scope(current_user, institution_id)` intercepts all institution-scoped queries:
```python
def enforce_institution_scope(current_user: User, institution_id: Optional[int]) -> Optional[int]:
    if current_user.role == UserRole.AICTE_ADMIN:
        return institution_id
    if current_user.institution_id != institution_id:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: You do not have permission to access records outside your institution."
        )
    return current_user.institution_id
```

### 5.3 Export Formula-Injection Protection
In `ReportService.generate_reconciliation_csv`, all user-controlled text values starting with spreadsheet formula trigger characters (`=`, `+`, `-`, `@`, `\t`, `\r`) are automatically escaped with a leading single quote (`'`), neutralizing CSV injection vulnerabilities when exported files are opened in Microsoft Excel or Google Sheets.

---

## 6. Real-Time Events & Background Processing

- **Server-Sent Events (SSE):** `backend/app/core/sse.py` implements a native Starlette `StreamingResponse` asynchronous event broker.
- When an upload batch is committed, a review decision is recorded, or an EoA document is confirmed, the server broadcasts an event payload (`records_committed`, `issue_resolved`, `alert`) to all connected frontend clients.
- Client browsers update dashboard metrics in real time without polling.
