
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import settings and apply test overrides
from backend.config import settings
settings.PARALLEL_LLM_PROCESSING = True

from backend.database import get_db
from backend.mock_llm_service import get_mock_llm_service
from tools.batch_processor import BatchProcessor, SlotProcessingContext

async def test_partial_logic():
    print("=" * 70)
    print("PARTIAL GENERATION LOGIC TEST")
    print("=" * 70)
    
    db = get_db()
    llm_service = get_mock_llm_service()
    processor = BatchProcessor(llm_service)
    
    user_id = "test_user_partial"
    week_of = "12/22-12/26"
    
    # 1. Define an existing plan structure
    existing_lesson_json = {
        "metadata": {"week_of": week_of, "subject": "Multiple"},
        "days": {
            "monday": {
                "slots": [
                    {
                        "slot_number": 1, 
                        "subject": "Math", 
                        "unit_lesson": "Existing Math Lesson",
                        "objective": "Learn sums"
                    }
                ]
            },
            "tuesday": {"slots": []},
            "wednesday": {"slots": []},
            "thursday": {"slots": []},
            "friday": {"slots": []}
        },
        "_images": [{"_source_slot": 1, "path": "old_image.png"}],
        "_hyperlinks": [{"_source_slot": 1, "text": "Old Link"}]
    }
    
    # 2. Mock DB and Processor methods
    with patch.object(db, 'get_user') as mock_get_user, \
         patch.object(db, 'get_user_slots') as mock_get_slots, \
         patch.object(db, 'get_user_schedule', return_value=[]), \
         patch.object(db, 'get_user_plans') as mock_get_plans, \
         patch.object(db, 'create_weekly_plan', return_value="new_plan_id"), \
         patch.object(db, 'update_weekly_plan'), \
         patch.object(processor, '_resolve_primary_file', return_value="dummy.docx"), \
         patch.object(processor, '_extract_slots_parallel_db') as mock_extract_parallel, \
         patch.object(processor, '_process_slots_parallel_llm') as mock_transform_parallel, \
         patch.object(processor, '_process_slot') as mock_process_slot, \
         patch.object(processor, '_combine_lessons', return_value="mock_output.docx"), \
         patch.object(processor, '_generate_combined_original_docx'), \
         patch("backend.utils.lesson_json_enricher.enrich_lesson_json_from_steps", side_effect=lambda j, p, d: j):

        # Setup mock behavior
        mock_get_user.return_value = MagicMock(id=user_id, name="Test User")
        
        # We have 2 slots in DB: Math (1) and Science (2)
        slot1_obj = {"id": "slot1", "slot_number": 1, "subject": "Math"}
        slot2_obj = {"id": "slot2", "slot_number": 2, "subject": "Science"}
            
        mock_get_slots.return_value = [slot1_obj, slot2_obj]

        # Mock existing plan in DB
        existing_plan = MagicMock(id="existing_plan_id", week_of=week_of, lesson_json=json.dumps(existing_lesson_json))
        mock_get_plans.return_value = [existing_plan]
        
        # Mock Science slot data
        new_science_json = {
            "metadata": {"subject": "Science"},
            "days": {
                "monday": {"unit_lesson": "New Science Lesson", "objective": "Learn chemicals"},
                "tuesday": {}, "wednesday": {}, "thursday": {}, "friday": {}
            },
            "_images": [{"path": "new_science_img.png"}],
            "_hyperlinks": []
        }
        
        # Parallel mocks
        async def mock_extract_parallel_impl(slots, *args, **kwargs):
            results = []
            for i, slot in enumerate(slots, 1):
                ctx = SlotProcessingContext(slot=slot, slot_index=i, total_slots=len(slots))
                ctx.extracted_content = "dummy"
                results.append(ctx)
            return results
            
        async def mock_transform_parallel_impl(contexts, *args, **kwargs):
            for ctx in contexts:
                ctx.lesson_json = new_science_json
            return contexts
            
        mock_extract_parallel.side_effect = mock_extract_parallel_impl
        mock_transform_parallel.side_effect = mock_transform_parallel_impl
        
        # Sequential mock
        mock_process_slot.return_value = new_science_json

        print("\nTEST 1: Partial generation for missing_only=True")
        print("Expected: Should identify Slot 2 as missing and process only that.")
        
        result = await processor.process_user_week(
            user_id=user_id,
            week_of=week_of,
            missing_only=True,
            partial=True
        )
        
        print(f"Result Success: {result['success']}")
        
        # If len(slots) == 1, it uses sequential mode (_process_slot)
        # Verify that slot 2 was processed
        print(f"Sequential calls: {mock_process_slot.call_count}")
        assert mock_process_slot.call_count == 1
        args, kwargs = mock_process_slot.call_args
        processed_slot = args[0]
        assert processed_slot['slot_number'] == 2
        
        # Verify merged result passed to _combine_lessons
        args, kwargs = processor._combine_lessons.call_args
        lessons_for_rendering = args[1]
        print(f"Total slots for rendering: {len(lessons_for_rendering)}")
        
        slot_nums = sorted([l['slot_number'] for l in lessons_for_rendering])
        print(f"Slot numbers in final list: {slot_nums}")
        assert slot_nums == [1, 2]
        
        # Check content of merged slots
        for l in lessons_for_rendering:
             slot_num = l['slot_number']
             content = l['lesson_json']['days']['monday'].get('unit_lesson')
             print(f" - Slot {slot_num} content: {content}")
             if slot_num == 1:
                 assert content == "Existing Math Lesson"
             if slot_num == 2:
                 assert content == "New Science Lesson"
        
        print("\nTEST 1 PASSED!")

        # Reset mocks for next test
        mock_process_slot.reset_mock()
        mock_transform_parallel.reset_mock()
        mock_extract_parallel.reset_mock()
        processor._combine_lessons.reset_mock()

        print("\nTEST 2: Partial generation for specific slot_ids=['slot1']")
        print("Expected: Should process Math (Slot 1) and merge with existing Science (Slot 2)")
        
        # Update existing plan to include Science
        updated_existing_json = existing_lesson_json.copy()
        updated_existing_json["days"]["monday"]["slots"].append({
            "slot_number": 2, "subject": "Science", "unit_lesson": "Old Science Lesson"
        })
        existing_plan.lesson_json = json.dumps(updated_existing_json)
        
        # New content for Math
        updated_math_json = {
            "metadata": {"subject": "Math"},
            "days": {
                "monday": {"unit_lesson": "Updated Math Lesson"},
                "tuesday": {}, "wednesday": {}, "thursday": {}, "friday": {}
            }
        }
        mock_process_slot.return_value = updated_math_json

        result = await processor.process_user_week(
            user_id=user_id,
            week_of=week_of,
            slot_ids=["slot1"],
            partial=True
        )
        
        print(f"Result Success: {result['success']}")
        assert mock_process_slot.call_count == 1
        assert mock_process_slot.call_args[0][0]['slot_number'] == 1
        
        args, kwargs = processor._combine_lessons.call_args
        lessons_for_rendering = args[1]
        print(f"Total slots for rendering: {len(lessons_for_rendering)}")
        
        for l in lessons_for_rendering:
             slot_num = l['slot_number']
             content = l['lesson_json']['days']['monday'].get('unit_lesson')
             print(f" - Slot {slot_num} content: {content}")
             if slot_num == 1:
                 assert content == "Updated Math Lesson"
             if slot_num == 2:
                 assert content == "Old Science Lesson"
                 
        print("\nTEST 2 PASSED!")

    print("\n" + "=" * 70)
    print("ALL LOGIC TESTS PASSED")
    print("=" * 70)

if __name__ == "__main__":
    try:
        asyncio.run(test_partial_logic())
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
