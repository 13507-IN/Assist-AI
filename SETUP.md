# OutreachAI - Setup & Installation Guide

## 📋 Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB (local or Atlas)
- Git
- Google Gemini API Key
- Gmail API Credentials (optional, for email sending)

## 🚀 Installation Steps

### Option 1: Local Development (Recommended for Development)

#### Backend Setup

1. **Clone/Navigate to project:**
   ```bash
   cd Cold_Mail/backend
   ```

2. **Create Python virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables:**
   ```bash
   cp .env.example .env
   ```

5. **Edit `.env` file with your credentials:**
   ```
   MONGODB_URI=mongodb://localhost:27017
   OPENAI_API_KEY=sk-your-key-here
   ```

6. **Ensure MongoDB is running:**
   ```bash
   # If using local MongoDB
   mongod
   
   # Or update MONGODB_URI to use MongoDB Atlas
   ```

7. **Start the backend server:**
   ```bash
   python main.py
   # or
   uvicorn app.main:app --reload
   ```

   ✅ Backend will be available at `http://localhost:8000`

#### Frontend Setup

1. **In a new terminal, navigate to frontend:**
   ```bash
   cd Cold_Mail/frontend
   ```

2. **Install Node dependencies:**
   ```bash
   npm install
   ```

3. **Create `.env.local`:**
   ```bash
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local
   ```

4. **Start development server:**
   ```bash
   npm run dev
   ```

   ✅ Frontend will be available at `http://localhost:3000`

### Option 2: Docker Setup (Production-like)

1. **Ensure Docker and Docker Compose are installed**

2. **From project root, create `.env` file:**
   ```bash
   cp backend/.env.example .env
   ```

3. **Update `.env` with your OpenAI API key:**
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```

4. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

   ✅ Services will be available at:
   - Frontend: `http://localhost:3000`
   - Backend: `http://localhost:8000`
   - MongoDB: `localhost:27017`

## 🔧 Configuration

### Google Gemini API Key

1. Get your key from https://ai.google.dev/
2. Add to `.env` file:
   ```
   GEMINI_API_KEY=your_key_here
   ```

### Gmail API Setup (Optional for Sending)

1. Create a Google Cloud project: https://console.cloud.google.com
2. Enable Gmail API
3. Create OAuth 2.0 credentials
4. Add to `.env`:
   ```
   GMAIL_CLIENT_ID=...
   GMAIL_CLIENT_SECRET=...
   ```

### MongoDB Setup

**Option A: Local MongoDB**
```bash
# Install MongoDB from https://www.mongodb.com/try/download/community
# Run MongoDB
mongod
```

**Option B: MongoDB Atlas (Cloud)**
1. Create account at https://www.mongodb.com/cloud/atlas
2. Create a cluster
3. Get connection string
4. Update `.env`:
   ```
   MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority
   ```

## ✅ Verify Installation

### Check Backend Health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","service":"OutreachAI Backend"}
```

### Access API Documentation
Visit: `http://localhost:8000/docs`

### Check Frontend
Visit: `http://localhost:3000`

You should see the OutreachAI dashboard.

## 📊 Test the Application

1. **Open frontend:** `http://localhost:3000`
2. **Fill in user profile:**
   - Role: "Senior Software Engineer"
   - Experience: 5
   - Skills: "Python, React, FastAPI"
   - Location: "San Francisco, US"
3. **Click "Discover Companies"**
4. **View results and generate emails**

## 🐛 Troubleshooting

### MongoDB Connection Error
```
Error: connect ECONNREFUSED 127.0.0.1:27017
```
**Solution:** Make sure MongoDB is running:
```bash
mongod
```

### OpenAI API Error
```
Error: Invalid API key provided
```
**Solution:** Verify your API key in `.env`:
```bash
OPENAI_API_KEY=sk-... # Check it's correct
```

### Port Already in Use
```
Error: Address already in use :::8000
```
**Solution:** Kill the process on that port:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

### CORS Issues
If frontend can't reach backend:
1. Check `NEXT_PUBLIC_API_URL` in frontend `.env.local`
2. Make sure backend is running
3. Check CORS middleware in `app/main.py`

## 📦 Project Structure

```
Cold_Mail/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph agents
│   │   ├── models/          # MongoDB models
│   │   ├── services/        # Business logic
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── utils/           # Utilities
│   │   ├── main.py          # FastAPI app
│   │   └── config.py        # Configuration
│   ├── requirements.txt      # Python dependencies
│   ├── .env.example          # Example env
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── components/      # React components
│   │   ├── services/        # API client
│   │   ├── store/           # Zustand store
│   │   ├── types/           # TypeScript types
│   │   └── globals.css      # Tailwind CSS
│   ├── package.json
│   ├── tsconfig.json
│   └── Dockerfile
│
├── docker-compose.yml
├── README.md
└── SETUP.md
```

## 🚀 Next Steps

1. **Customize agents** - Modify prompts in `app/agents/outreach_graph.py`
2. **Add authentication** - Implement user auth with JWT
3. **Add email validation** - Verify email addresses before sending
4. **Setup rate limiting** - Implement Redis-based rate limits
5. **Deploy** - Deploy to Heroku, Vercel, or AWS

## 📚 Resources

- [LangChain Docs](https://python.langchain.com/)
- [LangGraph Docs](https://langgraph.dev/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [MongoDB Docs](https://docs.mongodb.com/)

## 💡 Tips

- Use `DEBUG=True` in `.env` for development
- Check API docs at `http://localhost:8000/docs`
- Monitor backend logs for errors
- Use MongoDB Compass GUI for database inspection
- Test agents individually before full pipeline

---

**Ready to launch? Start with Option 1 for quick development setup!** 🎉
