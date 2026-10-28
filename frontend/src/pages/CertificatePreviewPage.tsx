import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Award, Printer, ShieldCheck, QrCode, ExternalLink, RefreshCw } from 'lucide-react';
import { api } from '../lib/api';
import { CertificatePreview } from '../types';

export const CertificatePreviewPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const enrolmentIdParam = searchParams.get('enrolmentId');
  const [enrolmentId, setEnrolmentId] = useState<number>(enrolmentIdParam ? Number(enrolmentIdParam) : 1);
  const [cert, setCert] = useState<CertificatePreview | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [qrVerifyResult, setQrVerifyResult] = useState<any | null>(null);
  const [isVerifyingQr, setIsVerifyingQr] = useState<boolean>(false);

  const fetchCertificate = async (id: number) => {
    try {
      setIsLoading(true);
      const data = await api.getCertificatePreview(id);
      setCert(data);
      setQrVerifyResult(null);
    } catch (e) {
      console.error('Failed to load certificate:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCertificate(enrolmentId);
  }, [enrolmentId]);

  const handlePrint = () => {
    window.print();
  };

  const handleTestQrRoute = async (slug: string) => {
    setIsVerifyingQr(true);
    try {
      const res = await api.verifyBySlug(slug);
      setQrVerifyResult(res);
    } catch (e: any) {
      alert('QR verification failed: ' + e.message);
    } finally {
      setIsVerifyingQr(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 no-print">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            Verifiable Degree Credential Preview
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Student record credential with side-by-side APAAR ID and Student ID, degree-awarding body, and cryptographic QR verification.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Quick Enrolment Switcher */}
          <select
            value={enrolmentId}
            onChange={(e) => setEnrolmentId(Number(e.target.value))}
            className="px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 bg-white"
          >
            <option value={1}>COEP Student #001 (CSE)</option>
            <option value={10}>COEP Student #010 (CSE - Cross Dup)</option>
            <option value={150}>COEP Student #020 (ECE)</option>
            <option value={341}>Anna University Student #001</option>
            <option value={450}>VJTI Student #001</option>
          </select>

          <button
            onClick={handlePrint}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 transition-colors shadow-xs"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print / PDF Export</span>
          </button>
        </div>
      </div>

      {isLoading || !cert ? (
        <div className="p-16 text-center text-xs text-slate-400">Loading credential preview...</div>
      ) : (
        <div className="space-y-6">
          {/* High-Fidelity Printable Degree Certificate Card */}
          <div className="relative bg-white border-8 border-double border-indigo-950 p-8 sm:p-12 rounded-xl shadow-xl overflow-hidden print:shadow-none print:border-4">
            {/* Watermark text */}
            <div className="certificate-watermark">
              {cert.watermark_text}
            </div>

            {/* Certificate Header */}
            <div className="text-center border-b-2 border-indigo-900/20 pb-6 relative z-10">
              <div className="w-14 h-14 rounded-full bg-indigo-950 text-amber-400 flex items-center justify-center mx-auto mb-3 shadow-md font-bold text-xl">
                ET
              </div>
              <h2 className="text-lg sm:text-2xl font-black text-indigo-950 uppercase tracking-widest font-serif">
                {cert.degree_awarding_body}
              </h2>
              <div className="text-xs sm:text-sm font-semibold text-slate-600 uppercase tracking-wider mt-1">
                Conducted at {cert.institution_name} • Institute Code: {cert.institution_code}
              </div>
              <div className="text-[11px] font-mono text-slate-500 mt-1">
                AICTE Regulatory Affiliation Academic Year: {cert.academic_year}
              </div>
            </div>

            {/* Certificate Body */}
            <div className="py-8 text-center space-y-4 relative z-10 font-serif">
              <p className="text-xs sm:text-sm text-slate-600 italic">
                This is to certify that
              </p>

              <div className="text-xl sm:text-3xl font-black text-indigo-950 tracking-wide font-sans">
                {cert.student_name}
              </div>

              {/* Side-by-Side Dual Identity Verification Badges */}
              <div className="flex flex-wrap items-center justify-center gap-4 py-2 font-sans">
                <div className="px-3 py-1.5 rounded-lg bg-slate-100 border border-slate-300 text-xs">
                  <span className="text-slate-500 text-[10px] block uppercase font-bold">Institution Student ID</span>
                  <span className="font-mono font-extrabold text-slate-900">{cert.student_id}</span>
                </div>

                <div className="px-3 py-1.5 rounded-lg bg-indigo-50 border border-indigo-300 text-xs">
                  <span className="text-indigo-600 text-[10px] block uppercase font-bold flex items-center gap-1 justify-center">
                    <ShieldCheck className="w-3 h-3" />
                    <span>APAAR Identifier</span>
                  </span>
                  <span className="font-mono font-extrabold text-indigo-950">{cert.masked_apaar_id}</span>
                </div>
              </div>

              <p className="text-xs sm:text-sm text-slate-700 max-w-xl mx-auto leading-relaxed">
                has successfully completed all prescribed courses and passed the examination with{' '}
                <strong className="text-slate-900 font-bold">{cert.grade_or_division}</strong>, and is hereby admitted to the degree of
              </p>

              <div className="text-lg sm:text-2xl font-black text-indigo-900 font-sans tracking-tight">
                {cert.degree_name}
              </div>
            </div>

            {/* Certificate Footer with QR Code */}
            <div className="pt-6 border-t-2 border-indigo-900/20 flex flex-col sm:flex-row items-center justify-between gap-4 relative z-10 text-xs font-sans">
              <div className="text-left space-y-1">
                <div><span className="text-slate-400">Certificate No:</span> <strong className="font-mono text-slate-800">{cert.certificate_number}</strong></div>
                <div><span className="text-slate-400">Date of Conferment:</span> <span className="text-slate-800">{cert.issue_date}</span></div>
                <div className="text-[10px] text-slate-400">Issued under state university statutory governance</div>
              </div>

              {/* QR Verification Box */}
              <div className="flex items-center gap-3 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                <div className="w-14 h-14 bg-white border border-slate-300 rounded flex items-center justify-center text-slate-800 flex-shrink-0">
                  <QrCode className="w-10 h-10 text-indigo-950" />
                </div>
                <div className="text-left text-[10px] leading-tight max-w-[150px]">
                  <div className="font-bold text-indigo-900">Scan to Verify</div>
                  <div className="text-slate-500 mt-0.5">Route: /verify/{cert.qr_verification_slug}</div>
                  <button
                    onClick={() => handleTestQrRoute(cert.qr_verification_slug)}
                    className="mt-1 text-indigo-600 font-bold hover:underline inline-flex items-center gap-0.5 no-print"
                  >
                    <span>Test QR Route</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* QR Verification Interactive Tester Drawer (No-print) */}
          {qrVerifyResult && (
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-950 space-y-2 no-print">
              <div className="font-bold flex items-center gap-1.5 text-emerald-900">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Working Prototype QR Route Result (/verify/{cert.qr_verification_slug})</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 bg-white/80 p-3 rounded-lg text-[11px]">
                <div><span className="text-slate-500">Status:</span> <strong className="text-emerald-700">{qrVerifyResult.status}</strong></div>
                <div><span className="text-slate-500">Candidate:</span> <strong>{qrVerifyResult.student_name}</strong></div>
                <div><span className="text-slate-500">Student ID:</span> <span className="font-mono">{qrVerifyResult.student_id}</span></div>
                <div><span className="text-slate-500">Masked APAAR:</span> <span className="font-mono font-bold text-indigo-900">{qrVerifyResult.masked_apaar_id}</span></div>
              </div>
              <div className="text-[10px] text-emerald-800">
                Verified against {qrVerifyResult.verification_provider}. Proves live QR routing without disclosing unpermitted personal records.
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
