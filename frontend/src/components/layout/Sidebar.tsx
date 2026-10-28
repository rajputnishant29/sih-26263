import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Building2,
  FileCheck2,
  UploadCloud,
  Users,
  AlertOctagon,
  ShieldCheck,
  Award,
  BarChart3,
  History,
  Sliders,
  CheckSquare,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Sidebar: React.FC<{ isOpen: boolean; onToggle: () => void }> = ({ isOpen }) => {
  const { user } = useAuth();

  const navItems = [
    { label: 'AICTE Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Institutions', path: '/institutions', icon: Building2 },
    { label: 'Programmes & EoA', path: '/programmes', icon: FileCheck2 },
    { label: 'Student Data Upload', path: '/upload', icon: UploadCloud },
    { label: 'Student Repository', path: '/students', icon: Users },
    { label: 'Exceptions & Review', path: '/exceptions', icon: AlertOctagon, badge: '12' },
    { label: 'Authorized Verification', path: '/verification', icon: ShieldCheck },
    { label: 'Degree Certificate Preview', path: '/certificates', icon: Award },
    { label: 'Reports & Analytics', path: '/reports', icon: BarChart3 },
    { label: 'Audit Trail', path: '/audit', icon: History },
    { label: 'Rules & Integrations', path: '/rules', icon: Sliders },
    { label: 'Traceability Matrix', path: '/traceability', icon: CheckSquare },
  ];

  return (
    <aside
      className={`fixed lg:static inset-y-0 left-0 z-40 bg-slate-900 text-slate-200 border-r border-slate-800 transition-all duration-300 flex flex-col no-print ${
        isOpen ? 'w-64' : 'w-20'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 px-4 flex items-center gap-3 border-b border-slate-800">
        <div className="w-10 h-10 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white text-lg shadow-md shadow-indigo-500/20 flex-shrink-0">
          ET
        </div>
        {isOpen && (
          <div className="overflow-hidden">
            <h1 className="font-extrabold text-base tracking-tight text-white m-0 p-0 leading-tight">
              EDUTrace
            </h1>
            <p className="text-[10px] text-slate-400 font-medium tracking-wide">
              AICTE Student Governance
            </p>
          </div>
        )}
      </div>

      {/* Role Chip */}
      {isOpen && (
        <div className="px-4 py-2.5 mx-3 my-2 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs">
          <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
            Current Role
          </div>
          <div className="font-semibold text-emerald-400 truncate">
            {user?.role.replace(/_/g, ' ')}
          </div>
          {user?.institution_name && (
            <div className="text-[11px] text-slate-300 truncate mt-0.5">
              {user.institution_name}
            </div>
          )}
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-600 text-white shadow-sm shadow-indigo-600/30'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
                }`
              }
              title={!isOpen ? item.label : undefined}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {isOpen && <span className="flex-1 truncate">{item.label}</span>}
              {isOpen && item.badge && (
                <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/30">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer Info */}
      {isOpen && (
        <div className="p-4 border-t border-slate-800 text-xs text-slate-500">
          <div className="flex items-center gap-1.5 text-indigo-400 font-semibold mb-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>SIH 2026 Prototype</span>
          </div>
          <div>Problem Statement: SIH26263</div>
          <div className="text-[10px] text-slate-500 mt-1">AICTE National Prototype v1.0</div>
        </div>
      )}
    </aside>
  );
};
