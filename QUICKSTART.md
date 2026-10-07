"""
OutreachAI - Quick Start Guide

This file contains copy-paste commands to get started quickly.
"""

# ============================================
# QUICK START - LOCAL DEVELOPMENT
# ============================================

"""
STEP 1: Backend Setup

# From project root
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env

# Edit .env and add your Gemini API key
GEMINI_API_KEY=your_gemini_key

# Make sure MongoDB is running
# Then start backend
python main.py
"""

"""
STEP 2: Frontend Setup (in new terminal)

cd frontend

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local

# Start frontend
npm run dev
"""

"""
STEP 3: Test the Application

1. Open http://localhost:3000
2. Fill in your profile:
   - Role: Senior Software Engineer
   - Experience: 5
   - Skills: Python, React, FastAPI
   - Location: San Francisco, US
   - Companies to find: 10
3. Click "Discover Companies"
4. View results and generate emails
"""

# ============================================
# DOCKER SETUP
# ============================================

"""
DOCKER QUICK START

# From project root
cp backend/.env.example .env

# Update .env with your OpenAI key
OPENAI_API_KEY=sk-...

# Build and run
docker-compose up --build

# Access:
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
# MongoDB: localhost:27017
"""

# ============================================
# USEFUL COMMANDS
# ============================================

"""
# Check backend health
curl http://localhost:8000/health

# View API documentation
# Open: http://localhost:8000/docs

# Access MongoDB
mongosh localhost:27017

# Check database
use outreach_ai
db.companies.find()
db.email_logs.find()

# Run backend tests
pytest app/

# Lint backend
flake8 app/

# Format backend
black app/

# Type check backend
mypy app/

# Run frontend in production mode
npm run build
npm start

# Lint frontend
npm run lint

# Run frontend tests
npm test
"""

# ============================================
# TROUBLESHOOTING
# ============================================

"""
ISSUE: MongoDB connection error
SOLUTION: Make sure MongoDB is running
$ mongod

ISSUE: Gemini API error
SOLUTION: Check your API key in .env
GEMINI_API_KEY=... (should be a valid Gemini key)

ISSUE: Port already in use (port 8000)
SOLUTION:
$ netstat -ano | findstr :8000  (Windows)
$ kill -9 <PID>

ISSUE: CORS error from frontend
SOLUTION: Check .env.local has correct API_URL
NEXT_PUBLIC_API_URL=http://localhost:8000/api

ISSUE: npm module not found
SOLUTION: Reinstall node_modules
$ rm -rf node_modules package-lock.json
$ npm install
"""

# ============================================
# CUSTOMIZATION
# ============================================

"""
CUSTOMIZE AGENT PROMPTS

File: backend/app/agents/outreach_graph.py

# Company Finder Agent
- Modify _create_company_prompt() method
- Change what companies are found

# Email Generator
- Modify _create_email_prompt() method
- Change email tone/length/style

# Research Agent
- Modify scraping logic
- Add more sources to check
"""

"""
ADD NEW DATABASE MODELS

File: backend/app/models/

1. Create new model class:
   class MyModel:
       def __init__(self, ...): ...
       def to_dict(self): ...

2. Add MongoDB collection creation:
   File: backend/app/models/database.py
   In create_indexes(): 
   await db.my_collection.create_index("field_name")

3. Use in API endpoints:
   db = get_database()
   result = await db.my_collection.insert_one({...})
"""

"""
EXTEND FRONTEND COMPONENTS

File: frontend/src/components/

1. Create new component:
   export const MyComponent: React.FC = () => {
       return <div>...</div>;
   };

2. Import in page:
   import MyComponent from '@/components/MyComponent';

3. Add to store if needed:
   // frontend/src/store/outreach.ts
   myData: any;
   setMyData: (data: any) => void;
"""

# ============================================
# API USAGE EXAMPLES
# ============================================

"""
GENERATE COMPANIES

POST http://localhost:8000/api/generate-companies
Content-Type: application/json

{
    "role": "Senior Software Engineer",
    "experience": 5,
    "skills": ["Python", "React", "FastAPI"],
    "location": "San Francisco, US",
    "salary": 180000,
    "num_companies": 10
}

Response:
{
    "total": 10,
    "actively_hiring": [
        {
            "id": "1",
            "name": "Anthropic",
            "website": "anthropic.com",
            "hiring_signal": "active",
            ...
        }
    ],
    "strategic_targets": [...]
}
"""

"""
GENERATE EMAIL

POST http://localhost:8000/api/generate-email
Content-Type: application/json

{
    "user_id": "user123",
    "company_id": "comp456",
    "company_name": "Anthropic",
    "company_summary": "AI safety company...",
    "user_role": "Senior Software Engineer",
    "user_skills": ["Python", "React", "FastAPI"]
}

Response:
{
    "subject": "Let's Collaborate on AI Safety",
    "body": "Hi there,\n\n..."
}
"""

"""
SEND EMAIL

POST http://localhost:8000/api/send-email
Content-Type: application/json

{
    "user_id": "user123",
    "recipient_email": "careers@anthropic.com",
    "company_id": "comp456",
    "company_name": "Anthropic",
    "subject": "Let's Collaborate",
    "body": "..."
}

Response:
{
    "success": true,
    "message_id": "gmail_message_123"
}
"""

"""
GET ACTIVITY LOG

GET http://localhost:8000/api/activity?user_id=user123

Response:
{
    "total_emails_sent": 5,
    "emails": [
        {
            "id": "email1",
            "company_name": "Anthropic",
            "recipient_email": "careers@anthropic.com",
            "subject": "...",
            "status": "sent",
            "created_at": "2024-01-15T10:30:00",
            "sent_at": "2024-01-15T10:35:00"
        }
    ]
}
"""

# ============================================
# DEPLOYMENT
# ============================================

"""
DEPLOY TO HEROKU

# Install Heroku CLI
# Log in
heroku login

# Create app
heroku create your-app-name

# Add MongoDB (Atlas)
heroku config:set MONGODB_URI=mongodb+srv://...

# Add OpenAI key
heroku config:set OPENAI_API_KEY=sk-...

# Deploy backend
git push heroku main

# Deploy frontend to Vercel
npm install -g vercel
vercel

# Set NEXT_PUBLIC_API_URL in Vercel dashboard
"""

"""
DEPLOY WITH DOCKER

# Build image
docker build -t outreach-ai-backend ./backend

# Run container
docker run -p 8000:8000 \\
  -e MONGODB_URI=... \\
  -e OPENAI_API_KEY=... \\
  outreach-ai-backend
"""

# ============================================
# NEXT STEPS
# ============================================

"""
1. Add user authentication (JWT)
2. Add email validation with email verification API
3. Implement rate limiting for email sends
4. Add email tracking (opens/clicks)
5. Create follow-up email templates
6. Add analytics dashboard
7. Implement user preferences/settings
8. Add admin panel
9. Setup CI/CD with GitHub Actions
10. Add comprehensive error handling

See IMPLEMENTATION.md for more details!
"""
