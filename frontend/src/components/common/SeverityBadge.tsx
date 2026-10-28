import React from 'react';

export const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => {
  const styles: Record<string, string> = {
    CRITICAL: 'bg-rose-50 text-rose-700 border-rose-300 font-bold',
    HIGH: 'bg-orange-50 text-orange-700 border-orange-300 font-semibold',
    MEDIUM: 'bg-amber-50 text-amber-700 border-amber-300 font-semibold',
    LOW: 'bg-slate-50 text-slate-700 border-slate-300 font-medium',
    INFO: 'bg-sky-50 text-sky-700 border-sky-300 font-medium',
  };

  const style = styles[severity.toUpperCase()] || styles.LOW;

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs border ${style}`}>
      {severity}
    </span>
  );
};
