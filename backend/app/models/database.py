from motor.motor_asyncio import AsyncClient, AsyncDatabase
from app.config import settings
import logging

logger = logging.getLogger(__name__)

mongodb_client: AsyncClient = None
db: AsyncDatabase = None


async def connect_to_mongo():
    """Connect to MongoDB"""
    global mongodb_client, db
    mongodb_client = AsyncClient(settings.mongodb_uri)
    db = mongodb_client[settings.database_name]
    
    # Create indexes
    await create_indexes()
    logger.info("Connected to MongoDB")


async def close_mongo_connection():
    """Close MongoDB connection"""
    global mongodb_client, db
    if mongodb_client:
        mongodb_client.close()
        logger.info("Disconnected from MongoDB")


async def create_indexes():
    """Create database indexes"""
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
    return db
