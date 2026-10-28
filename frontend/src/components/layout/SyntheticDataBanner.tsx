import React from 'react';
import { AlertTriangle } from 'lucide-react';

export const SyntheticDataBanner: React.FC = () => {
  return (
    <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2 text-xs text-amber-900 flex items-center justify-between no-print">
      <div className="flex items-center gap-2 max-w-5xl mx-auto">
        <span className="inline-flex items-center gap-1 font-bold tracking-wider px-2 py-0.5 rounded bg-amber-600 text-white text-[10px] uppercase">
          <AlertTriangle className="w-3 h-3" />
          Synthetic Demo Data
        </span>
        <span className="font-medium text-amber-950">
          Illustrative synthetic prototype data. These figures are not official AICTE statistics.
          Official APAAR verification and institutional integrations are not enabled unless explicitly demonstrated.
        </span>
      </div>
    </div>
  );
};
