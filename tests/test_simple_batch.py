"""
Simple batch processor test to debug Day 7 issues.
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.database import get_db
from backend.mock_llm_service import get_mock_llm_service
from tools.batch_processor import BatchProcessor


async def main():
    print("=" * 70)
    print("SIMPLE BATCH PROCESSOR TEST")
    print("=" * 70)
    
    # Initialize
    db = get_db()
    llm_service = get_mock_llm_service()
    processor = BatchProcessor(llm_service)
    
    # Create test user
    print("\n1. Creating test user...")
    user_id = db.create_user("Test User", "test@example.com")
    print(f"   Created user: {user_id}")
    
    # Create single slot with existing file
    print("\n2. Creating test slot...")
    slot_id = db.create_class_slot(
        user_id=user_id,
        slot_number=1,
        subject="Math",
        grade="3",
        homeroom="3-1",
        proficiency_levels='["Entering", "Emerging"]',
        primary_teacher_file="input/primary_math.docx"
    )
    
    # Update with teacher name
    db.update_class_slot(
        slot_id,
        primary_teacher_name="Primary",
        primary_teacher_file_pattern="primary_math.docx"
    )
    print(f"   Created slot: {slot_id}")
    
    # Verify slot
    slot = db.get_slot(slot_id)
    print(f"\n3. Slot configuration:")
    print(f"   Subject: {slot['subject']}")
    print(f"   Grade: {slot['grade']}")
    print(f"   Teacher Name: {slot.get('primary_teacher_name')}")
    print(f"   File Pattern: {slot.get('primary_teacher_file_pattern')}")
    print(f"   File Path: {slot.get('primary_teacher_file')}")
    
    # Check if file exists
    file_path = Path(slot.get('primary_teacher_file', ''))
    print(f"\n4. File check:")
    print(f"   Path: {file_path}")
    print(f"   Exists: {file_path.exists()}")
    
    # Process week
    print("\n5. Processing week...")
    try:
        result = await processor.process_user_week(
            user_id=user_id,
            week_of="10/06-10/10",
            provider="mock"
        )
        
        print(f"\n6. Result:")
        print(f"   Success: {result['success']}")
        print(f"   Processed slots: {result.get('processed_slots', 0)}")
        print(f"   Failed slots: {result.get('failed_slots', 0)}")
        print(f"   Output file: {result.get('output_file')}")
        
        if result.get('errors'):
            print(f"\n   Errors:")
            for error in result['errors']:
                print(f"      - {error}")
        
        if result.get('output_file'):
            output_path = Path(result['output_file'])
            if output_path.exists():
                size_kb = output_path.stat().st_size / 1024
                print(f"\n   Output file size: {size_kb:.1f} KB")
            else:
                print(f"\n   WARNING: Output file not found at {output_path}")
    
    except Exception as e:
        print(f"\n   ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    print("\n7. Cleaning up...")
    db.delete_user(user_id)
    print("   Done!")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
