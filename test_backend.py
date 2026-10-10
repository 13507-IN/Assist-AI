"""
Simple test to verify backend setup
Run with: python test_backend.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.config import settings
from app.models.database import close_mongo_connection, connect_to_mongo, get_database


async def test_mongodb_connection():
    """Test MongoDB connection"""
    print("Testing MongoDB connection...")
    try:
        connected = await connect_to_mongo()
        if not connected:
            return False
        db = get_database()
        
        # Test ping
        ping_result = await db.command("ping")
        if ping_result.get("ok") == 1:
            print("[OK] MongoDB connection successful")
            return True
        else:
            print("[FAIL] MongoDB ping failed")
            return False
    except Exception as e:
        print(f"[FAIL] MongoDB connection failed: {e}")
        return False


def test_gemini_config():
    """Test Gemini configuration"""
    print("Testing Gemini configuration...")
    if settings.gemini_api_key and not settings.gemini_api_key.startswith("your_"):
        print(f"[OK] Gemini configured with {settings.gemini_model}")
        return True
    else:
        print("[FAIL] GEMINI_API_KEY is missing from backend/.env")
        return False


def test_gmail_config():
    """Test Gmail OAuth configuration"""
    print("Testing Gmail OAuth configuration...")
    if settings.gmail_client_id and settings.gmail_client_secret:
        print(f"[OK] Gmail OAuth configured for {settings.gmail_redirect_uri}")
        return True
    print("[FAIL] GMAIL_CLIENT_ID/GMAIL_CLIENT_SECRET are missing from backend/.env")
    return False


async def main():
    """Run all tests"""
    print("\nOutreachAI Backend Tests\n")
    
    results = []
    
    # Test configs
    results.append(("Gemini Configuration", test_gemini_config()))
    results.append(("Gmail Configuration", test_gmail_config()))
    
    # Test database
    results.append(("MongoDB Connection", await test_mongodb_connection()))
    await close_mongo_connection()
    
    # Print summary
    print("\n" + "="*40)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Tests: {passed}/{total} passed\n")
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {test_name}: {status}")
    
    print("="*40 + "\n")
    
    if passed == total:
        print("All tests passed. Ready to run OutreachAI.\n")
    else:
        print("Configure the failing integrations before running the full flow.\n")


if __name__ == "__main__":
    asyncio.run(main())
