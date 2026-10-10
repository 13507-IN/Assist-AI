// API Types

export interface UserProfile {
  role: string;
  experience: number;
  skills: string[];
  location: string;
  salary?: number;
  num_companies: number;
}

export interface Company {
  id: string;
  name: string;
  website?: string;
  hiring_signal: string;
  summary?: string;
  domain?: string;
  relevance_score: number;
  tech_signals: string[];
  outreach_method?: string;
  outreach_instructions?: string;
  tags: string[];
  source?: string;
  research_error?: string;
}

export interface CompanyListResponse {
  total: number;
  actively_hiring: Company[];
  strategic_targets: Company[];
}

export interface Email {
  subject: string;
  body: string;
}

export interface EmailLog {
  id: string;
  company_name: string;
  recipient_email: string;
  subject: string;
  body: string;
  status: string;
  error_message?: string;
  created_at: string;
  sent_at?: string;
}

export interface ActivityResponse {
  total_emails_sent: number;
  total_drafts: number;
  total_failed: number;
  emails: EmailLog[];
}

export interface ServiceHealth {
  status: 'ok' | 'error' | 'disconnected';
  detail: string;
  configured?: boolean;
  connected?: boolean;
  email?: string;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded';
  service: string;
  services: Record<string, ServiceHealth>;
}

export interface GmailStatus extends ServiceHealth {
  configured: boolean;
  connected: boolean;
}

export interface LinkedInProfile {
  full_name: string;
  email: string;
  phone?: string;
  location: string;
  headline?: string;
  years_experience: number;
  skills: string[];
  linkedin_url?: string;
  resume_url?: string;
  common_answers: Record<string, string>;
}

export interface LinkedInJobInput {
  title: string;
  company: string;
  linkedin_url: string;
  location?: string;
  work_mode?: string;
  description: string;
}

export interface LinkedInApplication extends LinkedInJobInput {
  id: string;
  status: string;
  match_score?: number | null;
  matched_skills: string[];
  tailored_summary: string;
  cover_letter: string;
  screening_answers: Record<string, string>;
  note: string;
  created_at: string;
  updated_at: string;
}
