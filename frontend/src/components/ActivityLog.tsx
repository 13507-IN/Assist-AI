'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import axios from 'axios';
import useOutreachStore from '@/store/outreach';
import apiService from '@/services/api';
import { ActivityResponse, EmailLog } from '@/types';


type Filter = 'all' | 'drafted' | 'sent' | 'failed';

export const ActivityLog: React.FC = () => {
  const userId = useOutreachStore(state => state.userId);
  const [activity, setActivity] = useState<ActivityResponse | null>(null);
  const [filter, setFilter] = useState<Filter>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    apiService.getActivity(userId)
      .then(setActivity)
      .catch(requestError => {
        setError(
          axios.isAxiosError(requestError)
            ? requestError.response?.data?.detail || requestError.message
            : 'Could not load activity.'
        );
      })
      .finally(() => setIsLoading(false));
  }, [userId]);

  const filtered = useMemo(
    () => (activity?.emails || []).filter(email => filter === 'all' || email.status === filter),
    [activity, filter]
  );

  const statusColor = (status: string) => {
    if (status === 'sent') return 'bg-green-100 text-green-800';
    if (status === 'failed') return 'bg-red-100 text-red-800';
    return 'bg-yellow-100 text-yellow-800';
  };

  return (
    <div className="mx-auto w-full max-w-5xl">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="mb-2 text-4xl font-bold text-slate-900">Activity Log</h1>
          <p className="text-slate-600">Drafts and every Gmail send attempt are recorded here.</p>
        </div>
        <Link href="/" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white">
          Start new campaign
        </Link>
      </div>

      {activity && (
        <div className="mb-6 grid grid-cols-3 gap-3">
          <Metric label="Sent" value={activity.total_emails_sent} color="text-green-700" />
          <Metric label="Drafts" value={activity.total_drafts} color="text-amber-700" />
          <Metric label="Failed" value={activity.total_failed} color="text-red-700" />
        </div>
      )}

      <div className="mb-6 flex flex-wrap gap-2">
        {(['all', 'drafted', 'sent', 'failed'] as Filter[]).map(value => (
          <button
            key={value}
            onClick={() => setFilter(value)}
            className={`rounded-full px-4 py-2 text-sm font-semibold ${
              filter === value ? 'bg-slate-900 text-white' : 'bg-white text-slate-600 shadow-sm'
            }`}
          >
            {value === 'all' ? 'All' : value.charAt(0).toUpperCase() + value.slice(1)}
          </button>
        ))}
      </div>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">{error}</div>}
      {isLoading ? (
        <p className="py-12 text-center text-slate-600">Loading activity…</p>
      ) : filtered.length === 0 ? (
        <div className="rounded-lg bg-white p-8 text-center shadow">
          <p className="text-slate-600">No {filter === 'all' ? '' : filter} activity yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map(log => (
            <ActivityCard key={log.id} log={log} statusColor={statusColor(log.status)} />
          ))}
        </div>
      )}
    </div>
  );
};

function Metric({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="rounded-lg bg-white p-4 text-center shadow-sm">
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
    </div>
  );
}

function ActivityCard({
  log,
  statusColor,
}: {
  log: EmailLog;
  statusColor: string;
}) {
  return (
    <article className="rounded-lg bg-white p-6 shadow-md">
      <div className="flex flex-wrap justify-between gap-4">
        <div>
          <h3 className="font-semibold text-slate-900">{log.company_name}</h3>
          <p className="text-sm text-slate-600">{log.subject}</p>
          <p className="mt-2 text-xs text-slate-500">To: {log.recipient_email}</p>
          <p className="text-xs text-slate-500">{new Date(log.created_at).toLocaleString()}</p>
        </div>
        <span className={`h-fit rounded px-3 py-1 text-xs font-medium ${statusColor}`}>
          {log.status.charAt(0).toUpperCase() + log.status.slice(1)}
        </span>
      </div>
      {log.error_message && (
        <p className="mt-4 rounded bg-red-50 p-3 text-sm text-red-800">Reason: {log.error_message}</p>
      )}
    </article>
  );
}

export default ActivityLog;
