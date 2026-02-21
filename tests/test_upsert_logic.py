
import os
import sys
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import get_db
from backend.schema import OriginalLessonPlan

def test_upsert_original_plan():
    print("Testing OriginalLessonPlan UPSERT (session.merge)...")
    db = get_db()
    
    user_id = "test_upsert_user"
    week_of = "2025-12-22"
    slot_num = 99
    plan_id = f"orig_{user_id}_{week_of}_{slot_num}"
    
    # 1. Create initial record
    data1 = {
        "id": plan_id,
        "user_id": user_id,
        "week_of": week_of,
        "slot_number": slot_num,
        "subject": "Initial Subject",
        "grade": "Initial Grade",
        "source_file_path": "path/1",
        "source_file_name": "file1.docx",
        "content_json": {"test": "data1"}
    }
    
    print(f"Adding initial record for {plan_id}...")
    db.create_original_lesson_plan(data1)
    
    # Verify initial
    with db.get_connection() as session:
        p1 = session.get(OriginalLessonPlan, plan_id)
        assert p1 is not None
        assert p1.subject == "Initial Subject"
        print(" - Verified initial record exists.")
        
    # 2. Update same record with new data (UPSERT)
    data2 = data1.copy()
    data2["subject"] = "Updated Subject"
    data2["content_json"] = {"test": "data2"}
    
    print(f"Updating record for {plan_id} (should merge)...")
    db.create_original_lesson_plan(data2)
    
    # Verify update
    with db.get_connection() as session:
        p2 = session.get(OriginalLessonPlan, plan_id)
        assert p2 is not None
        assert p2.subject == "Updated Subject"
        assert p2.content_json == {"test": "data2"}
        print(" - SUCCESS: Record updated successfully via UPSERT.")

    # Cleanup (optional, but good for repeatability)
    with db.get_connection() as session:
        p_final = session.get(OriginalLessonPlan, plan_id)
        if p_final:
            session.delete(p_final)
            session.commit()
            print(" - Cleaned up test record.")

if __name__ == "__main__":
    try:
        test_upsert_original_plan()
    except Exception as e:
        print(f"FAILURE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
