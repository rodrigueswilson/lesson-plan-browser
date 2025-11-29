"""
Test to reproduce the processing crash.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.database import Database
from backend.config import settings
from tools.batch_processor import BatchProcessor
from backend.llm_service import get_llm_service

async def test_processing():
    """Test the processing that's crashing."""
    
    print("=" * 80)
    print("TESTING PROCESSING CRASH")
    print("=" * 80)
    
    try:
        # Initialize database
        print("\n1. Initializing database...")
        db = Database()
        print(f"   Database path: {db.db_path}")
        print(f"   Database exists: {db.db_path.exists()}")
        
        # Get a user (hardcode a known user ID)
        print("\n2. Getting user...")
        user_id = "04fe8898-cb89-4a73-affb-64a97a98f820"  # From logs
        user = db.get_user(user_id)
        if not user:
            print("   ❌ User not found")
            return
        
        print(f"   ✓ User: {user['name']} ({user['id']})")
        
        # Get slots
        print("\n3. Getting slots...")
        slots = db.get_user_slots(user['id'])
        print(f"   ✓ Found {len(slots)} slots")
        
        # Try to create a plan (this is where it might crash)
        print("\n4. Creating weekly plan record...")
        try:
            plan_id = db.create_weekly_plan(
                user_id=user['id'],
                week_of="10/21-10/25",
                output_file="",
                week_folder_path="test_path",
                consolidated=False,
                total_slots=1
            )
            print(f"   ✓ Plan created: {plan_id}")
        except Exception as e:
            print(f"   ❌ CRASH HERE: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Try to get LLM service
        print("\n5. Getting LLM service...")
        try:
            llm_service = get_llm_service()
            print(f"   ✓ LLM service: {llm_service}")
        except Exception as e:
            print(f"   ❌ LLM service error: {e}")
            # This is OK, we can use mock
        
        # Try to create processor
        print("\n6. Creating batch processor...")
        try:
            processor = BatchProcessor(llm_service if 'llm_service' in locals() else None)
            print(f"   ✓ Processor created")
        except Exception as e:
            print(f"   ❌ Processor error: {e}")
            import traceback
            traceback.print_exc()
            return
        
        print("\n" + "=" * 80)
        print("✓ All initialization steps passed!")
        print("The crash must be happening during actual processing.")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_processing())
