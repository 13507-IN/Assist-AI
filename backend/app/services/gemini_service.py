from typing import Literal, Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.config import is_configured, settings


class CompanySuggestion(BaseModel):
    name: str
    website: str
    hiring_signal: Literal["active", "strategic", "unknown"] = "unknown"
    reasoning: str
    relevance_score: float = Field(ge=0, le=1)
    tech_signals: list[str] = []
    outreach_method: Literal["email", "linkedin", "apply"] = "email"
    outreach_instructions: str = ""
    tags: list[str] = []


class CompanySuggestions(BaseModel):
    companies: list[CompanySuggestion]


class GeneratedEmail(BaseModel):
    subject: str
    body: str


class GeminiService:
    """Use one structured Gemini call for each user operation."""

    def __init__(self) -> None:
        self.client = (
            genai.Client(api_key=settings.gemini_api_key)
            if is_configured(settings.gemini_api_key)
            else None
        )

    async def status(self) -> dict:
        if not is_configured(settings.gemini_api_key):
            return {"status": "error", "detail": "Missing GEMINI_API_KEY in backend/.env"}
        try:
            assert self.client is not None
            await self.client.aio.models.get(model=settings.gemini_model)
            return {"status": "ok", "detail": f"Model {settings.gemini_model} is available"}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    async def find_companies(
        self,
        *,
        role: str,
        experience: int,
        skills: list[str],
        location: str,
        salary: Optional[int],
        count: int,
    ) -> list[dict]:
        if self.client is None:
            raise RuntimeError("Missing GEMINI_API_KEY in backend/.env")

        prompt = (
            f"Suggest exactly {count} real companies relevant to this candidate. "
            "Prefer companies with a public website and realistic hiring potential. "
            "Use active only for a credible current hiring signal; otherwise use strategic or unknown.\n\n"
            f"Target role: {role}\n"
            f"Experience: {experience} years\n"
            f"Skills: {', '.join(skills)}\n"
            f"Location/timezone: {location}\n"
            f"Salary expectation: {salary if salary else 'not specified'}"
        )
        response = await self.client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CompanySuggestions,
                temperature=0.2,
            ),
        )
        parsed = response.parsed
        if parsed is None:
            raise RuntimeError("Gemini returned no structured company data")
        suggestions = (
            parsed if isinstance(parsed, CompanySuggestions) else CompanySuggestions.model_validate(parsed)
        )
        return [company.model_dump() for company in suggestions.companies[:count]]

    async def generate_email(
        self,
        *,
        user_role: str,
        user_skills: list[str],
        company_name: str,
        company_summary: str,
    ) -> dict[str, str]:
        if self.client is None:
            raise RuntimeError("Missing GEMINI_API_KEY in backend/.env")
        prompt = (
            "Write a concise, natural cold email under 120 words. Include a specific value proposition, "
            "avoid invented facts, and do not include placeholders.\n\n"
            f"Candidate role: {user_role}\n"
            f"Candidate skills: {', '.join(user_skills)}\n"
            f"Company: {company_name}\n"
            f"Company context: {company_summary}"
        )
        response = await self.client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=GeneratedEmail,
                temperature=0.4,
            ),
        )
        parsed = response.parsed
        if parsed is None:
            raise RuntimeError("Gemini returned no structured email")
        email = parsed if isinstance(parsed, GeneratedEmail) else GeneratedEmail.model_validate(parsed)
        return email.model_dump()

    async def close(self) -> None:
        if self.client is not None:
            await self.client.aio.aclose()
            self.client.close()
