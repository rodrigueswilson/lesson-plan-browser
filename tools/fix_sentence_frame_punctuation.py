import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.config import settings
from backend.supabase_database import SupabaseDatabase

def normalize_text(text: str, frame_type: str) -> str:
    """Normalize punctuation based on frame_type."""
    if not text or not isinstance(text, str):
        return text
    
    text = text.strip()
    if not text:
        return text

    if frame_type in ["frame", "stem"]:
        if not text.endswith("."):
            if text[-1] in ["?", "!", ":", ";"]:
                text = text[:-1] + "."
            else:
                text = text + "."
    elif frame_type == "open_question":
        if not text.endswith("?"):
            if text[-1] in [".", "!", ":", ";"]:
                text = text[:-1] + "?"
            else:
                text = text + "?"
    return text

def fix_lesson_json(lesson_json_str: str) -> (str, bool):
    """Normalize sentence frames within lesson_json string."""
    try:
        lesson_json = json.loads(lesson_json_str)
    except Exception:
        return lesson_json_str, False

    if "days" not in lesson_json:
        return lesson_json_str, False

    changed = False
    for day_name, day_data in lesson_json["days"].items():
        if not isinstance(day_data, dict):
            continue
        
        # Handle single-slot (legacy) structure
        frames = day_data.get("sentence_frames")
        if isinstance(frames, list):
            for frame in frames:
                if not isinstance(frame, dict):
                    continue
                frame_type = frame.get("frame_type")
                for lang in ["english", "portuguese"]:
                    old_text = frame.get(lang)
                    new_text = normalize_text(old_text, frame_type)
                    if old_text != new_text:
                        frame[lang] = new_text
                        changed = True
        
        # Handle multi-slot structure
        slots = day_data.get("slots")
        if isinstance(slots, list):
            for slot in slots:
                if not isinstance(slot, dict):
                    continue
                slot_frames = slot.get("sentence_frames")
                if isinstance(slot_frames, list):
                    for frame in slot_frames:
                        if not isinstance(frame, dict):
                            continue
                        frame_type = frame.get("frame_type")
                        for lang in ["english", "portuguese"]:
                            old_text = frame.get(lang)
                            new_text = normalize_text(old_text, frame_type)
                            if old_text != new_text:
                                frame[lang] = new_text
                                changed = True
    
    if changed:
        return json.dumps(lesson_json), True
    return lesson_json_str, False

def fix_sentence_frames_column(frames_json_str: str) -> (str, bool):
    """Normalize sentence frames within a standalone JSON array string."""
    if not frames_json_str:
        return frames_json_str, False
    try:
        frames = json.loads(frames_json_str)
    except Exception:
        return frames_json_str, False

    if not isinstance(frames, list):
        return frames_json_str, False

    changed = False
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        
        frame_type = frame.get("frame_type")
        for lang in ["english", "portuguese"]:
            old_text = frame.get(lang)
            new_text = normalize_text(old_text, frame_type)
            if old_text != new_text:
                frame[lang] = new_text
                changed = True
    
    if changed:
        return json.dumps(frames), True
    return frames_json_str, False

def run_fix_sqlite():
    db_path = r"d:\LP\data\lesson_planner.db"
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("--- Fixing SQLite weekly_plans table ---")
    cursor.execute("SELECT id, lesson_json FROM weekly_plans")
    rows = cursor.fetchall()
    updated_plans = 0
    for plan_id, lesson_json_str in rows:
        new_json, changed = fix_lesson_json(lesson_json_str)
        if changed:
            cursor.execute("UPDATE weekly_plans SET lesson_json = ? WHERE id = ?", (new_json, plan_id))
            updated_plans += 1
    print(f"Updated {updated_plans} records in weekly_plans.")

    print("\n--- Fixing SQLite lesson_steps table ---")
    cursor.execute("SELECT id, sentence_frames FROM lesson_steps WHERE sentence_frames IS NOT NULL")
    rows = cursor.fetchall()
    updated_steps = 0
    for step_id, frames_str in rows:
        new_frames, changed = fix_sentence_frames_column(frames_str)
        if changed:
            cursor.execute("UPDATE lesson_steps SET sentence_frames = ? WHERE id = ?", (new_frames, step_id))
            updated_steps += 1
    print(f"Updated {updated_steps} records in lesson_steps.")

    conn.commit()
    conn.close()

def run_fix_supabase():
    print("\n--- Fixing Supabase ---")
    try:
        db = SupabaseDatabase()
    except Exception as e:
        print(f"Could not initialize Supabase: {e}")
        return

    # Fix weekly_plans
    print("Fetching weekly_plans from Supabase...")
    plans = db.client.table("weekly_plans").select("id, lesson_json").execute()
    updated_plans = 0
    for plan in plans.data:
        lesson_json = plan.get("lesson_json")
        if not lesson_json:
            continue
        
        # Supabase returns dict, so we can pass it through a modified fix_lesson_json or similar
        # Let's adapt fix_lesson_json to handle dict or str
        lesson_json_str = json.dumps(lesson_json) if isinstance(lesson_json, dict) else lesson_json
        new_json_str, changed = fix_lesson_json(lesson_json_str)
        
        if changed:
            db.client.table("weekly_plans").update({"lesson_json": json.loads(new_json_str)}).eq("id", plan["id"]).execute()
            updated_plans += 1
    print(f"Updated {updated_plans} records in Supabase weekly_plans.")

    # Fix lesson_steps
    print("Fetching lesson_steps from Supabase...")
    steps = db.client.table("lesson_steps").select("id, sentence_frames").not_.is_("sentence_frames", "null").execute()
    updated_steps = 0
    for step in steps.data:
        frames = step.get("sentence_frames")
        if not frames:
            continue
        
        frames_str = json.dumps(frames) if isinstance(frames, list) else frames
        new_frames_str, changed = fix_sentence_frames_column(frames_str)
        
        if changed:
            db.client.table("lesson_steps").update({"sentence_frames": json.loads(new_frames_str)}).eq("id", step["id"]).execute()
            updated_steps += 1
    print(f"Updated {updated_steps} records in Supabase lesson_steps.")

def run_fix():
    run_fix_sqlite()
    if settings.USE_SUPABASE or settings.supabase_url:
        run_fix_supabase()
    print("\nDone! Punctuation normalization complete.")

if __name__ == "__main__":
    run_fix()
