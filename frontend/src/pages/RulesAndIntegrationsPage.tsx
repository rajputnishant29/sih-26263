import React, { useState, useEffect } from 'react';
import { Sliders, CheckCircle2, ArrowRight, ShieldCheck, Activity, Layers, FileCode } from 'lucide-react';
import { api } from '../lib/api';
import { SeverityBadge } from '../components/common/SeverityBadge';

export const RulesAndIntegrationsPage: React.FC = () => {
  const [rules, setRules] = useState<any[]>([]);
  const [statusData, setStatusData] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const [r, s] = await Promise.all([api.getRules(), api.getIntegrationStatus()]);
        setRules(r);
        setStatusData(s);
      } catch (e) {
        console.error('Failed to load rules & integration data:', e);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">
          Rules Engine & Integration Architecture
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Deterministic admission rules, versioned AICTE approval schemas, and progressive external integration roadmap.
        </p>
      </div>

      {/* 3-Phase Architecture Progression Roadmap */}
      {statusData && (
        <div className="p-6 rounded-2xl border border-slate-200 bg-white shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600 font-mono">
                Architecture Roadmap
              </span>
              <h2 className="text-base font-extrabold text-slate-900 mt-0.5">
                Onboarding & Integration Progression
              </h2>
            </div>
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
              CSV → REST APIs → Authorized Adapter
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {statusData.architecture_progression.map((phase: any, index: number) => (
              <div key={index} className="p-4 rounded-xl border border-slate-200 bg-slate-50/60 space-y-2 text-xs flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 text-xs">{phase.phase}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      phase.status === 'OPERATIONAL_PROTOTYPE'
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-amber-100 text-amber-800'
                    }`}>
                      {phase.readiness}
                    </span>
                  </div>
                  <p className="text-slate-600 text-[11px] mt-2 leading-relaxed">
                    {phase.description}
                  </p>
                </div>
                <div className="pt-2 border-t border-slate-200/80 text-[10px] text-slate-500">
                  <strong>Deployment Dependency:</strong> {phase.official_dependency}
                </div>
              </div>
            ))}
          </div>

          {/* Adapter Health Indicators */}
          <div className="p-4 rounded-xl bg-slate-900 text-slate-300 text-xs space-y-3">
            <div className="flex items-center justify-between font-bold text-slate-100">
              <span className="flex items-center gap-1.5">
                <Activity className="w-4 h-4 text-emerald-400" />
                <span>Internal Core Engine & Adapter Health Diagnostics</span>
              </span>
              <span className="text-[10px] font-mono text-emerald-400">All Systems Operational</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-[11px]">
              {Object.entries(statusData.adapters_health).map(([k, v]: [string, any]) => (
                <div key={k} className="p-2 rounded bg-slate-800/80 border border-slate-700">
                  <span className="text-slate-400 block text-[9px] uppercase font-mono">{k.replace(/_/g, ' ')}</span>
                  <span className="font-bold text-emerald-400 mt-0.5 block truncate">{v}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Versioned Rules Registry Table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden">
        <div className="p-4 sm:p-5 border-b border-slate-200">
          <h2 className="text-sm font-bold text-slate-900 tracking-tight">
            Active Versioned Deterministic Validation Rules
          </h2>
          <p className="text-xs text-slate-500">
            Rules-first validation with deterministic counting semantics. AI serves as a secondary outlier signal.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-200">
              <tr>
                <th className="py-3 px-4 font-bold">Rule Code</th>
                <th className="py-3 px-4 font-bold">Version</th>
                <th className="py-3 px-4 font-bold">Severity</th>
                <th className="py-3 px-4 font-bold">Rule Name & Operational Intent</th>
                <th className="py-3 px-4 font-bold">Parameters</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-slate-400">Loading rule registry...</td>
                </tr>
              ) : (
                rules.map((rule) => (
                  <tr key={rule.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-indigo-700">
                      {rule.rule_code}
                    </td>
                    <td className="py-3 px-4 font-mono font-medium">{rule.rule_version}</td>
                    <td className="py-3 px-4">
                      <SeverityBadge severity={rule.severity} />
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">{rule.rule_name}</div>
                      <div className="text-[11px] text-slate-500 mt-0.5 leading-relaxed">{rule.description}</div>
                    </td>
                    <td className="py-3 px-4 font-mono text-[10px] text-slate-500">
                      <pre className="bg-slate-50 p-1.5 rounded border border-slate-200 overflow-x-auto max-w-[200px]">
                        {JSON.stringify(rule.config_payload, null, 1)}
                      </pre>
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
