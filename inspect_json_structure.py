#!/usr/bin/env python
"""Inspect the structure of a JSON file."""

import json
import sys
from pathlib import Path

json_path = Path(r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W47\Wilson_Rodrigues_Weekly_W47_11-17-11-21_20251122_162906.json")

if not json_path.exists():
    print(f"Error: File not found: {json_path}")
    sys.exit(1)

print(f"Loading JSON file: {json_path}")
print("=" * 80)

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"\nFile size: {json_path.stat().st_size} bytes")
print(f"JSON string size: {len(json.dumps(data))} bytes")

print("\n" + "=" * 80)
print("TOP-LEVEL STRUCTURE")
print("=" * 80)

print(f"\nTop-level keys ({len(data.keys())}):")
for key in sorted(data.keys()):
    value = data[key]
    value_type = type(value).__name__
    if isinstance(value, dict):
        print(f"  {key}: dict (with {len(value)} keys)")
    elif isinstance(value, list):
        print(f"  {key}: list (with {len(value)} items)")
    elif isinstance(value, str):
        print(f"  {key}: str (length: {len(value)})")
    else:
        print(f"  {key}: {value_type}")

print("\n" + "=" * 80)
print("METADATA STRUCTURE")
print("=" * 80)

if 'metadata' in data:
    metadata = data['metadata']
    print(f"\nMetadata keys ({len(metadata.keys())}):")
    for key in sorted(metadata.keys()):
        value = metadata[key]
        print(f"  {key}: {type(value).__name__} = {repr(str(value)[:50]) if isinstance(value, str) and len(str(value)) > 50 else repr(value)}")

print("\n" + "=" * 80)
print("DAYS STRUCTURE")
print("=" * 80)

if 'days' in data:
    days = data['days']
    print(f"\nDays available ({len(days.keys())}): {list(days.keys())}")
    
    # Inspect first day structure
    if days:
        first_day = list(days.keys())[0]
        first_day_data = days[first_day]
        print(f"\nFirst day ({first_day}) structure:")
        print(f"  Type: {type(first_day_data).__name__}")
        if isinstance(first_day_data, dict):
            print(f"  Keys: {list(first_day_data.keys())}")
            if 'slots' in first_day_data:
                slots = first_day_data['slots']
                print(f"  Slots count: {len(slots)}")
                if slots:
                    first_slot = slots[0]
                    print(f"  First slot keys: {list(first_slot.keys())[:15]}...")

print("\n" + "=" * 80)
print("SPECIAL FIELDS")
print("=" * 80)

special_fields = ['_hyperlinks', '_images', '_media_schema_version']
for field in special_fields:
    if field in data:
        value = data[field]
        value_type = type(value).__name__
        if isinstance(value, dict):
            print(f"\n{field}: dict with {len(value)} keys")
            print(f"  Sample keys: {list(value.keys())[:5]}")
        elif isinstance(value, list):
            print(f"\n{field}: list with {len(value)} items")
            if value:
                print(f"  First item type: {type(value[0]).__name__}")
        else:
            print(f"\n{field}: {value_type} = {repr(value)[:100]}")
    else:
        print(f"\n{field}: NOT FOUND")

print("\n" + "=" * 80)
print("FILE SUMMARY")
print("=" * 80)

total_slots = 0
for day_name, day_data in data.get('days', {}).items():
    if isinstance(day_data, dict) and 'slots' in day_data:
        total_slots += len(day_data['slots'])

print(f"\nTotal slots across all days: {total_slots}")
print(f"Metadata week_of: {data.get('metadata', {}).get('week_of', 'N/A')}")
print(f"Metadata subject: {data.get('metadata', {}).get('subject', 'N/A')}")
print(f"Metadata teacher: {data.get('metadata', {}).get('teacher_name', 'N/A')[:50]}...")

print("\n" + "=" * 80)
print("HYPERLINKS DETAILS")
print("=" * 80)

if '_hyperlinks' in data:
    hyperlinks = data['_hyperlinks']
    print(f"\nTotal hyperlinks: {len(hyperlinks)}")
    if hyperlinks:
        print(f"\nFirst 3 hyperlinks:")
        for i, hlink in enumerate(hyperlinks[:3], 1):
            if isinstance(hlink, dict):
                print(f"  {i}. Keys: {list(hlink.keys())}")
                for k, v in hlink.items():
                    if isinstance(v, str) and len(v) > 80:
                        print(f"     {k}: {v[:80]}...")
                    else:
                        print(f"     {k}: {v}")
            else:
                print(f"  {i}. {hlink}")

print("\n" + "=" * 80)
print("SLOTS PER DAY")
print("=" * 80)

for day_name in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
    if day_name in data.get('days', {}):
        day_data = data['days'][day_name]
        if isinstance(day_data, dict) and 'slots' in day_data:
            slot_count = len(day_data['slots'])
            print(f"  {day_name.capitalize()}: {slot_count} slot(s)")

