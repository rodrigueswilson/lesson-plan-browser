#!/usr/bin/env python3
"""
Generate objectives PDF/HTML for Wilson Rodrigues using real database data.
"""

import sys
import json
from pathlib import Path
import tempfile

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.database import SQLiteDatabase
from backend.services.objectives_pdf_generator import ObjectivesPDFGenerator


def generate_wilson_objectives():
    """Generate objectives for Wilson's most recent lesson plan."""
    print("=" * 80)
    print("GENERATING OBJECTIVES FOR WILSON RODRIGUES")
    print("=" * 80)
    print()
    
    db = SQLiteDatabase()
    
    # Get Wilson's user info
    print("Finding Wilson Rodrigues...")
    wilson = db.get_user_by_name("Wilson Rodrigues")
    
    if not wilson:
        print("Wilson Rodrigues not found in database")
        return
    
    print(f"Found: {wilson.name} (ID: {wilson.id})")
    print()
    
    # Get Wilson's most recent completed plan
    print("Finding most recent completed lesson plan...")
    plans = db.get_user_plans(wilson.id, limit=5)
    
    recent_plan = None
    for plan in plans:
        if plan.status == 'completed' and plan.lesson_json:
            recent_plan = plan
            break
    
    if not recent_plan:
        print("No completed plans with lesson_json found")
        return
    
    print(f"Found: Week {recent_plan.week_of}")
    print(f"Total Slots: {getattr(recent_plan, 'total_slots', 'N/A')}")
    print()
    
    # Extract objectives
    print("Extracting objectives...")
    print("-" * 40)
    
    generator = ObjectivesPDFGenerator()
    lesson_json = recent_plan.lesson_json
    objectives = generator.extract_objectives(lesson_json)
    
    print(f"Total objectives extracted: {len(objectives)}")
    print()
    
    # Group by day
    by_day = {}
    for obj in objectives:
        day = obj['day']
        if day not in by_day:
            by_day[day] = []
        by_day[day].append(obj)
    
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
        if day in by_day:
            print(f"{day}: {len(by_day[day])} objectives")
            for i, obj in enumerate(by_day[day], 1):
                print(f"  {i}. {obj['subject']} (Slot {obj.get('slot_number', '?')})")
                print(f"     Grade: {obj.get('grade', 'N/A')}, Room: {obj.get('homeroom', 'N/A')}, Time: {obj.get('time', 'N/A')}")
                print(f"     Unit: {obj['unit_lesson'][:60]}...")
                print(f"     WIDA length: {len(obj.get('wida_objective', ''))} chars")
    
    print()
    
    # Generate HTML
    print("Generating HTML...")
    print("-" * 40)
    
    output_dir = Path(tempfile.gettempdir()) / "objectives_demo"
    output_dir.mkdir(exist_ok=True)
    
    html_path = output_dir / f"wilson_objectives_week_{recent_plan.week_of.replace('/', '-')}.html"
    html_path = generator.generate_html(
        lesson_json,
        str(html_path),
        user_name=wilson.name
    )
    
    print(f"✓ HTML generated: {html_path}")
    print()
    
    # Show sample headers
    print("Sample headers from HTML:")
    print("-" * 40)
    
    with open(html_path, 'r') as f:
        content = f.read()
    
    import re
    headers = re.findall(r'<div class="header">(.*?)</div>', content, re.DOTALL)
    
    for i, header in enumerate(headers[:5], 1):  # Show first 5
        clean_header = header.replace('<br>', ' | ').strip()
        print(f"{i}. {clean_header}")
    
    if len(headers) > 5:
        print(f"... and {len(headers) - 5} more")
    
    print()
    print("=" * 80)
    print("GENERATION COMPLETE!")
    print("=" * 80)
    print()
    print("FIXES APPLIED:")
    print("-" * 40)
    print("1. ✓ All objectives extracted (not just 7)")
    print("2. ✓ Slot-specific metadata used (grade, homeroom, time)")
    print("3. ✓ WIDA text display improved (better line-height and spacing)")
    print("4. ✓ Headers show actual slot metadata instead of merged metadata")
    print()
    print(f"Open the HTML file to view: {html_path}")
    
    # Try to open in browser
    try:
        import webbrowser
        webbrowser.open(f'file://{html_path}')
        print("\n✓ HTML file opened in default browser")
    except:
        print("\nCould not open browser automatically.")


if __name__ == "__main__":
    generate_wilson_objectives()
