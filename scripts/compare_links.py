import sys
import os
import json
import re
from typing import Dict, List, Any
from datetime import datetime

# Add the project root to sys.path
sys.path.append(os.getcwd())

from backend.database import SQLiteDatabase
from backend.config import settings

def compare_links(plan_id: str):
    db = SQLiteDatabase()
    
    # 1. Get the Weekly Plan (Transformed)
    plan = db.get_weekly_plan(plan_id)
    if not plan:
        print(f"Error: Plan {plan_id} not found.")
        return
    
    transformed_json = plan.lesson_json
    if not transformed_json:
        print(f"Error: Plan {plan_id} has no lesson_json.")
        return

    # 2. Extract Source of Truth from _hyperlinks
    all_source_links = transformed_json.get('_hyperlinks', [])
    print(f"Comparing Plan: {plan_id}")
    print(f"Total Source Links intended: {len(all_source_links)}")
    print("-" * 60)

    # Organize source links by [Day][Slot]
    source_map = {} # day -> slot -> list of links
    for link in all_source_links:
        day = (link.get('day_hint') or link.get('col_header') or 'unknown').lower().strip()
        slot = link.get('_source_slot', 'unknown')
        
        if day not in source_map: source_map[day] = {}
        if slot not in source_map[day]: source_map[day][slot] = []
        source_map[day][slot].append(link)

    # 3. Analyze Content Placement
    days_data = transformed_json.get('days', {})
    
    leaks = 0
    missing = 0
    placed_correctly = 0

    for day_name in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
        day_content = days_data.get(day_name, {})
        slots = day_content.get('slots', [])
        
        print(f"\n[{day_name.upper()}]")
        
        should_be_in_day = source_map.get(day_name, {})
        
        for slot_idx, slot_content in enumerate(slots):
            slot_num = slot_content.get('slot_number') or (slot_idx + 1)
            subject = slot_content.get('subject') or 'Unknown'
            
            def find_links_recursive(obj):
                links = []
                if isinstance(obj, str):
                    links.extend(re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', obj))
                elif isinstance(obj, list):
                    for item in obj: links.extend(find_links_recursive(item))
                elif isinstance(obj, dict):
                    for k, v in obj.items(): 
                        if k != 'metadata': # skip metadata
                            links.extend(find_links_recursive(v))
                return links

            actual_links = find_links_recursive(slot_content)
            intended_links = should_be_in_day.get(slot_num, [])
            
            print(f"  Slot {slot_num} ({subject}):")
            print(f"    - Intended links for this cell: {len(intended_links)}")
            print(f"    - Actual links found in text:  {len(actual_links)}")
            
            # Show actual links found
            for text, url in actual_links:
                # Is it an intended link for THIS SPECIFIC [Day][Slot]?
                matches = [l for l in intended_links if l.get('url') == url]
                
                if matches:
                    print(f"      - [OK] [{text}] ({url[:40]}...)")
                    placed_correctly += 1
                else:
                    # It's a leak! Where did it come from?
                    leak_info = "!! UNKNOWN SOURCE !!"
                    for s_day, s_slots in source_map.items():
                        for s_slot, s_links in s_slots.items():
                            match = next((l for l in s_links if l.get('url') == url), None)
                            if match:
                                if s_day != day_name:
                                    leak_info = f"!! LEAKED FROM {s_day.upper()} !!"
                                elif s_slot != slot_num:
                                    leak_info = f"!! LEAKED FROM SLOT {s_slot} !!"
                                else:
                                    leak_info = "!! UNKNOWN (Internal consistency error) !!"
                                break
                    print(f"      - {leak_info}: [{text}] ({url[:40]}...)")
                    leaks += 1

            # Check for Missing links
            actual_urls = [l[1] for l in actual_links]
            for il in intended_links:
                if il.get('url') not in actual_urls:
                    print(f"      - MISSING: [{il.get('text')}] ({il.get('url')[:40]}...)")
                    missing += 1

    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("-" * 60)
    print(f"Correctly Placed: {placed_correctly}")
    print(f"Leaked Links:     {leaks}")
    print(f"Missing Links:    {missing}")
    print("="*60)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/compare_links.py <plan_id>")
    else:
        compare_links(sys.argv[1])
