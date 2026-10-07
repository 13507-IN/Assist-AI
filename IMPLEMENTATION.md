# OutreachAI - Implementation Guide

## 🎯 System Overview

OutreachAI is a multi-agent AI system that orchestrates the entire cold email outreach workflow:

```
User Input (Profile) 
    ↓
[LangGraph Workflow]
    ├─ Company Finder Agent
    ├─ Hiring Classifier Agent
    ├─ Company Research Agent
    ├─ Outreach Strategy Agent
    └─ Email Generator Agent
    ↓
Generated Companies + Emails
    ↓
Gmail Integration → Send Emails
    ↓
Activity Dashboard
```

## 🧠 How Each Agent Works

### 1. Company Finder Agent

**Purpose:** Find relevant companies based on user profile

**Input:**
- User role
- Years of experience
- Key skills
- Location
- Salary expectations
- Number of companies to find

**Process:**
1. Constructs a detailed search prompt with user profile
2. Uses GPT-4 to suggest relevant companies
3. Returns list with company names, websites, and initial hiring signals

**Output:**
```python
[
    {
        "name": "Anthropic",
        "website": "www.anthropic.com",
        "hiring_signal": "actively hiring",
        "reasoning": "Recently hired for AI roles matching profile"
    },
    # ... more companies
]
```

### 2. Hiring Classifier Agent

**Purpose:** Classify companies as actively hiring or not

**Logic:**
- If "active" or "hiring" in hiring_signal → **Active**
- Otherwise → **Inactive**

**Why:** Helps prioritize outreach efforts

### 3. Company Research Agent

**Purpose:** Gather detailed information about each company

**Process:**
1. **Website Scraping:**
   - Fetches company homepage
   - Extracts title, meta description, preview text
   
2. **Hiring Signal Check:**
   - Checks `/careers`, `/jobs`, `/hiring` pages
   - Looks for job posting indicators
   - Returns hiring signal confidence

3. **LLM Summarization:**
   - Uses GPT-4 to summarize company info
   - Creates concise 2-3 sentence description

**Output:**
```python
{
    "company_info": {
        "title": "Anthropic",
        "description": "AI safety company...",
        "preview": "We build reliable, interpretable..."
    },
    "hiring_check": {
        "hiring_signal": "active",
        "confidence": 0.8,
        "source": "careers page"
    },
    "summary": "Anthropic is an AI safety company..."
}
```

### 4. Outreach Strategy Agent

**Purpose:** Decide best contact method

**Options:**
- `"email"` - If public email exists
- `"linkedin"` - If email not found
- `"apply"` - If active careers page

**Process:**
1. Analyzes research data
2. Decides optimal contact method
3. Provides specific instructions

### 5. Email Generator Agent

**Purpose:** Create personalized cold emails

**Prompt Template:**
```
Write a short, highly personalized cold email for a {ROLE} applying to {COMPANY}.

Company Information:
- Name: {COMPANY_NAME}
- Domain: {DOMAIN}
- Summary: {SUMMARY}

Applicant Profile:
- Role: {ROLE}
- Skills: {SKILLS}

Requirements:
1. Keep it under 120 words
2. Personalize based on company info
3. Sound natural, not generic
4. Include specific value proposition

Generate the email now:
```

**Output:**
```json
{
    "subject": "Excited About AI Safety Work at Anthropic",
    "body": "Hi team,\n\nI've been following Anthropic's work on AI safety..."
}
```

## 🔄 Data Flow

### 1. User Creates Profile

```python
POST /api/generate-companies
{
    "role": "Senior Software Engineer",
    "experience": 5,
    "skills": ["Python", "React", "FastAPI"],
    "location": "San Francisco",
    "salary": 180000,
    "num_companies": 10
}
```

### 2. Backend Processes

```python
# app/main.py - generate_companies endpoint

# 1. Create initial state
initial_state = {
    "user_profile": {...},
    "companies": [],
    "messages": []
}

# 2. Run agent graph
result = agent_graph.invoke(initial_state)

# 3. Separate results
active = [c for c in result["companies"] if c["classification"] == "active"]
inactive = [c for c in result["companies"] if c["classification"] != "active"]

# 4. Return to frontend
return {
    "total": len(companies),
    "actively_hiring": active,
    "strategic_targets": inactive
}
```

### 3. Frontend Displays Results

```python
# Results page shows:
# - Companies actively hiring (with 🔥 emoji)
# - Strategic targets (with 🎯 emoji)
# - Relevance scores
# - Generate Email buttons
```

### 4. Email Generation

```python
POST /api/generate-email
{
    "user_id": "user123",
    "company_id": "comp456",
    "company_name": "Anthropic",
    "company_summary": "AI safety company...",
    "user_role": "Senior Software Engineer",
    "user_skills": ["Python", "React", "FastAPI"]
}

# Response:
{
    "subject": "Let's Collaborate on AI Safety",
    "body": "Hi there,\n\n..."
}
```

### 5. Email Sending

```python
POST /api/send-email
{
    "user_id": "user123",
    "recipient_email": "careers@anthropic.com",
    "company_id": "comp456",
    "company_name": "Anthropic",
    "subject": "...",
    "body": "..."
}

# Response:
{
    "success": true,
    "message_id": "gmail_message_123"
}
```

## 📝 Key Implementation Details

### LangGraph State Management

```python
class AgentState(TypedDict):
    user_profile: Dict[str, Any]        # User input
    companies: List[Dict[str, Any]]     # Accumulated company data
    current_company: Dict[str, Any]     # Company being processed
    research_data: Dict[str, Any]       # Research findings
    outreach_strategy: Dict[str, Any]   # Contact strategy
    generated_email: Dict[str, str]     # Generated email
    messages: List[Dict]                # LLM messages
```

### Agent Execution Flow

```python
# app/agents/outreach_graph.py

workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("company_finder", company_finder.run)
workflow.add_node("hiring_classifier", hiring_classifier.run)
workflow.add_node("research_agent", research_agent.run)
workflow.add_node("strategy_agent", strategy_agent.run)

# Add edges
workflow.add_edge(START, "company_finder")
workflow.add_edge("company_finder", "hiring_classifier")
workflow.add_edge("hiring_classifier", "research_agent")
workflow.add_edge("research_agent", "strategy_agent")
workflow.add_edge("strategy_agent", END)

graph = workflow.compile()
```

### Async Operations

```python
# Email scraping is async to handle multiple companies
async def extract_company_info(company_name, website):
    async with self.session.get(website, timeout=10) as response:
        html = await response.text()
        return parse_html(html)

# MongoDB operations are async
emails = await db.email_logs.find({...}).to_list(None)
```

### Error Handling

```python
try:
    response = llm.invoke(prompt)
except Exception as e:
    logger.error(f"Error: {e}")
    # Return fallback values
    return {
        "companies": [],
        "error": str(e)
    }
```

## 🔐 Security Best Practices

### API Authentication (TODO)
```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/api/generate-companies")
async def generate_companies(
    request: UserProfileRequest,
    credentials: HTTPAuthCredentials = Depends(security)
):
    # Verify JWT token
    user_id = verify_token(credentials.credentials)
    # Proceed...
```

### Input Validation
```python
# Use Pydantic models
class UserProfileRequest(BaseModel):
    role: str  # Required
    experience: int = Field(ge=0, le=60)  # Validated range
    skills: List[str] = Field(min_items=1)  # Min 1 skill
```

### Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/send-email")
@limiter.limit("5/minute")
async def send_email(...):
    # Max 5 emails per minute per IP
```

### Environment Secrets
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str  # Never commit this
    gmail_secret: str    # Use environment variables
    
    class Config:
        env_file = ".env"
```

## 🚀 Performance Optimizations

### Caching Company Data
```python
# Cache research results to avoid re-scraping
@functools.lru_cache(maxsize=1000)
async def get_company_research(company_name: str):
    return await research_service.extract_company_info(...)
```

### Batch Processing
```python
# Process multiple companies in parallel
tasks = [
    research_agent.run(company)
    for company in companies
]
results = await asyncio.gather(*tasks)
```

### Database Indexing
```python
# Create indexes for fast queries
await db.companies.create_index("name")
await db.email_logs.create_index("user_id")
await db.email_logs.create_index("timestamp")
```

## 📊 Monitoring & Logging

### Application Logging
```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Found {len(companies)} companies")
logger.error(f"Error generating email: {e}")
logger.debug(f"Processing company: {company_name}")
```

### Metrics to Track
- Companies found per search
- Email generation success rate
- Email send success rate
- Average research time
- API response times

## 🔄 Continuous Improvement

### Feedback Loop
```python
# Track which emails get responses
# Use this to improve future prompts
email_reply_rate = successful_replies / total_emails_sent
```

### Agent Refinement
```python
# Update prompts based on performance
# A/B test different email templates
# Monitor LLM token usage and costs
```

## 📚 Testing

### Unit Tests
```python
# Test individual agents
def test_company_finder():
    agent = CompanyFinderAgent(llm)
    state = {
        "user_profile": {...},
        "companies": []
    }
    result = asyncio.run(agent.run(state))
    assert len(result["companies"]) > 0
```

### Integration Tests
```python
# Test full pipeline
async def test_full_workflow():
    result = await agent_graph.invoke(initial_state)
    assert result["companies"] is not None
    assert result["outreach_strategy"] is not None
```

---

This guide provides the architectural foundation for OutreachAI. Customize agents and prompts based on your specific needs!
