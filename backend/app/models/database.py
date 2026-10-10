import logging
from typing import Optional

from fastapi import HTTPException
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.config import settings

logger = logging.getLogger(__name__)

mongodb_client: Optional[AsyncMongoClient] = None
db: Optional[AsyncDatabase] = None
database_error: Optional[str] = None


async def connect_to_mongo() -> bool:
    """Connect to MongoDB without preventing the health endpoint from starting."""
    global mongodb_client, db, database_error
    try:
        mongodb_client = AsyncMongoClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
        )
        await mongodb_client.admin.command("ping")
        db = mongodb_client[settings.database_name]
        await create_indexes()
        database_error = None
        logger.info("MongoDB: connected to %s", settings.database_name)
        return True
    except Exception as exc:
        database_error = str(exc)
        db = None
        if mongodb_client is not None:
            await mongodb_client.close()
            mongodb_client = None
        logger.error("MongoDB unavailable: %s", database_error)
        return False


async def close_mongo_connection():
    """Close MongoDB connection"""
    global mongodb_client, db
    if mongodb_client is not None:
        await mongodb_client.close()
        mongodb_client = None
        db = None
        logger.info("Disconnected from MongoDB")


async def create_indexes():
    """Create database indexes"""
    if db is None:
        return

    # User email index
    await db.users.create_index("email", unique=True)
    
    # Company name index
    await db.companies.create_index("name")
    await db.companies.create_index("website")
    
    # Email log indexes
    await db.email_logs.create_index("user_id")
    await db.email_logs.create_index("timestamp")
    
    # OAuth tokens index
    await db.oauth_tokens.create_index("user_id", unique=True)

    # Personal LinkedIn application assistant indexes
    await db.linkedin_profiles.create_index("profile_key", unique=True)
    await db.linkedin_applications.create_index("updated_at")
    await db.linkedin_applications.create_index("linkedin_url", unique=True)


def get_database() -> AsyncDatabase:
    """Get database instance"""
    if db is None:
        raise HTTPException(
            status_code=503,
            detail=f"MongoDB is unavailable: {database_error or 'not connected'}",
        )
    return db


async def database_status() -> dict:
    """Return a live MongoDB health result."""
    if mongodb_client is None or db is None:
        return {"status": "error", "detail": database_error or "Not connected"}
    try:
        await mongodb_client.admin.command("ping")
        return {"status": "ok", "detail": f"Connected to {settings.database_name}"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
