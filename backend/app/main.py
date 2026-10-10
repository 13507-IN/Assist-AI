import logging
import secrets
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlencode

from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import settings
from app.models import database as database_module
from app.models.database import (
    close_mongo_connection,
    connect_to_mongo,
    database_status,
    get_database,
)
from app.schemas.requests import (
    CompanyResponse,
    CompanyListResponse,
    EmailDraftRequest,
    EmailGenerationRequest,
    EmailLogResponse,
    EmailResponse,
    EmailSendRequest,
    ActivityResponse,
    LinkedInApplicationResponse,
    LinkedInApplicationUpdate,
    LinkedInJobRequest,
    LinkedInProfileRequest,
    UserProfileRequest,
)
from app.services.company_service import CompanyResearchService
from app.services.gemini_service import GeminiService
from app.services.gmail_service import GmailService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

company_research_service = CompanyResearchService()
gemini_service = GeminiService()
gmail_service = GmailService()
OAUTH_STATE_TTL_SECONDS = 600


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager"""
    logger.info("Starting OutreachAI Backend...")
    missing = [
        key
        for key, value in {
            "GEMINI_API_KEY": settings.gemini_api_key,
            "GMAIL_CLIENT_ID": settings.gmail_client_id,
            "GMAIL_CLIENT_SECRET": settings.gmail_client_secret,
        }.items()
        if not value or value.startswith("your_")
    ]
    if missing:
        logger.error("Missing settings in backend/.env: %s", ", ".join(missing))

    await connect_to_mongo()
    await company_research_service.initialize()
    startup_checks = {
        "mongodb": await database_status(),
        "gemini": await gemini_service.status(),
        "gmail": await gmail_service.status(database_module.db),
    }
    app.state.startup_checks = startup_checks
    for service, result in startup_checks.items():
        log = logger.info if result["status"] == "ok" else logger.error
        log("%s startup check: %s - %s", service, result["status"], result["detail"])
    
    yield
    
    logger.info("Shutting down OutreachAI Backend...")
    await close_mongo_connection()
    await company_research_service.close()
    await gemini_service.close()
    logger.info("Services shutdown")


app = FastAPI(
    title="OutreachAI API",
    description="AI-powered outreach platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_linkedin_application(application: dict) -> LinkedInApplicationResponse:
    """Convert a MongoDB application document to the public API shape."""
    return LinkedInApplicationResponse(
        id=str(application["_id"]),
        title=application["title"],
        company=application["company"],
        linkedin_url=application["linkedin_url"],
        location=application.get("location", ""),
        work_mode=application.get("work_mode", ""),
        description=application.get("description", ""),
        status=application.get("status", "saved"),
        match_score=application.get("match_score"),
        matched_skills=application.get("matched_skills", []),
        tailored_summary=application.get("tailored_summary", ""),
        cover_letter=application.get("cover_letter", ""),
        screening_answers=application.get("screening_answers", {}),
        note=application.get("note", ""),
        created_at=application["created_at"],
        updated_at=application["updated_at"]
    )


# Health check
@app.get("/health")
async def health_check():
    """Report each external dependency instead of hiding partial failures."""
    services = {
        "backend": {"status": "ok", "detail": "API is running"},
        "mongodb": await database_status(),
        "gemini": await gemini_service.status(),
        "gmail": await gmail_service.status(database_module.db),
    }
    overall = "healthy" if all(
        service["status"] == "ok" for service in services.values()
    ) else "degraded"
    return {"status": overall, "service": "OutreachAI Backend", "services": services}


def company_response(company: dict) -> CompanyResponse:
    return CompanyResponse(
        id=str(company["_id"]),
        name=company["name"],
        website=company.get("website"),
        hiring_signal=company.get("hiring_signal", "unknown"),
        summary=company.get("summary") or company.get("reasoning", ""),
        domain=company.get("domain"),
        relevance_score=company.get("relevance_score", 0),
        tech_signals=company.get("tech_signals", []),
        outreach_method=company.get("outreach_method"),
        outreach_instructions=company.get("outreach_instructions"),
        tags=company.get("tags", []),
        source=company.get("source"),
        research_error=company.get("research_error"),
    )


def company_id(value: str):
    return ObjectId(value) if ObjectId.is_valid(value) else value


@app.post("/api/generate-companies", response_model=CompanyListResponse)
async def generate_companies(request: UserProfileRequest, db=Depends(get_database)):
    """Generate structured suggestions, verify their sites concurrently, and persist them."""
    logger.info("Generating %s companies for role: %s", request.num_companies, request.role)
    try:
        suggestions = await gemini_service.find_companies(
            role=request.role,
            experience=request.experience,
            skills=request.skills,
            location=request.location,
            salary=request.salary,
            count=request.num_companies,
        )
        if not suggestions:
            raise RuntimeError("Gemini returned no companies")

        companies = await company_research_service.research_companies(suggestions)
        now = datetime.now(timezone.utc)
        profile = request.model_dump()
        documents = [
            {**company, "user_profile": profile, "created_at": now, "updated_at": now}
            for company in companies
        ]
        result = await db.companies.insert_many(documents)
        for document, inserted_id in zip(documents, result.inserted_ids):
            document["_id"] = inserted_id

        active = [company_response(c) for c in documents if c["hiring_signal"] == "active"]
        strategic = [company_response(c) for c in documents if c["hiring_signal"] != "active"]
        return CompanyListResponse(
            total=len(documents),
            actively_hiring=active,
            strategic_targets=strategic,
        )
    except RuntimeError as exc:
        logger.error("Company generation failed: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Company generation failed")
        raise HTTPException(status_code=502, detail=f"Company search failed: {exc}") from exc


@app.post("/api/generate-email", response_model=EmailResponse)
async def generate_email(request: EmailGenerationRequest):
    logger.info("Generating email for %s", request.company_name)
    try:
        email = await gemini_service.generate_email(
            user_role=request.user_role,
            user_skills=request.user_skills,
            company_name=request.company_name,
            company_summary=request.company_summary,
        )
        return EmailResponse(**email)
    except Exception as exc:
        logger.error("Email generation failed: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def email_log_document(request: EmailSendRequest, status: str, error: Optional[str] = None) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "user_id": request.user_id,
        "company_id": company_id(request.company_id),
        "company_name": request.company_name,
        "recipient_email": str(request.recipient_email),
        "subject": request.subject,
        "body": request.body,
        "status": status,
        "error_message": error,
        "created_at": now,
        "sent_at": now if status == "sent" else None,
    }


@app.post("/api/email-drafts", status_code=201)
async def save_email_draft(request: EmailDraftRequest, db=Depends(get_database)):
    result = await db.email_logs.insert_one(email_log_document(request, "drafted"))
    return {"success": True, "id": str(result.inserted_id)}


@app.get("/api/companies/{company_id_value}/email-status")
async def company_email_status(
    company_id_value: str,
    user_id: str = "local-user",
    db=Depends(get_database),
):
    previous = await db.email_logs.find_one(
        {
            "user_id": user_id,
            "company_id": company_id(company_id_value),
            "status": "sent",
        },
        sort=[("sent_at", -1)],
    )
    return {
        "contacted": previous is not None,
        "last_sent_at": previous.get("sent_at") if previous else None,
        "recipient_email": previous.get("recipient_email") if previous else None,
    }


@app.post("/api/send-email")
async def send_email(request: EmailSendRequest, db=Depends(get_database)):
    logger.info("Sending email to %s", request.recipient_email)
    result = await gmail_service.send_email(
        db=db,
        user_id=request.user_id,
        to_email=str(request.recipient_email),
        subject=request.subject,
        body=request.body,
    )
    status = "sent" if result.get("success") else "failed"
    log_result = await db.email_logs.insert_one(
        email_log_document(request, status, result.get("error"))
    )
    result["log_id"] = str(log_result.inserted_id)
    return result


@app.get("/api/activity", response_model=ActivityResponse)
async def get_activity(
    user_id: str = "local-user",
    status: Optional[str] = None,
    db=Depends(get_database),
):
    query = {"user_id": user_id}
    if status in {"drafted", "sent", "failed"}:
        query["status"] = status
    logs = await db.email_logs.find(query).sort("created_at", -1).limit(100).to_list()
    emails = [
        EmailLogResponse(
            id=str(log["_id"]),
            company_name=log.get("company_name", ""),
            recipient_email=log.get("recipient_email", ""),
            subject=log.get("subject", ""),
            body=log.get("body", ""),
            status=log.get("status", "drafted"),
            error_message=log.get("error_message"),
            created_at=log.get("created_at"),
            sent_at=log.get("sent_at"),
        )
        for log in logs
    ]
    return ActivityResponse(
        total_emails_sent=sum(email.status == "sent" for email in emails),
        total_drafts=sum(email.status == "drafted" for email in emails),
        total_failed=sum(email.status == "failed" for email in emails),
        emails=emails,
    )


@app.get("/api/linkedin/profile")
async def get_linkedin_profile(db=Depends(get_database)):
    """Return this private app's single saved job-seeker profile."""
    profile = await db.linkedin_profiles.find_one({"profile_key": "local-user"}, {"_id": 0})
    return {"success": True, "profile": profile or None}


@app.put("/api/linkedin/profile")
async def save_linkedin_profile(
    profile: LinkedInProfileRequest,
    db=Depends(get_database)
):
    """Save a personal application profile; it is never shared with LinkedIn."""
    data = profile.model_dump()
    data.update({"profile_key": "local-user", "updated_at": datetime.utcnow()})
    await db.linkedin_profiles.update_one(
        {"profile_key": "local-user"},
        {"$set": data, "$setOnInsert": {"created_at": datetime.utcnow()}},
        upsert=True
    )
    return {"success": True, "profile": data}


@app.get("/api/linkedin/applications", response_model=List[LinkedInApplicationResponse])
async def list_linkedin_applications(db=Depends(get_database)):
    """List locally tracked LinkedIn applications. Nothing is scraped from LinkedIn."""
    applications = await db.linkedin_applications.find({}).sort("updated_at", -1).to_list(100)
    return [serialize_linkedin_application(application) for application in applications]


@app.post("/api/linkedin/applications", response_model=LinkedInApplicationResponse, status_code=201)
async def create_linkedin_application(
    job: LinkedInJobRequest,
    db=Depends(get_database)
):
    """Add a job URL explicitly supplied by the user to the private review queue."""
    now = datetime.utcnow()
    document = {
        **job.model_dump(),
        "status": "saved",
        "match_score": None,
        "matched_skills": [],
        "tailored_summary": "",
        "cover_letter": "",
        "screening_answers": {},
        "note": "",
        "created_at": now,
        "updated_at": now
    }
    result = await db.linkedin_applications.insert_one(document)
    document["_id"] = result.inserted_id
    return serialize_linkedin_application(document)


@app.post("/api/linkedin/applications/{application_id}/prepare", response_model=LinkedInApplicationResponse)
async def prepare_linkedin_application(application_id: str, db=Depends(get_database)):
    """
    Prepare application material from the user's saved profile and job description.
    This deliberately stops before submission: the user reviews everything on LinkedIn.
    """
    from bson import ObjectId

    try:
        job = await db.linkedin_applications.find_one({"_id": ObjectId(application_id)})
    except Exception:
        raise HTTPException(status_code=404, detail="Application not found")
    if not job:
        raise HTTPException(status_code=404, detail="Application not found")

    profile = await db.linkedin_profiles.find_one({"profile_key": "local-user"})
    if not profile:
        raise HTTPException(status_code=400, detail="Save your personal profile before preparing an application")

    description = job.get("description", "").lower()
    matched_skills = [
        skill for skill in profile.get("skills", [])
        if skill.lower().strip() and skill.lower().strip() in description
    ]
    score = min(100, 35 + (len(matched_skills) * 12) + min(profile.get("years_experience", 0) * 3, 20))
    name = profile.get("full_name", "Applicant")
    headline = profile.get("headline") or "professional"
    skills_sentence = ", ".join(matched_skills[:6]) or ", ".join(profile.get("skills", [])[:4]) or "relevant skills"
    tailored_summary = (
        f"{headline} with {profile.get('years_experience', 0)} years of experience. "
        f"Strongest match for this role: {skills_sentence}."
    )
    cover_letter = (
        f"Dear {job['company']} hiring team,\n\n"
        f"I am excited to apply for the {job['title']} role. As a {headline}, "
        f"I bring {profile.get('years_experience', 0)} years of experience and hands-on strength in {skills_sentence}. "
        f"I am especially interested in this opportunity because it aligns with my background and the role's requirements.\n\n"
        f"I would welcome the chance to discuss how I can contribute to {job['company']}.\n\n"
        f"Best regards,\n{name}"
    )
    answers = {
        "work_authorization": profile.get("common_answers", {}).get("work_authorization", "Please confirm before submitting."),
        "salary_expectation": profile.get("common_answers", {}).get("salary_expectation", "Please confirm before submitting."),
        "notice_period": profile.get("common_answers", {}).get("notice_period", "Please confirm before submitting.")
    }
    updates = {
        "status": "ready_for_review",
        "match_score": score,
        "matched_skills": matched_skills,
        "tailored_summary": tailored_summary,
        "cover_letter": cover_letter,
        "screening_answers": answers,
        "updated_at": datetime.utcnow()
    }
    await db.linkedin_applications.update_one({"_id": job["_id"]}, {"$set": updates})
    job.update(updates)
    return serialize_linkedin_application(job)


@app.patch("/api/linkedin/applications/{application_id}", response_model=LinkedInApplicationResponse)
async def update_linkedin_application(
    application_id: str,
    update: LinkedInApplicationUpdate,
    db=Depends(get_database)
):
    """Record review or submitted status after the user acts on LinkedIn."""
    from bson import ObjectId

    try:
        object_id = ObjectId(application_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Application not found")
    updates = {key: value for key, value in update.model_dump().items() if value is not None}
    updates["updated_at"] = datetime.utcnow()
    await db.linkedin_applications.update_one(
        {"_id": object_id},
        {"$set": updates}
    )
    result = await db.linkedin_applications.find_one({"_id": object_id})
    if not result:
        raise HTTPException(status_code=404, detail="Application not found")
    return serialize_linkedin_application(result)


@app.get("/api/auth/gmail/start")
async def gmail_auth_start(
    user_id: str = "local-user",
    db=Depends(get_database),
):
    """Start the server-side Google OAuth flow with persisted CSRF/PKCE state."""
    state = secrets.token_urlsafe(32)
    try:
        await db.oauth_states.delete_many(
            {"created_at": {"$lt": time.time() - OAUTH_STATE_TTL_SECONDS}}
        )
        authorization_url, code_verifier = gmail_service.authorization_url(state)
        await db.oauth_states.insert_one(
            {
                "state": state,
                "user_id": user_id,
                "code_verifier": code_verifier,
                "created_at": time.time(),
            }
        )
        return RedirectResponse(authorization_url)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/auth/gmail/callback")
async def gmail_auth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db=Depends(get_database),
):
    """Exchange the OAuth code, persist the renewable token, and return to the app."""
    def back_to_app(message: str) -> RedirectResponse:
        logger.error("Gmail OAuth callback failed: %s", message)
        query = urlencode({"gmail": "error", "message": message})
        return RedirectResponse(f"{settings.frontend_url}/?{query}")

    if error:
        if state:
            await db.oauth_states.delete_one({"state": state})
        return back_to_app(error_description or error)
    if not code or not state:
        if state:
            await db.oauth_states.delete_one({"state": state})
        return back_to_app("Google did not return an authorization code and state.")

    pending = await db.oauth_states.find_one_and_delete({"state": state})
    if not pending:
        return back_to_app("Gmail sign-in expired or was already used. Please try again.")
    if time.time() - pending["created_at"] > OAUTH_STATE_TTL_SECONDS:
        return back_to_app("Gmail sign-in expired. Please try again.")

    try:
        email = await gmail_service.exchange_code(
            code,
            state,
            db,
            pending["user_id"],
            pending.get("code_verifier"),
        )
        query = urlencode({"gmail": "connected", "email": email})
        return RedirectResponse(f"{settings.frontend_url}/?{query}")
    except Exception as exc:
        return back_to_app(str(exc))


@app.get("/api/auth/gmail/status")
async def gmail_auth_status(
    user_id: str = "local-user",
    db=Depends(get_database),
):
    return await gmail_service.status(db, user_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
