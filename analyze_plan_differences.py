
import sys
import os
import json
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.getcwd())

from backend.database import SQLiteDatabase
from backend.schema import WeeklyPlan, OriginalLessonPlan

def analyze_plan_differences(plan_id: str):
    print(f"Analyzing Plan: {plan_id}")
    db = SQLiteDatabase()
    
    # 1. Get Transformed Plan
    transformed_plan = db.get_weekly_plan(plan_id)
    if not transformed_plan:
        print(f"[ERROR] Error: Plan {plan_id} not found in weekly_plans table.")
        return

    transformed_json = transformed_plan.lesson_json
    if not transformed_json:
        print("[ERROR] Error: Transformed plan has no lesson_json.")
        return
        
    print(f"[OK] Found Transformed Plan (Week: {transformed_plan.week_of})")

    # 2. Get Original Plans for this user/week
    # We need to find the originals that correspond to this week.
    # The originals table has `week_of` and `user_id`.
    
    user_id = transformed_plan.user_id
    week_of = transformed_plan.week_of
    
    with db.get_connection() as session:
        # Query originals using SQLModel session for better filtering
        from sqlmodel import select
        statement = select(OriginalLessonPlan).where(
            OriginalLessonPlan.user_id == user_id,
            OriginalLessonPlan.week_of == week_of
        )
        originals = session.exec(statement).all()
        
    if not originals:
        print(f"[ERROR] Error: No OriginalLessonPlans found for user {user_id} and week {week_of}.")
        return

    print(f"[OK] Found {len(originals)} Original Lesson Plans.")
    
    # 3. Compare Slot by Slot
    transformed_days = transformed_json.get("days", {})
    
    # Flatten transformed slots for easier lookup
    transformed_slots_map = {} # slot_number -> subject -> content
    
    for day, day_content in transformed_days.items():
        if day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            slots = day_content.get("slots", [])
            for slot in slots:
                s_num = slot.get("slot_number")
                subj = slot.get("subject")
                if s_num and subj:
                    if s_num not in transformed_slots_map: transformed_slots_map[s_num] = {}
                    # Store by day as well? No, let's just grab the Monday content as a sample
                    if day not in transformed_slots_map[s_num]: transformed_slots_map[s_num][day] = {}
                    transformed_slots_map[s_num][day] = slot

    print("\n" + "="*80)
    print("COMPARISON (Original vs Transformed)")
    print("="*80)

    from rapidfuzz import fuzz

    stats = {
        "total_slots": 0,
        "objective_matches": 0,
        "avg_objective_similarity": 0.0,
        "avg_instruction_retention": 0.0,
        "instruction_missing": 0
    }

    print("\n" + "="*80)
    print(f"{'Slot':<10} | {'Subj':<15} | {'Obj Sim':<10} | {'Instr Len':<10} | {'Retention':<10}")
    print("-" * 80)

    for orig in originals:
        s_num = orig.slot_number
        
        # Get flattened original text for comparison
        orig_full_text = orig.full_text or ""
        if len(orig_full_text) < 10: continue # Skip empty slots
        
        # Check transformed versions (Monday)
        ts_slots = transformed_slots_map.get(s_num, {})
        monday_ts = ts_slots.get("monday")
        
        if not monday_ts:
            continue
            
        stats["total_slots"] += 1
        
        # 1. Objective Similarity
        ts_obj = ""
        if isinstance(monday_ts.get("objective"), dict):
            ts_obj = monday_ts["objective"].get("content_objective", "")
        elif isinstance(monday_ts.get("objective"), str):
             ts_obj = monday_ts.get("objective")
        
        obj_sim = 0
        if ts_obj:
            obj_sim = fuzz.partial_ratio(ts_obj.lower(), orig_full_text.lower())
        
        stats["avg_objective_similarity"] += obj_sim
        if obj_sim > 90: stats["objective_matches"] += 1

        # 2. Instruction Retention
        ts_instr = ""
        if isinstance(monday_ts.get("instruction"), dict):
            ts_instr = monday_ts["instruction"].get("activities", "")
        
        if not ts_instr and isinstance(monday_ts.get("tailored_instruction"), dict):
             ts_instr = monday_ts["tailored_instruction"].get("original_content", "")

        ts_len = len(ts_instr) if ts_instr else 0
        orig_len = len(orig_full_text)
        retention = (ts_len / orig_len * 100) if orig_len > 0 else 0
        
        stats["avg_instruction_retention"] += retention
        if not ts_instr: stats["instruction_missing"] += 1

        print(f"{s_num:<10} | {orig.subject[:14]:<15} | {obj_sim:>9.1f}% | {ts_len:>10} | {retention:>9.1f}%")

    # Final Stats
    if stats["total_slots"] > 0:
        stats["avg_objective_similarity"] /= stats["total_slots"]
        stats["avg_instruction_retention"] /= stats["total_slots"]
    
    print("="*80)
    print("SUMMARY")
    print(f"Total Slots Analyzed:      {stats['total_slots']}")
    print(f"Avg Objective Similarity:  {stats['avg_objective_similarity']:.1f}% (Targets > 90% implies extraction vs rewriting)")
    print(f"Avg Instruction Retention: {stats['avg_instruction_retention']:.1f}% (Transformed / Original length)")
    print(f"Empty Instructions:        {stats['instruction_missing']}")
    print("="*80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_plan_differences.py <plan_id>")
    else:
        analyze_plan_differences(sys.argv[1])
