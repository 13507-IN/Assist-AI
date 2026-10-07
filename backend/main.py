"""
OutreachAI Backend

Multi-agent system for company discovery and cold email generation using:
- LangChain for LLM interactions
- LangGraph for agent orchestration
- FastAPI for REST API
- MongoDB for data persistence
- Gmail API for email sending
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
