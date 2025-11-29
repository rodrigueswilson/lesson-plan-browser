#!/usr/bin/env python3
"""
Inspect real lesson plan data from the database to understand the actual structure.
"""

import sys
import json
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.database import SQLiteDatabase

def inspect_wilson_data():
    """Inspect Wilson Rodrigues's actual lesson plan data."""
    print("=" * 80)
    print("INSPECTING WILSON RODRIGUES'S LESSON PLAN DATA")
    print("=" * 80)
    print()
    
    db = SQLiteDatabase()
    
    # Get Wilson's user info
    print("FINDING WILSON RODRIGUES...")
    print("-" * 40)
    
    wilson = db.get_user_by_name("Wilson Rodrigues")
    
    if not wilson:
        print("Wilson Rodrigues not found in database")
        print("Trying alternative names...")
        wilson = db.get_user_by_name("wilson rodrigues")
    
    if not wilson:
        print("User not found. Please check the exact name in the database.")
        return
    
    print(f"Found: {wilson.name} (ID: {wilson.id})")
    print()
    
    # Get Wilson's recent lesson plans
    print("RECENT LESSON PLANS:")
    print("-" * 40)
    
    plans = db.get_user_plans(wilson.id, limit=5)
    
    if not plans:
        print("No lesson plans found")
        return
    
    for i, plan in enumerate(plans, 1):
        print(f"{i}. Week {plan.week_of} - Status: {plan.status}")
        print(f"   File: {getattr(plan, 'output_file', 'N/A')}")
        print(f"   Slots: {getattr(plan, 'total_slots', 'N/A')}")
        print(f"   Created: {getattr(plan, 'created_at', 'N/A')}")
        print()
    
    # Inspect the most recent completed plan
    print("INSPECTING MOST RECENT COMPLETED PLAN:")
    print("-" * 40)
    
    recent_plan = None
    for plan in plans:
        if plan.status == 'completed' and plan.lesson_json:
            recent_plan = plan
            break
    
    if not recent_plan:
        print("No completed plans with lesson_json found")
        return
    
    lesson_json = recent_plan.lesson_json
    
    print(f"Week: {recent_plan.week_of}")
    print(f"Total Slots: {getattr(recent_plan, 'total_slots', 'N/A')}")
    print()
    
    # Inspect metadata
    print("METADATA:")
    print("-" * 40)
    metadata = lesson_json.get('metadata', {})
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    print()
    
    # Inspect days structure
    print("DAYS STRUCTURE:")
    print("-" * 40)
    days = lesson_json.get('days', {})
    
    for day_name in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
        if day_name not in days:
            continue
        
        day_data = days[day_name]
        print(f"\n{day_name.upper()}:")
        
        # Check if it's multi-slot
        if 'slots' in day_data:
            slots = day_data['slots']
            print(f"  Slots: {len(slots)}")
            
            for slot in slots:
                print(f"\n  Slot {slot.get('slot_number', '?')}:")
                print(f"    Subject: {slot.get('subject', 'N/A')}")
                print(f"    Grade: {slot.get('grade', 'N/A')}")
                print(f"    Homeroom: {slot.get('homeroom', 'N/A')}")
                print(f"    Teacher: {slot.get('teacher_name', 'N/A')}")
                print(f"    Time: {slot.get('time', 'N/A')}")
                print(f"    Unit: {slot.get('unit_lesson', 'N/A')[:60]}...")
                
                objective = slot.get('objective', {})
                if objective:
                    student_goal = objective.get('student_goal', '')
                    wida = objective.get('wida_objective', '')
                    print(f"    Student Goal: {student_goal[:60]}...")
                    print(f"    WIDA Length: {len(wida)} chars")
                    if len(wida) > 100:
                        print(f"    WIDA Preview: {wida[:100]}...")
        else:
            # Single slot structure
            print(f"  Single slot structure")
            print(f"  Subject: {day_data.get('subject', 'N/A')}")
            print(f"  Unit: {day_data.get('unit_lesson', 'N/A')[:60]}...")
    
    print()
    print("=" * 80)
    print("INSPECTION COMPLETE")
    print("=" * 80)
    
    # Save sample to file for reference
    sample_file = Path("wilson_lesson_sample.json")
    with open(sample_file, 'w') as f:
        json.dump(lesson_json, f, indent=2)
    
    print(f"\nFull lesson JSON saved to: {sample_file}")


if __name__ == "__main__":
    inspect_wilson_data()
