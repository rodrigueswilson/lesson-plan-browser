
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.batch_processor import BatchProcessor
from backend.llm_service import LLMService
from backend.database import get_db
from backend.telemetry import logger

async def test_real_w51_originals():
    # Configuration
    # Wilson Rodrigues matching the files in W51 (Lang, Savoca, Davies)
    user_id = "04fe8898-cb89-4a73-affb-64a97a98f820" 
    week_of = "12/15-12/19"
    week_folder = r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W51"
    
    print(f"\n--- TESTING REAL ORIGINALS GEN: WEEK 51 ---")
    print(f"User: Daniela Silva ({user_id})")
    print(f"Week: {week_of}")
    print(f"Folder: {week_folder}")
    
    # Initialize BatchProcessor
    # We use mock LLM to focus on the extraction and originals generation
    processor = BatchProcessor(LLMService())
    
    # Force Mock LLM inside processor and disable parallel
    import tools.batch_processor
    from backend.config import settings
    tools.batch_processor.MOCK_LLM_CALL = True
    settings.PARALLEL_LLM_PROCESSING = False
    print("\n[NOTE] Using MOCK_LLM_CALL = True and PARALLEL_LLM_PROCESSING = False.")
    
    try:
        # 1. Process the week
        # This will trigger:
        # - Extraction (Phase 1)
        # - _map_day_content_to_schema
        # - DB persistence of OriginalLessonPlan
        # - Automated _generate_combined_original_docx
        # - Mocked Transformation (Phase 2)
        
        print("\nStep 1: Processing user week (Extraction + Originals Gen)...")
        result = await processor.process_user_week(
            user_id=user_id,
            week_of=week_of,
            week_folder_path=week_folder
        )
        
        print("\n--- PROCESS RESULT ---")
        import json
        print(json.dumps(result, indent=2, default=str))
        
        if result.get("success"):
            print(f"\n[SUCCESS] process_user_week completed.")
            print(f"  - Plans processed: {len(result.get('plans', []))}")
            if "originals_docx" in result:
                print(f"  - Originals DOCX: {result['originals_docx']}")
            else:
                # Check directly if file exists
                filename = f"combined_originals_{week_of.replace('/', '-').replace(' ', '_')}.docx"
                expected_path = Path(week_folder) / "originals" / filename
                if expected_path.exists():
                     print(f"  - Originals DOCX found at: {expected_path}")
                else:
                     print(f"  - [FAILURE] Originals DOCX NOT found at: {expected_path}")
        else:
            print(f"\n[FAILURE] process_user_week failed: {result.get('error')}")

        # 2. Verify Database Persistence
        print("\nStep 2: Verifying DB persistence for OriginalLessonPlan...")
    
        db = get_db(user_id=user_id)
        originals = db.get_original_lesson_plans_for_week(user_id, week_of)
        
        if originals:
            print(f"[OK] Found {len(originals)} original plans in database.")
            for p in originals:
                days_with_content = []
                for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
                    if getattr(p, f"{day}_content"):
                        days_with_content.append(day)
                print(f"  - Slot {p.slot_number} ({p.subject}): Content for {days_with_content}")
        else:
            print("[FAILURE] No original plans found in database for this week/user.")

    except Exception as e:
        import traceback
        print(f"\n[ERROR] Test crashed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_w51_originals())
