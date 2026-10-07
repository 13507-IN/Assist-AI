import aiohttp
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class CompanyResearchService:
    """Service for researching companies"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    async def extract_company_info(self, company_name: str, website: str) -> Dict:
        """
        Extract company information from website
        """
        try:
            if not website:
                return {"error": "No website provided"}
            
            # Ensure URL has protocol
            if not website.startswith(('http://', 'https://')):
                website = f"https://{website}"
            
            async with self.session.get(website, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_html(html, company_name)
                else:
                    return {"error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"Error extracting company info for {company_name}: {e}")
            return {"error": str(e)}
    
    def _parse_html(self, html: str, company_name: str) -> Dict:
        """Parse HTML to extract company information"""
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract meta tags and title
        title = soup.find('title')
        meta_description = soup.find('meta', attrs={'name': 'description'})
        
        # Extract text content
        text_content = ' '.join([p.get_text() for p in soup.find_all('p')[:5]])
        
        return {
            "company_name": company_name,
            "title": title.string if title else None,
            "description": meta_description.get('content') if meta_description else None,
            "preview": text_content[:500] if text_content else None,
        }
    
    async def check_hiring_signals(self, website: str, company_name: str) -> Dict:
        """
        Check for recent hiring signals on the website
        """
        try:
            if not website:
                return {"hiring_signal": "unknown", "confidence": 0}
            
            if not website.startswith(('http://', 'https://')):
                website = f"https://{website}"
            
            # Check careers page
            careers_urls = [
                f"{website}/careers",
                f"{website}/jobs",
                f"{website}/hiring",
            ]
            
            for careers_url in careers_urls:
                try:
                    async with self.session.get(
                        careers_url, 
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        if response.status == 200:
                            html = await response.text()
                            
                            # Look for job posting indicators
                            if self._has_active_job_postings(html):
                                return {
                                    "hiring_signal": "active",
                                    "confidence": 0.8,
                                    "source": careers_url
                                }
                except Exception as e:
                    logger.debug(f"Error checking {careers_url}: {e}")
                    continue
            
            return {"hiring_signal": "unknown", "confidence": 0.5}
        except Exception as e:
            logger.error(f"Error checking hiring signals: {e}")
            return {"hiring_signal": "unknown", "confidence": 0}
    
    def _has_active_job_postings(self, html: str) -> bool:
        """Check if HTML contains active job postings"""
        soup = BeautifulSoup(html, 'lxml')
        
        # Common job listing indicators
        indicators = [
            soup.find_all('a', {'href': '/job'}),
            soup.find_all('a', {'href': '/careers'}),
            soup.find_all('div', {'class': ['job-listing', 'position', 'vacancy']}),
            soup.find_all(string=['Join our team', 'We are hiring', 'Open positions']),
        ]
        
        return any(indicators)


class EmailGenerationService:
    """Service for generating personalized cold emails"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def generate_email(
        self,
        user_role: str,
        user_skills: List[str],
        company_name: str,
        company_summary: str,
        company_domain: str
    ) -> Dict[str, str]:
        """
        Generate personalized cold email using LLM
        """
        prompt = self._create_email_prompt(
            user_role, 
            user_skills, 
            company_name, 
            company_summary, 
            company_domain
        )
        
        try:
            response = self.llm_client.invoke(prompt)
            email_content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse email (assuming format: Subject: ... \n\nBody: ...)
            return self._parse_email_response(email_content)
        except Exception as e:
            logger.error(f"Error generating email: {e}")
            return {
                "subject": f"Exciting Opportunity at {company_name}",
                "body": f"Hello,\n\nI'm interested in opportunities at {company_name}."
            }
    
    def _create_email_prompt(
        self,
        user_role: str,
        user_skills: List[str],
        company_name: str,
        company_summary: str,
        company_domain: str
    ) -> str:
        """Create prompt for email generation"""
        skills_str = ", ".join(user_skills)
        
        return f"""Write a short, highly personalized cold email for a {user_role} applying to {company_name}.

Company Information:
- Name: {company_name}
- Domain: {company_domain}
- Summary: {company_summary}

Applicant Profile:
- Role: {user_role}
- Skills: {skills_str}

Requirements:
1. Keep it under 120 words
2. Personalize based on company info and applicant skills
3. Format with "Subject:" and "Body:" clearly separated
4. Sound natural, not generic
5. Include specific value proposition

Generate the email now:"""
    
    def _parse_email_response(self, response_text: str) -> Dict[str, str]:
        """Parse email response from LLM"""
        # Split by Subject and Body
        parts = response_text.split('\n\n', 1)
        
        subject = ""
        body = ""
        
        for part in parts:
            if part.startswith('Subject:'):
                subject = part.replace('Subject:', '').strip()
            elif part.startswith('Body:'):
                body = part.replace('Body:', '').strip()
        
        # Fallback parsing
        if not subject or not body:
            lines = response_text.strip().split('\n')
            for i, line in enumerate(lines):
                if 'Subject:' in line:
                    subject = line.split('Subject:', 1)[1].strip()
                elif 'Body:' in line:
                    body = '\n'.join(lines[i+1:]).replace('Body:', '').strip()
        
        return {
            "subject": subject or "Let's Connect",
            "body": body or response_text
        }


class GmailService:
    """Service for Gmail API integration"""
    
    def __init__(self):
        self.service = None
    
    def authenticate(self, credentials):
        """Authenticate with Gmail API"""
        from google.auth.transport.requests import Request
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        
        try:
            self.service = build('gmail', 'v1', credentials=credentials)
            return True
        except Exception as e:
            logger.error(f"Gmail authentication failed: {e}")
            return False
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        user_email: str
    ) -> Dict:
        """
        Send email via Gmail API
        """
        if not self.service:
            return {"success": False, "error": "Not authenticated"}
        
        try:
            from email.mime.text import MIMEText
            import base64
            
            message = MIMEText(body)
            message['to'] = to_email
            message['subject'] = subject
            message['from'] = user_email
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            result = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Email sent to {to_email}, MessageId: {result.get('id')}")
            return {
                "success": True,
                "message_id": result.get('id')
            }
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {"success": False, "error": str(e)}
