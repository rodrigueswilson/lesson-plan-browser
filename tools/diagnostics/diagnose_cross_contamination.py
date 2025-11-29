"""
Diagnostic script to check if hyperlinks have proper slot metadata.
Run this on your output JSON to see what's happening.
"""

import json
import sys
from pathlib import Path

def diagnose_hyperlinks(json_path):
    """Check hyperlinks in a merged JSON file."""
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"\n📄 Analyzing: {json_path}")
    print("=" * 80)
    
    # Check if it's merged JSON (has multiple slots)
    if 'slots' in data:
        print(f"✓ Multi-slot document with {len(data['slots'])} slots")
        for slot in data['slots']:
            print(f"  - Slot {slot.get('slot_number')}: {slot.get('subject')}")
    else:
        print("✗ Single-slot document")
    
    # Check hyperlinks
    if '_hyperlinks' not in data:
        print("\n⚠️  No hyperlinks found in JSON")
        return
    
    hyperlinks = data['_hyperlinks']
    print(f"\n🔗 Found {len(hyperlinks)} hyperlinks")
    print("-" * 80)
    
    # Group by slot
    by_slot = {}
    no_slot = []
    
    for link in hyperlinks:
        text = link.get('text', '')[:50]
        url = link.get('url', '')
        slot = link.get('_source_slot')
        subject = link.get('_source_subject')
        
        if slot is None:
            no_slot.append((text, url, subject))
        else:
            if slot not in by_slot:
                by_slot[slot] = []
            by_slot[slot].append((text, url, subject))
    
    # Report by slot
    for slot_num in sorted(by_slot.keys()):
        links = by_slot[slot_num]
        print(f"\n📌 Slot {slot_num}: {len(links)} hyperlinks")
        for text, url, subject in links[:5]:  # Show first 5
            print(f"   - [{subject}] {text}")
            print(f"     {url}")
        if len(links) > 5:
            print(f"   ... and {len(links) - 5} more")
    
    # Report links without slot metadata
    if no_slot:
        print(f"\n⚠️  {len(no_slot)} hyperlinks WITHOUT _source_slot:")
        for text, url, subject in no_slot[:5]:
            print(f"   - [{subject or 'NO SUBJECT'}] {text}")
            print(f"     {url}")
        if len(no_slot) > 5:
            print(f"   ... and {len(no_slot) - 5} more")
        
        print("\n❌ PROBLEM: Hyperlinks without _source_slot will not be filtered!")
        print("   They can appear in any slot during rendering.")
    else:
        print("\n✓ All hyperlinks have _source_slot metadata")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python diagnose_cross_contamination.py <path_to_merged_json>")
        print("\nExample:")
        print("  python diagnose_cross_contamination.py output/Wilson_W44_merged.json")
        sys.exit(1)
    
    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"❌ File not found: {json_path}")
        sys.exit(1)
    
    diagnose_hyperlinks(json_path)
