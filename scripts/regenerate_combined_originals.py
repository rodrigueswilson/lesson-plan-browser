import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath("d:/LP"))

from backend.database import SQLiteDatabase
from tools.batch_processor import BatchProcessor
from backend.file_manager import get_file_manager

async def regenerate():
    # 1. Setup
    db = SQLiteDatabase()
    
    # HARDCODED TARGET FOR DEBUGGING
    user_id = "04fe8898-cb89-4a73-affb-64a97a98f820"
    user = db.get_user(user_id)
    if not user:
        print(f"User {user_id} not found!")
        return
        
    # Try formats
    week_formats = ["12-15-12-19"] # Confirmed correct format
    plans = []
    week_of = ""
    
    for w in week_formats:
        print(f"Checking plans for week: {w}")
        plans = db.get_original_lesson_plans_for_week(user_id, w)
        if plans:
            week_of = w
            print(f"  -> Found {len(plans)} plans.")
            break
        else:
            print("  -> No plans found.")
            
    if not plans:
        print("Could not find plans for Dec 15th week in DB.")
        return

    print(f"Regenerating for User: {user.name} ({user_id}), Week: {week_of}")

    # 3. Initialize Processor
    processor = BatchProcessor(db)
    
    # Needs user base path
    base_path = user.base_path_override or getattr(user, "base_path", None)
    
    # 4. Get Week Folder
    file_mgr = get_file_manager(base_path=base_path)
    week_folder_path = file_mgr.get_week_folder(week_of)
    print(f"Target Week Folder: {week_folder_path}")

    # 5. Inject user metadata into processor (needed for some internal logic)
    processor._user_base_path = base_path
    
    # 6. Generate
    # Correct signature: _generate_combined_original_docx(user_id, week_of, plan_id, week_folder_path)
    try:
        output_path = await processor._generate_combined_original_docx(
            user_id, 
            week_of, 
            "manual_regen",
            str(week_folder_path)
        )
        if output_path:
             print(f"SUCCESS! Created: {output_path}")
        else:
             print("Failed to generate (returned None).")

    except Exception as e:
        print(f"Error during generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(regenerate())
