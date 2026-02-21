
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import re
import sqlite3
from typing import Any, Dict, List
from collections import Counter

# Mocking parts of the system to test the logic
def normalize_subj(s):
    if not s:
        return ""
    return re.sub(r"[^a-z0-9]", "", s.lower())

def test_wilson_enrichment():
    DB_PATH = "d:/LP/data/lesson_planner.db"
    USER_ID = "04fe8898-cb89-4a73-affb-64a97a98f820"
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get Wilson's slots
    cursor.execute("SELECT slot_number, subject FROM class_slots WHERE user_id = ?", (USER_ID,))
    slots = [dict(row) for row in cursor.fetchall()]
    
    # Get Wilson's schedule
    cursor.execute("SELECT slot_number, subject, start_time, end_time, is_active FROM schedules WHERE user_id = ?", (USER_ID,))
    schedule_entries_dict = [dict(row) for row in cursor.fetchall()]
    
    print(f"Testing enrichment for {len(slots)} slots...")
    
    # Apply the new logic
    for slot in slots:
        slot_subj_norm = normalize_subj(slot.get("subject", ""))
        slot_num = slot.get("slot_number")

        # Find matching schedule entry using a multi-stage strategy
        # Stage 1: Match by both subject and slot number (tightest)
        matching_entries = [
            e
            for e in schedule_entries_dict
            if normalize_subj(e.get("subject", "")) == slot_subj_norm
            and e.get("slot_number") == slot_num
            and e.get("is_active") == 1
        ]

        # Stage 2: Match by subject only (useful if slot numbers shifted)
        if not matching_entries:
            matching_entries = [
                e
                for e in schedule_entries_dict
                if normalize_subj(e.get("subject", "")) == slot_subj_norm
                and e.get("is_active") == 1
            ]

        # Stage 3: Match by slot number only (legacy fallback)
        if not matching_entries:
            matching_entries = [
                e
                for e in schedule_entries_dict
                if e.get("slot_number") == slot_num
                and e.get("is_active") == 1
            ]

        if matching_entries:
            times = [(e.get("start_time"), e.get("end_time")) for e in matching_entries]
            most_common_time = Counter(times).most_common(1)[0][0]
            slot["start_time"] = most_common_time[0]
            slot["end_time"] = most_common_time[1]
            print(f"SUCCESS: Slot {slot['slot_number']} ({slot['subject']}) -> {slot['start_time']} - {slot['end_time']}")
        else:
            print(f"FAIL: No schedule entry found for slot {slot['slot_number']} ({slot['subject']})")

    # Verify specific expectations
    ela_slot = next(s for s in slots if s['subject'] == 'ELA')
    elass_slot = next(s for s in slots if s['subject'] == 'ELA/SS')
    
    print("\nVerification:")
    if ela_slot['start_time'] == '08:30':
        print("✓ ELA correctly assigned 08:30")
    else:
        print(f"✗ ELA assigned {ela_slot['start_time']}, expected 08:30")
        
    if elass_slot['start_time'] == '09:18':
        print("✓ ELA/SS correctly assigned 09:18")
    else:
        print(f"✗ ELA/SS assigned {elass_slot['start_time']}, expected 09:18")

def test_json_merger_sorting():
    from tools.json_merger import merge_lesson_jsons
    
    print("\nTesting JSON Merger sorting...")
    
    # Simulate lessons with times
    lessons = [
        {
            'slot_number': 1,
            'subject': 'ELA',
            'lesson_json': {
                'metadata': {'start_time': '08:30'},
                'days': {'monday': {'unit_lesson': 'ELA Lesson'}}
            }
        },
        {
            'slot_number': 2,
            'subject': 'ELA/SS',
            'lesson_json': {
                'metadata': {'start_time': '09:18'},
                'days': {'monday': {'unit_lesson': 'ELA/SS Lesson'}}
            }
        }
    ]
    
    # Test case where slot number order DOES NOT match time order
    lessons_out_of_order = [
         {
            'slot_number': 5, # High slot number
            'subject': 'Math',
            'lesson_json': {
                'metadata': {'start_time': '08:00'}, # but earliest time
                'days': {'monday': {'unit_lesson': 'Early Math'}}
            }
        },
        {
            'slot_number': 1, # Low slot number
            'subject': 'ELA',
            'lesson_json': {
                'metadata': {'start_time': '09:00'}, # but later time
                'days': {'monday': {'unit_lesson': 'Late ELA'}}
            }
        }
    ]
    
    merged = merge_lesson_jsons(lessons_out_of_order)
    slots = merged['days']['monday']['slots']
    
    print("Merged order (should be by time):")
    for s in slots:
        print(f"  Slot {s['slot_number']} ({s['subject']}): {s.get('start_time')}")
        
    if slots[0]['subject'] == 'Math' and slots[1]['subject'] == 'ELA':
        print("✓ Chronological sorting success!")
    else:
        print("✗ Sorting failed (likely still using slot_number)")

if __name__ == "__main__":
    test_wilson_enrichment()
    try:
        test_json_merger_sorting()
    except Exception as e:
        print(f"Error in merger test: {e}")
