import sys
import os
sys.path.append(os.path.abspath("d:/LP"))

from backend.database import SQLiteDatabase
from sqlmodel import select
from backend.schema import OriginalLessonPlan

def inspect_plans():
    db = SQLiteDatabase()
    # Hardcode the user ID found in the dump
    target_user_id = "04fe8898-cb89-4a73-affb-64a97a98f820"
    user_name = "Unknown" 
    
    # Check "12/15-12/19" (or other formats determined previously)
    week_formats = ["12-15-12-19", "12/15-12/19", "12/15/2025", "2025-12-15"]
    
    print(f"Checking specifically for User ID: {target_user_id}")
    
    found_any = False
    for w in week_formats:
        print(f"\nChecking week: {w}")
        plans = db.get_original_lesson_plans_for_week(target_user_id, w)
        if plans:
            found_any = True
            print(f"Found {len(plans)} plans.")
            
            files = {}
            for p in plans:
                if p.source_file_path not in files:
                    files[p.source_file_path] = []
                files[p.source_file_path].append(f"Slot {p.slot_number} ({p.primary_teacher_name})")
                
            print(f"Unique Source Files: {len(files)}")
            for f, slots in files.items():
                fname = os.path.basename(f)
                print(f"  File: {fname}")
                print(f"    Covers: {', '.join(slots)}")
                if "Davies" in fname:
                    print("    ^^^ DAVIES FILE FOUND ^^^")
                    
                    slot_indices = [int(s.split()[1]) for s in slots]
                    print(f"    Checking content for slots: {slot_indices}")
                    
                    with db.get_connection() as session:
                        from sqlmodel import select
                        from backend.schema import OriginalLessonPlan
                        stmt = select(OriginalLessonPlan).where(
                            OriginalLessonPlan.source_file_path == f,
                            OriginalLessonPlan.user_id == target_user_id,
                            OriginalLessonPlan.week_of.in_(week_formats)
                        )
                        davies_plans = session.exec(stmt).all()
                        
                        for p in davies_plans:
                            # Check presence of content for each day
                            days_present = []
                            if p.monday_content: days_present.append("Mon")
                            if p.tuesday_content: days_present.append("Tue")
                            if p.wednesday_content: days_present.append("Wed")
                            if p.thursday_content: days_present.append("Thu")
                            if p.friday_content: days_present.append("Fri")
                            
                            # Signature used in code:
                            content_sig = str(p.monday_content) if p.monday_content else (str(p.tuesday_content) if p.tuesday_content else str(p.id))
                            sig_hash = hash(content_sig)
                            
                            print(f"      Slot {p.slot_number} Days: {days_present} | SigHash: {sig_hash}")
        else:
            print("  No plans found.")
            
    print("\nListing ALL OriginalLessonPlans in the database (Raw Dump):")
    with db.get_connection() as session:
        all_plans = session.exec(select(OriginalLessonPlan)).all()
        print(f"Total Plans in DB: {len(all_plans)}")
        for p in all_plans:
            print(f"  User: {p.user_id} | Week: {p.week_of} | Slot {p.slot_number} | {p.subject} | File: {p.source_file_path}")

if __name__ == "__main__":
    inspect_plans()
