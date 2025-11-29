"""
Debug script to inspect the multi-slot JSON structure.
"""

import sys
import asyncio
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import get_db
from backend.mock_llm_service import get_mock_llm_service
from tools.batch_processor import BatchProcessor


async def main():
    print("=" * 70)
    print("DEBUG: Multi-Slot JSON Structure")
    print("=" * 70)
    
    db = get_db()
    llm_service = get_mock_llm_service()
    processor = BatchProcessor(llm_service)
    
    # Create test user with 2 slots
    user_id = db.create_user("Debug User", "debug@example.com")
    
    # Create slot 1
    slot1_id = db.create_class_slot(
        user_id=user_id,
        slot_number=1,
        subject="ELA",
        grade="3",
        homeroom="3-1",
        proficiency_levels='["Entering"]',
        primary_teacher_file="input/Lang Lesson Plans 9_15_25-9_19_25.docx"
    )
    db.update_class_slot(slot1_id, primary_teacher_name="Lang")
    
    # Create slot 2
    slot2_id = db.create_class_slot(
        user_id=user_id,
        slot_number=2,
        subject="Math",
        grade="3",
        homeroom="3-1",
        proficiency_levels='["Emerging"]',
        primary_teacher_file="input/9_15-9_19 Davies Lesson Plans.docx"
    )
    db.update_class_slot(slot2_id, primary_teacher_name="Davies")
    
    # Process week
    print("\nProcessing week...")
    result = await processor.process_user_week(
        user_id=user_id,
        week_of="9/15-9/19",
        provider="mock"
    )
    
    print(f"\nResult: {result['success']}")
    print(f"Output file: {result.get('output_file')}")
    
    # Try to find the merged JSON file
    output_dir = Path(result.get('output_file', '')).parent
    json_files = list(output_dir.glob("*merged*.json"))
    
    if json_files:
        json_file = json_files[0]
        print(f"\nFound merged JSON: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            merged_json = json.load(f)
        
        # Inspect Monday's slots
        print("\n" + "=" * 70)
        print("MONDAY SLOTS STRUCTURE:")
        print("=" * 70)
        
        monday_slots = merged_json.get('days', {}).get('monday', {}).get('slots', [])
        print(f"\nNumber of slots: {len(monday_slots)}")
        
        for i, slot in enumerate(monday_slots, 1):
            print(f"\n--- Slot {i} ---")
            print(f"Slot Number: {slot.get('slot_number')}")
            print(f"Subject: {slot.get('subject')}")
            print(f"Teacher: {slot.get('teacher_name')}")
            print(f"\nUnit/Lesson: {slot.get('unit_lesson', 'MISSING')[:200]}")
            print(f"\nObjective keys: {list(slot.get('objective', {}).keys()) if isinstance(slot.get('objective'), dict) else 'Not a dict'}")
            print(f"\nAll keys in slot: {list(slot.keys())}")
    else:
        print("\nNo merged JSON file found in output directory")
    
    # Cleanup
    db.delete_user(user_id)
    print("\n" + "=" * 70)
    print("DEBUG COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
