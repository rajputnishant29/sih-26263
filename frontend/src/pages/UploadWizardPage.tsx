import React, { useState } from 'react';
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ArrowRight,
  RefreshCw,
  Download,
  ShieldAlert,
  Info,
} from 'lucide-react';
import { api } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { StatusPill } from '../components/common/StatusPill';

export const UploadWizardPage: React.FC = () => {
  const { user, selectedAcademicYearId } = useAuth();

  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [institutionId, setInstitutionId] = useState<number>(user?.institution_id || 1);
  const [academicYearId, setAcademicYearId] = useState<number>(selectedAcademicYearId || 1);
  const [programmeId, setProgrammeId] = useState<number | undefined>(undefined);
  const [declaredCount, setDeclaredCount] = useState<number>(200);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isStaging, setIsStaging] = useState(false);
  const [stagedBatch, setStagedBatch] = useState<any | null>(null);

  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<any | null>(null);

  const [isCommitting, setIsCommitting] = useState(false);
  const [commitResult, setCommitResult] = useState<any | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Quick seed samples for testing
  const loadQuickCleanSample = async () => {
    try {
      const resp = await fetch('/api/uploads/template/csv');
      const text = await resp.text();
      const file = new File([text], 'Clean_Sample_Admissions_2026.csv', { type: 'text/csv' });
      setSelectedFile(file);
      setDeclaredCount(3);
    } catch (e: any) {
      alert('Failed to load clean sample: ' + e.message);
    }
  };

  const loadQuickProblematicSample = () => {
    const csvContent =
      'student_id,apaar_id,name,dob,gender,admission_date,enrolment_status,seat_category,programme_code,is_nri,is_oci,is_fn,is_supernumerary,supernumerary_type\n' +
      'COEP-2026-CSE-601,900000000601,Nikhil Sawant,2005-04-10,MALE,2026-07-22,ACTIVE,OPEN,CSE,FALSE,FALSE,FALSE,FALSE,\n' +
      'COEP-2026-CSE-602,,Shruti Kadam,2005-08-15,FEMALE,2026-07-22,ACTIVE,OBC,CSE,FALSE,FALSE,FALSE,FALSE,\n' +
      'COEP-2026-CSE-603,9000000603,Omkar More,2005-01-20,MALE,2026-07-22,ACTIVE,OPEN,CSE,FALSE,FALSE,FALSE,FALSE,\n' +
      'COEP-2026-CSE-604,900000000604,Devika Nambiar,2004-12-12,FEMALE,2026-07-23,ACTIVE,SC,CSE,TRUE,FALSE,FALSE,FALSE,\n' +
      'COEP-2026-CSE-604,900000000604,Devika Nambiar,2004-12-12,FEMALE,2026-07-23,ACTIVE,SC,CSE,TRUE,FALSE,FALSE,FALSE,\n' +
      'COEP-2026-CSE-605,900000000010,Suresh Raina,2005-05-18,MALE,2026-07-23,ACTIVE,OPEN,CSE,FALSE,FALSE,FALSE,FALSE,\n';

    const file = new File([csvContent], 'Problematic_Admissions_Demonstration.csv', { type: 'text/csv' });
    setSelectedFile(file);
    setDeclaredCount(10); // Deliberate mismatch (10 vs 6 rows)
  };

  const handleStageFile = async () => {
    if (!selectedFile) return;
    setIsStaging(true);
    setErrorMessage(null);
    try {
      const formData = new FormData();
      formData.append('institution_id', institutionId.toString());
      formData.append('academic_year_id', academicYearId.toString());
      if (programmeId) formData.append('programme_id', programmeId.toString());
      formData.append('declared_count', declaredCount.toString());
      formData.append('file', selectedFile);

      const batch = await api.stageUpload(formData);
      setStagedBatch(batch);
      setStep(2);
    } catch (e: any) {
      setErrorMessage(e.message || 'File staging failed');
    } finally {
      setIsStaging(false);
    }
  };

  const handleRunValidation = async () => {
    if (!stagedBatch) return;
    setIsValidating(true);
    setErrorMessage(null);
    try {
      const outcome = await api.validateUpload(stagedBatch.id);
      setValidationResult(outcome);
      setStep(3);
    } catch (e: any) {
      setErrorMessage(e.message || 'Validation failed');
    } finally {
      setIsValidating(false);
    }
  };

  const handleCommitBatch = async () => {
    if (!stagedBatch) return;
    setIsCommitting(true);
    setErrorMessage(null);
    try {
      const res = await api.commitUpload(stagedBatch.id);
      setCommitResult(res);
      setStep(4);
    } catch (e: any) {
      setErrorMessage(e.message || 'Batch commit failed');
    } finally {
      setIsCommitting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Title */}
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">
          Student Data Ingestion & Validation Wizard
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Six-stage operational pipeline: INGEST → VALIDATE → RECONCILE → REVIEW → RESOLVE → MONITOR.
        </p>
      </div>

      {/* Stepper Header */}
      <div className="grid grid-cols-4 gap-2 border-b border-slate-200 pb-4">
        {[
          { num: 1, label: '1. Select & Upload' },
          { num: 2, label: '2. Staging & Dry Run' },
          { num: 3, label: '3. Reconcile & Review' },
          { num: 4, label: '4. Authoritative Commit' },
        ].map((s) => (
          <div
            key={s.num}
            className={`flex items-center gap-2 text-xs font-bold ${
              step >= s.num ? 'text-indigo-600' : 'text-slate-400'
            }`}
          >
            <span
              className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                step >= s.num
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-200 text-slate-600'
              }`}
            >
              {s.num}
            </span>
            <span className="hidden sm:inline">{s.label}</span>
          </div>
        ))}
      </div>

      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* STEP 1: Select & Upload */}
      {step === 1 && (
        <div className="p-6 rounded-2xl border border-slate-200 bg-white shadow-xs space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                Institution
              </label>
              <select
                value={institutionId}
                onChange={(e) => setInstitutionId(Number(e.target.value))}
                className="w-full p-2.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-800 focus:ring-2 focus:ring-indigo-500"
              >
                <option value={1}>COEP Technological University (1-10023841)</option>
                <option value={2}>CEG Anna University (1-20045612)</option>
                <option value={3}>VJTI Mumbai (1-30078923)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                Academic Year
              </label>
              <select
                value={academicYearId}
                onChange={(e) => setAcademicYearId(Number(e.target.value))}
                className="w-full p-2.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-800 focus:ring-2 focus:ring-indigo-500"
              >
                <option value={1}>2026-27 (Current)</option>
                <option value={2}>2025-26</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                Declared Total Admissions
              </label>
              <input
                type="number"
                value={declaredCount}
                onChange={(e) => setDeclaredCount(Number(e.target.value))}
                className="w-full p-2.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-800 focus:ring-2 focus:ring-indigo-500"
              />
              <span className="text-[10px] text-slate-400">Total declared by institute for variance check</span>
            </div>
          </div>

          {/* Upload Area */}
          <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center bg-slate-50 hover:bg-slate-50/80 transition-colors">
            <UploadCloud className="w-10 h-10 text-indigo-500 mx-auto mb-3" />
            <div className="font-bold text-sm text-slate-800">
              {selectedFile ? selectedFile.name : 'Choose a CSV or XLSX spreadsheet to upload'}
            </div>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Supports student ID, APAAR identifier, legal name, admission date, seat category, and foreign quota flags.
            </p>

            <div className="mt-4 flex items-center justify-center gap-3">
              <label className="px-4 py-2 rounded-lg bg-indigo-600 text-white font-bold text-xs hover:bg-indigo-700 cursor-pointer shadow-xs">
                <span>Browse Files</span>
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={(e) => e.target.files && setSelectedFile(e.target.files[0])}
                  className="hidden"
                />
              </label>

              <a
                href="/api/uploads/template/csv"
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-white border border-slate-300 text-slate-700 font-semibold text-xs hover:bg-slate-100"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download Official Template</span>
              </a>
            </div>
          </div>

          {/* Seeded Demonstration Samples Buttons */}
          <div className="p-4 rounded-xl bg-indigo-50/60 border border-indigo-200/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            <div>
              <span className="font-bold text-indigo-900 block">Demonstration Test Fixtures:</span>
              <span className="text-indigo-800/80 text-[11px]">
                Load pre-configured sample files to test clean onboarding or intentional anomalies.
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={loadQuickCleanSample}
                className="px-3 py-1.5 rounded-lg bg-white border border-emerald-300 text-emerald-800 font-bold hover:bg-emerald-50 text-xs shadow-2xs"
              >
                Load Clean Sample
              </button>
              <button
                type="button"
                onClick={loadQuickProblematicSample}
                className="px-3 py-1.5 rounded-lg bg-white border border-amber-300 text-amber-900 font-bold hover:bg-amber-50 text-xs shadow-2xs"
              >
                Load Problematic Sample (Intake/Dup/Format)
              </button>
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <button
              onClick={handleStageFile}
              disabled={!selectedFile || isStaging}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 text-white font-bold text-xs hover:bg-indigo-700 disabled:opacity-50 shadow-md shadow-indigo-600/20"
            >
              {isStaging ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Staging File & Checking SHA-256...</span>
                </>
              ) : (
                <>
                  <span>Stage File & Verify Columns</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: Staging Confirmation & Dry Run Trigger */}
      {step === 2 && stagedBatch && (
        <div className="p-6 rounded-2xl border border-slate-200 bg-white shadow-xs space-y-6">
          <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900">
            <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0" />
            <div>
              <h3 className="font-bold text-sm">Batch #{stagedBatch.id} Successfully Staged</h3>
              <p className="text-xs text-emerald-800">
                Parsed {stagedBatch.row_count} rows from <code className="font-mono bg-white/70 px-1 py-0.5 rounded">{stagedBatch.file_name}</code>.
                SHA-256 integrity hash recorded for idempotency.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Total Rows</span>
              <span className="text-lg font-bold text-slate-800">{stagedBatch.row_count}</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Declared Total</span>
              <span className="text-lg font-bold text-slate-800">{stagedBatch.declared_count}</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">File Size</span>
              <span className="text-lg font-bold text-slate-800">{Math.round(stagedBatch.file_size / 1024)} KB</span>
            </div>
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Batch Status</span>
              <StatusPill status={stagedBatch.status} />
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-600 space-y-2">
            <div className="font-bold text-slate-800 flex items-center gap-1.5">
              <Info className="w-4 h-4 text-indigo-600" />
              <span>Next Operational Stage: Deterministic Validation Dry Run</span>
            </div>
            <p>
              EDUTrace will execute deterministic admission rules on staging data without altering live student records.
              This checks: mandatory APAAR presence, 12-digit format readiness, in-file duplicate rows,
              institutional roll number collisions, seat category consistency, and intake capacity reconciliation.
            </p>
          </div>

          <div className="flex items-center justify-between pt-2">
            <button
              onClick={() => setStep(1)}
              className="px-4 py-2 rounded-lg border border-slate-300 text-slate-700 text-xs font-semibold hover:bg-slate-50"
            >
              Back
            </button>
            <button
              onClick={handleRunValidation}
              disabled={isValidating}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 text-white font-bold text-xs hover:bg-indigo-700 disabled:opacity-50 shadow-md shadow-indigo-600/20"
            >
              {isValidating ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Evaluating Deterministic Rules...</span>
                </>
              ) : (
                <>
                  <span>Run Deterministic Dry Run Validation</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: Dry-Run Validation Outcome & Reconciliation Breakdown */}
      {step === 3 && validationResult && (
        <div className="p-6 rounded-2xl border border-slate-200 bg-white shadow-xs space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                Dry Run Validation & Reconciliation Outcome
              </h2>
              <p className="text-xs text-slate-500">
                Executed in {validationResult.duration_ms} ms. Inspect findings before explicit commit.
              </p>
            </div>
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
              DRY RUN COMPLETE
            </span>
          </div>

          {/* Metrics summary */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200">
              <span className="text-[10px] uppercase font-bold text-emerald-800">Valid Rows</span>
              <div className="text-2xl font-extrabold text-emerald-700 mt-0.5">
                {validationResult.valid_count}
              </div>
            </div>
            <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200">
              <span className="text-[10px] uppercase font-bold text-amber-800">Warnings / Exceptions</span>
              <div className="text-2xl font-extrabold text-amber-700 mt-0.5">
                {validationResult.warning_count}
              </div>
            </div>
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200">
              <span className="text-[10px] uppercase font-bold text-rose-800">Rejected Rows</span>
              <div className="text-2xl font-extrabold text-rose-700 mt-0.5">
                {validationResult.error_count}
              </div>
            </div>
            <div className="p-3.5 rounded-xl bg-indigo-50 border border-indigo-200">
              <span className="text-[10px] uppercase font-bold text-indigo-800">Total Checked</span>
              <div className="text-2xl font-extrabold text-indigo-900 mt-0.5">
                {validationResult.total_rows}
              </div>
            </div>
          </div>

          {/* Intake Reconciliation Banner */}
          {validationResult.intake_reconciliation && (
            <div className={`p-4 rounded-xl border text-xs ${
              validationResult.intake_reconciliation.is_exceeded
                ? 'bg-rose-50 border-rose-200 text-rose-950'
                : 'bg-emerald-50 border-emerald-200 text-emerald-950'
            }`}>
              <div className="font-bold text-sm flex items-center gap-2">
                {validationResult.intake_reconciliation.is_exceeded ? (
                  <>
                    <ShieldAlert className="w-4 h-4 text-rose-600" />
                    <span>Intake Capacity Exceeded Flag Detected!</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Intake Capacity Reconciliation Verified</span>
                  </>
                )}
              </div>
              <div className="mt-1 text-[11px] leading-relaxed">
                Base Sanctioned: <strong>{validationResult.intake_reconciliation.base_approved_intake}</strong> •
                Supernumerary Limit: <strong>+{validationResult.intake_reconciliation.supernumerary_seats}</strong> •
                Effective Approved Limit: <strong>{validationResult.intake_reconciliation.effective_limit}</strong> •
                Prospective Enrolment: <strong>{validationResult.intake_reconciliation.calculated_enrolment}</strong>
                {validationResult.intake_reconciliation.is_exceeded && (
                  <span className="font-bold text-rose-700 ml-1">
                    (Exceeds effective limit by {validationResult.intake_reconciliation.excess_count} seats!)
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Row Previews Table */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
              Parsed Row Staging Results (Showing up to 25 rows)
            </h3>
            <div className="rounded-lg border border-slate-200 overflow-hidden text-xs">
              <table className="w-full text-left">
                <thead className="bg-slate-50 text-[10px] uppercase text-slate-500 border-b border-slate-200">
                  <tr>
                    <th className="py-2 px-3">Row #</th>
                    <th className="py-2 px-3">Student ID</th>
                    <th className="py-2 px-3">Student Name</th>
                    <th className="py-2 px-3">Masked APAAR</th>
                    <th className="py-2 px-3">Validation Status</th>
                    <th className="py-2 px-3">Findings & Rule Trigger</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {validationResult.row_previews.map((r: any) => (
                    <tr key={r.row_number} className="hover:bg-slate-50">
                      <td className="py-2 px-3 font-mono font-medium">{r.row_number}</td>
                      <td className="py-2 px-3 font-mono font-bold text-slate-900">{r.student_id || '-'}</td>
                      <td className="py-2 px-3 font-medium text-slate-800">{r.student_name || '-'}</td>
                      <td className="py-2 px-3 font-mono text-[11px] text-slate-600">{r.masked_apaar || 'MISSING'}</td>
                      <td className="py-2 px-3">
                        <StatusPill status={r.status} />
                      </td>
                      <td className="py-2 px-3 text-[11px]">
                        {r.messages && r.messages.length > 0 ? (
                          <div className="space-y-0.5">
                            {r.messages.map((m: any, idx: number) => (
                              <div key={idx} className="text-rose-700 font-semibold flex items-center gap-1">
                                <span className="font-mono text-[10px] bg-rose-50 px-1 rounded">{m.rule_code}:</span>
                                <span>{m.title}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <span className="text-emerald-700 font-medium">All checks passed</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center justify-between pt-2">
            <button
              onClick={() => setStep(2)}
              className="px-4 py-2 rounded-lg border border-slate-300 text-slate-700 text-xs font-semibold hover:bg-slate-50"
            >
              Back
            </button>
            <button
              onClick={handleCommitBatch}
              disabled={isCommitting}
              className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-emerald-600 text-white font-bold text-xs hover:bg-emerald-700 disabled:opacity-50 shadow-md shadow-emerald-600/20"
            >
              {isCommitting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Committing Valid Records to Database...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Confirm Explicit Commit ({validationResult.valid_count + validationResult.warning_count} Records)</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: Authoritative Commit Result */}
      {step === 4 && commitResult && (
        <div className="p-8 rounded-2xl border border-emerald-200 bg-white shadow-xs text-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto shadow-md">
            <CheckCircle2 className="w-8 h-8" />
          </div>

          <h2 className="text-xl font-black text-slate-900 tracking-tight">
            Authoritative Batch Commit Successfully Executed!
          </h2>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            {commitResult.message}
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-lg mx-auto text-xs pt-2">
            <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200">
              <span className="text-slate-500 block text-[10px]">Persisted Enrolments</span>
              <span className="text-xl font-black text-emerald-700">{commitResult.committed_enrolments_count}</span>
            </div>
            <div className="p-3 rounded-lg bg-amber-50 border border-amber-200">
              <span className="text-slate-500 block text-[10px]">Reviewable Issues</span>
              <span className="text-xl font-black text-amber-700">{commitResult.issues_generated_count}</span>
            </div>
            <div className="p-3 rounded-lg bg-indigo-50 border border-indigo-200">
              <span className="text-slate-500 block text-[10px]">Candidate Duplicates</span>
              <span className="text-xl font-black text-indigo-700">{commitResult.duplicate_candidates_flagged}</span>
            </div>
          </div>

          <div className="pt-4 flex items-center justify-center gap-3">
            <button
              onClick={() => {
                setSelectedFile(null);
                setStagedBatch(null);
                setValidationResult(null);
                setCommitResult(null);
                setStep(1);
              }}
              className="px-4 py-2 rounded-lg border border-slate-300 text-slate-700 text-xs font-bold hover:bg-slate-50"
            >
              Upload Another Batch
            </button>
            <a
              href="/exceptions"
              className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 shadow-xs"
            >
              Inspect Generated Review Queue
            </a>
          </div>
        </div>
      )}
    </div>
  );
};
