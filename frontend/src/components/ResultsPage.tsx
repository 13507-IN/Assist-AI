'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import axios from 'axios';
import useOutreachStore from '@/store/outreach';
import apiService from '@/services/api';
import Button from './Button';
import { useToast } from './ToastProvider';
import { Company, GmailStatus } from '@/types';


const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function errorMessage(error: unknown, fallback: string) {
  return axios.isAxiosError(error)
    ? error.response?.data?.detail || error.message
    : fallback;
}

interface CompanyCardProps {
  company: Company;
  onSelect: (company: Company) => void;
}

const CompanyCard: React.FC<CompanyCardProps> = ({ company, onSelect }) => (
  <div className="rounded-lg bg-white p-6 shadow-md transition-shadow hover:shadow-lg">
    <h3 className="mb-2 text-lg font-semibold text-slate-900">{company.name}</h3>
    {company.website && (
      <p className="mb-2 truncate text-sm text-blue-600">
        <a href={company.website} target="_blank" rel="noopener noreferrer">
          {company.website}
        </a>
      </p>
    )}
    <div className="mb-4 flex flex-wrap gap-2">
      <span className={`rounded px-2 py-1 text-xs ${
        company.hiring_signal === 'active'
          ? 'bg-green-100 text-green-800'
          : 'bg-yellow-100 text-yellow-800'
      }`}>
        {company.hiring_signal === 'active' ? 'Actively Hiring' : 'Strategic Target'}
      </span>
      <span className="rounded bg-blue-100 px-2 py-1 text-xs text-blue-800">
        Relevance: {(company.relevance_score * 100).toFixed(0)}%
      </span>
    </div>
    {company.summary && <p className="mb-4 line-clamp-3 text-sm text-slate-600">{company.summary}</p>}
    {company.research_error && (
      <p className="mb-4 rounded bg-amber-50 p-2 text-xs text-amber-800">
        Verification note: {company.research_error}
      </p>
    )}
    <Button variant="primary" size="sm" onClick={() => onSelect(company)} className="w-full">
      Create Email
    </Button>
  </div>
);

export const ResultsPage: React.FC = () => {
  const {
    activelyHiring,
    strategicTargets,
    setSelectedCompany,
    setGeneratedEmail,
  } = useOutreachStore();
  const [selectedCompany, setSelected] = useState<Company | null>(null);

  const selectCompany = (company: Company) => {
    setGeneratedEmail(null);
    setSelected(company);
    setSelectedCompany(company);
  };

  const totalCompanies = activelyHiring.length + strategicTargets.length;

  return (
    <div className="mx-auto w-full max-w-7xl">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="mb-2 text-4xl font-bold text-slate-900">Discovery Results</h1>
          <p className="text-slate-600">Found {totalCompanies} saved company matches</p>
        </div>
        <Link href="/" className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700">
          New search
        </Link>
      </div>

      {activelyHiring.length > 0 && (
        <section className="mb-12">
          <h2 className="mb-4 text-2xl font-bold text-green-700">🔥 Actively Hiring ({activelyHiring.length})</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {activelyHiring.map(company => (
              <CompanyCard key={company.id} company={company} onSelect={selectCompany} />
            ))}
          </div>
        </section>
      )}

      {strategicTargets.length > 0 && (
        <section className="mb-12">
          <h2 className="mb-4 text-2xl font-bold text-blue-700">🎯 Strategic Targets ({strategicTargets.length})</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {strategicTargets.map(company => (
              <CompanyCard key={company.id} company={company} onSelect={selectCompany} />
            ))}
          </div>
        </section>
      )}

      {totalCompanies === 0 && (
        <div className="rounded-lg bg-white p-10 text-center shadow">
          <p className="mb-4 text-lg text-slate-600">No saved results yet.</p>
          <Link href="/" className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white">
            Start a company search
          </Link>
        </div>
      )}

      {selectedCompany && (
        <EmailModal company={selectedCompany} onClose={() => setSelected(null)} />
      )}
    </div>
  );
};

function EmailModal({ company, onClose }: { company: Company; onClose: () => void }) {
  const {
    generatedEmail,
    setGeneratedEmail,
    isLoading,
    setIsLoading,
    userProfile,
    userId,
  } = useOutreachStore();
  const notify = useToast();
  const [recipient, setRecipient] = useState('');
  const [subject, setSubject] = useState(generatedEmail?.subject || '');
  const [body, setBody] = useState(generatedEmail?.body || '');
  const [isGenerating, setIsGenerating] = useState(false);
  const [message, setMessage] = useState('');
  const [previousContact, setPreviousContact] = useState<{
    contacted: boolean;
    last_sent_at?: string;
    recipient_email?: string;
  } | null>(null);
  const [gmail, setGmail] = useState<GmailStatus | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([
      apiService.getCompanyEmailStatus(company.id, userId),
      apiService.getGmailStatus(userId),
    ]).then(([contact, gmailStatus]) => {
      if (!active) return;
      setPreviousContact(contact);
      setGmail(gmailStatus);
      if (contact.recipient_email) setRecipient(contact.recipient_email);
    }).catch(error => {
      if (active) setMessage(errorMessage(error, 'Could not load email history or Gmail status.'));
    });
    return () => { active = false; };
  }, [company.id, userId]);

  const validRecipient = EMAIL_PATTERN.test(recipient);

  const generate = async () => {
    if (!userProfile) {
      setMessage('Your search profile is missing. Start a new company search first.');
      return;
    }
    setMessage('');
    setIsGenerating(true);
    try {
      const email = await apiService.generateEmail(
        userId,
        company.id,
        company.name,
        company.summary || 'No verified summary available',
        userProfile.role,
        userProfile.skills
      );
      setGeneratedEmail(email);
      setSubject(email.subject);
      setBody(email.body);
      notify('Email draft generated', 'success');
    } catch (error) {
      setMessage(errorMessage(error, 'Email generation failed.'));
      notify('Email generation failed', 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  const validateDraft = () => {
    if (!validRecipient) {
      setMessage('Enter a valid recipient email address.');
      return false;
    }
    if (!subject.trim() || !body.trim()) {
      setMessage('Subject and body cannot be empty.');
      return false;
    }
    setMessage('');
    return true;
  };

  const saveDraft = async () => {
    if (!validateDraft()) return;
    setIsLoading(true);
    try {
      await apiService.saveDraft(userId, recipient, company.id, company.name, subject, body);
      notify('Draft saved to the activity log', 'success');
    } catch (error) {
      setMessage(errorMessage(error, 'Could not save the draft.'));
    } finally {
      setIsLoading(false);
    }
  };

  const copyEmail = async () => {
    await navigator.clipboard.writeText(`To: ${recipient}\nSubject: ${subject}\n\n${body}`);
    notify('Email copied to clipboard', 'success');
  };

  const openInGmail = () => {
    const params = new URLSearchParams({
      view: 'cm',
      fs: '1',
      to: recipient,
      su: subject,
      body,
    });
    window.open(`https://mail.google.com/mail/?${params.toString()}`, '_blank', 'noopener,noreferrer');
  };

  const sendEmail = async () => {
    if (!validateDraft()) return;
    if (!gmail?.connected) {
      setMessage('Gmail is not connected. Connect it or use Open in Gmail.');
      return;
    }
    setIsLoading(true);
    try {
      const result = await apiService.sendEmail(
        userId,
        recipient,
        company.id,
        company.name,
        subject,
        body
      );
      if (!result.success) {
        setMessage(`${result.error || 'Gmail send failed'}. You can still open the draft in Gmail.`);
        notify('Send failed and was logged', 'error');
        return;
      }
      notify('Email sent and logged', 'success');
      onClose();
    } catch (error) {
      setMessage(errorMessage(error, 'Email send failed.'));
      notify('Send failed', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-lg bg-white shadow-xl">
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 bg-slate-100 px-6 py-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Email for {company.name}</h2>
            <p className="text-xs text-slate-500">Edit everything before saving or sending.</p>
          </div>
          <button onClick={onClose} aria-label="Close editor" className="text-2xl text-slate-500 hover:text-slate-800">✕</button>
        </div>

        <div className="space-y-5 p-6">
          {previousContact?.contacted && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
              You already emailed this company
              {previousContact.last_sent_at ? ` on ${new Date(previousContact.last_sent_at).toLocaleString()}` : ''}.
            </div>
          )}
          {message && (
            <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
              {message}
            </div>
          )}
          {!gmail?.connected && (
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">
              <span>{gmail?.detail || 'Checking Gmail connection…'}</span>
              {gmail?.configured && (
                <a href={apiService.gmailConnectUrl(userId)} className="rounded bg-blue-700 px-3 py-1.5 font-semibold text-white">
                  Connect Gmail
                </a>
              )}
            </div>
          )}

          {!subject && !body ? (
            <div className="py-8 text-center">
              <p className="mb-5 text-slate-600">Generate a personalized starting point, then review it.</p>
              <Button variant="primary" size="lg" onClick={generate} disabled={isGenerating}>
                {isGenerating ? 'Generating…' : 'Generate Email'}
              </Button>
            </div>
          ) : (
            <>
              <label className="block text-sm font-medium text-slate-700">
                Recipient
                <input
                  type="email"
                  value={recipient}
                  onChange={event => setRecipient(event.target.value)}
                  placeholder="hiring@company.com"
                  className={`mt-2 w-full rounded-lg border px-3 py-2 outline-none focus:ring-2 ${
                    recipient && !validRecipient ? 'border-red-400 focus:ring-red-200' : 'border-slate-300 focus:ring-blue-200'
                  }`}
                />
              </label>
              <label className="block text-sm font-medium text-slate-700">
                Subject
                <input
                  value={subject}
                  onChange={event => setSubject(event.target.value)}
                  className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-blue-200"
                />
              </label>
              <label className="block text-sm font-medium text-slate-700">
                Email body
                <textarea
                  value={body}
                  onChange={event => setBody(event.target.value)}
                  rows={11}
                  className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-blue-200"
                />
              </label>

              <div className="flex flex-wrap gap-3 border-t border-slate-200 pt-5">
                <Button variant="outline" onClick={generate} disabled={isGenerating}>Regenerate</Button>
                <Button variant="outline" onClick={copyEmail}>Copy</Button>
                <Button variant="outline" onClick={saveDraft} disabled={isLoading}>Save draft</Button>
                <Button variant="outline" onClick={openInGmail}>Open in Gmail</Button>
                <Button variant="primary" onClick={sendEmail} disabled={isLoading || !gmail?.connected}>
                  {isLoading ? 'Working…' : 'Send'}
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default ResultsPage;
