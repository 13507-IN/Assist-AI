'use client';

import { useCallback, useEffect, useState } from 'react';
import apiService from '@/services/api';
import useOutreachStore from '@/store/outreach';
import { HealthResponse } from '@/types';
import { useToast } from './ToastProvider';

export default function StatusBanner() {
  const userId = useOutreachStore(state => state.userId);
  const notify = useToast();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [backendError, setBackendError] = useState('');

  const refresh = useCallback(async () => {
    try {
      setHealth(await apiService.getHealth());
      setBackendError('');
    } catch {
      setBackendError('Backend is not reachable at http://localhost:8000');
      setHealth(null);
    }
  }, []);

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 30000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const gmail = params.get('gmail');
    if (gmail === 'connected') {
      notify(`Gmail connected${params.get('email') ? ` as ${params.get('email')}` : ''}`, 'success');
      refresh();
    } else if (gmail === 'error') {
      notify(params.get('message') || 'Gmail sign-in failed', 'error');
    }
    if (gmail) {
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, [notify, refresh]);

  const issues = backendError
    ? [{ name: 'Backend', detail: backendError }]
    : Object.entries(health?.services || {})
        .filter(([, service]) => service.status !== 'ok')
        .map(([name, service]) => ({ name, detail: service.detail }));

  if (issues.length === 0) return null;
  const gmail = health?.services.gmail;

  return (
    <div className="border-b border-amber-300 bg-amber-50 text-amber-950">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3 text-sm">
        <div>
          <span className="font-semibold">Connection notice:</span>{' '}
          {issues.map(issue => `${issue.name}: ${issue.detail}`).join(' • ')}
        </div>
        {gmail?.configured && !gmail.connected && (
          <a
            href={apiService.gmailConnectUrl(userId)}
            className="rounded-md bg-amber-900 px-3 py-1.5 font-semibold text-white hover:bg-amber-800"
          >
            Connect Gmail
          </a>
        )}
      </div>
    </div>
  );
}
