import sys
import os
import json

sys.path.append(os.getcwd())
from backend.database import SQLiteDatabase

def check_originals(week_of, user_id):
    db = SQLiteDatabase()
    originals = db.get_original_lesson_plans_for_week(user_id, week_of)
    print(f"Total Original Plans for {week_of}: {len(originals)}")
    
    for orig in originals:
        print(f"\n--- Slot {orig.slot_number} ({orig.subject}) ---")
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
            content = getattr(orig, f"{day}_content", {}) or {}
            links = content.get('hyperlinks', [])
            if isinstance(links, dict) and 'root' in links:
                links = links['root']
            
            if links:
                print(f"  [{day.upper()}] Links:")
                for l in links:
                    print(f"    - [{l.get('text')}] ({l.get('url')})")

if __name__ == "__main__":
    # From previous dump:
    user_id = "04fe8898-cb89-4a73-affb-64a97a98f820"
    week_of = "12-15-12-19"
    check_originals(week_of, user_id)
