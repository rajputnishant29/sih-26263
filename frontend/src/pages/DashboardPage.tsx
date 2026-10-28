import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Building2,
  FileCheck2,
  Users,
  AlertOctagon,
  Percent,
  TrendingUp,
  ShieldAlert,
  ArrowUpRight,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import { DashboardSummary } from '../types';
import { MetricCard } from '../components/ui/MetricCard';

export const DashboardPage: React.FC = () => {
  const { user, selectedAcademicYearId } = useAuth();
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = async () => {
    try {
      setIsLoading(true);
      const summary = await api.getDashboardSummary(
        selectedAcademicYearId || undefined,
        user?.institution_id || undefined
      );
      setData(summary);
      setError(null);
    } catch (e: any) {
      console.error('Failed to load dashboard:', e);
      setError(e.message || 'Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();

    // Listen for live Server-Sent Events updates
    const eventSource = new EventSource('/api/dashboard/events');
    eventSource.addEventListener('batch_committed', () => {
      console.log('Real-time event: batch committed, refreshing metrics...');
      fetchSummary();
    });
    eventSource.addEventListener('issue_updated', () => {
      console.log('Real-time event: issue updated, refreshing metrics...');
      fetchSummary();
    });
    eventSource.addEventListener('record_corrected', () => {
      fetchSummary();
    });

    return () => {
      eventSource.close();
    };
  }, [selectedAcademicYearId, user?.role, user?.institution_id]);

  if (isLoading && !data) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center gap-2">
          <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin" />
          <span className="text-sm text-slate-500 font-medium">Reconciling student-level metrics...</span>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 rounded-xl bg-rose-50 border border-rose-200 text-rose-800">
        <h3 className="font-bold text-base">Dashboard Query Error</h3>
        <p className="text-sm mt-1">{error || 'Unknown error occurred'}</p>
        <button
          onClick={fetchSummary}
          className="mt-3 px-3 py-1.5 rounded-lg bg-rose-600 text-white text-xs font-semibold"
        >
          Retry
        </button>
      </div>
    );
  }

  // Chart colors
  const COLORS = ['#4f46e5', '#059669', '#d97706', '#dc2626', '#0284c7', '#9333ea', '#e11d48'];

  return (
    <div className="space-y-6">
      {/* Page Title & Scope Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            AICTE Regulatory Command Dashboard
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Student-level enrolment records reconciled against versioned AICTE Extension of Approval (EoA) data.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchSummary}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-200 text-slate-700 text-xs font-semibold hover:bg-slate-50 transition-colors shadow-2xs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh Reconciliation</span>
          </button>
          <Link
            to="/upload"
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 transition-colors shadow-xs shadow-indigo-600/30"
          >
            <span>Upload Student Data</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Top 4 KPI Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Onboarded Scope"
          value={data.institutions_count}
          subtitle={`${data.programmes_count} Technical Programmes`}
          icon={Building2}
          variant="primary"
          badge="Verified Institutions"
        />
        <MetricCard
          title="Approved Intake"
          value={data.approved_intake_total}
          subtitle={`+${data.supernumerary_seats_total} Supernumerary Sanctioned`}
          icon={FileCheck2}
          variant="info"
          badge={`${data.approved_intake_total + data.supernumerary_seats_total} Effective`}
        />
        <MetricCard
          title="Actual Enrolment"
          value={data.actual_enrolment_total}
          subtitle={`Capacity Utilization: ${data.intake_utilization_rate}%`}
          icon={Users}
          variant="success"
          badge={`${data.remaining_capacity_total} Remaining`}
        />
        <MetricCard
          title="Unresolved Exceptions"
          value={data.unresolved_issues_count}
          subtitle={`${data.critical_issues_count} Critical • ${data.duplicate_candidates_count} Duplicate Candidates`}
          icon={AlertOctagon}
          variant={data.critical_issues_count > 0 ? 'danger' : 'warning'}
          badge="Review Required"
        />
      </div>

      {/* Visualizations Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Approved Intake vs Calculated Enrolment Bar Chart */}
        <div className="lg:col-span-2 p-5 rounded-xl border border-slate-200 bg-white shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-900 tracking-tight">
                Programme-Wise Approved Intake vs Actual Enrolment
              </h2>
              <p className="text-xs text-slate-500">
                Comparing effective sanctioned capacity against active student-level records.
              </p>
            </div>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700">
              Live Reconciled
            </span>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={data.programme_reconciliations}
                margin={{ top: 10, right: 10, left: -20, bottom: 20 }}
              >
                <XAxis
                  dataKey="programme_code"
                  tick={{ fontSize: 11 }}
                  interval={0}
                />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Bar dataKey="effective_limit" name="Effective Approved Intake" fill="#6366f1" radius={[4, 4, 0, 0]} />
                <Bar dataKey="calculated_enrolment" name="Actual Enrolment" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Breakdown Donut Chart */}
        <div className="p-5 rounded-xl border border-slate-200 bg-white shadow-xs">
          <div className="mb-4">
            <h2 className="text-sm font-bold text-slate-900 tracking-tight">
              Admission Category Distribution
            </h2>
            <p className="text-xs text-slate-500">
              Enrolment share across quotas and supernumerary categories.
            </p>
          </div>

          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.category_distributions}
                  dataKey="count"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={3}
                >
                  {data.category_distributions.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 gap-2 mt-3 pt-3 border-t border-slate-100 text-[11px]">
            {data.category_distributions.map((c, i) => (
              <div key={c.category} className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                <span className="text-slate-600 truncate">{c.category}:</span>
                <span className="font-bold text-slate-900 ml-auto">{c.count} ({c.percentage}%)</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Programme-Level Reconciliation Table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden">
        <div className="p-4 sm:p-5 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h2 className="text-sm font-bold text-slate-900 tracking-tight">
              Programme-Level Intake & Enrolment Reconciliation
            </h2>
            <p className="text-xs text-slate-500">
              Traceable association: Approval value → EoA document → Programme → Rule version → Calculated result.
            </p>
          </div>
          <Link
            to="/reports"
            className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
          >
            <span>View Full Report & CSV Export</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-200">
              <tr>
                <th className="py-3 px-4 font-bold">Institution & Programme</th>
                <th className="py-3 px-4 font-bold">Base EoA Intake</th>
                <th className="py-3 px-4 font-bold">Supernumerary</th>
                <th className="py-3 px-4 font-bold">Effective Limit</th>
                <th className="py-3 px-4 font-bold">Calculated Enrolment</th>
                <th className="py-3 px-4 font-bold">Variance</th>
                <th className="py-3 px-4 font-bold">Intake Utilization</th>
                <th className="py-3 px-4 font-bold">Approval Source Ref</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.programme_reconciliations.map((p) => {
                const isOver = p.is_exceeded;
                return (
                  <tr key={`${p.institution_id}-${p.programme_id}`} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4 font-medium">
                      <div className="font-bold text-slate-900">{p.programme_name} ({p.programme_code})</div>
                      <div className="text-[11px] text-slate-500">{p.institution_name}</div>
                    </td>
                    <td className="py-3 px-4 font-mono font-medium">{p.base_approved_intake}</td>
                    <td className="py-3 px-4 font-mono text-emerald-700">+{p.supernumerary_sanctioned}</td>
                    <td className="py-3 px-4 font-mono font-bold text-indigo-900">{p.effective_limit}</td>
                    <td className="py-3 px-4 font-mono font-bold">
                      <span className={isOver ? 'text-rose-600 font-extrabold' : 'text-slate-900'}>
                        {p.calculated_enrolment}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono">
                      {isOver ? (
                        <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-700 font-bold border border-rose-200">
                          +{p.variance} Excess
                        </span>
                      ) : (
                        <span className="text-slate-500">
                          {p.variance} ({Math.abs(p.variance)} capacity left)
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              isOver ? 'bg-rose-500' : p.utilization_rate > 90 ? 'bg-emerald-500' : 'bg-indigo-500'
                            }`}
                            style={{ width: `${Math.min(100, p.utilization_rate)}%` }}
                          />
                        </div>
                        <span className="font-mono text-[11px] font-semibold">{p.utilization_rate}%</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-mono text-[11px] text-slate-600 truncate max-w-[180px]" title={p.source_eoa_reference}>
                        {p.source_eoa_reference}
                      </div>
                      <div className="text-[10px] text-indigo-600 font-medium">Rule: {p.rule_version}</div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Exception Queue Quick Action Panel */}
      <div className="p-5 rounded-xl border border-rose-200 bg-rose-50/40 shadow-xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="p-3 rounded-xl bg-rose-100 text-rose-700 flex-shrink-0">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-rose-950">
              {data.unresolved_issues_count} Active Exceptions Require Regulatory Investigation
            </h3>
            <p className="text-xs text-rose-800/80 mt-0.5">
              Includes missing APAAR references, declared total mismatches, cross-institution duplicate candidates, and intake excess.
            </p>
          </div>
        </div>

        <Link
          to="/exceptions"
          className="px-4 py-2 rounded-lg bg-rose-600 text-white font-bold text-xs hover:bg-rose-700 transition-colors shadow-xs shadow-rose-600/20 whitespace-nowrap text-center"
        >
          Open Actionable Review Queue
        </Link>
      </div>
    </div>
  );
};
