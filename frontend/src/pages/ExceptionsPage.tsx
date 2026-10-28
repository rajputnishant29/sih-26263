import React, { useState, useEffect } from 'react';
import {
  AlertOctagon,
  ShieldAlert,
  Users,
  CheckCircle2,
  XCircle,
  HelpCircle,
  X,
  FileText,
  UserCheck,
  Send,
  RefreshCw,
  Search,
} from 'lucide-react';
import { api } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { ValidationIssue, ValidationIssueDetail, DuplicateCandidateGroup } from '../types';
import { SeverityBadge } from '../components/common/SeverityBadge';
import { StatusPill } from '../components/common/StatusPill';
import { MaskedIdViewer } from '../components/common/MaskedIdViewer';

export const ExceptionsPage: React.FC = () => {
  const { user, selectedAcademicYearId } = useAuth();

  const [activeTab, setActiveTab] = useState<'issues' | 'duplicate_candidates'>('issues');
  const [issues, setIssues] = useState<ValidationIssue[]>([]);
  const [duplicateGroups, setDuplicateGroups] = useState<DuplicateCandidateGroup[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Filters
  const [ruleFilter, setRuleFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  // Drawer & Decision Modal
  const [selectedIssueId, setSelectedIssueId] = useState<number | null>(null);
  const [issueDetail, setIssueDetail] = useState<ValidationIssueDetail | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false);

  const [isDecisionModalOpen, setIsDecisionModalOpen] = useState<boolean>(false);
  const [decisionAction, setDecisionAction] = useState<string>('RESOLVE');
  const [decisionReason, setDecisionReason] = useState<string>('');
  const [decisionNotes, setDecisionNotes] = useState<string>('');
  const [isSubmittingDecision, setIsSubmittingDecision] = useState<boolean>(false);

  const fetchIssues = async () => {
    try {
      setIsLoading(true);
      const data = await api.getIssues({
        rule_code: ruleFilter || undefined,
        severity: severityFilter || undefined,
        status: statusFilter || undefined,
        institution_id: user?.institution_id || undefined,
        academic_year_id: selectedAcademicYearId || undefined,
      });
      setIssues(data);
    } catch (e) {
      console.error('Failed to load issues:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchDuplicateCandidates = async () => {
    try {
      const data = await api.getDuplicateCandidates();
      setDuplicateGroups(data);
    } catch (e) {
      console.error('Failed to load duplicate candidates:', e);
    }
  };

  useEffect(() => {
    fetchIssues();
    fetchDuplicateCandidates();
  }, [ruleFilter, severityFilter, statusFilter, selectedAcademicYearId, user?.role]);

  const handleSelectIssue = async (id: number) => {
    setSelectedIssueId(id);
    setIsLoadingDetail(true);
    try {
      const detail = await api.getIssue(id);
      setIssueDetail(detail);
    } catch (e) {
      console.error('Failed to load issue detail:', e);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleRecordDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedIssueId || !decisionReason) return;
    setIsSubmittingDecision(true);
    try {
      await api.recordDecision(selectedIssueId, {
        action: decisionAction,
        reason: decisionReason,
        notes: decisionNotes,
      });
      setIsDecisionModalOpen(false);
      setDecisionReason('');
      setDecisionNotes('');
      handleSelectIssue(selectedIssueId);
      fetchIssues();
    } catch (err: any) {
      alert('Decision recording failed: ' + err.message);
    } finally {
      setIsSubmittingDecision(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title & Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            Validation & Exception Review Center
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Actionable evidence queue, cross-institution duplicate investigations, and human-in-the-loop decisions.
          </p>
        </div>

        <div className="flex items-center gap-1 p-1 bg-slate-200/70 rounded-xl text-xs font-semibold">
          <button
            onClick={() => setActiveTab('issues')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              activeTab === 'issues' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Review Queue ({issues.length})
          </button>
          <button
            onClick={() => setActiveTab('duplicate_candidates')}
            className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
              activeTab === 'duplicate_candidates' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Users className="w-3.5 h-3.5 text-indigo-500" />
            <span>Duplicate Candidates ({duplicateGroups.length})</span>
          </button>
        </div>
      </div>

      {/* TAB 1: Issues Queue */}
      {activeTab === 'issues' && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-xs flex flex-wrap items-center gap-3">
            <div className="w-48">
              <select
                value={ruleFilter}
                onChange={(e) => setRuleFilter(e.target.value)}
                className="w-full py-2 px-2.5 rounded-lg border border-slate-300 text-xs font-medium text-slate-700 bg-white"
              >
                <option value="">All Validation Rules</option>
                <option value="INTAKE_CAPACITY_EXCEEDED">Intake Exceeded</option>
                <option value="APAAR_PRESENCE_CHECK">Missing APAAR</option>
                <option value="APAAR_FORMAT_READINESS">Format Readiness</option>
                <option value="CROSS_INSTITUTION_DUPLICATE_CANDIDATE">Cross-Institution Duplicate</option>
                <option value="FILE_DUPLICATE_ROW">File Duplicate</option>
                <option value="DECLARED_TOTAL_MISMATCH">Declared Count Mismatch</option>
                <option value="CATEGORY_INCONSISTENCY">Category Inconsistency</option>
                <option value="HISTORICAL_UTILIZATION_ANOMALY">AI Anomaly Signal</option>
              </select>
            </div>

            <div className="w-40">
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="w-full py-2 px-2.5 rounded-lg border border-slate-300 text-xs font-medium text-slate-700 bg-white"
              >
                <option value="">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>

            <div className="w-40">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full py-2 px-2.5 rounded-lg border border-slate-300 text-xs font-medium text-slate-700 bg-white"
              >
                <option value="">All Review Statuses</option>
                <option value="OPEN">Open</option>
                <option value="ASSIGNED">Assigned</option>
                <option value="CORRECTION_REQUESTED">Correction Requested</option>
                <option value="RESOLVED">Resolved</option>
                <option value="FALSE_POSITIVE">False Positive</option>
              </select>
            </div>

            <button
              onClick={fetchIssues}
              className="ml-auto p-2 rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50"
              title="Refresh Queue"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          {/* Table & Evidence Drawer */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className={`rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden ${selectedIssueId ? 'lg:col-span-2' : 'lg:col-span-3'}`}>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-700">
                  <thead className="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-200">
                    <tr>
                      <th className="py-3 px-4 font-bold">Severity</th>
                      <th className="py-3 px-4 font-bold">Triggering Rule & Title</th>
                      <th className="py-3 px-4 font-bold">Institution / Programme</th>
                      <th className="py-3 px-4 font-bold">Status</th>
                      <th className="py-3 px-4 font-bold">Assigned To</th>
                      <th className="py-3 px-4 font-bold">Detected</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {isLoading ? (
                      <tr>
                        <td colSpan={6} className="py-12 text-center text-slate-400">Loading issues...</td>
                      </tr>
                    ) : issues.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="py-12 text-center text-slate-400">No issues match current filters.</td>
                      </tr>
                    ) : (
                      issues.map((iss) => (
                        <tr
                          key={iss.id}
                          onClick={() => handleSelectIssue(iss.id)}
                          className={`hover:bg-slate-50 cursor-pointer transition-colors ${
                            selectedIssueId === iss.id ? 'bg-indigo-50/50' : ''
                          }`}
                        >
                          <td className="py-3 px-4">
                            <SeverityBadge severity={iss.severity} />
                          </td>
                          <td className="py-3 px-4">
                            <div className="font-bold text-slate-900 leading-snug">{iss.title}</div>
                            <div className="text-[10px] font-mono text-indigo-600">{iss.rule_code} ({iss.rule_version})</div>
                          </td>
                          <td className="py-3 px-4">
                            <div className="font-medium text-slate-800">{iss.programme_name || 'All Programmes'}</div>
                            <div className="text-[10px] text-slate-500 truncate max-w-[140px]">{iss.institution_name}</div>
                          </td>
                          <td className="py-3 px-4">
                            <StatusPill status={iss.status} />
                          </td>
                          <td className="py-3 px-4 text-slate-600">
                            {iss.assigned_to_email ? (
                              <span className="font-medium text-slate-800 truncate max-w-[120px] block">
                                {iss.assigned_to_email}
                              </span>
                            ) : (
                              <span className="text-slate-400 italic">Unassigned</span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-slate-500 font-mono text-[11px]">
                            {iss.detected_at.slice(0, 10)}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Evidence Drawer */}
            {selectedIssueId && (
              <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-md space-y-4 lg:col-span-1">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Evidence & Decision Drawer
                    </span>
                    <h3 className="text-sm font-extrabold text-slate-900 mt-0.5">
                      Issue #{selectedIssueId}
                    </h3>
                  </div>
                  <button
                    onClick={() => setSelectedIssueId(null)}
                    className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {isLoadingDetail || !issueDetail ? (
                  <div className="py-12 text-center text-xs text-slate-400">Loading evidence...</div>
                ) : (
                  <div className="space-y-4 text-xs">
                    <div>
                      <div className="flex items-center justify-between">
                        <SeverityBadge severity={issueDetail.severity} />
                        <StatusPill status={issueDetail.status} />
                      </div>
                      <h4 className="font-bold text-sm text-slate-900 mt-2">
                        {issueDetail.title}
                      </h4>
                      <p className="text-slate-600 text-xs mt-1 leading-relaxed">
                        {issueDetail.description}
                      </p>
                    </div>

                    {/* Sourced Rule & Scope */}
                    <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1.5 text-[11px]">
                      <div><strong className="text-slate-700">Triggering Rule:</strong> <span className="font-mono text-indigo-700 font-bold">{issueDetail.rule_code}</span></div>
                      <div><strong className="text-slate-700">Rule Version:</strong> <span className="font-mono">{issueDetail.rule_version}</span></div>
                      <div><strong className="text-slate-700">Institution:</strong> {issueDetail.institution_name}</div>
                      {issueDetail.affected_student_id && (
                        <div><strong className="text-slate-700">Affected Student ID:</strong> <span className="font-mono font-bold text-slate-900">{issueDetail.affected_student_id}</span></div>
                      )}
                      {issueDetail.affected_masked_apaar && (
                        <div className="flex items-center gap-1.5">
                          <strong className="text-slate-700">Masked APAAR:</strong>
                          <MaskedIdViewer maskedId={issueDetail.affected_masked_apaar} />
                        </div>
                      )}
                    </div>

                    {/* Evidence Details JSON Diff Box */}
                    <div>
                      <span className="font-bold text-[10px] uppercase tracking-wider text-slate-500 block mb-1">
                        Inspection Evidence Payload
                      </span>
                      <pre className="p-3 rounded-lg bg-slate-900 text-emerald-400 font-mono text-[10px] overflow-x-auto max-h-40 leading-relaxed">
                        {JSON.stringify(issueDetail.evidence_details, null, 2)}
                      </pre>
                    </div>

                    {/* Review Decisions History */}
                    {issueDetail.decision_history.length > 0 && (
                      <div>
                        <span className="font-bold text-[10px] uppercase tracking-wider text-slate-500 block mb-1">
                          Reviewer Decisions History
                        </span>
                        <div className="space-y-1.5 max-h-32 overflow-y-auto">
                          {issueDetail.decision_history.map((d) => (
                            <div key={d.id} className="p-2 rounded bg-slate-50 border border-slate-200 text-[11px]">
                              <div className="font-bold text-slate-800">
                                {d.action}: {d.previous_status} → {d.new_status}
                              </div>
                              <div className="text-slate-600 text-[10px]">{d.reason}</div>
                              <div className="text-slate-400 text-[9px]">{d.actor_email} • {d.timestamp.slice(0, 16).replace('T', ' ')}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Action Button */}
                    <div className="pt-2">
                      <button
                        onClick={() => setIsDecisionModalOpen(true)}
                        className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 text-white font-bold text-xs hover:bg-indigo-700 shadow-xs flex items-center justify-center gap-2"
                      >
                        <UserCheck className="w-4 h-4" />
                        <span>Record Reviewer Decision</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: Duplicate Candidates */}
      {activeTab === 'duplicate_candidates' && (
        <div className="space-y-4">
          <div className="p-4 rounded-xl bg-indigo-50/60 border border-indigo-200 text-xs text-indigo-950">
            <h3 className="font-bold text-indigo-900">
              Cross-Institution Duplicate Candidate Investigation
            </h3>
            <p className="mt-1 leading-relaxed text-indigo-900/80">
              A potential duplicate is a finding requiring investigation, not proof of wrongdoing.
              Never automatically merge student identities, reject admissions, or impose adverse consequences without formal reviewer sign-off.
            </p>
          </div>

          <div className="space-y-4">
            {duplicateGroups.map((group) => (
              <div key={group.id} className="p-5 rounded-xl border border-slate-200 bg-white shadow-xs space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs text-slate-900">
                        Candidate Group #{group.id}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-indigo-100 text-indigo-800">
                        {group.match_type}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">{group.review_notes}</p>
                  </div>
                  <StatusPill status={group.status} />
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-[10px] uppercase text-slate-500 border-b border-slate-200">
                      <tr>
                        <th className="py-2.5 px-3">Institution</th>
                        <th className="py-2.5 px-3">Roll No</th>
                        <th className="py-2.5 px-3">Student Name</th>
                        <th className="py-2.5 px-3">Masked APAAR</th>
                        <th className="py-2.5 px-3">Programme</th>
                        <th className="py-2.5 px-3">Admission Date</th>
                        <th className="py-2.5 px-3">Match Confidence</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {group.members.map((m) => (
                        <tr key={m.member_id} className="hover:bg-slate-50">
                          <td className="py-2.5 px-3 font-semibold text-slate-900">{m.institution_name}</td>
                          <td className="py-2.5 px-3 font-mono font-bold text-indigo-700">{m.student_id}</td>
                          <td className="py-2.5 px-3 font-medium">{m.student_name}</td>
                          <td className="py-2.5 px-3">
                            <MaskedIdViewer maskedId={m.masked_apaar_id} />
                          </td>
                          <td className="py-2.5 px-3 text-slate-600">{m.programme}</td>
                          <td className="py-2.5 px-3 font-mono text-slate-500">{m.admission_date || '-'}</td>
                          <td className="py-2.5 px-3">
                            <span className="font-bold font-mono text-emerald-700">{Math.round(m.match_confidence * 100)}%</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Decision Modal */}
      {isDecisionModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100 space-y-4 text-xs">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-extrabold text-sm text-slate-900">
                Record Reviewer Decision
              </h3>
              <button
                onClick={() => setIsDecisionModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleRecordDecision} className="space-y-3">
              <div>
                <label className="block font-bold text-slate-700 mb-1 uppercase tracking-wider text-[10px]">
                  Review Action
                </label>
                <select
                  value={decisionAction}
                  onChange={(e) => setDecisionAction(e.target.value)}
                  className="w-full p-2.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-800"
                >
                  <option value="RESOLVE">Resolve Issue (Clear Exception)</option>
                  <option value="REQUEST_CORRECTION">Request Correction from Institution</option>
                  <option value="CONFIRM_FINDING">Confirm Finding as Genuine Violation</option>
                  <option value="MARK_FALSE_POSITIVE">Mark False Positive with Justification</option>
                  <option value="ASSIGN">Assign / Reassign Reviewer</option>
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1 uppercase tracking-wider text-[10px]">
                  Authoritative Justification / Reason (Mandatory)
                </label>
                <textarea
                  required
                  rows={3}
                  value={decisionReason}
                  onChange={(e) => setDecisionReason(e.target.value)}
                  placeholder="Record documented reason for regulatory decision..."
                  className="w-full p-2.5 rounded-lg border border-slate-300 text-xs text-slate-800"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1 uppercase tracking-wider text-[10px]">
                  Reviewer Internal Notes
                </label>
                <textarea
                  rows={2}
                  value={decisionNotes}
                  onChange={(e) => setDecisionNotes(e.target.value)}
                  placeholder="Supporting observations, phone verification, or evidence details..."
                  className="w-full p-2.5 rounded-lg border border-slate-300 text-xs text-slate-800"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsDecisionModalOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-300 text-slate-700 text-xs font-bold hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingDecision}
                  className="px-5 py-2 rounded-lg bg-indigo-600 text-white font-bold text-xs hover:bg-indigo-700 disabled:opacity-50"
                >
                  {isSubmittingDecision ? 'Submitting...' : 'Sign & Record Decision'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
