
import sqlite3
import json
import sys
from pathlib import Path

def inspect_db():
    db_path = Path("data/lesson_planner.db")
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    print(f"Inspecting {db_path}...")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find plans for the relevant week
    # User mentioned 12/15/25. The week_of might be "2025-12-15" or similar.
    # Debug: List all weeks
    cursor.execute("SELECT DISTINCT week_of FROM weekly_plans")
    weeks = cursor.fetchall()
    print("Available weeks:", [w['week_of'] for w in weeks])

    cursor.execute(
        "SELECT id, week_of, generated_at, lesson_json FROM weekly_plans"
    )
    plans = cursor.fetchall()
    
    print(f"Found {len(plans)} plans for week 12/15.")
    
    for plan in plans:
        print(f"\nPlan ID: {plan['id']}")
        print(f"Generated At: {plan['generated_at']}")
        
        try:
            data = json.loads(plan['lesson_json'])
            # Navigate to Monday -> Slot?
            # User said "Monday 09:18 - 10:03".
            # We'll search the JSON for the phrases.
            
            json_str = json.dumps(data)
            
            phrase1 = "I see a picture of"
            phrase2 = "This is the character"
            
            if phrase1 in json_str:
                print(f"  [FOUND] Phrase '{phrase1}' (Old Version?)")
            else:
                print(f"  [MISSING] Phrase '{phrase1}'")
                
            if phrase2 in json_str:
                print(f"  [FOUND] Phrase '{phrase2}' (New Version?)")
            else:
                print(f"  [MISSING] Phrase '{phrase2}'")
                
            # Try to print specific content if possible
            days = data.get('days', {})
            monday = days.get('monday', {}) or days.get('Monday', {})
            slots = monday.get('slots', [])
            
            for i, slot in enumerate(slots):
                time_range = slot.get('time_range', 'Unknown Time')
                print(f"  Slot {i+1} ({time_range}):")
                # content = slot.get('content', {})
                # print(str(content)[:100] + "...")
                
        except Exception as e:
            print(f"  Error parsing JSON: {e}")

    conn.close()

if __name__ == "__main__":
    inspect_db()
