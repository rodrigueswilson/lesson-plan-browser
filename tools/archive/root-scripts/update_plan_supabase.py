"""
Update plan in Supabase database with vocabulary/frames.
"""
import sys
import json
import requests
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from backend.config import settings
from backend.supabase_database import SupabaseDatabase

API_BASE = "http://localhost:8000/api"
SOURCE_FILE = Path(r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W47\Wilson_Rodrigues_Weekly_W47_11-17-11-21_20251122_162906.json")
plan_id = "6dc1bd72-9481-44f4-9ee7-123c7dc2d1b0"
user_id = "04fe8898-cb89-4a73-affb-64a97a98f820"

print("="*80)
print(f"UPDATING PLAN IN SUPABASE: {plan_id}")
print("="*80)

# Step 1: Load source JSON
print(f"\n[1] Loading source JSON...")
with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
    source_json = json.load(f)

source_days = source_json.get("days", {})

# Get vocabulary/frames for Monday slot 1 (for verification)
monday = source_days.get("monday", {})
slots = monday.get("slots", [])
slot1 = next((s for s in slots if s.get("slot_number") == 1), None)

if not slot1:
    print("[FAIL] Slot 1 not found in source JSON")
    sys.exit(1)

vocab = slot1.get("vocabulary_cognates", [])
frames = slot1.get("sentence_frames", [])

print(f"[OK] Source has vocabulary_cognates: {len(vocab)} items")
print(f"[OK] Source has sentence_frames: {len(frames)} items")

# Step 2: Get plan via API
print(f"\n[2] Getting current plan via API...")
detail_response = requests.get(
    f"{API_BASE}/plans/{plan_id}",
    headers={"X-Current-User-Id": user_id}
)

if detail_response.status_code != 200:
    print(f"[FAIL] Cannot get plan: {detail_response.status_code}")
    sys.exit(1)

plan_detail = detail_response.json()
lesson_json = plan_detail.get("lesson_json", {})

if not lesson_json:
    print(f"[FAIL] Plan has no lesson_json")
    sys.exit(1)

print(f"[OK] Plan found: {plan_detail.get('week_of')}")

# Step 3: Update all slots with vocabulary/frames from source
print(f"\n[3] Updating all slots with vocabulary/frames from source...")

days = lesson_json.get("days", {})
updated_slots = 0

for day_name in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
    day_data = days.get(day_name, {})
    source_day = source_days.get(day_name, {})
    
    if not day_data or not source_day:
        continue
    
    slots = day_data.get("slots", [])
    source_slots = source_day.get("slots", [])
    
    if not slots or not source_slots:
        continue
    
    # Update each slot that matches
    for slot in slots:
        slot_num = slot.get("slot_number")
        source_slot = next((s for s in source_slots if s.get("slot_number") == slot_num), None)
        
        if source_slot:
            source_vocab = source_slot.get("vocabulary_cognates", [])
            source_frames = source_slot.get("sentence_frames", [])
            
            # Update if source has data
            if source_vocab and isinstance(source_vocab, list) and len(source_vocab) > 0:
                slot["vocabulary_cognates"] = source_vocab
                updated_slots += 1
                print(f"    Updated {day_name} slot {slot_num}: {len(source_vocab)} vocab items")
            
            if source_frames and isinstance(source_frames, list) and len(source_frames) > 0:
                slot["sentence_frames"] = source_frames
                print(f"    Updated {day_name} slot {slot_num}: {len(source_frames)} frames")

print(f"\n[OK] Updated {updated_slots} slots with vocabulary/frames")

# Step 4: Save via Supabase database
print(f"\n[4] Saving updated lesson_json to Supabase...")

try:
    # Get Supabase database instance
    db = SupabaseDatabase()
    
    # Update plan
    success = db.update_weekly_plan(
        plan_id=plan_id,
        lesson_json=lesson_json
    )
    
    if success:
        print(f"[OK] Plan updated successfully in Supabase!")
    else:
        print(f"[FAIL] update_weekly_plan returned False")
        success = False
        
except Exception as e:
    print(f"[FAIL] Error updating plan in Supabase: {e}")
    import traceback
    traceback.print_exc()
    success = False

if success:
    # Step 5: Delete existing steps so they can be regenerated
    print(f"\n[5] Deleting existing steps for regeneration...")
    try:
        # Delete via Supabase client directly
        from backend.schema import LessonStep
        
        # Get steps first
        steps = db.get_lesson_steps(plan_id, day_of_week="monday", slot_number=1)
        
        if steps:
            print(f"    Found {len(steps)} steps to delete...")
            for step in steps:
                try:
                    # Delete via Supabase client
                    db.client.table("lesson_steps").delete().eq("id", step.id).execute()
                    print(f"    Deleted step: {step.step_name}")
                except Exception as e:
                    print(f"    [WARN] Could not delete step {step.id}: {e}")
            
            print(f"[OK] Deleted existing steps")
        else:
            print(f"[INFO] No steps found - will be generated on next access")
            
    except Exception as e:
        print(f"[WARN] Could not delete steps: {e}")
        print(f"       Steps will be regenerated when accessed")
    
    print(f"\n{'='*80}")
    print(f"[SUCCESS] Plan {plan_id} updated with vocabulary and sentence frames!")
    print(f"{'='*80}")
    print(f"\nNext steps:")
    print(f"1. Refresh the frontend page (F5 or Ctrl+R)")
    print(f"2. Navigate to Lesson Mode for this plan")
    print(f"3. Steps will be automatically regenerated with vocabulary/frames")
    print(f"4. Click 'Vocabulary' and 'Sentence Frames' resources to see the data")
else:
    print(f"\n{'='*80}")
    print(f"[FAIL] Could not update plan in Supabase")
    print(f"{'='*80}")

print("\n" + "="*80)

