import React, { useState } from 'react';
import {
  ShieldCheck,
  Search,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Lock,
  Building2,
  FileCheck2,
  Calendar,
  Sparkles,
} from 'lucide-react';
import { api } from '../lib/api';
import { MaskedIdViewer } from '../components/common/MaskedIdViewer';
import { StatusPill } from '../components/common/StatusPill';

export const VerificationPortalPage: React.FC = () => {
  const [queryIdentifier, setQueryIdentifier] = useState('COEP-2026-CSE-001');
  const [requesterOrg, setRequesterOrg] = useState('Tata Consultancy Services — Talent Acquisition');
  const [purpose, setPurpose] = useState('Employment Background Verification');
  const [consentProofRef, setConsentProofRef] = useState('CANDIDATE-DPDP-CONSENT-2026-7892');
  const [isVerifying, setIsVerifying] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsVerifying(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.submitVerification({
        query_identifier: queryIdentifier,
        requester_organization: requesterOrg,
        purpose,
        consent_proof_ref: consentProofRef,
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Verification request failed');
    } finally {
      setIsVerifying(false);
    }
  };

  const sampleQuickQueries = [
    { label: 'COEP CSE Student #001 (Valid)', id: 'COEP-2026-CSE-001' },
    { label: 'Anna Univ CSE Student #010 (Valid)', id: 'CEG-2026-CSE-010' },
    { label: 'Unregistered / Invalid Reference', id: 'FAKE-999-NONEXISTENT' },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">
          Authorized Verification Portal
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Purpose-bound student enrolment and credential verification for authorized employers, universities, and regulators.
        </p>
      </div>

      <div className="p-4 rounded-xl bg-indigo-50/60 border border-indigo-200 text-xs text-indigo-950 flex items-start gap-3">
        <Lock className="w-4 h-4 text-indigo-700 flex-shrink-0 mt-0.5" />
        <div>
          <strong className="text-indigo-900">Privacy by Design & Purpose Limitation:</strong>
          <p className="text-[11px] mt-0.5 leading-relaxed text-indigo-900/80">
            Per Digital Personal Data Protection principles, verification requires an explicit lawful purpose
            and verifiable candidate consent reference. Only permitted claims are disclosed in response.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Verification Request Form */}
        <div className="p-6 rounded-2xl border border-slate-200 bg-white shadow-xs space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700 border-b border-slate-100 pb-2">
            Submit Verification Request
          </h2>

          {error && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold">
              {error}
            </div>
          )}

          <form onSubmit={handleVerify} className="space-y-3.5 text-xs">
            <div>
              <label className="block font-bold text-slate-700 mb-1">
                Student Identifier or APAAR Reference
              </label>
              <input
                type="text"
                required
                value={queryIdentifier}
                onChange={(e) => setQueryIdentifier(e.target.value)}
                placeholder="e.g. COEP-2026-CSE-001 or 900000000001"
                className="w-full p-2.5 rounded-lg border border-slate-300 font-mono text-xs font-bold text-slate-900 focus:ring-2 focus:ring-indigo-500"
              />
              <div className="flex flex-wrap gap-1 mt-1.5">
                {sampleQuickQueries.map((sq) => (
                  <button
                    key={sq.id}
                    type="button"
                    onClick={() => setQueryIdentifier(sq.id)}
                    className="text-[10px] text-indigo-600 hover:text-indigo-800 bg-indigo-50 px-1.5 py-0.5 rounded"
                  >
                    {sq.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">
                Requesting Organization
              </label>
              <input
                type="text"
                required
                value={requesterOrg}
                onChange={(e) => setRequesterOrg(e.target.value)}
                placeholder="e.g. Tata Consultancy Services / State Scholarship Portal"
                className="w-full p-2.5 rounded-lg border border-slate-300 text-xs font-medium text-slate-800 focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">
                Lawful Verification Purpose
              </label>
              <select
                value={purpose}
                onChange={(e) => setPurpose(e.target.value)}
                className="w-full p-2.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-800 focus:ring-2 focus:ring-indigo-500"
              >
                <option value="Employment Background Verification">Employment Background Verification</option>
                <option value="Government Scholarship Eligibility Audit">Government Scholarship Eligibility Audit</option>
                <option value="Inter-University Academic Credit Transfer">Inter-University Academic Credit Transfer</option>
                <option value="Regulatory AICTE Enrolment Inspection">Regulatory AICTE Enrolment Inspection</option>
              </select>
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">
                Candidate Consent Proof Reference
              </label>
              <input
                type="text"
                required
                value={consentProofRef}
                onChange={(e) => setConsentProofRef(e.target.value)}
                placeholder="e.g. CANDIDATE-CONSENT-TOKEN-2026-X99"
                className="w-full p-2.5 rounded-lg border border-slate-300 text-xs font-mono font-medium text-slate-800 focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <button
              type="submit"
              disabled={isVerifying}
              className="w-full mt-2 py-2.5 px-4 rounded-lg bg-indigo-600 text-white font-bold text-xs hover:bg-indigo-700 transition-colors shadow-xs flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isVerifying ? (
                <span>Executing Verification Gateway Query...</span>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>Execute Authorized Verification</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Verification Result Output */}
        <div className="p-6 rounded-2xl border border-slate-200 bg-white shadow-xs space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700 border-b border-slate-100 pb-2">
            Verification Claims Response
          </h2>

          {result ? (
            <div className="space-y-4">
              <div
                className={`p-4 rounded-xl border flex items-center gap-3 ${
                  result.verification_status === 'VERIFIED_LOCAL'
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                    : 'bg-rose-50 border-rose-200 text-rose-900'
                }`}
              >
                {result.verification_status === 'VERIFIED_LOCAL' ? (
                  <CheckCircle2 className="w-7 h-7 text-emerald-600 flex-shrink-0" />
                ) : (
                  <XCircle className="w-7 h-7 text-rose-600 flex-shrink-0" />
                )}
                <div>
                  <div className="font-extrabold text-sm">
                    {result.verification_status === 'VERIFIED_LOCAL'
                      ? 'Record Verified in Prototype Repository'
                      : 'Record Not Found in Prototype Repository'}
                  </div>
                  <div className="text-[11px] opacity-80 mt-0.5">
                    Provider: {result.verification_provider}
                  </div>
                </div>
              </div>

              {result.verification_status === 'VERIFIED_LOCAL' && (
                <div className="space-y-2.5 text-xs bg-slate-50 p-4 rounded-xl border border-slate-200">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Student Name:</span>
                    <span className="font-bold text-slate-900">{result.student_name}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Student ID / Roll No:</span>
                    <span className="font-mono font-bold text-slate-900">{result.student_id}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Masked APAAR:</span>
                    <MaskedIdViewer maskedId={result.masked_apaar_id} />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Institution:</span>
                    <span className="font-medium text-slate-800 text-right">{result.institution_name}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Programme:</span>
                    <span className="font-medium text-slate-800">{result.programme_name}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Academic Year:</span>
                    <span className="font-mono">{result.academic_year}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500">Admission Status:</span>
                    <StatusPill status={result.enrolment_status} />
                  </div>
                  <div className="flex items-center justify-between pt-1 border-t border-slate-200">
                    <span className="text-slate-400 text-[10px]">Audit Ref:</span>
                    <span className="font-mono text-[10px] text-indigo-700">{result.verification_reference}</span>
                  </div>
                </div>
              )}

              <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-[10px] leading-relaxed">
                <strong>Simulated Provider Disclaimer:</strong> A local database match in this demonstration
                verifies registration in the EDUTrace prototype repository. It does not establish official APAAR
                identity validity with UIDAI or DigiLocker until production authorized credentials are configured.
              </div>
            </div>
          ) : (
            <div className="p-12 text-center text-xs text-slate-400 border border-dashed border-slate-200 rounded-xl">
              Fill in the verification form and click 'Execute Authorized Verification' to inspect permitted claims.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
