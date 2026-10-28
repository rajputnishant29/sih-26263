import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'info';
  badge?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'primary',
  badge,
}) => {
  const variantStyles = {
    primary: 'border-slate-200 bg-white text-indigo-600',
    success: 'border-emerald-200 bg-white text-emerald-600',
    warning: 'border-amber-200 bg-white text-amber-600',
    danger: 'border-rose-200 bg-white text-rose-600',
    info: 'border-sky-200 bg-white text-sky-600',
  };

  const iconBgStyles = {
    primary: 'bg-indigo-50 text-indigo-600',
    success: 'bg-emerald-50 text-emerald-600',
    warning: 'bg-amber-50 text-amber-600',
    danger: 'bg-rose-50 text-rose-600',
    info: 'bg-sky-50 text-sky-600',
  };

  return (
    <div className={`p-5 rounded-xl border ${variantStyles[variant]} shadow-xs flex flex-col justify-between transition-all hover:shadow-md`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          {title}
        </span>
        <div className={`p-2.5 rounded-lg ${iconBgStyles[variant]}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <div>
        <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          {value}
        </div>
        {(subtitle || badge) && (
          <div className="flex items-center gap-2 mt-1.5">
            {badge && (
              <span className="px-1.5 py-0.5 rounded text-[11px] font-bold bg-slate-100 text-slate-700">
                {badge}
              </span>
            )}
            {subtitle && <span className="text-xs text-slate-500 font-medium">{subtitle}</span>}
          </div>
        )}
      </div>
    </div>
  );
};
