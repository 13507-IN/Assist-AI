# OutreachAI - Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Dashboard         Results Page      Email Modal   Activity Log  │
│  (User Input)      (Companies)       (Compose)     (Tracking)   │
│                                                                   │
│  ↓ Zustand Store (State Management)                              │
│                                                                   │
│  ↓ API Client (Axios)                                            │
└─────────────────────────────────────────────────────────────────┘
                            ↓ HTTP
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Routes:                                                          │
│  ├─ POST /api/generate-companies                                 │
│  ├─ POST /api/generate-email                                     │
│  ├─ POST /api/send-email                                         │
│  └─ GET  /api/activity                                           │
│                                                                   │
│  ↓                                                                │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │        LangGraph - Multi-Agent Orchestration              │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │                                                             │  │
│  │  [Company Finder] → [Hiring Classifier] → [Researcher]   │  │
│  │       ↓                  ↓                    ↓            │  │
│  │    Find companies    Classify active      Extract info    │  │
│  │                                                             │  │
│  │  [Outreach Strategy] → [Email Generator]                 │  │
│  │       ↓                    ↓                              │  │
│  │   Decide method        Create email                       │  │
│  │                                                             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ↓                                                                │
│                                                                   │
│  Services:                                                        │
│  ├─ CompanyResearchService (Web scraping, HTML parsing)          │
│  ├─ EmailGenerationService (LLM + Prompt Engineering)            │
│  └─ GmailService (OAuth, email sending)                          │
│                                                                   │
│  ↓                                                                │
│                                                                   │
│  LangChain / OpenAI GPT-4                                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
         ↓                           ↓
  ┌────────────────────────┐  ┌──────────────────────┐
  │     MongoDB            │  │   Gmail API          │
  │ (Companies, Emails,    │  │ (Send Emails,        │
  │  Users, Email Logs)    │  │  OAuth2)             │
  └────────────────────────┘  └──────────────────────┘
```

## Data Flow - Company Discovery

```
1. User Input (Dashboard)
   ↓
   {
     "role": "Senior Software Engineer",
     "experience": 5,
     "skills": ["Python", "React", "FastAPI"],
     "location": "San Francisco",
     "num_companies": 10
   }
   
   ↓ POST /api/generate-companies
   
2. Backend Processing (LangGraph)
   ├─ Company Finder Agent
   │  ├─ Input: user profile
   │  ├─ LLM Prompt: "Find 10 companies hiring {role}s"
   │  └─ Output: List of companies
   │
   ├─ Hiring Classifier Agent
   │  ├─ Input: Company list
   │  ├─ Logic: "active hiring" vs "not hiring"
   │  └─ Output: Classified companies
   │
   ├─ Company Research Agent
   │  ├─ For each company:
   │  │  ├─ Scrape website
   │  │  ├─ Check careers page
   │  │  └─ Extract info
   │  └─ Output: Research data
   │
   ├─ Outreach Strategy Agent
   │  ├─ Input: Company info
   │  ├─ Decide: email vs linkedin vs apply
   │  └─ Output: Contact method
   │
   └─ Store in MongoDB
   
   ↓
   
3. Response to Frontend
   {
     "total": 10,
     "actively_hiring": [
       {
         "id": "1",
         "name": "Anthropic",
         "hiring_signal": "active",
         "relevance_score": 0.95,
         "summary": "AI safety company...",
         ...
       }
     ],
     "strategic_targets": [...]
   }
   
   ↓ Display in Results Page
   
4. User Interaction
   ├─ Click "Generate Email" on company card
   │  ↓ POST /api/generate-email
   │  ├─ LLM: "Write personalized email"
   │  └─ Response: Subject + Body
   │
   └─ Click "Send Email"
      ↓ POST /api/send-email
      ├─ Gmail OAuth
      ├─ Send email
      └─ Log in database
```

## Component Hierarchy - Frontend

```
app/layout.tsx (Root Layout)
├─ Header
├─ main
│  ├─ page.tsx
│  │  └─ Dashboard
│  │     ├─ Form (User Input)
│  │     ├─ Button (Submit)
│  │     └─ Input (Fields)
│  │
│  ├─ results/page.tsx
│  │  └─ ResultsPage
│  │     ├─ CompanyCard (Actively Hiring)
│  │     ├─ CompanyCard (Strategic Targets)
│  │     └─ EmailModal
│  │        ├─ Email Preview
│  │        ├─ Generate Button
│  │        └─ Send Button
│  │
│  └─ activity/page.tsx
│     └─ ActivityLog
│        └─ EmailLogItem[]
│
└─ Footer
```

## Database Schema - MongoDB

```
outreach_ai (Database)
├─ users
│  ├─ _id: ObjectId
│  ├─ email: String (unique)
│  ├─ name: String
│  ├─ role: String
│  ├─ experience: Integer
│  ├─ skills: Array
│  ├─ location: String
│  ├─ salary: Integer
│  └─ gmail_credentials: Object
│
├─ companies
│  ├─ _id: ObjectId
│  ├─ name: String
│  ├─ website: String
│  ├─ hiring_signal: String
│  ├─ summary: String
│  ├─ relevance_score: Float
│  └─ outreach_method: String
│
├─ email_logs
│  ├─ _id: ObjectId
│  ├─ user_id: ObjectId (ref: users)
│  ├─ company_id: ObjectId (ref: companies)
│  ├─ subject: String
│  ├─ body: String
│  ├─ status: String
│  ├─ created_at: DateTime
│  └─ sent_at: DateTime
│
└─ oauth_tokens
   ├─ _id: ObjectId
   ├─ user_id: ObjectId (ref: users)
   ├─ service: String (gmail)
   ├─ access_token: String
   ├─ refresh_token: String
   └─ expires_at: DateTime
```

## Request-Response Flow - Email Generation

```
Frontend                Backend                 LLM
   │                      │                      │
   ├──POST /generate──→    │                      │
   │   company_id          ├──Research Data──→    │
   │   user_skills         │                      │
   │                       ├──Prompt──────────→   │
   │                       │  "Write email for    │
   │                       │   {company} from    │
   │                       │   {user_skills}"    │
   │                       │                      │
   │                       ←──Response────────────┤
   │                       │  {                  │
   │                       │   "subject": "...", │
   │                       │   "body": "..."     │
   │                       │  }                  │
   │     ←──Response────────                      │
   │       {subject,body}  │                      │
   │                       │                      │
   Display email           │                      │
   for editing             │                      │
        │                  │                      │
   ├──POST /send-email───→ ├──Gmail API──────→   │
   │   recipient_email     │  Send email         │
   │   subject             │                      │
   │   body                │                      │
   │                       │                      │
   │                       ├──Store in DB        │
   │                       │                      │
   │     ←──Success────────                      │
   │       {message_id}    │                      │
   │                       │                      │
   Show success message    │                      │
```

## Agent State Transitions

```
START
  │
  ├─ company_finder.run(state)
  │  Input:  user_profile
  │  Output: state["companies"] = [...]
  │
  ├─ hiring_classifier.run(state)
  │  Input:  state["companies"]
  │  Output: state["companies"] updated with classification
  │
  ├─ research_agent.run(state)
  │  Input:  state["companies"][0]
  │  Output: state["research_data"] = {...}
  │
  ├─ strategy_agent.run(state)
  │  Input:  state["research_data"]
  │  Output: state["outreach_strategy"] = {...}
  │
  END
  
Result: Ready for email generation and sending
```

---

This architecture ensures:
- **Scalability**: Async operations, MongoDB for horizontal scaling
- **Maintainability**: Clear separation of concerns (agents, services, models)
- **Extensibility**: Easy to add new agents or integrate new APIs
- **Reliability**: Error handling, logging, monitoring
