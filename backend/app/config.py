from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[1]


def is_configured(value: str) -> bool:
    return bool(value and not value.strip().lower().startswith("your_"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "outreach_ai"
    
    # Google Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    
    # Gmail API
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_redirect_uri: str = "http://localhost:8000/api/auth/gmail/callback"
    frontend_url: str = "http://localhost:3000"
    
    # Search APIs
    serpapi_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    
    # App settings
    debug: bool = True


settings = Settings()
