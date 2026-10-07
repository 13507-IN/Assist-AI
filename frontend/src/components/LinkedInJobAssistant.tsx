'use client';

import { FormEvent, useEffect, useState } from 'react';
import apiService from '@/services/api';
import { LinkedInApplication, LinkedInJobInput, LinkedInProfile } from '@/types';

const emptyProfile: LinkedInProfile = {
  full_name: '', email: '', phone: '', location: '', headline: '', years_experience: 0,
  skills: [], linkedin_url: '', resume_url: '',
  common_answers: { work_authorization: '', salary_expectation: '', notice_period: '' }
};

const emptyJob: LinkedInJobInput = {
  title: '', company: '', linkedin_url: '', location: '', work_mode: 'Remote', description: ''
};

const messageFrom = (error: unknown, fallback: string) => {
  const response = error as { response?: { data?: { detail?: string } }; message?: string };
  return response.response?.data?.detail || response.message || fallback;
};

export default function LinkedInJobAssistant() {
  const [profile, setProfile] = useState<LinkedInProfile>(emptyProfile);
  const [job, setJob] = useState<LinkedInJobInput>(emptyJob);
  const [applications, setApplications] = useState<LinkedInApplication[]>([]);
  const [selected, setSelected] = useState<LinkedInApplication | null>(null);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const refresh = async () => {
    const entries = await apiService.getLinkedInApplications();
    setApplications(entries);
    setSelected((current) => entries.find((entry) => entry.id === current?.id) || entries[0] || null);
  };

  useEffect(() => {
    Promise.all([apiService.getLinkedInProfile(), refresh()])
      .then(([saved]) => saved && setProfile(saved))
      .catch((loadError) => setError(messageFrom(loadError, 'Could not load the LinkedIn workspace.')));
  }, []);

  const saveProfile = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true); setError(''); setNotice('');
    try {
      const saved = await apiService.saveLinkedInProfile(profile);
      setProfile(saved);
      setNotice('Your private application profile was saved.');
    } catch (saveError) {
      setError(messageFrom(saveError, 'Could not save your profile.'));
    } finally { setBusy(false); }
  };

  const addJob = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true); setError(''); setNotice('');
    try {
      const application = await apiService.addLinkedInApplication(job);
      setApplications((current) => [application, ...current]);
      setSelected(application);
      setJob(emptyJob);
      setNotice('Job added to the private review queue.');
    } catch (addError) {
      setError(messageFrom(addError, 'Could not add this job.'));
    } finally { setBusy(false); }
  };

  const prepare = async (application: LinkedInApplication) => {
    setBusy(true); setError(''); setNotice('');
    try {
      const prepared = await apiService.prepareLinkedInApplication(application.id);
      setApplications((current) => current.map((entry) => entry.id === prepared.id ? prepared : entry));
      setSelected(prepared);
      setNotice('Tailored draft is ready for your review.');
    } catch (prepareError) {
      setError(messageFrom(prepareError, 'Could not prepare this application.'));
    } finally { setBusy(false); }
  };

  const markApplied = async () => {
    if (!selected) return;
    setBusy(true); setError('');
    try {
      const updated = await apiService.updateLinkedInApplication(selected.id, { status: 'applied' });
      setApplications((current) => current.map((entry) => entry.id === updated.id ? updated : entry));
      setSelected(updated);
      setNotice('Marked as applied after your LinkedIn submission.');
    } catch (updateError) {
      setError(messageFrom(updateError, 'Could not update this application.'));
    } finally { setBusy(false); }
  };

  const saved = applications.filter((entry) => entry.status === 'saved').length;
  const ready = applications.filter((entry) => entry.status === 'ready_for_review').length;
  const applied = applications.filter((entry) => entry.status === 'applied').length;

  return (
    <div className="space-y-8">
      <section className="rounded-3xl bg-gradient-to-br from-blue-700 via-indigo-700 to-slate-900 px-8 py-10 text-white shadow-xl">
        <p className="text-sm font-semibold uppercase tracking-[.18em] text-blue-200">New workspace · LinkedIn applications</p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight">Prepare better LinkedIn applications.</h1>
        <p className="mt-3 max-w-3xl text-blue-100">This complements your current company discovery and cold-email workflow. It saves jobs you choose, creates drafts from your profile, and always leaves the final submission to you on LinkedIn.</p>
        <div className="mt-6 flex flex-wrap gap-3 text-sm">
          <Metric label="Saved" value={saved} /><Metric label="Ready to review" value={ready} /><Metric label="Applied" value={applied} />
        </div>
      </section>

      {(error || notice) && <div className={`rounded-xl border px-4 py-3 text-sm ${error ? 'border-red-200 bg-red-50 text-red-700' : 'border-emerald-200 bg-emerald-50 text-emerald-700'}`}>{error || notice}</div>}

      <div className="grid gap-8 xl:grid-cols-2">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-bold text-slate-900">Your application profile</h2>
          <p className="mt-1 text-sm text-slate-500">Stored in your own database and used to tailor drafts.</p>
          <form onSubmit={saveProfile} className="mt-5 space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Full name" value={profile.full_name} required onChange={(value) => setProfile({ ...profile, full_name: value })} />
              <Field label="Email" type="email" value={profile.email} required onChange={(value) => setProfile({ ...profile, email: value })} />
              <Field label="Phone" value={profile.phone || ''} onChange={(value) => setProfile({ ...profile, phone: value })} />
              <Field label="Location" value={profile.location} required onChange={(value) => setProfile({ ...profile, location: value })} />
            </div>
            <Field label="Professional headline" value={profile.headline || ''} placeholder="e.g. Frontend engineer, React and TypeScript" onChange={(value) => setProfile({ ...profile, headline: value })} />
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Years of experience" type="number" value={String(profile.years_experience)} onChange={(value) => setProfile({ ...profile, years_experience: Number(value) || 0 })} />
              <Field label="Resume link" value={profile.resume_url || ''} onChange={(value) => setProfile({ ...profile, resume_url: value })} />
            </div>
            <Field label="Skills" value={profile.skills.join(', ')} placeholder="React, Python, SQL, Node.js" onChange={(value) => setProfile({ ...profile, skills: value.split(',').map((skill) => skill.trim()).filter(Boolean) })} />
            <div className="grid gap-4 sm:grid-cols-3">
              <Field label="Work authorization" value={profile.common_answers.work_authorization || ''} onChange={(value) => setProfile({ ...profile, common_answers: { ...profile.common_answers, work_authorization: value } })} />
              <Field label="Salary expectation" value={profile.common_answers.salary_expectation || ''} onChange={(value) => setProfile({ ...profile, common_answers: { ...profile.common_answers, salary_expectation: value } })} />
              <Field label="Notice period" value={profile.common_answers.notice_period || ''} onChange={(value) => setProfile({ ...profile, common_answers: { ...profile.common_answers, notice_period: value } })} />
            </div>
            <button disabled={busy} className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-slate-700 disabled:opacity-60">Save profile</button>
          </form>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-bold text-slate-900">Add a job you found</h2>
          <p className="mt-1 text-sm text-slate-500">Paste the URL and full description from a LinkedIn role.</p>
          <form onSubmit={addJob} className="mt-5 space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Job title" value={job.title} required onChange={(value) => setJob({ ...job, title: value })} />
              <Field label="Company" value={job.company} required onChange={(value) => setJob({ ...job, company: value })} />
            </div>
            <Field label="LinkedIn job URL" type="url" required value={job.linkedin_url} placeholder="https://www.linkedin.com/jobs/view/…" onChange={(value) => setJob({ ...job, linkedin_url: value })} />
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Location" value={job.location || ''} onChange={(value) => setJob({ ...job, location: value })} />
              <Field label="Work mode" value={job.work_mode || ''} onChange={(value) => setJob({ ...job, work_mode: value })} />
            </div>
            <label className="block text-sm font-medium text-slate-700">Job description<textarea required rows={8} value={job.description} onChange={(event) => setJob({ ...job, description: event.target.value })} className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" placeholder="Paste the role description." /></label>
            <button disabled={busy} className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60">Add to review queue</button>
          </form>
        </section>
      </div>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-5 flex items-end justify-between gap-4"><div><h2 className="text-xl font-bold text-slate-900">LinkedIn application queue</h2><p className="mt-1 text-sm text-slate-500">Review the prepared material, then submit yourself on LinkedIn.</p></div><button onClick={() => refresh().catch((refreshError) => setError(messageFrom(refreshError, 'Could not refresh the queue.')))} className="text-sm font-semibold text-blue-700">Refresh</button></div>
        {!applications.length ? <p className="rounded-xl border border-dashed border-slate-300 px-6 py-12 text-center text-sm text-slate-500">No LinkedIn jobs have been added yet.</p> : <div className="grid gap-5 lg:grid-cols-[.8fr_1.2fr]">
          <div className="space-y-3">{applications.map((application) => <button key={application.id} onClick={() => setSelected(application)} className={`w-full rounded-xl border p-4 text-left ${selected?.id === application.id ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:bg-slate-50'}`}><div className="flex justify-between gap-3"><div><p className="font-semibold text-slate-900">{application.title}</p><p className="mt-1 text-sm text-slate-500">{application.company}</p></div><Badge status={application.status} /></div>{application.match_score !== null && application.match_score !== undefined && <p className="mt-3 text-xs font-semibold text-emerald-700">Match score: {application.match_score}%</p>}</button>)}</div>
          {selected && <Review application={selected} busy={busy} onPrepare={prepare} onApplied={markApplied} />}
        </div>}
      </section>
    </div>
  );
}

function Field({ label, value, onChange, type = 'text', placeholder, required = false }: { label: string; value: string; onChange: (value: string) => void; type?: string; placeholder?: string; required?: boolean }) {
  return <label className="block text-sm font-medium text-slate-700">{label}<input type={type} required={required} value={value} placeholder={placeholder} onChange={(event) => onChange(event.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" /></label>;
}

function Metric({ label, value }: { label: string; value: number }) {
  return <div className="rounded-lg border border-white/20 bg-white/10 px-4 py-2"><strong>{value}</strong><span className="ml-2 text-blue-100">{label}</span></div>;
}

function Badge({ status }: { status: string }) {
  const color = status === 'applied' ? 'bg-emerald-100 text-emerald-800' : status === 'ready_for_review' ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-700';
  return <span className={`whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold ${color}`}>{status.replace(/_/g, ' ')}</span>;
}

function Review({ application, busy, onPrepare, onApplied }: { application: LinkedInApplication; busy: boolean; onPrepare: (application: LinkedInApplication) => void; onApplied: () => void }) {
  const ready = application.status === 'ready_for_review' || application.status === 'applied';
  const copy = (text: string) => navigator.clipboard.writeText(text);
  if (!ready) return <div className="rounded-xl bg-slate-50 p-5"><h3 className="text-lg font-bold text-slate-900">{application.title}</h3><p className="mt-2 text-sm text-slate-600">Use your saved profile and the role description to create a draft before opening LinkedIn.</p><button disabled={busy} onClick={() => onPrepare(application)} className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60">Prepare application</button></div>;
  return <div className="rounded-xl bg-slate-50 p-5"><div className="flex justify-between gap-4"><div><h3 className="text-lg font-bold text-slate-900">{application.title}</h3><p className="text-sm text-slate-500">{application.company}</p></div><Badge status={application.status} /></div><ReviewText title="Tailored summary" text={application.tailored_summary} onCopy={() => copy(application.tailored_summary)} /><ReviewText title="Cover letter draft" text={application.cover_letter} onCopy={() => copy(application.cover_letter)} /><div className="mt-5"><h4 className="text-sm font-bold text-slate-800">Answers to confirm</h4><div className="mt-2 grid gap-2 sm:grid-cols-3">{Object.entries(application.screening_answers).map(([key, value]) => <div key={key} className="rounded-lg border border-slate-200 bg-white p-3"><p className="text-xs font-semibold uppercase text-slate-400">{key.replace(/_/g, ' ')}</p><p className="mt-1 text-sm text-slate-700">{value}</p></div>)}</div></div><div className="mt-5 flex flex-wrap gap-3 border-t border-slate-200 pt-5"><a href={application.linkedin_url} target="_blank" rel="noreferrer" className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white">Open in LinkedIn</a>{application.status !== 'applied' && <button disabled={busy} onClick={onApplied} className="rounded-lg border border-emerald-600 px-4 py-2 text-sm font-semibold text-emerald-700 disabled:opacity-60">Mark as applied</button>}</div></div>;
}

function ReviewText({ title, text, onCopy }: { title: string; text: string; onCopy: () => void }) {
  return <div className="mt-5"><div className="flex justify-between gap-3"><h4 className="text-sm font-bold text-slate-800">{title}</h4><button onClick={onCopy} className="text-xs font-semibold text-blue-700">Copy</button></div><p className="mt-2 whitespace-pre-wrap rounded-lg border border-slate-200 bg-white p-3 text-sm leading-6 text-slate-700">{text}</p></div>;
}
