import React, { useState, useEffect } from 'react';
import { BarChart3, Download, FileSpreadsheet, RefreshCw, CheckCircle2 } from 'lucide-react';
import { api } from '../lib/api';
import { useAuth } from '../context/AuthContext';

export const ReportsPage: React.FC = () => {
  const { user, selectedAcademicYearId } = useAuth();
  const [rows, setRows] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchReports = async () => {
    try {
      setIsLoading(true);
      const res = await api.getReconciliationReport(
        selectedAcademicYearId || undefined,
        user?.institution_id || undefined
      );
      setRows(res.rows);
    } catch (e) {
      console.error('Failed to load reports:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [selectedAcademicYearId, user?.role]);

  const handleExportCsv = () => {
    const params = new URLSearchParams();
    if (selectedAcademicYearId) params.set('academic_year_id', selectedAcademicYearId.toString());
    if (user?.institution_id) params.set('institution_id', user.institution_id.toString());
    window.location.href = `/api/reports/reconciliation/export-csv?${params.toString()}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            Regulatory Reports & Reconciliation Exports
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Audit-grade reconciliation datasets with Formula Injection protection and traceable source metadata.
          </p>
        </div>

        <button
          onClick={handleExportCsv}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 text-white font-bold text-xs hover:bg-emerald-700 transition-colors shadow-xs"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Export Reconciled CSV (Sanitized)</span>
        </button>
      </div>

      {/* Main Report Table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden">
        <div className="p-4 sm:p-5 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold text-slate-900 tracking-tight">
              Approved Intake vs Actual Enrolment Regulatory Audit Table
            </h2>
            <p className="text-xs text-slate-500">
              Derives aggregate counts strictly from active eligible student-level records.
            </p>
          </div>
          <button
            onClick={fetchReports}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-200">
              <tr>
                <th className="py-3 px-4 font-bold">Institution</th>
                <th className="py-3 px-4 font-bold">Programme</th>
                <th className="py-3 px-4 font-bold">Base Intake</th>
                <th className="py-3 px-4 font-bold">Supernumerary</th>
                <th className="py-3 px-4 font-bold">Effective Limit</th>
                <th className="py-3 px-4 font-bold">Actual Enrolment</th>
                <th className="py-3 px-4 font-bold">NRI</th>
                <th className="py-3 px-4 font-bold">FN / OCI</th>
                <th className="py-3 px-4 font-bold">Variance</th>
                <th className="py-3 px-4 font-bold">Utilization</th>
                <th className="py-3 px-4 font-bold">Source EoA Letter</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr>
                  <td colSpan={11} className="py-12 text-center text-slate-400">Loading report data...</td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan={11} className="py-12 text-center text-slate-400">No report rows found.</td>
                </tr>
              ) : (
                rows.map((r, i) => (
                  <tr key={i} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4 font-semibold text-slate-900">
                      {r.institution_name}
                      <span className="text-[10px] text-slate-400 block font-mono">PID: {r.institution_code}</span>
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-800">
                      {r.programme_name} ({r.programme_code})
                    </td>
                    <td className="py-3 px-4 font-mono font-medium">{r.base_approved_intake}</td>
                    <td className="py-3 px-4 font-mono text-emerald-700">+{r.supernumerary_sanctioned}</td>
                    <td className="py-3 px-4 font-mono font-extrabold text-indigo-900">{r.effective_limit}</td>
                    <td className="py-3 px-4 font-mono font-bold">{r.calculated_enrolment}</td>
                    <td className="py-3 px-4 font-mono">{r.nri_enrolled}</td>
                    <td className="py-3 px-4 font-mono">{r.fn_oci_enrolled}</td>
                    <td className="py-3 px-4 font-mono">
                      {r.is_exceeded ? (
                        <span className="font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                          +{r.variance} (Excess)
                        </span>
                      ) : (
                        <span className="text-slate-600">{r.variance}</span>
                      )}
                    </td>
                    <td className="py-3 px-4 font-mono font-bold">
                      <span className={r.is_exceeded ? 'text-rose-600' : 'text-slate-900'}>
                        {r.utilization_rate}%
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-[10px] text-slate-500 truncate max-w-[160px]" title={r.source_eoa_reference}>
                      {r.source_eoa_reference}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
