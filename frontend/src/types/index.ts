export type UserRole =
  | 'AICTE_ADMIN'
  | 'INSTITUTION_ADMIN'
  | 'INSTITUTION_DATA_OPERATOR'
  | 'AUTHORIZED_REVIEWER'
  | 'EXTERNAL_VERIFIER';

export interface UserSummary {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  institution_id: number | null;
  institution_name: string | null;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user: UserSummary;
}

export interface AcademicYear {
  id: number;
  year_code: string;
  is_current: boolean;
}

export interface ProgrammeReconciliationItem {
  institution_id: number;
  institution_name: string;
  programme_id: number;
  programme_name: string;
  programme_code: string;
  academic_year: string;
  base_approved_intake: number;
  supernumerary_sanctioned: number;
  effective_limit: number;
  calculated_enrolment: number;
  supernumerary_enrolled: number;
  variance: number;
  utilization_rate: number;
  is_exceeded: boolean;
  source_eoa_reference: string;
  rule_version: string;
}

export interface CategoryDistributionItem {
  category: string;
  count: number;
  percentage: number;
}

export interface AcademicYearTrendItem {
  academic_year: string;
  approved_intake: number;
  actual_enrolment: number;
  utilization_rate: number;
}

export interface ExceptionDistributionItem {
  rule_code: string;
  severity: string;
  count: number;
}

export interface DashboardSummary {
  institutions_count: number;
  programmes_count: number;
  approved_intake_total: number;
  actual_enrolment_total: number;
  supernumerary_seats_total: number;
  supernumerary_enrolled_total: number;
  remaining_capacity_total: number;
  intake_utilization_rate: number;
  unresolved_issues_count: number;
  critical_issues_count: number;
  duplicate_candidates_count: number;
  programme_reconciliations: ProgrammeReconciliationItem[];
  category_distributions: CategoryDistributionItem[];
  academic_year_trends: AcademicYearTrendItem[];
  exception_distributions: ExceptionDistributionItem[];
  is_synthetic_data: boolean;
  disclaimer: string;
}

export interface Institution {
  id: number;
  code: string;
  name: string;
  state: string;
  district?: string;
  institution_type: string;
  address?: string;
  contact_email?: string;
  programmes_count: number;
  total_approved_intake: number;
  total_actual_enrolment: number;
  open_issues_count: number;
  programmes: {
    id: number;
    programme_code: string;
    programme_name: string;
    degree_level: string;
    department: string;
    duration_years: number;
  }[];
}

export interface StudentEnrolment {
  id: number;
  institution_id: number;
  institution_name: string;
  programme_id: number;
  programme_name: string;
  programme_code: string;
  academic_year: string;
  institution_student_id: string;
  masked_apaar_id: string;
  student_name: string;
  admission_date: string;
  enrolment_status: string;
  seat_category: string;
  is_nri: boolean;
  is_oci: boolean;
  is_fn: boolean;
  is_supernumerary: boolean;
  is_eligible_enrolment: boolean;
  has_validation_issue: boolean;
}

export interface StudentEnrolmentDetail extends StudentEnrolment {
  institution_code: string;
  dob?: string;
  gender?: string;
  supernumerary_type?: string;
  source_upload_batch_id?: number;
  correction_history: {
    id: number;
    field_name: string;
    original_value?: string;
    corrected_value?: string;
    actor_email?: string;
    reason: string;
    timestamp: string;
  }[];
  active_issues: {
    id: number;
    rule_code: string;
    title: string;
    severity: string;
    status: string;
    description: string;
    detected_at: string;
  }[];
}

export interface ValidationIssue {
  id: number;
  rule_code: string;
  rule_version: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  institution_id: number;
  institution_name: string;
  programme_name?: string;
  academic_year: string;
  title: string;
  status: 'OPEN' | 'ASSIGNED' | 'CORRECTION_REQUESTED' | 'FALSE_POSITIVE' | 'RESOLVED' | 'CONFIRMED';
  assigned_to_email?: string;
  detected_at: string;
  resolved_at?: string;
}

export interface ValidationIssueDetail extends ValidationIssue {
  programme_id?: number;
  affected_student_enrolment_id?: number;
  affected_student_id?: string;
  affected_student_name?: string;
  affected_masked_apaar?: string;
  description: string;
  evidence_details: Record<string, any>;
  assigned_to_user_id?: number;
  reviewer_notes?: string;
  resolution_reason?: string;
  decision_history: {
    id: number;
    action: string;
    actor_email?: string;
    previous_status: string;
    new_status: string;
    reason: string;
    notes?: string;
    timestamp: string;
  }[];
}

export interface DuplicateCandidateGroup {
  id: number;
  rule_code: string;
  match_type: string;
  status: string;
  review_notes?: string;
  created_at: string;
  members: {
    member_id: number;
    institution_id: number;
    institution_name: string;
    student_id: string;
    student_name: string;
    masked_apaar_id: string;
    programme: string;
    admission_date?: string;
    match_confidence: number;
  }[];
}

export interface CertificatePreview {
  certificate_number: string;
  degree_awarding_body: string;
  institution_name: string;
  institution_code: string;
  student_name: string;
  student_id: string;
  masked_apaar_id: string;
  degree_name: string;
  grade_or_division: string;
  academic_year: string;
  issue_date: string;
  qr_verification_slug: string;
  qr_verification_url: string;
  is_revoked: boolean;
  watermark_text: string;
  disclaimer: string;
}

export interface AuditEventItem {
  id: number;
  event_type: string;
  actor_email?: string;
  actor_role: string;
  institution_name?: string;
  resource_type: string;
  resource_id?: string;
  action_outcome: string;
  ip_address: string;
  event_details: Record<string, any>;
  timestamp: string;
}
