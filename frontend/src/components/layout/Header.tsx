import React, { useState, useEffect } from 'react';
import {
  Menu,
  Radio,
  User as UserIcon,
  LogOut,
  ChevronDown,
  RefreshCw,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../lib/api';
import { AcademicYear, UserRole } from '../../types';

export const Header: React.FC<{ onToggleSidebar: () => void }> = ({ onToggleSidebar }) => {
  const { user, logout, switchDemoRole, selectedAcademicYearId, setSelectedAcademicYearId } = useAuth();
  const [academicYears, setAcademicYears] = useState<AcademicYear[]>([]);
  const [showRoleMenu, setShowRoleMenu] = useState(false);
  const [isSwitching, setIsSwitching] = useState(false);

  useEffect(() => {
    const fetchAYs = async () => {
      try {
        const years = await api.getAcademicYears();
        setAcademicYears(years);
        if (!selectedAcademicYearId && years.length > 0) {
          const current = years.find((y: AcademicYear) => y.is_current) || years[0];
          setSelectedAcademicYearId(current.id);
        }
      } catch (e) {
        console.error('Failed to load academic years:', e);
      }
    };
    fetchAYs();
  }, []);

  const handleRoleSwitch = async (role: UserRole, instId?: number) => {
    setIsSwitching(true);
    setShowRoleMenu(false);
    await switchDemoRole(role, instId);
    setIsSwitching(false);
  };

  const demoRoles: { label: string; role: UserRole; instId?: number; desc: string }[] = [
    { label: 'AICTE Administrator', role: 'AICTE_ADMIN', desc: 'System-wide monitoring, all institutions' },
    { label: 'COEP Institution Admin', role: 'INSTITUTION_ADMIN', instId: 1, desc: 'COEP Tech Univ institutional scope' },
    { label: 'COEP Data Operator', role: 'INSTITUTION_DATA_OPERATOR', instId: 1, desc: 'Upload wizard & staging corrections' },
    { label: 'Authorized Reviewer', role: 'AUTHORIZED_REVIEWER', desc: 'Evidence review & decision recording' },
    { label: 'External Verifier (TCS)', role: 'EXTERNAL_VERIFIER', desc: 'Purpose-bound credential verification' },
  ];

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-4 flex items-center justify-between shadow-xs sticky top-0 z-30 no-print">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-800 transition-colors"
          title="Toggle Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Live SSE Pulse Indicator */}
        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-xs font-semibold text-emerald-800">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <Radio className="w-3.5 h-3.5 text-emerald-600" />
          <span>Live Sync Active</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Academic Year Switcher */}
        <div className="flex items-center gap-1.5 text-xs">
          <span className="text-slate-500 hidden md:inline font-medium">Academic Year:</span>
          <select
            value={selectedAcademicYearId || ''}
            onChange={(e) => setSelectedAcademicYearId(Number(e.target.value))}
            className="px-2.5 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {academicYears.map((ay) => (
              <option key={ay.id} value={ay.id}>
                {ay.year_code} {ay.is_current ? '(Current)' : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Demo Role Switcher Menu */}
        <div className="relative">
          <button
            onClick={() => setShowRoleMenu(!showRoleMenu)}
            disabled={isSwitching}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-semibold hover:bg-indigo-100 transition-colors"
          >
            {isSwitching ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <UserIcon className="w-3.5 h-3.5 text-indigo-600" />
            )}
            <span className="hidden sm:inline">Demo Role Switcher</span>
            <ChevronDown className="w-3 h-3 text-indigo-500" />
          </button>

          {showRoleMenu && (
            <div className="absolute right-0 mt-2 w-72 rounded-xl bg-white border border-slate-200 shadow-xl py-2 z-50 text-xs">
              <div className="px-3 py-1.5 font-bold text-slate-400 uppercase tracking-wider text-[10px] border-b border-slate-100">
                Switch Demo Evaluation Persona
              </div>
              {demoRoles.map((dr) => (
                <button
                  key={dr.label}
                  onClick={() => handleRoleSwitch(dr.role, dr.instId)}
                  className={`w-full text-left px-3 py-2 hover:bg-slate-50 transition-colors flex flex-col ${
                    user?.role === dr.role && (dr.instId ? user?.institution_id === dr.instId : true)
                      ? 'bg-indigo-50/70 border-l-4 border-indigo-600'
                      : ''
                  }`}
                >
                  <span className="font-semibold text-slate-800">{dr.label}</span>
                  <span className="text-[10px] text-slate-500">{dr.desc}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Current User Info & Logout */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
          <div className="hidden lg:block text-right">
            <div className="text-xs font-bold text-slate-800 truncate max-w-[140px]">
              {user?.full_name}
            </div>
            <div className="text-[10px] text-slate-500 truncate max-w-[140px]">
              {user?.email}
            </div>
          </div>
          <button
            onClick={logout}
            className="p-2 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
            title="Log Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
