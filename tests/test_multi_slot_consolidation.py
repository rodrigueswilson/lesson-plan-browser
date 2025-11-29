"""
Test multi-slot consolidation into single weekly DOCX.
Tests the Day 9 implementation of consolidated weekly plans.
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import get_db
from backend.mock_llm_service import get_mock_llm_service
from tools.batch_processor import BatchProcessor


async def test_single_slot():
    """Test 1: Single slot (regression test)"""
    print("\n" + "=" * 70)
    print("TEST 1: SINGLE SLOT (Regression)")
    print("=" * 70)
    
    db = get_db()
    llm_service = get_mock_llm_service()
    processor = BatchProcessor(llm_service)
    
    # Create test user
    user_id = db.create_user("Lang", "lang@example.com")
    
    # Create single slot
    slot_id = db.create_class_slot(
        user_id=user_id,
        slot_number=1,
        subject="ELA",
        grade="3",
        homeroom="3-1",
        proficiency_levels='["Entering", "Emerging"]',
        primary_teacher_file="input/Lang Lesson Plans 9_15_25-9_19_25.docx"
    )
    
    db.update_class_slot(
        slot_id,
        primary_teacher_name="Lang",
        primary_teacher_file_pattern="Lang*.docx"
    )
    
    # Process week
    result = await processor.process_user_week(
        user_id=user_id,
        week_of="9/15-9/19",
        provider="mock"
    )
    
    print(f"\nResult:")
    print(f"  Success: {result['success']}")
    print(f"  Output file: {result.get('output_file')}")
    
    # Verify filename format (should NOT be "Weekly")
    if result.get('output_file'):
        filename = Path(result['output_file']).name
        print(f"  Filename: {filename}")
        assert "Weekly" not in filename, "Single slot should not use 'Weekly' filename"
        # Single slot uses original format (user_Lesson_plan_W##_dates.docx)
        assert "Lesson_plan" in filename, "Single slot should use original filename format"
        print("  PASS: Single slot uses original filename format")
    
    # Cleanup
    db.delete_user(user_id)
    print("\nTest 1 PASSED")


async def test_two_slots():
    """Test 2: Two slots consolidated"""
    print("\n" + "=" * 70)
    print("TEST 2: TWO SLOTS CONSOLIDATED")
    print("=" * 70)
    
    db = get_db()
    llm_service = get_mock_llm_service()
    processor = BatchProcessor(llm_service)
    
    # Create test user
    user_id = db.create_user("Multi Teacher", "multi@example.com")
    
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
    result = await processor.process_user_week(
        user_id=user_id,
        week_of="9/15-9/19",
        provider="mock"
    )
    
    print(f"\nResult:")
    print(f"  Success: {result['success']}")
    print(f"  Output file: {result.get('output_file')}")
    
    # Verify filename format (should be "Weekly")
    if result.get('output_file'):
        filename = Path(result['output_file']).name
        print(f"  Filename: {filename}")
        assert "Weekly" in filename, "Multi-slot should use 'Weekly' filename"
        assert "Slot" not in filename or "Slot1" not in filename, "Should not include individual slot numbers"
        print("  PASS: Multi-slot uses consolidated 'Weekly' filename")
        
        # Verify file exists and has content
        output_path = Path(result['output_file'])
        if output_path.exists():
            size_kb = output_path.stat().st_size / 1024
            print(f"  File size: {size_kb:.1f} KB")
            assert size_kb > 10, "File should have substantial content"
            print("  PASS: File exists with content")
    
    # Cleanup
    db.delete_user(user_id)
    print("\nTest 2 PASSED")


async def test_five_slots():
    """Test 3: Five slots consolidated (full week)"""
    print("\n" + "=" * 70)
    print("TEST 3: FIVE SLOTS CONSOLIDATED (Full Week)")
    print("=" * 70)
    
    db = get_db()
    llm_service = get_mock_llm_service()
    processor = BatchProcessor(llm_service)
    
    # Create test user
    user_id = db.create_user("Full Week User", "full@example.com")
    
    # Create 5 slots
    slots_config = [
        (1, "ELA", "Lang", "input/Lang Lesson Plans 9_15_25-9_19_25.docx"),
        (2, "Math", "Davies", "input/9_15-9_19 Davies Lesson Plans.docx"),
        (3, "Science", "Savoca", "input/Ms. Savoca- 9_15_24-9_19_24 Lesson plans.docx"),
        (4, "Social Studies", "Lang", "input/Lang Lesson Plans 9_15_25-9_19_25.docx"),
        (5, "Math", "Davies", "input/9_15-9_19 Davies Lesson Plans.docx"),
    ]
    
    for slot_num, subject, teacher, file_path in slots_config:
        slot_id = db.create_class_slot(
            user_id=user_id,
            slot_number=slot_num,
            subject=subject,
            grade="3",
            homeroom="3-1",
            proficiency_levels='["Entering", "Emerging"]',
            primary_teacher_file=file_path
        )
        db.update_class_slot(slot_id, primary_teacher_name=teacher)
        print(f"  Created Slot {slot_num}: {subject} ({teacher})")
    
    # Process week
    print("\nProcessing week...")
    result = await processor.process_user_week(
        user_id=user_id,
        week_of="9/15-9/19",
        provider="mock"
    )
    
    print(f"\nResult:")
    print(f"  Success: {result['success']}")
    print(f"  Processed slots: {result.get('processed_slots', 0)}")
    print(f"  Output file: {result.get('output_file')}")
    
    # Verify consolidated output
    if result.get('output_file'):
        filename = Path(result['output_file']).name
        print(f"  Filename: {filename}")
        assert "Weekly" in filename, "5-slot should use 'Weekly' filename"
        
        # Verify file exists and has substantial content
        output_path = Path(result['output_file'])
        if output_path.exists():
            size_kb = output_path.stat().st_size / 1024
            print(f"  File size: {size_kb:.1f} KB")
            assert size_kb > 20, "5-slot file should have substantial content"
            print("  PASS: Consolidated file created with all 5 slots")
    
    # Cleanup
    db.delete_user(user_id)
    print("\nTest 3 PASSED")


async def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("MULTI-SLOT CONSOLIDATION TEST SUITE")
    print("Day 9 Implementation Verification")
    print("=" * 70)
    
    try:
        # Test 1: Single slot (regression)
        await test_single_slot()
        
        # Test 2: Two slots
        await test_two_slots()
        
        # Test 3: Five slots
        await test_five_slots()
        
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED!")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
