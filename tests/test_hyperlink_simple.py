"""
Simple standalone test for hyperlink diagnostics.
Processes one file directly without needing the full app.
"""

import asyncio
from pathlib import Path
from backend.database import get_db
from backend.llm_service import LLMService
from tools.batch_processor import BatchProcessor


async def simple_test():
    """Process one lesson plan directly."""
    
    print("=" * 80)
    print("SIMPLE HYPERLINK DIAGNOSTIC TEST")
    print("=" * 80)
    
    # Get database
    db = get_db()
    
    # Get users and slots
    users = db.list_users()
    if not users:
        print("\n❌ No users in database.")
        print("\nTo create a test user:")
        print("  1. Start backend: python -m uvicorn backend.api:app --port 8000")
        print("  2. Start frontend: cd frontend && npm run tauri dev")
        print("  3. Create user and slot through UI")
        return
    
    # Find a user with slots
    user = None
    slots = []
    for u in users:
        slots = db.get_user_slots(u['id'])
        if slots:
            user = u
            break
    
    if not user or not slots:
        print(f"\n❌ No users with configured slots found.")
        print(f"   Found {len(users)} users but none have slots configured.")
        print("\nTo configure slots:")
        print("  1. Start the app")
        print("  2. Go to user settings")
        print("  3. Add at least one slot with a primary teacher file")
        return
    
    print(f"\n✓ Using user: {user['name']}")
    print(f"✓ Found {len(slots)} slots")
    
    # Use first slot
    slot = slots[0]
    print(f"✓ Using slot: {slot['subject']} (Slot {slot['slot_number']})")
    
    # Check if file exists
    primary_file = slot.get('primary_teacher_file')
    if not primary_file:
        print(f"\n❌ Slot has no primary_teacher_file configured")
        return
    
    if not Path(primary_file).exists():
        print(f"\n❌ File not found: {primary_file}")
        print("\nPlease update the slot configuration with a valid file path.")
        return
    
    print(f"✓ Input file: {Path(primary_file).name}")
    
    # Initialize LLM service
    try:
        llm_service = LLMService()
        print("✓ LLM service initialized")
    except Exception as e:
        print(f"\n❌ Failed to initialize LLM service: {e}")
        print("\nCheck your .env file for API keys:")
        print("  OPENAI_API_KEY=your_key_here")
        return
    
    # Process
    print(f"\n{'='*80}")
    print("PROCESSING...")
    print(f"{'='*80}\n")
    
    processor = BatchProcessor(llm_service)
    
    try:
        result = await processor.process_user_week(
            user_id=user['id'],
            week_of="10/21-10/25",
            provider="openai",
            slot_ids=[slot['id']]
        )
        
        print(f"\n{'='*80}")
        print("RESULT")
        print(f"{'='*80}")
        
        if result['success']:
            print(f"\n✓ SUCCESS!")
            print(f"  Output: {result['output_file']}")
            print(f"  Time: {result['total_time_ms']:.0f}ms")
            
            print(f"\n{'='*80}")
            print("NEXT STEPS")
            print(f"{'='*80}")
            print("\n1. Analyze diagnostics:")
            print("   python tools/analyze_hyperlink_diagnostics.py backend_debug.log")
            print("\n2. Check output file for hyperlink placement")
            print(f"   {result['output_file']}")
            
        else:
            print(f"\n❌ FAILED")
            if result.get('errors'):
                for error in result['errors']:
                    print(f"  - {error}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(simple_test())
