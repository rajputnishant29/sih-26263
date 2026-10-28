import React from 'react';

export const StatusPill: React.FC<{ status: string }> = ({ status }) => {
  const normalized = status.toUpperCase();
  const styles: Record<string, string> = {
    ACTIVE: 'bg-emerald-50 text-emerald-700 border-emerald-300',
    VALID: 'bg-emerald-50 text-emerald-700 border-emerald-300',
    COMMITTED: 'bg-emerald-50 text-emerald-700 border-emerald-300',
    CONFIRMED: 'bg-emerald-50 text-emerald-700 border-emerald-300',
    RESOLVED: 'bg-emerald-50 text-emerald-700 border-emerald-300',
    VERIFIED_LOCAL: 'bg-emerald-50 text-emerald-700 border-emerald-300',

    OPEN: 'bg-rose-50 text-rose-700 border-rose-300',
    ERROR: 'bg-rose-50 text-rose-700 border-rose-300',
    RECORD_NOT_FOUND: 'bg-rose-50 text-rose-700 border-rose-300',
    REJECTED: 'bg-rose-50 text-rose-700 border-rose-300',

    ASSIGNED: 'bg-sky-50 text-sky-700 border-sky-300',
    PENDING_REVIEW: 'bg-amber-50 text-amber-700 border-amber-300',
    PENDING_CONFIRMATION: 'bg-amber-50 text-amber-700 border-amber-300',
    CORRECTION_REQUESTED: 'bg-amber-50 text-amber-700 border-amber-300',
    WARNING: 'bg-amber-50 text-amber-700 border-amber-300',
    STAGED: 'bg-blue-50 text-blue-700 border-blue-300',

    FALSE_POSITIVE: 'bg-slate-100 text-slate-700 border-slate-300',
    WITHDRAWN: 'bg-slate-100 text-slate-700 border-slate-300',
    CANCELLED: 'bg-slate-100 text-slate-700 border-slate-300',
    TRANSFERRED: 'bg-indigo-50 text-indigo-700 border-indigo-300',
  };

  const style = styles[normalized] || 'bg-slate-50 text-slate-700 border-slate-200';

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${style}`}>
      {status.replace(/_/g, ' ')}
    </span>
  );
};
