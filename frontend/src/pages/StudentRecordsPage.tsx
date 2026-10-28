import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Search,
  Filter,
  Users,
  Award,
  Edit3,
  X,
  History,
  AlertOctagon,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
} from 'lucide-react';
import { api } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { StudentEnrolment, StudentEnrolmentDetail } from '../types';
import { StatusPill } from '../components/common/StatusPill';
import { MaskedIdViewer } from '../components/common/MaskedIdViewer';

export const StudentRecordsPage: React.FC = () => {
  const { user, selectedAcademicYearId } = useAuth();

  const [enrolments, setEnrolments] = useState<StudentEnrolment[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [limit] = useState<number>(20);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [search, setSearch] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Detail Drawer & Correction Modal state
  const [selectedEnrolmentId, setSelectedEnrolmentId] = useState<number | null>(null);
  const [enrolmentDetail, setEnrolmentDetail] = useState<StudentEnrolmentDetail | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false);

  const [isCorrectModalOpen, setIsCorrectModalOpen] = useState<boolean>(false);
  const [correctionField, setCorrectionField] = useState<string>('seat_category');
  const [correctionNewValue, setCorrectionNewValue] = useState<string>('OPEN');
  const [correctionReason, setCorrectionReason] = useState<string>('');
  const [correctionSourceRef, setCorrectionSourceRef] = useState<string>('Document Verification Proof #2026-X');
  const [isSubmittingCorrection, setIsSubmittingCorrection] = useState<boolean>(false);
  const [successToast, setSuccessToast] = useState<string | null>(null);

  const fetchEnrolments = async () => {
    try {
      setIsLoading(true);
      const res = await api.getEnrolments({
        page,
        limit,
        search,
        status: statusFilter || undefined,
        seat_category: categoryFilter || undefined,
        institution_id: user?.institution_id || undefined,
        academic_year_id: selectedAcademicYearId || undefined,
      });
      setEnrolments(res.items);
      setTotalCount(res.total);
      setTotalPages(res.pages);
    } catch (e) {
      console.error('Failed to load enrolments:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEnrolments();
  }, [page, search, statusFilter, categoryFilter, selectedAcademicYearId, user?.role]);

  const handleSelectRecord = async (id: number) => {
    setSelectedEnrolmentId(id);
    setIsLoadingDetail(true);
    try {
      const detail = await api.getEnrolment(id);
      setEnrolmentDetail(detail);
    } catch (e) {
      console.error('Failed to load detail:', e);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleApplyCorrection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEnrolmentId || !correctionReason) return;
    setIsSubmittingCorrection(true);
    try {
      await api.correctEnrolment(selectedEnrolmentId, {
        field_name: correctionField,
        new_value: correctionNewValue,
        reason: correctionReason,
        source_reference: correctionSourceRef,
      });
      setIsCorrectModalOpen(false);
      setSuccessToast(`Field '${correctionField}' updated with immutable audit history.`);
      setTimeout(() => setSuccessToast(null), 4000);
      handleSelectRecord(selectedEnrolmentId);
      fetchEnrolments();
    } catch (err: any) {
      alert('Correction failed: ' + err.message);
    } finally {
      setIsSubmittingCorrection(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title & Filter Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            Student Records Repository
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Student-level academic identities with privacy-protected APAAR references and immutable audit trails.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
            {totalCount} Total Enrolments
          </span>
        </div>
      </div>

      {successToast && (
        <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{successToast}</span>
        </div>
      )}

      {/* Filter Bar */}
      <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-xs flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by student name or roll number..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="w-40">
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="w-full py-2 px-2.5 rounded-lg border border-slate-300 text-xs font-medium text-slate-700 bg-white"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="WITHDRAWN">Withdrawn</option>
            <option value="CANCELLED">Cancelled</option>
            <option value="TRANSFERRED">Transferred</option>
          </select>
        </div>

        <div className="w-40">
          <select
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(e.target.value);
              setPage(1);
            }}
            className="w-full py-2 px-2.5 rounded-lg border border-slate-300 text-xs font-medium text-slate-700 bg-white"
          >
            <option value="">All Categories</option>
            <option value="OPEN">Open</option>
            <option value="OBC">OBC</option>
            <option value="SC">SC</option>
            <option value="ST">ST</option>
            <option value="EWS">EWS</option>
            <option value="TFW">TFW</option>
          </select>
        </div>
      </div>

      {/* Table & Drawer Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Table */}
        <div className={`rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden ${selectedEnrolmentId ? 'lg:col-span-2' : 'lg:col-span-3'}`}>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4 font-bold">Student Roll No</th>
                  <th className="py-3 px-4 font-bold">Protected APAAR Reference</th>
                  <th className="py-3 px-4 font-bold">Student Name</th>
                  <th className="py-3 px-4 font-bold">Programme</th>
                  <th className="py-3 px-4 font-bold">Admission Date</th>
                  <th className="py-3 px-4 font-bold">Quota / Category</th>
                  <th className="py-3 px-4 font-bold">Status</th>
                  <th className="py-3 px-4 font-bold">Issues</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {isLoading ? (
                  <tr>
                    <td colSpan={8} className="py-12 text-center text-slate-400">Loading student records...</td>
                  </tr>
                ) : enrolments.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-12 text-center text-slate-400">No student records match filters.</td>
                  </tr>
                ) : (
                  enrolments.map((e) => (
                    <tr
                      key={e.id}
                      onClick={() => handleSelectRecord(e.id)}
                      className={`hover:bg-slate-50 cursor-pointer transition-colors ${
                        selectedEnrolmentId === e.id ? 'bg-indigo-50/50' : ''
                      }`}
                    >
                      <td className="py-3 px-4 font-mono font-bold text-slate-900">
                        {e.institution_student_id}
                      </td>
                      <td className="py-3 px-4">
                        <MaskedIdViewer maskedId={e.masked_apaar_id} />
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-900">
                        {e.student_name}
                      </td>
                      <td className="py-3 px-4 text-slate-600">
                        <div className="font-medium">{e.programme_code}</div>
                        <div className="text-[10px] text-slate-400 truncate max-w-[120px]">{e.institution_name}</div>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-500">{e.admission_date}</td>
                      <td className="py-3 px-4">
                        <span className="font-semibold text-slate-800">{e.seat_category}</span>
                        {e.is_supernumerary && (
                          <span className="ml-1 text-[10px] text-emerald-700 bg-emerald-50 px-1 py-0.2 rounded font-bold">
                            TFW
                          </span>
                        )}
                        {e.is_nri && (
                          <span className="ml-1 text-[10px] text-purple-700 bg-purple-50 px-1 py-0.2 rounded font-bold">
                            NRI
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <StatusPill status={e.enrolment_status} />
                      </td>
                      <td className="py-3 px-4">
                        {e.has_validation_issue ? (
                          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-rose-700 bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                            <AlertOctagon className="w-3 h-3 text-rose-600" />
                            <span>Flagged</span>
                          </span>
                        ) : (
                          <span className="text-[10px] font-medium text-emerald-600">Clean</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="p-3 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500 bg-slate-50">
            <span>
              Showing {enrolments.length} of {totalCount} records (Page {page} of {totalPages})
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="p-1 rounded border border-slate-300 bg-white disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
                className="p-1 rounded border border-slate-300 bg-white disabled:opacity-40"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Detail Drawer */}
        {selectedEnrolmentId && (
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-md space-y-5 lg:col-span-1">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Student Record Dossier
                </span>
                <h3 className="text-base font-extrabold text-slate-900 mt-0.5">
                  {enrolmentDetail?.student_name || 'Loading...'}
                </h3>
              </div>
              <button
                onClick={() => setSelectedEnrolmentId(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {isLoadingDetail || !enrolmentDetail ? (
              <div className="py-12 text-center text-xs text-slate-400">Loading student details...</div>
            ) : (
              <div className="space-y-4 text-xs">
                {/* Identity Box */}
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Roll Number:</span>
                    <span className="font-mono font-bold text-slate-900">{enrolmentDetail.institution_student_id}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">APAAR Reference:</span>
                    <MaskedIdViewer maskedId={enrolmentDetail.masked_apaar_id} />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Institution:</span>
                    <span className="font-medium text-slate-800 text-right truncate max-w-[160px]">{enrolmentDetail.institution_name}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Programme:</span>
                    <span className="font-medium text-slate-800">{enrolmentDetail.programme_name}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Admission Date:</span>
                    <span className="font-mono">{enrolmentDetail.admission_date}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Seat Category:</span>
                    <span className="font-bold text-slate-800">{enrolmentDetail.seat_category}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Enrolment Status:</span>
                    <StatusPill status={enrolmentDetail.enrolment_status} />
                  </div>
                </div>

                {/* Active Validation Issues */}
                {enrolmentDetail.active_issues.length > 0 && (
                  <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 space-y-2">
                    <div className="font-bold text-rose-900 flex items-center gap-1.5 text-[11px]">
                      <AlertOctagon className="w-3.5 h-3.5 text-rose-600" />
                      <span>{enrolmentDetail.active_issues.length} Active Exception(s)</span>
                    </div>
                    {enrolmentDetail.active_issues.map((iss) => (
                      <div key={iss.id} className="text-[11px] text-rose-800 border-l-2 border-rose-500 pl-2 py-0.5">
                        <div className="font-bold">{iss.title}</div>
                        <div className="text-[10px] text-rose-600">{iss.description}</div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Immutable Correction History */}
                <div>
                  <div className="flex items-center gap-1 font-bold text-[11px] text-slate-700 uppercase tracking-wider mb-2">
                    <History className="w-3.5 h-3.5 text-slate-500" />
                    <span>Correction History ({enrolmentDetail.correction_history.length})</span>
                  </div>
                  {enrolmentDetail.correction_history.length === 0 ? (
                    <div className="text-[11px] text-slate-400 italic">No historical corrections applied.</div>
                  ) : (
                    <div className="space-y-2 max-h-36 overflow-y-auto">
                      {enrolmentDetail.correction_history.map((c) => (
                        <div key={c.id} className="p-2 rounded bg-slate-50 border border-slate-200 text-[11px] space-y-0.5">
                          <div className="font-bold text-slate-800">
                            Changed <span className="font-mono text-indigo-700">{c.field_name}</span>: '{c.original_value}' → '{c.corrected_value}'
                          </div>
                          <div className="text-slate-500 text-[10px]">Reason: {c.reason}</div>
                          <div className="text-slate-400 text-[9px]">{c.actor_email} • {c.timestamp.slice(0, 19).replace('T', ' ')}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="pt-2 flex flex-col gap-2">
                  <button
                    onClick={() => {
                      setCorrectionField('seat_category');
                      setCorrectionNewValue(enrolmentDetail.seat_category);
                      setIsCorrectModalOpen(true);
                    }}
                    className="w-full py-2 px-3 rounded-lg border border-indigo-300 text-indigo-700 bg-indigo-50/50 font-bold text-xs hover:bg-indigo-100 transition-colors flex items-center justify-center gap-1.5"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                    <span>Correct Record Field (Traceable)</span>
                  </button>

                  <Link
                    to={`/certificates?enrolmentId=${enrolmentDetail.id}`}
                    className="w-full py-2 px-3 rounded-lg bg-indigo-600 text-white font-bold text-xs hover:bg-indigo-700 transition-colors flex items-center justify-center gap-1.5 shadow-xs"
                  >
                    <Award className="w-3.5 h-3.5" />
                    <span>Preview Degree Credential & QR</span>
                  </Link>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Record Correction Modal */}
      {isCorrectModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100 space-y-4 text-xs">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-extrabold text-sm text-slate-900">
                Correct Student Enrolment Record
              </h3>
              <button
                onClick={() => setIsCorrectModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleApplyCorrection} className="space-y-3">
              <div>
                <label className="block font-bold text-slate-700 mb-1 uppercase tracking-wider text-[10px]">
                  Target Field to Correct
                </label>
                <select
                  value={correctionField}
                  onChange={(e) => setCorrectionField(e.target.value)}
                  className="w-full p-2 rounded-lg border border-slate-300 text-xs font-semibold text-slate-800"
                >
                  <option value="seat_category">Seat Category</option>
                  <option value="enrolment_status">Enrolment Status</option>
                  <option value="is_supernumerary">Supernumerary Flag</option>
                  <option value="is_nri">NRI Quota Flag</option>
                  <option value="is_fn">Foreign National (FN) Flag</option>
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1 uppercase tracking-wider text-[10px]">
                  New Authoritative Value
                </label>
                <input
                  type="text"
                  required
                  value={correctionNewValue}
                  onChange={(e) => setCorrectionNewValue(e.target.value)}
                  placeholder="e.g. OPEN or ACTIVE or TRUE"
                  className="w-full p-2 rounded-lg border border-slate-300 text-xs font-mono font-medium text-slate-800"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1 uppercase tracking-wider text-[10px]">
                  Regulatory Correction Reason (Mandatory)
                </label>
                <textarea
                  required
                  rows={3}
                  value={correctionReason}
                  onChange={(e) => setCorrectionReason(e.target.value)}
                  placeholder="State the audit / institutional verification ground for this correction..."
                  className="w-full p-2 rounded-lg border border-slate-300 text-xs text-slate-800"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700 mb-1 uppercase tracking-wider text-[10px]">
                  Source Reference Proof
                </label>
                <input
                  type="text"
                  value={correctionSourceRef}
                  onChange={(e) => setCorrectionSourceRef(e.target.value)}
                  placeholder="e.g. State CET Cell Allotment Letter #9982"
                  className="w-full p-2 rounded-lg border border-slate-300 text-xs text-slate-800 font-mono"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsCorrectModalOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-300 text-slate-700 text-xs font-bold hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingCorrection}
                  className="px-5 py-2 rounded-lg bg-indigo-600 text-white font-bold text-xs hover:bg-indigo-700 disabled:opacity-50"
                >
                  {isSubmittingCorrection ? 'Recording...' : 'Commit Traceable Correction'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
