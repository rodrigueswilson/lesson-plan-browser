import sys
import os
import json
from typing import Dict, List, Any

sys.path.append(os.getcwd())

from backend.database import SQLiteDatabase
from backend.config import settings

def dump_data(plan_id: str):
    db = SQLiteDatabase()
    
    # 1. Weekly Plan
    plan = db.get_weekly_plan(plan_id)
    if plan:
        print(f"--- Weekly Plan: {plan_id} ---")
        print(f"Week of: {plan.week_of}")
        print(f"User ID: {plan.user_id}")
        if plan.lesson_json:
            print(f"JSON Keys: {list(plan.lesson_json.keys())}")
            days = plan.lesson_json.get('days', {})
            print(f"Days in JSON: {list(days.keys())}")
            if days:
                first_day = list(days.keys())[0]
                day_data = days[first_day]
                print(f"Structure of '{first_day}': {list(day_data.keys())}")
                slots = day_data.get('slots', [])
                print(f"Slots in '{first_day}': {len(slots)}")
                if slots:
                    print(f"First slot keys: {list(slots[0].keys())}")
                    print(f"First slot metadata: {slots[0].get('metadata', {})}")
                    # print(f"First slot transformed_content snippet: {slots[0].get('transformed_content', '')[:100]}")
        else:
            print("Plan has NO lesson_json")

    # 2. Original Plans
    if plan:
        originals = db.get_original_lesson_plans_for_week(plan.user_id, plan.week_of)
        print(f"\n--- Original Plans ({len(originals)}) ---")
        if originals:
            first_orig = originals[0]
            print(f"Slot Number: {first_orig.slot_number}")
            print(f"Subject: {first_orig.subject}")
            print(f"content_json keys: {list(first_orig.content_json.keys()) if first_orig.content_json else 'None'}")
            if first_orig.content_json:
                # Original content_json usually has a top-level 'hyperlinks' key from extraction context
                links = first_orig.content_json.get('_extracted_hyperlinks', [])
                if not links:
                    links = first_orig.content_json.get('hyperlinks', [])
                print(f"Extracted hyperlinks found in content_json: {len(links)}")
            
            print(f"Monday content keys: {list(first_orig.monday_content.keys()) if first_orig.monday_content else 'None'}")
            if first_orig.monday_content:
                links = first_orig.monday_content.get('hyperlinks', [])
                print(f"Hyperlinks in monday_content: {len(links) if isinstance(links, list) else type(links)}")

        if plan.lesson_json:
            root_links = plan.lesson_json.get('_hyperlinks', [])
            print(f"\nRoot _hyperlinks in transformed JSON: {len(root_links)}")
            if root_links:
                print("Sample Hyperlink Metadata:")
                for i in range(min(3, len(root_links))):
                    print(f"  Link {i}: {root_links[i]}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dump_data.py <plan_id>")
    else:
        dump_data(sys.argv[1])
