import React, { useState } from 'react';
import { Shield, Copy, Check } from 'lucide-react';

export const MaskedIdViewer: React.FC<{ maskedId: string; showIcon?: boolean }> = ({
  maskedId,
  showIcon = true,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(maskedId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-xs font-mono font-medium text-slate-800 tracking-tight"
      title="Protected Deterministic Identity Reference (DPDP-Compliant Protected Mask)"
    >
      {showIcon && <Shield className="w-3 h-3 text-indigo-500" />}
      <span>{maskedId}</span>
      <button
        onClick={handleCopy}
        className="text-slate-400 hover:text-slate-600 transition-colors p-0.5"
        title="Copy Masked Reference"
      >
        {copied ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
      </button>
    </div>
  );
};
