# OutreachAI - AI-Powered Cold Email Outreach Platform

**OutreachAI** is an intelligent, multi-agent system that helps professionals discover companies and generate personalized cold emails using cutting-edge AI technologies.

## 🎯 Key Features

- **AI-Powered Company Discovery**: Find relevant companies hiring similar roles
- **Intelligent Classification**: Automatically classify companies as actively hiring or strategic targets
- **Company Research**: Deep dive into company information and hiring signals
- **Personalized Email Generation**: Create compelling cold emails tailored to each company
- **Gmail Integration**: Send emails directly via Gmail API
- **Activity Tracking**: Monitor all your outreach activities

## 🏗️ Architecture

### Tech Stack

**Backend:**
- Python 3.10+
- FastAPI - Modern web framework
- LangChain - LLM interactions
- LangGraph - Multi-agent orchestration
- Motor - Async MongoDB driver
- Gmail API - Email integration

**Frontend:**
- Next.js 14 - React framework
- TypeScript - Type safety
- Tailwind CSS - Styling
- Zustand - State management
- Axios - HTTP client

**Database:**
- MongoDB - Document storage

**AI/LLM:**
- Google Gemini

### Multi-Agent System (LangGraph)

```
User Input
    ↓
Company Finder Agent → Finds 10+ relevant companies
    ↓
Hiring Classifier Agent → Classifies as Active/Inactive
    ↓
Company Research Agent → Extracts company info
    ↓
Outreach Strategy Agent → Decides contact method
    ↓
Email Generator Agent → Creates personalized emails
    ↓
Output: Ready-to-send emails
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB (local or Atlas)
- OpenAI API Key
- Gmail API Credentials

### Backend Setup

1. **Navigate to backend folder:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows
   # or
   source venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Start MongoDB:**
   ```bash
   # Local MongoDB
   mongod
   # or use MongoDB Atlas connection string in .env
   ```

6. **Run backend:**
   ```bash
   python main.py
   # or
   uvicorn app.main:app --reload
   ```

Backend will be available at: `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend folder:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment:**
   ```bash
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local
   ```

4. **Run development server:**
   ```bash
   npm run dev
   ```

Frontend will be available at: `http://localhost:3000`

## 📚 API Endpoints

### Companies

**POST /api/generate-companies**
- Generate company suggestions based on user profile
- Input: User profile (role, skills, experience, location)
- Output: List of companies (actively hiring + strategic targets)

**Request:**
```json
{
  "role": "Senior Software Engineer",
  "experience": 5,
  "skills": ["Python", "React", "FastAPI"],
  "location": "San Francisco, US",
  "salary": 180000,
  "num_companies": 10
}
```

**Response:**
```json
{
  "total": 10,
  "actively_hiring": [...],
  "strategic_targets": [...]
}
```

### Emails

**POST /api/generate-email**
- Generate personalized cold email
- Input: Company info + user profile
- Output: Email subject & body

**POST /api/send-email**
- Send email via Gmail
- Requires Gmail OAuth authentication
- Logs email in activity

**GET /api/activity**
- Get user's email activity log
- Query param: `user_id`
- Returns: List of sent emails with status

## 📊 Data Models

### User
```
{
  _id: ObjectId,
  email: String (unique),
  name: String,
  role: String,
  experience: Integer,
  skills: [String],
  location: String,
  salary: Integer,
  preferences: Object,
  gmail_credentials: Object,
  created_at: DateTime,
  updated_at: DateTime
}
```

### Company
```
{
  _id: ObjectId,
  name: String,
  website: String,
  hiring_signal: String (active/inactive/unknown),
  summary: String,
  domain: String,
  relevance_score: Float,
  tech_signals: [String],
  outreach_method: String (email/linkedin/apply),
  outreach_instructions: String,
  tags: [String],
  source: String,
  last_checked: DateTime,
  created_at: DateTime,
  updated_at: DateTime
}
```

### EmailLog
```
{
  _id: ObjectId,
  user_id: ObjectId,
  company_id: ObjectId,
  company_name: String,
  recipient_email: String,
  subject: String,
  body: String,
  status: String (drafted/sent/failed),
  error_message: String,
  opened: Boolean,
  clicked: Boolean,
  replied: Boolean,
  created_at: DateTime,
  sent_at: DateTime
}
```

## 🔧 Configuration

### Environment Variables

**Backend (.env):**
```
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=outreach_ai
GEMINI_API_KEY=your_gemini_key
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
SERPAPI_API_KEY=...
DEBUG=True
```

**Frontend (.env.local):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## 🧠 LangGraph Agents

### 1. Company Finder Agent
- Uses Google Gemini to suggest relevant companies
- Considers role, skills, experience, location
- Finds both actively hiring and strategic targets

### 2. Hiring Classifier Agent
- Analyzes hiring signals
- Classification rules:
  - Job posts within 14 days → "active"
  - Else → "inactive"

### 3. Company Research Agent
- Scrapes company websites
- Extracts company information
- Checks for hiring signals (careers page, job posts)
- Summarizes findings with LLM

### 4. Outreach Strategy Agent
- Decides best contact method:
  - "email" - Direct email or support
  - "linkedin" - LinkedIn search
  - "apply" - Career page application

### 5. Email Generator Agent
- Creates personalized cold emails
- Incorporates:
  - Company info
  - User skills alignment
  - Company domain/focus
- Keeps emails under 120 words

## 🔒 Security Considerations

- ✅ OAuth 2.0 for Gmail authentication
- ✅ No private data scraping (public info only)
- ✅ Rate limiting for email sends
- ✅ Environment variables for secrets
- ✅ MongoDB indexes for performance
- ⚠️ Implement CORS properly in production
- ⚠️ Add authentication/authorization
- ⚠️ Validate all user inputs

## 📈 Scaling Considerations

- Async email sending with task queue (Celery/RQ)
- Caching for company research data
- Batch processing for multiple users
- Redis for rate limiting
- Database sharding for large scale

## 🐛 Development & Debugging

### Check Backend Health
```bash
curl http://localhost:8000/health
```

### Check API Docs
```
http://localhost:8000/docs
```

### MongoDB Shell
```bash
mongosh
use outreach_ai
db.companies.find()
```

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit PR with clear description

## 📝 License

This project is open source and available under the MIT License.

## 🎓 Learning Resources

- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://langgraph.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)
- [MongoDB Documentation](https://docs.mongodb.com/)

## 🤔 FAQ

**Q: Can I use different LLMs?**
A: Yes, LangChain supports OpenAI, Claude, Ollama, etc.

**Q: How is data privacy handled?**
A: We use public information only. No scraping of private data.

**Q: Can I customize company search criteria?**
A: Yes, modify the CompanyFinderAgent prompt and search logic.

**Q: How do I rate limit email sends?**
A: Implement Redis-based rate limiting in the email sender.

## 📞 Support

For issues, questions, or feature requests, please open an GitHub issue.

---

**Happy Outreaching! 🚀**
