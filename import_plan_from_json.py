"""
Import an existing lesson plan JSON file into the database.
This allows us to test the vocabulary/frames pipeline with existing data.
"""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from backend.database import get_db
from backend.config import settings
from backend.services.objectives_utils import normalize_objectives_in_lesson

SOURCE_FILE = Path(r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W47\Wilson_Rodrigues_Weekly_W47_11-17-11-21_20251122_162906.json")

def import_plan_from_json(source_file: Path, user_id: str = None):
    """Import a JSON file into the database as a weekly plan."""
    print(f"\n{'=' * 80}")
    print(f"  IMPORTING PLAN FROM JSON")
    print(f"{'=' * 80}")
    
    # Load JSON file
    if not source_file.exists():
        print(f"[FAIL] Source file not found: {source_file}")
        return None
    
    print(f"[OK] Loading JSON file: {source_file.name}")
    with open(source_file, 'r', encoding='utf-8') as f:
        lesson_json = json.load(f)
    
    # Normalize objectives
    normalize_objectives_in_lesson(lesson_json)
    
    # Extract metadata
    metadata = lesson_json.get("metadata", {})
    week_of = metadata.get("week_of", "")
    user_name = metadata.get("user_name", "")
    total_slots = metadata.get("total_slots", 1)
    
    print(f"[OK] Extracted metadata:")
    print(f"     Week: {week_of}")
    print(f"     User: {user_name}")
    print(f"     Total slots: {total_slots}")
    
    # Get database
    db = get_db()
    
    # Find or create user
    if user_id:
        user = db.get_user(user_id)
    elif user_name:
        user = db.get_user_by_name(user_name)
    else:
        # Get first user or create a test user
        users = db.list_users()
        if users:
            user = users[0]
            user_id = user.id
            print(f"[OK] Using existing user: {user.name}")
        else:
            print("[INFO] No user found, creating test user...")
            user_id = db.create_user(first_name="Test", last_name="User")
            user = db.get_user(user_id)
            print(f"[OK] Created test user: {user_id}")
    
    if not user:
        print("[FAIL] Could not find or create user")
        return None
    
    user_id = user.id if hasattr(user, 'id') else user.get('id')
    
    # Check if plan already exists for this week
    existing_plans = db.get_user_plans(user_id, limit=10)
    existing_plan = next((p for p in existing_plans if p.week_of == week_of), None)
    
    if existing_plan:
        print(f"[INFO] Plan already exists for week {week_of}: {existing_plan.id}")
        print(f"       Updating existing plan...")
        
        # Update the plan with the JSON
        success = db.update_weekly_plan(
            plan_id=existing_plan.id,
            lesson_json=lesson_json
        )
        
        if success:
            print(f"[OK] Plan updated: {existing_plan.id}")
            return existing_plan.id
        else:
            print(f"[FAIL] Failed to update plan")
            return None
    
    # Create new plan
    print(f"[INFO] Creating new plan for week {week_of}...")
    
    # Determine output file path
    week_folder_path = str(source_file.parent)
    output_file = source_file.name
    
    plan_id = db.create_weekly_plan(
        user_id=user_id,
        week_of=week_of,
        output_file=output_file,
        week_folder_path=week_folder_path,
        consolidated=True,
        total_slots=total_slots
    )
    
    print(f"[OK] Plan created: {plan_id}")
    
    # Update plan with lesson_json
    print(f"[INFO] Updating plan with lesson_json...")
    success = db.update_weekly_plan(
        plan_id=plan_id,
        lesson_json=lesson_json,
        status="completed"
    )
    
    if success:
        print(f"[OK] Plan updated with lesson_json")
        
        # Verify vocabulary/frames in lesson_json
        monday = lesson_json.get("days", {}).get("monday", {})
        slots = monday.get("slots", [])
        slot1 = next((s for s in slots if s.get("slot_number") == 1), None)
        
        if slot1:
            vocab = slot1.get("vocabulary_cognates", [])
            frames = slot1.get("sentence_frames", [])
            print(f"\n[OK] Verification:")
            print(f"     vocabulary_cognates: {len(vocab)} items")
            print(f"     sentence_frames: {len(frames)} items")
        
        return plan_id
    else:
        print(f"[FAIL] Failed to update plan with lesson_json")
        return None

if __name__ == "__main__":
    try:
        # Try to get user ID from command line or use None
        user_id = sys.argv[1] if len(sys.argv) > 1 else None
        
        plan_id = import_plan_from_json(SOURCE_FILE, user_id)
        
        if plan_id:
            print(f"\n{'=' * 80}")
            print(f"[SUCCESS] Plan imported successfully!")
            print(f"         Plan ID: {plan_id}")
            print(f"{'=' * 80}")
            print("\nNext steps:")
            print("  1. Run: python diagnose_vocab_pipeline.py")
            print("  2. Check the frontend for vocabulary/frames display")
        else:
            print(f"\n{'=' * 80}")
            print(f"[FAIL] Plan import failed")
            print(f"{'=' * 80}")
            sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

