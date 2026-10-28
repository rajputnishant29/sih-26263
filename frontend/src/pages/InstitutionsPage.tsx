import React, { useState, useEffect } from 'react';
import { Building2, Search, MapPin, Mail, Award, AlertCircle, FileText, ChevronRight } from 'lucide-react';
import { api } from '../lib/api';
import { Institution } from '../types';

export const InstitutionsPage: React.FC = () => {
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedInst, setSelectedInst] = useState<Institution | null>(null);

  const fetchInstitutions = async () => {
    try {
      setIsLoading(true);
      const data = await api.getInstitutions(search);
      setInstitutions(data);
      if (data.length > 0 && !selectedInst) {
        setSelectedInst(data[0]);
      }
    } catch (e) {
      console.error('Failed to load institutions:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchInstitutions();
  }, [search]);

  return (
    <div className="space-y-6">
      {/* Header & Search */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            AICTE-Approved Institutions
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Institutional profiles, technical programmes, and approved intake capacity.
          </p>
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search by name, code, or state..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Institutions List */}
        <div className="space-y-3 lg:col-span-1">
          {isLoading ? (
            <div className="p-8 text-center text-xs text-slate-400">Loading institutions...</div>
          ) : institutions.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-400">No institutions found matching search.</div>
          ) : (
            institutions.map((inst) => {
              const isSelected = selectedInst?.id === inst.id;
              return (
                <div
                  key={inst.id}
                  onClick={() => setSelectedInst(inst)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'border-indigo-600 bg-indigo-50/50 shadow-xs'
                      : 'border-slate-200 bg-white hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-700">
                        PID: {inst.code}
                      </span>
                      <h3 className="font-bold text-sm text-slate-900 mt-1 leading-snug">
                        {inst.name}
                      </h3>
                    </div>
                    <ChevronRight className={`w-4 h-4 text-slate-400 ${isSelected ? 'text-indigo-600' : ''}`} />
                  </div>

                  <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-2">
                    <MapPin className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                    <span className="truncate">{inst.district ? `${inst.district}, ` : ''}{inst.state}</span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-slate-100 text-[11px] text-center">
                    <div>
                      <span className="text-slate-400 block text-[10px]">Programmes</span>
                      <span className="font-bold text-slate-800">{inst.programmes_count}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Intake Limit</span>
                      <span className="font-bold text-indigo-700">{inst.total_approved_intake}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Enrolled</span>
                      <span className="font-bold text-emerald-700">{inst.total_actual_enrolment}</span>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Selected Institution Detail Profile */}
        <div className="lg:col-span-2">
          {selectedInst ? (
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs space-y-6">
              <div className="flex items-start justify-between border-b border-slate-100 pb-5">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-indigo-100 text-indigo-800">
                      Permanent Institute ID: {selectedInst.code}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-semibold border border-emerald-200">
                      {selectedInst.institution_type}
                    </span>
                  </div>
                  <h2 className="text-xl font-black text-slate-900 mt-2 tracking-tight">
                    {selectedInst.name}
                  </h2>
                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 mt-2">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5" />
                      {selectedInst.address || `${selectedInst.district}, ${selectedInst.state}`}
                    </span>
                    {selectedInst.contact_email && (
                      <span className="flex items-center gap-1">
                        <Mail className="w-3.5 h-3.5" />
                        {selectedInst.contact_email}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Statistics Row */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Total Approved Intake</span>
                  <div className="text-xl font-extrabold text-indigo-900 mt-0.5">
                    {selectedInst.total_approved_intake}
                  </div>
                </div>
                <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Actual Enrolment</span>
                  <div className="text-xl font-extrabold text-emerald-700 mt-0.5">
                    {selectedInst.total_actual_enrolment}
                  </div>
                </div>
                <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Capacity Utilization</span>
                  <div className="text-xl font-extrabold text-slate-800 mt-0.5">
                    {selectedInst.total_approved_intake > 0
                      ? `${Math.round((selectedInst.total_actual_enrolment / selectedInst.total_approved_intake) * 100)}%`
                      : '0%'}
                  </div>
                </div>
                <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Open Exceptions</span>
                  <div className={`text-xl font-extrabold mt-0.5 ${selectedInst.open_issues_count > 0 ? 'text-rose-600' : 'text-slate-700'}`}>
                    {selectedInst.open_issues_count}
                  </div>
                </div>
              </div>

              {/* Programmes Table */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                  Technical Programmes ({selectedInst.programmes.length})
                </h3>
                <div className="rounded-lg border border-slate-200 overflow-hidden">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-200">
                      <tr>
                        <th className="py-2.5 px-3 font-bold">Code</th>
                        <th className="py-2.5 px-3 font-bold">Programme Name</th>
                        <th className="py-2.5 px-3 font-bold">Degree Level</th>
                        <th className="py-2.5 px-3 font-bold">Department</th>
                        <th className="py-2.5 px-3 font-bold">Duration</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {selectedInst.programmes.map((p) => (
                        <tr key={p.id} className="hover:bg-slate-50">
                          <td className="py-2.5 px-3 font-mono font-bold text-indigo-700">{p.programme_code}</td>
                          <td className="py-2.5 px-3 font-medium text-slate-900">{p.programme_name}</td>
                          <td className="py-2.5 px-3 text-slate-600">{p.degree_level}</td>
                          <td className="py-2.5 px-3 text-slate-600">{p.department}</td>
                          <td className="py-2.5 px-3 text-slate-600">{p.duration_years} Years</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Official AICTE Extension of Approval Source Trace */}
              <div className="p-4 rounded-lg bg-indigo-50/60 border border-indigo-200/80 text-xs text-indigo-950">
                <div className="flex items-center gap-2 font-bold mb-1">
                  <FileText className="w-4 h-4 text-indigo-700" />
                  <span>Official Approval Provenance Track</span>
                </div>
                <p className="text-[11px] leading-relaxed text-indigo-900/80">
                  Intake sanctioned under AICTE Extension of Approval (EoA) Letter for Academic Year 2026-27.
                  Approval records are tied to permanent institute ID <code className="font-mono bg-white px-1 py-0.5 rounded border border-indigo-200">{selectedInst.code}</code> and versioned handbook rules.
                </p>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-slate-200 bg-white p-12 text-center text-xs text-slate-400">
              Select an institution on the left to inspect its complete profile.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
