"""
Quick test script to validate diagnostic logging is working.
Processes a single lesson plan and checks for diagnostic output.

Usage:
    python test_hyperlink_diagnostics.py
"""

import asyncio
from pathlib import Path
from backend.database import get_db
from backend.llm_service import LLMService
from tools.batch_processor import BatchProcessor
from backend.telemetry import logger


async def test_diagnostics():
    """Test diagnostic logging with a sample lesson plan."""
    
    print("=" * 80)
    print("HYPERLINK DIAGNOSTIC TEST")
    print("=" * 80)
    
    # Get database
    db = get_db()
    
    # Get first user
    users = db.list_users()
    if not users:
        print("\n❌ No users found in database.")
        print("Please create a user first using the frontend.")
        return
    
    user = users[0]
    print(f"\n✓ Using user: {user.name}")
    
    # Get user's slots
    slots = db.get_user_slots(user.id)
    if not slots:
        print(f"\n❌ No slots configured for user {user.name}")
        print("Please configure slots using the frontend.")
        return
    
    slot = slots[0]
    print(f"✓ Using slot: {slot.subject} (Slot {slot.slot_number})")
    
    # Check for input file
    primary_file = getattr(slot, 'primary_teacher_file', None)
    if not primary_file or not Path(primary_file).exists():
        print(f"\n❌ Primary teacher file not found: {primary_file}")
        print("Please ensure the file path is correct in the slot configuration.")
        return
    
    print(f"✓ Input file: {Path(primary_file).name}")
    
    # Initialize LLM service
    try:
        llm_service = LLMService()
        print("✓ LLM service initialized")
    except Exception as e:
        print(f"\n❌ Failed to initialize LLM service: {e}")
        print("Please check your API keys in .env file.")
        return
    
    # Initialize batch processor
    processor = BatchProcessor(llm_service)
    print("✓ Batch processor initialized")
    
    # Process the slot
    print(f"\n{'='*80}")
    print("PROCESSING LESSON PLAN")
    print(f"{'='*80}\n")
    
    try:
        result = await processor.process_user_week(
            user_id=user.id,
            week_of="10/21-10/25",  # Sample week
            provider="openai",
            slot_ids=[slot.id]  # Process only this slot
        )
        
        print(f"\n{'='*80}")
        print("PROCESSING COMPLETE")
        print(f"{'='*80}")
        
        if result['success']:
            print(f"\n✓ Success!")
            print(f"  Output file: {result['output_file']}")
            print(f"  Processed slots: {result['processed_slots']}")
            print(f"  Total time: {result['total_time_ms']:.0f}ms")
            
            print(f"\n{'='*80}")
            print("DIAGNOSTIC DATA")
            print(f"{'='*80}")
            print("\nCheck the log file for diagnostic output:")
            print("  backend/logs/app.log")
            print("\nRun analysis:")
            print("  python tools/analyze_hyperlink_diagnostics.py backend/logs/app.log")
            
        else:
            print(f"\n❌ Processing failed")
            if result.get('errors'):
                for error in result['errors']:
                    print(f"  - {error}")
    
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("\nThis script will process one lesson plan to test diagnostic logging.")
    print("Make sure you have:")
    print("  1. At least one user configured")
    print("  2. At least one slot with a valid input file")
    print("  3. API keys configured in .env")
    
    response = input("\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        exit(0)
    
    asyncio.run(test_diagnostics())
