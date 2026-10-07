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
from app.models.database import connect_to_mongo, get_database


async def test_mongodb_connection():
    """Test MongoDB connection"""
    print("Testing MongoDB connection...")
    try:
        await connect_to_mongo()
        db = get_database()
        
        # Test ping
        ping_result = await db.command("ping")
        if ping_result.get("ok") == 1:
            print("✅ MongoDB connection successful")
            return True
        else:
            print("❌ MongoDB ping failed")
            return False
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False


def test_openai_config():
    """Test OpenAI configuration"""
    print("Testing OpenAI configuration...")
    if settings.openai_api_key and settings.openai_api_key.startswith("sk-"):
        print("✅ OpenAI API key configured")
        return True
    else:
        print("❌ OpenAI API key not configured")
        return False


async def main():
    """Run all tests"""
    print("\n🧪 OutreachAI Backend Tests\n")
    
    results = []
    
    # Test configs
    results.append(("OpenAI Configuration", test_openai_config()))
    
    # Test database
    results.append(("MongoDB Connection", await test_mongodb_connection()))
    
    # Print summary
    print("\n" + "="*40)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"Tests: {passed}/{total} passed\n")
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print("="*40 + "\n")
    
    if passed == total:
        print("🎉 All tests passed! Ready to run OutreachAI\n")
    else:
        print("⚠️  Fix the failing tests before running\n")


if __name__ == "__main__":
    asyncio.run(main())
