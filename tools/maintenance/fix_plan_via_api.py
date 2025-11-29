"""
Fix a plan by updating its lesson_json with vocabulary/frames via direct database access.
"""
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from backend.database import get_db
from backend.config import settings

SOURCE_FILE = Path(r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W47\Wilson_Rodrigues_Weekly_W47_11-17-11-21_20251122_162906.json")
plan_id = "6dc1bd72-9481-44f4-9ee7-123c7dc2d1b0"

print("="*80)
print(f"FIXING PLAN VIA DIRECT DATABASE: {plan_id}")
print("="*80)

# Load source JSON
print(f"\n[1] Loading source JSON...")
with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
    source_json = json.load(f)

# Get vocabulary/frames from source
monday = source_json.get("days", {}).get("monday", {})
slots = monday.get("slots", [])
slot1 = next((s for s in slots if s.get("slot_number") == 1), None)

if not slot1:
    print("[FAIL] Slot 1 not found in source JSON")
    sys.exit(1)

vocab = slot1.get("vocabulary_cognates", [])
frames = slot1.get("sentence_frames", [])

print(f"[OK] Source has vocabulary_cognates: {len(vocab)} items")
print(f"[OK] Source has sentence_frames: {len(frames)} items")

# Get plan from database - try multiple methods
print(f"\n[2] Getting plan from database...")
db = get_db()

# Try to get plan directly
try:
    plan = db.get_weekly_plan(plan_id)
    if plan:
        print(f"[OK] Found plan directly: {plan.week_of}")
        lesson_json = plan.lesson_json or {}
    else:
        print(f"[INFO] Plan not found directly, trying user plans...")
        # Try to find via user plans
        users = db.list_users()
        user = next((u for u in users if "Wilson" in u.name), None)
        if user:
            plans = db.get_user_plans(user.id, limit=100)
            plan = next((p for p in plans if p.id == plan_id), None)
            if plan:
                print(f"[OK] Found plan via user plans: {plan.week_of}")
                lesson_json = plan.lesson_json or {}
            else:
                print(f"[FAIL] Plan not found in user plans either")
                sys.exit(1)
        else:
            print(f"[FAIL] User not found")
            sys.exit(1)
except Exception as e:
    print(f"[FAIL] Error getting plan: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if not lesson_json:
    print(f"[FAIL] Plan has no lesson_json")
    sys.exit(1)

print(f"[OK] Plan has lesson_json")

# Update Monday slot 1 with vocabulary/frames
days = lesson_json.get("days", {})
monday_data = days.get("monday", {})

if not monday_data:
    print(f"[FAIL] Plan has no Monday data")
    sys.exit(1)

slots = monday_data.get("slots", [])
slot1_data = next((s for s in slots if s.get("slot_number") == 1), None)

if not slot1_data:
    print(f"[FAIL] Slot 1 not found in plan")
    sys.exit(1)

print(f"[OK] Found slot 1 in plan")

# Update slot 1 with vocabulary/frames
slot1_data["vocabulary_cognates"] = vocab
slot1_data["sentence_frames"] = frames

print(f"\n[3] Updating plan with vocabulary/frames...")
print(f"    vocabulary_cognates: {len(vocab)} items")
print(f"    sentence_frames: {len(frames)} items")

# Save updated lesson_json - try direct database update
try:
    # Use SQLModel session to update directly
    from backend.schema import WeeklyPlan
    from sqlmodel import Session
    
    with Session(db.engine) as session:
        db_plan = session.get(WeeklyPlan, plan_id)
        if db_plan:
            db_plan.lesson_json = lesson_json
            session.add(db_plan)
            session.commit()
            session.refresh(db_plan)
            print(f"[OK] Plan updated directly in database")
            success = True
        else:
            print(f"[FAIL] Plan not found in database session")
            success = False
except Exception as e:
    print(f"[FAIL] Error updating plan directly: {e}")
    import traceback
    traceback.print_exc()
    # Try via update_weekly_plan method
    print(f"\n[INFO] Trying via update_weekly_plan method...")
    try:
        success = db.update_weekly_plan(
            plan_id=plan_id,
            lesson_json=lesson_json
        )
        print(f"[OK] Plan updated via update_weekly_plan method" if success else "[FAIL] update_weekly_plan returned False")
    except Exception as e2:
        print(f"[FAIL] update_weekly_plan also failed: {e2}")
        success = False

if success:
    print(f"\n{'='*80}")
    print(f"[SUCCESS] Plan {plan_id} updated with vocabulary and sentence frames!")
    print(f"{'='*80}")
    print(f"\nNext steps:")
    print(f"1. Regenerate lesson steps for this plan in the frontend")
    print(f"2. Navigate to Lesson Mode for this plan")
    print(f"3. Vocabulary and sentence frames should now appear")
else:
    print(f"\n{'='*80}")
    print(f"[FAIL] Could not update plan")
    print(f"{'='*80}")

print("\n" + "="*80)

