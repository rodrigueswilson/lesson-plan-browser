"""
Run actual processing to see the crash error.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.database import Database
from tools.batch_processor import BatchProcessor
from backend.llm_service import get_llm_service

async def test_real_processing():
    """Run actual processing to see what crashes."""
    
    print("=" * 80)
    print("RUNNING ACTUAL PROCESSING")
    print("=" * 80)
    
    try:
        # Initialize
        db = Database()
        llm_service = get_llm_service(provider="openai")
        processor = BatchProcessor(llm_service)
        
        # Use known user
        user_id = "04fe8898-cb89-4a73-affb-64a97a98f820"
        week_of = "10/21-10/25"
        
        print(f"\nProcessing for user: {user_id}")
        print(f"Week: {week_of}")
        print("\nThis will attempt actual processing and show any errors...\n")
        
        # Run the actual processing
        result = await processor.process_user_week(
            user_id=user_id,
            week_of=week_of,
            provider="openai",
            week_folder_path=None,  # Let it auto-detect
            slot_ids=None  # Process all slots
        )
        
        print("\n" + "=" * 80)
        print("RESULT:")
        print("=" * 80)
        print(result)
        
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ CRASH DETECTED:")
        print("=" * 80)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")
        print("\nFull traceback:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_processing())
