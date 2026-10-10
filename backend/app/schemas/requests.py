from pydantic import BaseModel, EmailStr, Field
from typing import Dict, List, Optional
from datetime import datetime


class UserProfileRequest(BaseModel):
    """User profile input for company suggestions"""
    role: str
    experience: int = Field(ge=0, le=60)
    skills: List[str] = Field(min_length=1)
    location: str
    salary: Optional[int] = None
    num_companies: int = Field(default=10, ge=1, le=20)


class UserProfileResponse(BaseModel):
    """User profile response"""
    id: str
    email: EmailStr
    name: str
    role: str
    experience: int
    skills: List[str]
    location: str
    salary: Optional[int]


class CompanyResponse(BaseModel):
    """Company response"""
    id: str
    name: str
    website: Optional[str]
    hiring_signal: str
    summary: Optional[str]
    domain: Optional[str]
    relevance_score: float
    tech_signals: List[str]
    outreach_method: Optional[str]
    outreach_instructions: Optional[str]
    tags: List[str]
    source: Optional[str] = None
    research_error: Optional[str] = None


class CompanyListResponse(BaseModel):
    """Company list response"""
    total: int
    actively_hiring: List[CompanyResponse]
    strategic_targets: List[CompanyResponse]


class EmailGenerationRequest(BaseModel):
    """Email generation request"""
    user_id: str
    company_id: str
    company_name: str
    company_summary: str
    user_role: str
    user_skills: List[str]


class EmailResponse(BaseModel):
    """Generated email response"""
    subject: str
    body: str


class EmailSendRequest(BaseModel):
    """Email send request"""
    user_id: str
    recipient_email: EmailStr
    company_id: str
    company_name: str
    subject: str
    body: str


class EmailDraftRequest(EmailSendRequest):
    """Editable email saved without sending."""


class EmailLogResponse(BaseModel):
    """Email log response"""
    id: str
    company_name: str
    recipient_email: str
    subject: str
    body: str = ""
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    sent_at: Optional[datetime]


class ActivityResponse(BaseModel):
    """Activity log response"""
    total_emails_sent: int
    total_drafts: int = 0
    total_failed: int = 0
    emails: List[EmailLogResponse]


class LinkedInProfileRequest(BaseModel):
    """Single-user application profile stored in this private workspace."""
    full_name: str
    email: EmailStr
    phone: Optional[str] = ""
    location: str
    headline: Optional[str] = ""
    years_experience: int = 0
    skills: List[str] = Field(default_factory=list)
    linkedin_url: Optional[str] = ""
    resume_url: Optional[str] = ""
    common_answers: Dict[str, str] = Field(default_factory=dict)


class LinkedInJobRequest(BaseModel):
    """A job selected by the user for a reviewed LinkedIn application."""
    title: str
    company: str
    linkedin_url: str
    location: Optional[str] = ""
    work_mode: Optional[str] = ""
    description: str


class LinkedInApplicationUpdate(BaseModel):
    status: Optional[str] = None
    note: Optional[str] = None


class LinkedInApplicationResponse(BaseModel):
    id: str
    title: str
    company: str
    linkedin_url: str
    location: str = ""
    work_mode: str = ""
    description: str
    status: str
    match_score: Optional[int] = None
    matched_skills: List[str] = Field(default_factory=list)
    tailored_summary: str = ""
    cover_letter: str = ""
    screening_answers: Dict[str, str] = Field(default_factory=dict)
    note: str = ""
    created_at: datetime
    updated_at: datetime
