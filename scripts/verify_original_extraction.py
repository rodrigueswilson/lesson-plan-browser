
import sys
import os
import asyncio
from pathlib import Path
from shutil import copy2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.batch_processor import BatchProcessor, SlotProcessingContext
from backend.llm_service import LLMService
from backend.database import get_db, SQLiteDatabase
from backend.schema import OriginalLessonPlan

async def main():
    try:
        db = get_db()
        
        # 1. Setup Data
        week_of = "9/15-9/19"
        user_id = "test_original_user" 
        
        # 2. Setup File
        input_file = Path("d:/LP/input/Ms. Savoca- 9_15_24-9_19_24 Lesson plans.docx")
        if not input_file.exists():
            print(f"Error: Input file not found: {input_file}")
            return

        # Simulate Week Folder
        from backend.file_manager import get_file_manager
        fm = get_file_manager()
        week_folder = fm.get_week_folder(week_of)
        if not week_folder.exists():
            week_folder.mkdir(parents=True, exist_ok=True)
        
        # Copy file to week folder
        dest_file = week_folder / input_file.name
        try:
            copy2(input_file, dest_file)
            print(f"Copied test file to {dest_file}")
        except Exception as e:
            print(f"Error copying file: {e}")

        # 3. Create BatchProcessor with Mock LLM
        class MockLLM(LLMService):
            def transform_lesson(self, *args, **kwargs):
                return True, {"metadata": {}, "days": {}}, None

        processor = BatchProcessor(MockLLM())
        processor.db = db # Use real DB
        processor._current_user_id = user_id
        processor._user_base_path = None # Use default
        
        # 4. Construct a Slot context manually
        slot = {
            "slot_number": 1,
            "subject": "Science", # Savoca has Science
            "primary_teacher_file_pattern": "Savoca",
            "primary_teacher_name": "Ms. Savoca",
            "grade": "2",
            "homeroom": "209"
        }
        
        context = SlotProcessingContext(
            slot=slot,
            slot_index=1,
            total_slots=1
        )
        
        # Clean up previous entries for this test
        # db.delete_original_lesson_plans(user_id, week_of) # Need to implement or use session directly
        
        # 5. Run Extraction
        print("Running extraction...")
        updated_context = await processor._extract_slot_content(
            context,
            week_of=week_of,
            week_folder_path=str(week_folder),
            user_base_path=None,
            plan_id="test_plan_id"
        )
        print("Extraction complete.")
        
        if updated_context.error:
            print(f"Extraction Error: {updated_context.error}")
        else:
            print(f"Extracted Content Length: {len(updated_context.extracted_content)}")
            
            # 6. Verify DB Persistence
            print("Verifying Database Persistence...")
            plans = db.get_original_lesson_plans_for_week(user_id, week_of)
            print(f"Found {len(plans)} plans in DB.")
            
            if plans:
                plan = plans[0]
                print(f"Plan ID: {plan.id}")
                
                # Check Monday Content
                if plan.monday_content:
                    print(f"\nMonday Content Detected!")
                    print(f"Keys: {list(plan.monday_content.keys())}")
                    
                    if 'instruction' in plan.monday_content:
                         print(f"Instruction: {plan.monday_content['instruction']}")
                    else:
                         print("Instruction field missing in monday_content")
                         
                    if 'objective' in plan.monday_content:
                         print(f"Objective: {plan.monday_content['objective']}")
                else:
                    print("Monday content is empty. Check extraction logic.")
                    # Debug table content
                    if plan.content_json and 'table_content' in plan.content_json:
                        print("Raw Table Content Keys: ", plan.content_json['table_content'].keys())
                        if 'Monday' in plan.content_json['table_content']:
                            print("Raw Monday content: ", plan.content_json['table_content']['Monday'])

                # 7. Run Document Generation
                print("\nGenerating Originals DOCX...")
                path = await processor._generate_combined_original_docx(
                    user_id, week_of, "test_plan_id", str(week_folder)
                )
                print(f"Generated DOCX at: {path}")
                
                if path and Path(path).exists():
                    print("SUCCESS: Document created.")
                else:
                    print("FAILURE: Document not created.")

            else:
                print("FAILURE: No plans found in DB.")
                
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
