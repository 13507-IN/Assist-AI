'use client';

import React, { useEffect, useState } from 'react';
import useOutreachStore from '@/store/outreach';
import apiService from '@/services/api';
import Button from './Button';
import { EmailLog } from '@/types';

export const ActivityLog: React.FC = () => {
  const [activity, setActivity] = useState<EmailLog[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [totalSent, setTotalSent] = useState(0);

  useEffect(() => {
    const loadActivity = async () => {
      setIsLoading(true);
      try {
        const result = await apiService.getActivity('user-id'); // TODO: Get from auth
        setActivity(result.emails);
        setTotalSent(result.total_emails_sent);
      } catch (error) {
        console.error('Error loading activity:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadActivity();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'sent':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-slate-900 mb-2">Activity Log</h1>
        <p className="text-slate-600">Total emails sent: {totalSent}</p>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <p className="text-slate-600">Loading activity...</p>
        </div>
      ) : activity.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-slate-600 mb-4">No emails sent yet</p>
          <Button
            variant="primary"
            onClick={() => window.location.href = '/'}
          >
            Start New Campaign
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          {activity.map(log => (
            <div
              key={log.id}
              className="bg-white rounded-lg shadow-md p-6 flex justify-between items-start"
            >
              <div>
                <h3 className="font-semibold text-slate-900">{log.company_name}</h3>
                <p className="text-sm text-slate-600">{log.subject}</p>
                <p className="text-xs text-slate-500 mt-2">
                  To: {log.recipient_email}
                </p>
                <p className="text-xs text-slate-500">
                  {new Date(log.created_at).toLocaleDateString()}
                </p>
              </div>
              <span className={`text-xs px-3 py-1 rounded font-medium ${getStatusColor(log.status)}`}>
                {log.status.charAt(0).toUpperCase() + log.status.slice(1)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ActivityLog;
