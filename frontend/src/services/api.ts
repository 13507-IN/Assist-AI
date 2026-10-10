import axios, { AxiosInstance } from 'axios';
import {
  UserProfile, CompanyListResponse, Email, ActivityResponse,
  GmailStatus, HealthResponse, LinkedInApplication, LinkedInJobInput, LinkedInProfile
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
const BACKEND_URL = API_BASE_URL.replace(/\/api\/?$/, '');

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async generateCompanies(profile: UserProfile): Promise<CompanyListResponse> {
    const response = await this.client.post('/generate-companies', profile);
    return response.data;
  }

  async generateEmail(
    userId: string,
    companyId: string,
    companyName: string,
    companySummary: string,
    userRole: string,
    userSkills: string[]
  ): Promise<Email> {
    const response = await this.client.post('/generate-email', {
      user_id: userId,
      company_id: companyId,
      company_name: companyName,
      company_summary: companySummary,
      user_role: userRole,
      user_skills: userSkills,
    });
    return response.data;
  }

  async sendEmail(
    userId: string,
    recipientEmail: string,
    companyId: string,
    companyName: string,
    subject: string,
    body: string
  ): Promise<{ success: boolean; message_id?: string; error?: string; log_id?: string }> {
    const response = await this.client.post('/send-email', {
      user_id: userId,
      recipient_email: recipientEmail,
      company_id: companyId,
      company_name: companyName,
      subject,
      body,
    });
    return response.data;
  }

  async saveDraft(
    userId: string,
    recipientEmail: string,
    companyId: string,
    companyName: string,
    subject: string,
    body: string
  ): Promise<{ success: boolean; id: string }> {
    const response = await this.client.post('/email-drafts', {
      user_id: userId,
      recipient_email: recipientEmail,
      company_id: companyId,
      company_name: companyName,
      subject,
      body,
    });
    return response.data;
  }

  async getCompanyEmailStatus(
    companyId: string,
    userId: string
  ): Promise<{ contacted: boolean; last_sent_at?: string; recipient_email?: string }> {
    const response = await this.client.get(`/companies/${companyId}/email-status`, {
      params: { user_id: userId },
    });
    return response.data;
  }

  async getActivity(userId: string, status?: string): Promise<ActivityResponse> {
    const response = await this.client.get('/activity', {
      params: { user_id: userId, status },
    });
    return response.data;
  }

  async getHealth(): Promise<HealthResponse> {
    const response = await axios.get(`${BACKEND_URL}/health`, { timeout: 10000 });
    return response.data;
  }

  async getGmailStatus(userId: string): Promise<GmailStatus> {
    const response = await this.client.get('/auth/gmail/status', {
      params: { user_id: userId },
    });
    return response.data;
  }

  gmailConnectUrl(userId: string): string {
    return `${API_BASE_URL}/auth/gmail/start?user_id=${encodeURIComponent(userId)}`;
  }

  async getLinkedInProfile(): Promise<LinkedInProfile | null> {
    const response = await this.client.get('/linkedin/profile');
    return response.data.profile;
  }

  async saveLinkedInProfile(profile: LinkedInProfile): Promise<LinkedInProfile> {
    const response = await this.client.put('/linkedin/profile', profile);
    return response.data.profile;
  }

  async getLinkedInApplications(): Promise<LinkedInApplication[]> {
    const response = await this.client.get('/linkedin/applications');
    return response.data;
  }

  async addLinkedInApplication(job: LinkedInJobInput): Promise<LinkedInApplication> {
    const response = await this.client.post('/linkedin/applications', job);
    return response.data;
  }

  async prepareLinkedInApplication(id: string): Promise<LinkedInApplication> {
    const response = await this.client.post(`/linkedin/applications/${id}/prepare`);
    return response.data;
  }

  async updateLinkedInApplication(
    id: string,
    update: { status?: string; note?: string }
  ): Promise<LinkedInApplication> {
    const response = await this.client.patch(`/linkedin/applications/${id}`, update);
    return response.data;
  }
}

export default new ApiService();
