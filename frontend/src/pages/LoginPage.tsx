import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  Building2,
  Users,
  AlertTriangle,
  Lock,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.login({ email, password });
      login(res.access_token, res.user);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Invalid email or password');
    } finally {
      setIsLoading(false);
    }
  };

  const quickLogins = [
    {
      title: 'AICTE Administrator',
      role: 'AICTE_ADMIN',
      email: 'aicte.admin@edutrace.gov.in',
      desc: 'National oversight, all institutions & cross-institution anomalies',
      icon: ShieldCheck,
      color: 'bg-indigo-50 border-indigo-200 text-indigo-700 hover:bg-indigo-100',
    },
    {
      title: 'COEP Institution Admin',
      role: 'INSTITUTION_ADMIN',
      email: 'inst.admin@coep.ac.in',
      desc: 'Institutional records, intake compliance, correction responses',
      icon: Building2,
      color: 'bg-emerald-50 border-emerald-200 text-emerald-700 hover:bg-emerald-100',
    },
    {
      title: 'COEP Data Operator',
      role: 'INSTITUTION_DATA_OPERATOR',
      email: 'data.operator@coep.ac.in',
      desc: 'CSV / Excel upload staging, column mapping, dry-run validation',
      icon: Users,
      color: 'bg-sky-50 border-sky-200 text-sky-700 hover:bg-sky-100',
    },
    {
      title: 'Authorized Reviewer',
      role: 'AUTHORIZED_REVIEWER',
      email: 'reviewer@aicte.gov.in',
      desc: 'Actionable exception queue, evidence inspection, decision recording',
      icon: AlertTriangle,
      color: 'bg-amber-50 border-amber-200 text-amber-700 hover:bg-amber-100',
    },
    {
      title: 'External Verifier (TCS)',
      role: 'EXTERNAL_VERIFIER',
      email: 'verifier.tcs@tcs.com',
      desc: 'Purpose-bound credential and enrolment verification',
      icon: ShieldCheck,
      color: 'bg-purple-50 border-purple-200 text-purple-700 hover:bg-purple-100',
    },
  ];

  const handleQuickLogin = (userEmail: string) => {
    setEmail(userEmail);
    setPassword('Demo@2026');
    // Auto submit
    setIsLoading(true);
    api
      .login({ email: userEmail, password: 'Demo@2026' })
      .then((res) => {
        login(res.access_token, res.user);
        navigate('/');
      })
      .catch((err) => {
        setError(err.message || 'Login failed');
        setIsLoading(false);
      });
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-600 text-white font-extrabold text-2xl shadow-xl shadow-indigo-600/30 mb-4">
          ET
        </div>
        <h2 className="text-3xl font-extrabold text-white tracking-tight">
          EDUTrace Platform
        </h2>
        <p className="mt-2 text-sm text-slate-400 max-w-sm mx-auto">
          APAAR ID-Based Student Data Management, Admission Reconciliation & Verification
        </p>
        <div className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800 text-slate-400 text-xs border border-slate-700">
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span>Smart India Hackathon 2026 • PS SIH26263</span>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-xl px-4">
        <div className="bg-white py-8 px-6 shadow-2xl rounded-2xl sm:px-10 border border-slate-100">
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold">
              {error}
            </div>
          )}

          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                Official Email Address
              </label>
              <div className="mt-1">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="aicte.admin@edutrace.gov.in"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                Password
              </label>
              <div className="mt-1">
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-indigo-600 text-white font-bold text-sm shadow-md hover:bg-indigo-700 transition-colors disabled:opacity-50"
            >
              {isLoading ? 'Authenticating...' : 'Sign In to Portal'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick 1-Click Demo Evaluation Login Personas */}
          <div className="mt-8 pt-6 border-t border-slate-100">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                1-Click Demo Evaluation Accounts
              </span>
              <span className="text-[10px] text-indigo-600 font-semibold bg-indigo-50 px-2 py-0.5 rounded">
                Password: Demo@2026
              </span>
            </div>

            <div className="space-y-2">
              {quickLogins.map((ql) => {
                const Icon = ql.icon;
                return (
                  <button
                    key={ql.role}
                    type="button"
                    onClick={() => handleQuickLogin(ql.email)}
                    className={`w-full text-left p-3 rounded-xl border ${ql.color} transition-all flex items-center justify-between group`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-white/80 shadow-xs">
                        <Icon className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="font-bold text-xs">{ql.title}</div>
                        <div className="text-[11px] opacity-80">{ql.desc}</div>
                      </div>
                    </div>
                    <ArrowRight className="w-4 h-4 opacity-50 group-hover:opacity-100 transition-opacity" />
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Synthetic Disclaimer */}
        <div className="text-center mt-6 text-xs text-slate-400">
          Illustrative synthetic prototype data. These figures are not official AICTE statistics.
        </div>
      </div>
    </div>
  );
};
