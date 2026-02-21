
import asyncio
import sys
import os
from pathlib import Path

# Add root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.batch_processor import BatchProcessor
from backend.llm_service import LLMService
from backend.database import get_db

async def verify_final_system():
    # Use the master template
    template_path = "d:/LP/input/Lesson Plan Template SY'25-26.docx"
    import uuid
    user_id = f"test-user-{uuid.uuid4()}" 
    week_of = "01/05-01/09"
    
    db = get_db()
    db.create_user(user_id, "Test Teacher", "test@example.com", "password")
    db.create_class_slot(user_id, 1, "ELA", grade="3")

    # Initialize processor with a local base path to d:/LP/output
    from backend.file_manager import get_file_manager
    file_mgr = get_file_manager(base_path="d:/LP/output")
    
    processor = BatchProcessor(LLMService())
    processor.db = db
    processor._user_base_path = "d:/LP/output"
    
    print("\n--- RUNNING FINAL SYSTEM VERIFICATION ---")
    print(f"Target: {template_path}")
    
    try:
        # 1. Process the week for this user (will trigger extraction + transformation + originals)
        # Note: We use slot_ids=[1] to isolate the template test
        # We also use a mock LLM service or just wait for extraction to finish
        
        # Actually, let's just trigger the extraction phase directly to see the Originals generated
        from tools.docx_parser import DOCXParser
        parser = DOCXParser(template_path)
        
        # Simulate the sequential path context
        from tools.batch_processor import SlotProcessingContext
        ctx = SlotProcessingContext(
            slot_index=1,
            total_slots=1,
            slot={"slot_number": 1, "subject": "ELA", "teacher_name": "Test Teacher", "grade": "3"}
        )
        
        print("\nStep 1: Extracting content...")
        # Since _extract_slot_content usually handles file resolution, we'll just mock the parts we need
        # but the actual code now calls _map_day_content_to_schema
        
        content = await asyncio.to_thread(parser.extract_subject_content_for_slot, 1, "ELA")
        content["_hyperlinks"] = [
            {"text": "Sample Link", "url": "http://example.com", "day": "Monday", "row_label": "Materials"}
        ]
        print(f"  - Extracted content found: {content.get('found')}")
        
        # 2. Verify mapping
        monday = content["table_content"].get("Monday", {})
        day_links = [h for h in content["_hyperlinks"] if h["day"] == "Monday"]
        mapped = processor._map_day_content_to_schema(monday, ctx.slot, day_hyperlinks=day_links)
        print(f"  - Mapped keys: {list(mapped.keys())}")
        if "hyperlinks" in mapped and mapped["hyperlinks"]:
            print(f"  - Hyperlinks mapped successfully: {mapped['hyperlinks']}")
        else:
            print("  - [FAILURE] Hyperlinks NOT found in mapped schema")
        
        # 3. Simulate DB save and Originals generation
        import uuid
        plan_id = f"test_{uuid.uuid4()}"
        from datetime import datetime
        
        structured_days = {"monday_content": mapped}
        plan_data = {
            "id": f"orig_{uuid.uuid4()}",
            "user_id": user_id,
            "week_of": week_of,
            "slot_number": 1,
            "subject": "ELA",
            "grade": "3",
            "source_file_path": template_path,
            "source_file_name": "Lesson Plan Template.docx",
            "primary_teacher_name": "Test Teacher",
            "extracted_at": datetime.utcnow(),
            "content_json": content,
            "full_text": content.get("full_text", ""),
            "available_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "status": "extracted",
            **structured_days
        }
        
        print("\nStep 2: Saving to database...")
        db.create_original_lesson_plan(plan_data)
        
        print("\nStep 3: Generating Originals DOCX...")
        await processor._generate_combined_original_docx(user_id, week_of, plan_id)
        
        # The implementation uses combined_originals_MM-DD-MM-DD.docx
        safe_week = week_of.replace("/", "-").replace("\\", "-").replace(" ", "_")
        filename = f"combined_originals_{safe_week}.docx"
        
        # Determine actual output path using the same logic as batch_processor
        # file_mgr is already initialized above
        week_folder = file_mgr.get_week_folder(week_of)
        expected_file = os.path.join(week_folder, "originals", filename)
        
        if os.path.exists(expected_file):
            print(f"\n[SUCCESS] Originals DOCX generated at: {expected_file}")
        else:
            print(f"\n[FAILURE] Originals DOCX NOT found at: {expected_file}")
            # List directory to help debug
            parent = os.path.join(week_folder, "originals")
            if os.path.exists(parent):
                print(f"Directory contents for {parent}: {os.listdir(parent)}")
            else:
                print(f"Directory {parent} does not exist.")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n[ERROR] Verification failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_final_system())
