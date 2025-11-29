"""
Check if merged JSON has proper multi-slot structure.
"""

import json
import sys
from pathlib import Path

def check_json_structure(json_path):
    """Check if JSON has slots arrays for multi-slot detection."""
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n📄 Checking: {json_path}")
    print("=" * 80)
    
    # Check top-level structure
    print("\n🔍 Top-level keys:")
    for key in data.keys():
        print(f"  - {key}")
    
    # Check if it has days
    if 'days' not in data:
        print("\n❌ PROBLEM: No 'days' key found!")
        return
    
    days = data['days']
    print(f"\n📅 Found {len(days)} days: {list(days.keys())}")
    
    # Check each day
    print("\n🔍 Checking each day structure:")
    print("-" * 80)
    
    multi_slot_days = []
    single_slot_days = []
    
    for day_name, day_data in days.items():
        print(f"\n{day_name}:")
        
        # Check for slots array
        if 'slots' in day_data:
            if isinstance(day_data['slots'], list):
                num_slots = len(day_data['slots'])
                print(f"  ✓ Has 'slots' array with {num_slots} slots")
                multi_slot_days.append(day_name)
                
                # Show slot details
                for slot in day_data['slots']:
                    slot_num = slot.get('slot_number', '?')
                    subject = slot.get('subject', 'Unknown')
                    print(f"    - Slot {slot_num}: {subject}")
            else:
                print(f"  ⚠️  Has 'slots' but it's not a list: {type(day_data['slots'])}")
        else:
            print(f"  ✗ No 'slots' array - will be treated as SINGLE-SLOT")
            single_slot_days.append(day_name)
            
            # Show what keys it has instead
            print(f"    Keys: {list(day_data.keys())[:5]}...")
    
    # Summary
    print("\n" + "=" * 80)
    print("\n📊 SUMMARY:")
    print(f"  Multi-slot days: {len(multi_slot_days)} → {multi_slot_days}")
    print(f"  Single-slot days: {len(single_slot_days)} → {single_slot_days}")
    
    # Diagnosis
    print("\n🔬 DIAGNOSIS:")
    if len(multi_slot_days) > 0 and len(single_slot_days) == 0:
        print("  ✅ All days have 'slots' arrays - multi-slot rendering will work")
    elif len(multi_slot_days) == 0 and len(single_slot_days) > 0:
        print("  ❌ NO days have 'slots' arrays - all will use single-slot rendering")
        print("  ⚠️  This means the JSON merger didn't create the slots structure!")
        print("  ⚠️  Check if json_merger.py is being called correctly")
    else:
        print("  ⚠️  MIXED: Some days multi-slot, some single-slot")
        print("  ⚠️  This is unusual - check your data")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python check_json_structure.py <path_to_merged_json>")
        print("\nExample:")
        print("  python check_json_structure.py output/Wilson_W44_merged.json")
        print("\nOr check the most recent file in output/:")
        
        # Find most recent merged JSON
        output_dir = Path("output")
        if output_dir.exists():
            json_files = list(output_dir.glob("*merged*.json"))
            if json_files:
                most_recent = max(json_files, key=lambda p: p.stat().st_mtime)
                print(f"\nMost recent: {most_recent}")
                print(f"Run: python check_json_structure.py {most_recent}")
        
        sys.exit(1)
    
    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"❌ File not found: {json_path}")
        sys.exit(1)
    
    check_json_structure(json_path)
