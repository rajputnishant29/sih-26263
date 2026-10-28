import React, { useState, useEffect } from 'react';
import { History, Shield, Filter, RefreshCw, Eye, X } from 'lucide-react';
import { api } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { AuditEventItem } from '../types';

export const AuditTrailPage: React.FC = () => {
  const { user } = useAuth();
  const [events, setEvents] = useState<AuditEventItem[]>([]);
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [resourceTypeFilter, setResourceTypeFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState<AuditEventItem | null>(null);

  const fetchAuditLogs = async () => {
    try {
      setIsLoading(true);
      const data = await api.getAuditLogs({
        event_type: eventTypeFilter || undefined,
        resource_type: resourceTypeFilter || undefined,
        institution_id: user?.institution_id || undefined,
      });
      setEvents(data);
    } catch (e) {
      console.error('Failed to load audit logs:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs();
  }, [eventTypeFilter, resourceTypeFilter, user?.role]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight">
          Append-Only Regulatory Audit Trail
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Immutable event ledger tracking uploads, validation runs, reviewer decisions, record corrections, and verifications.
        </p>
      </div>

      <div className="p-4 rounded-xl bg-slate-900 text-slate-300 text-xs flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-emerald-400" />
          <span>
            <strong>Tamper-Evident Security:</strong> Audit records are append-only. Passwords, secrets, and raw APAAR references are strictly redacted prior to persistence.
          </span>
        </div>
        <span className="font-mono text-[10px] text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
          {events.length} Recorded Events
        </span>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-xs flex flex-wrap items-center gap-3">
        <div className="w-52">
          <select
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            className="w-full py-2 px-2.5 rounded-lg border border-slate-300 text-xs font-medium text-slate-700 bg-white"
          >
            <option value="">All Event Types</option>
            <option value="AUTH_LOGIN">AUTH_LOGIN</option>
            <option value="FILE_UPLOAD_STAGED">FILE_UPLOAD_STAGED</option>
            <option value="FILE_VALIDATION_RUN">FILE_VALIDATION_RUN</option>
            <option value="RECORDS_COMMITTED">RECORDS_COMMITTED</option>
            <option value="ENROLMENT_CORRECTED">ENROLMENT_CORRECTED</option>
            <option value="ISSUE_STATUS_CHANGED">ISSUE_STATUS_CHANGED</option>
            <option value="VERIFICATION_REQUESTED">VERIFICATION_REQUESTED</option>
            <option value="CERTIFICATE_GENERATED">CERTIFICATE_GENERATED</option>
            <option value="EOA_DOCUMENT_CONFIRMED">EOA_DOCUMENT_CONFIRMED</option>
          </select>
        </div>

        <div className="w-44">
          <select
            value={resourceTypeFilter}
            onChange={(e) => setResourceTypeFilter(e.target.value)}
            className="w-full py-2 px-2.5 rounded-lg border border-slate-300 text-xs font-medium text-slate-700 bg-white"
          >
            <option value="">All Resource Types</option>
            <option value="UPLOAD_BATCH">UPLOAD_BATCH</option>
            <option value="VALIDATION_ISSUE">VALIDATION_ISSUE</option>
            <option value="STUDENT_ENROLMENT">STUDENT_ENROLMENT</option>
            <option value="VERIFICATION_REQUEST">VERIFICATION_REQUEST</option>
            <option value="CERTIFICATE_CREDENTIAL">CERTIFICATE_CREDENTIAL</option>
            <option value="SOURCE_DOCUMENT">SOURCE_DOCUMENT</option>
          </select>
        </div>

        <button
          onClick={fetchAuditLogs}
          className="ml-auto p-2 rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50"
          title="Refresh Log"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Audit Events Table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500 border-b border-slate-200">
              <tr>
                <th className="py-3 px-4 font-bold">Event Type</th>
                <th className="py-3 px-4 font-bold">Actor & Role</th>
                <th className="py-3 px-4 font-bold">Resource</th>
                <th className="py-3 px-4 font-bold">Outcome</th>
                <th className="py-3 px-4 font-bold">Timestamp (UTC)</th>
                <th className="py-3 px-4 font-bold text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">Loading audit trail...</td>
                </tr>
              ) : events.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">No audit events match filters.</td>
                </tr>
              ) : (
                events.map((ev) => (
                  <tr key={ev.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-indigo-700">
                      {ev.event_type}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900">{ev.actor_email || 'System'}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{ev.actor_role}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-slate-800">{ev.resource_type}</div>
                      {ev.resource_id && (
                        <div className="text-[10px] text-slate-400 font-mono">ID: {ev.resource_id}</div>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        ev.action_outcome === 'SUCCESS'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-rose-50 text-rose-700 border border-rose-200'
                      }`}>
                        {ev.action_outcome}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-500">
                      {ev.timestamp.slice(0, 19).replace('T', ' ')}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => setSelectedEvent(ev)}
                        className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:text-indigo-600 hover:bg-indigo-50 transition-colors inline-flex items-center gap-1 text-[11px] font-semibold"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Details Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 space-y-4 text-xs">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <span className="font-bold text-[10px] text-indigo-600 font-mono uppercase">
                  Audit Event #{selectedEvent.id}
                </span>
                <h3 className="font-extrabold text-sm text-slate-900">
                  {selectedEvent.event_type}
                </h3>
              </div>
              <button
                onClick={() => setSelectedEvent(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
              <div className="flex justify-between"><span className="text-slate-500">Actor Email:</span> <strong className="text-slate-900">{selectedEvent.actor_email}</strong></div>
              <div className="flex justify-between"><span className="text-slate-500">Actor Role:</span> <span className="font-mono">{selectedEvent.actor_role}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Client IP Address:</span> <span className="font-mono">{selectedEvent.ip_address}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Timestamp:</span> <span className="font-mono">{selectedEvent.timestamp}</span></div>
            </div>

            <div>
              <span className="font-bold text-[10px] uppercase tracking-wider text-slate-500 block mb-1">
                Sanitized Payload
              </span>
              <pre className="p-3.5 rounded-xl bg-slate-900 text-emerald-400 font-mono text-[11px] overflow-x-auto max-h-48 leading-relaxed">
                {JSON.stringify(selectedEvent.event_details, null, 2)}
              </pre>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setSelectedEvent(null)}
                className="px-4 py-2 rounded-lg bg-slate-100 text-slate-700 font-bold text-xs hover:bg-slate-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
