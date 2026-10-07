import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.models.database import connect_to_mongo, close_mongo_connection, get_database
from app.config import settings
from app.schemas.requests import (
    UserProfileRequest, 
    CompanyListResponse, 
    CompanyResponse,
    EmailGenerationRequest,
    EmailResponse,
    EmailSendRequest,
    EmailLogResponse,
    ActivityResponse,
    LinkedInProfileRequest,
    LinkedInJobRequest,
    LinkedInApplicationUpdate,
    LinkedInApplicationResponse
)
from app.services.company_service import CompanyResearchService, EmailGenerationService, GmailService
from app.agents.outreach_graph import (
    CompanyFinderAgent, 
    HiringClassifierAgent, 
    CompanyResearchAgent, 
    OutreachStrategyAgent,
    create_agent_graph,
    AgentState
)
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime
from typing import List
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=settings.gemini_api_key)
company_research_service = CompanyResearchService()
email_generation_service = EmailGenerationService(llm)
gmail_service = GmailService()

# Initialize agents
company_finder = CompanyFinderAgent(llm)
hiring_classifier = HiringClassifierAgent(llm)
research_agent = CompanyResearchAgent(llm, company_research_service)
strategy_agent = OutreachStrategyAgent(llm)

# Create agent graph
agent_graph = create_agent_graph(
    company_finder,
    hiring_classifier,
    research_agent,
    strategy_agent
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager"""
    # Startup
    logger.info("Starting OutreachAI Backend...")
    await connect_to_mongo()
    await company_research_service.initialize()
    logger.info("Services initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down OutreachAI Backend...")
    await close_mongo_connection()
    await company_research_service.close()
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
    """Health check endpoint"""
    return {"status": "healthy", "service": "OutreachAI Backend"}


# API Routes

@app.post("/api/generate-companies", response_model=CompanyListResponse)
async def generate_companies(
    request: UserProfileRequest,
    db=Depends(get_database)
):
    """
    Generate company suggestions based on user profile
    """
    logger.info(f"Generating companies for role: {request.role}")
    
    try:
        # Create initial state
        initial_state: AgentState = {
            "user_profile": {
                "role": request.role,
                "experience": request.experience,
                "skills": request.skills,
                "location": request.location,
                "salary": request.salary,
                "num_companies": request.num_companies,
            },
            "companies": [],
            "current_company": {},
            "research_data": {},
            "outreach_strategy": {},
            "generated_email": {},
            "messages": []
        }
        
        # Run agent graph
        result = agent_graph.invoke(initial_state)
        
        companies = result.get("companies", [])
        
        # Separate active and inactive
        active = [
            CompanyResponse(
                id=str(i),
                name=c.get("name"),
                website=c.get("website"),
                hiring_signal=c.get("classification", "unknown"),
                summary=c.get("summary", ""),
                domain=c.get("domain", ""),
                relevance_score=0.8,
                tech_signals=[],
                outreach_method=c.get("method", "email"),
                tags=[]
            )
            for i, c in enumerate(companies)
            if c.get("classification") == "active"
        ]
        
        inactive = [
            CompanyResponse(
                id=str(i + len(active)),
                name=c.get("name"),
                website=c.get("website"),
                hiring_signal=c.get("classification", "unknown"),
                summary=c.get("summary", ""),
                domain=c.get("domain", ""),
                relevance_score=0.6,
                tech_signals=[],
                outreach_method=c.get("method", "linkedin"),
                tags=[]
            )
            for i, c in enumerate(companies)
            if c.get("classification") != "active"
        ]
        
        # Store in MongoDB
        if companies:
            await db.companies.insert_many([
                {
                    "name": c.get("name"),
                    "website": c.get("website"),
                    "hiring_signal": c.get("classification"),
                    "created_at": datetime.utcnow(),
                    "user_profile": initial_state["user_profile"]
                }
                for c in companies
            ])
        
        return CompanyListResponse(
            total=len(companies),
            actively_hiring=active,
            strategic_targets=inactive
        )
    
    except Exception as e:
        logger.error(f"Error generating companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-email", response_model=EmailResponse)
async def generate_email(request: EmailGenerationRequest):
    """
    Generate personalized cold email
    """
    logger.info(f"Generating email for {request.company_name}")
    
    try:
        email = await email_generation_service.generate_email(
            user_role=request.user_role,
            user_skills=request.user_skills,
            company_name=request.company_name,
            company_summary=request.company_summary,
            company_domain=request.company_name
        )
        
        return EmailResponse(
            subject=email.get("subject", "Let's Connect"),
            body=email.get("body", "")
        )
    
    except Exception as e:
        logger.error(f"Error generating email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/send-email")
async def send_email(
    request: EmailSendRequest,
    db=Depends(get_database)
):
    """
    Send email via Gmail API
    """
    logger.info(f"Sending email to {request.recipient_email}")
    
    try:
        # Get user and their Gmail credentials
        user = await db.users.find_one({"_id": request.user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Note: In production, use OAuth credentials properly
        result = await gmail_service.send_email(
            to_email=request.recipient_email,
            subject=request.subject,
            body=request.body,
            user_email=user.get("email")
        )
        
        # Log email
        if result.get("success"):
            await db.email_logs.insert_one({
                "user_id": request.user_id,
                "company_id": request.company_id,
                "company_name": request.company_name,
                "recipient_email": request.recipient_email,
                "subject": request.subject,
                "body": request.body,
                "status": "sent",
                "created_at": datetime.utcnow(),
                "sent_at": datetime.utcnow()
            })
        
        return result
    
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/activity")
async def get_activity(
    user_id: str,
    db=Depends(get_database)
):
    """
    Get user's email activity log
    """
    try:
        from bson import ObjectId
        
        logs = await db.email_logs.find({
            "user_id": ObjectId(user_id)
        }).sort("created_at", -1).limit(50).to_list(None)
        
        emails = [
            EmailLogResponse(
                id=str(log["_id"]),
                company_name=log.get("company_name"),
                recipient_email=log.get("recipient_email"),
                subject=log.get("subject"),
                status=log.get("status"),
                created_at=log.get("created_at"),
                sent_at=log.get("sent_at")
            )
            for log in logs
        ]
        
        return ActivityResponse(
            total_emails_sent=len([e for e in emails if e.status == "sent"]),
            emails=emails
        )
    
    except Exception as e:
        logger.error(f"Error getting activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


@app.post("/api/auth/gmail/callback")
async def gmail_auth_callback(code: str, db=Depends(get_database)):
    """
    Handle Gmail OAuth callback
    """
    logger.info("Processing Gmail OAuth callback")
    
    try:
        # Exchange code for credentials (implementation depends on your OAuth setup)
        # This is a placeholder
        return {"success": True, "message": "Gmail authentication successful"}
    
    except Exception as e:
        logger.error(f"Error in Gmail callback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
