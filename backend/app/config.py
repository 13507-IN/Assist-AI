from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "outreach_ai"
    
    # Google Gemini
    gemini_api_key: str = ""
    
    # Gmail API
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_redirect_uri: str = "http://localhost:8000/api/auth/gmail/callback"
    
    # Search APIs
    serpapi_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    
    # App settings
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
