const API_BASE = '/api';

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('edutrace_token');
  const headers = new Headers(options.headers || {});

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = 'Request failed';
    let errorData = null;
    try {
      errorData = await response.json();
      errorDetail = errorData.detail || errorDetail;
    } catch {
      errorDetail = response.statusText;
    }
    throw new ApiError(response.status, errorDetail, errorData);
  }

  // Handle empty or raw responses
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json();
  }
  return response.text() as unknown as T;
}

export const api = {
  // Auth
  login: (data: { email: string; password: string }) =>
    request<any>('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  getMe: () => request<any>('/auth/me'),
  demoSwitchRole: (targetRole: string, institutionId?: number) =>
    request<any>('/auth/demo-switch', {
      method: 'POST',
      body: JSON.stringify({ target_role: targetRole, institution_id: institutionId }),
    }),

  // Dashboard
  getDashboardSummary: (ayId?: number, instId?: number) => {
    const params = new URLSearchParams();
    if (ayId) params.set('academic_year_id', ayId.toString());
    if (instId) params.set('institution_id', instId.toString());
    const q = params.toString() ? `?${params.toString()}` : '';
    return request<any>(`/dashboard/summary${q}`);
  },

  // Institutions
  getInstitutions: (search?: string) => {
    const q = search ? `?search=${encodeURIComponent(search)}` : '';
    return request<any>(`/institutions${q}`);
  },
  getInstitution: (id: number) => request<any>(`/institutions/${id}`),

  // Programmes & Approvals
  getProgrammes: (instId?: number, ayId?: number) => {
    const params = new URLSearchParams();
    if (instId) params.set('institution_id', instId.toString());
    if (ayId) params.set('academic_year_id', ayId.toString());
    const q = params.toString() ? `?${params.toString()}` : '';
    return request<any>(`/programmes${q}`);
  },
  getAcademicYears: () => request<any>('/programmes/academic-years'),
  parseEoA: (formData: FormData) =>
    request<any>('/programmes/eoa-parse', { method: 'POST', body: formData }),
  confirmEoA: (payload: any) =>
    request<any>('/programmes/eoa-confirm', { method: 'POST', body: JSON.stringify(payload) }),

  // Enrolments
  getEnrolments: (params: Record<string, any>) => {
    const sp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') sp.set(k, v.toString());
    });
    return request<any>(`/enrolments?${sp.toString()}`);
  },
  getEnrolment: (id: number) => request<any>(`/enrolments/${id}`),
  correctEnrolment: (id: number, data: { field_name: string; new_value: any; reason: string; source_reference?: string }) =>
    request<any>(`/enrolments/${id}/correct`, { method: 'POST', body: JSON.stringify(data) }),

  // Uploads
  stageUpload: (formData: FormData) =>
    request<any>('/uploads/stage', { method: 'POST', body: formData }),
  validateUpload: (batchId: number) =>
    request<any>(`/uploads/${batchId}/validate`, { method: 'POST' }),
  commitUpload: (batchId: number) =>
    request<any>(`/uploads/${batchId}/commit`, { method: 'POST' }),
  getUploadBatches: (instId?: number) => {
    const q = instId ? `?institution_id=${instId}` : '';
    return request<any>(`/uploads${q}`);
  },
  getUploadBatch: (batchId: number) => request<any>(`/uploads/${batchId}`),

  // Issues & Queue
  getIssues: (params: Record<string, any>) => {
    const sp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') sp.set(k, v.toString());
    });
    return request<any>(`/issues?${sp.toString()}`);
  },
  getIssue: (id: number) => request<any>(`/issues/${id}`),
  recordDecision: (id: number, data: { action: string; reason: string; notes?: string; assigned_to_user_id?: number }) =>
    request<any>(`/issues/${id}/decision`, { method: 'POST', body: JSON.stringify(data) }),
  getDuplicateCandidates: () => request<any>('/issues/duplicate-candidates/list'),

  // Verifications
  submitVerification: (data: { query_identifier: string; requester_organization: string; purpose: string; consent_proof_ref: string }) =>
    request<any>('/verifications', { method: 'POST', body: JSON.stringify(data) }),

  // Certificates
  getCertificatePreview: (enrolmentId: number) =>
    request<any>(`/certificates/preview/${enrolmentId}`),
  verifyBySlug: (slug: string) => request<any>(`/certificates/verify-qr/${slug}`),

  // Reports
  getReconciliationReport: (ayId?: number, instId?: number) => {
    const params = new URLSearchParams();
    if (ayId) params.set('academic_year_id', ayId.toString());
    if (instId) params.set('institution_id', instId.toString());
    return request<any>(`/reports/reconciliation?${params.toString()}`);
  },
  getDataQualityReport: (instId?: number, ayId?: number) => {
    const params = new URLSearchParams();
    if (instId) params.set('institution_id', instId.toString());
    if (ayId) params.set('academic_year_id', ayId.toString());
    return request<any>(`/reports/data-quality?${params.toString()}`);
  },

  // Audit
  getAuditLogs: (params: Record<string, any>) => {
    const sp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') sp.set(k, v.toString());
    });
    return request<any>(`/audit-logs?${sp.toString()}`);
  },

  // Rules & Architecture
  getRules: () => request<any>('/rules'),
  getIntegrationStatus: () => request<any>('/rules/integrations/status'),
};
