"""
Test Phase 2.2 renderer implementation with hybrid placement.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.docx_parser import DOCXParser
from tools.docx_renderer import DOCXRenderer

INPUT_FILE = r'F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W43\10_20-10_24 Davies Lesson Plans.docx'
TEMPLATE_FILE = r"d:\LP\input\Lesson Plan Template SY'25-26.docx"
OUTPUT_FILE = r'd:\LP\test_output_phase2.docx'

# Mock lesson JSON (minimal for testing hyperlinks)
MOCK_LESSON = {
    "metadata": {
        "teacher_name": "Test Teacher",
        "week_dates": "10/20-10/24",
        "grade": "3",
        "subject": "ELA"
    },
    "days": {
        "monday": {
            "unit_lesson": "Test Unit",
            "objective": {"content": "Test objective"},
            "anticipatory_set": {"content": "Test anticipatory"},
            "tailored_instruction": {"content": "Test instruction"},
            "misconceptions": {"content": "Test misconceptions"},
            "assessment": {"content": "Test assessment"},
            "homework": {"content": "Test homework"}
        }
    }
}

def test_phase2_renderer():
    print("="*80)
    print("TESTING PHASE 2.2 RENDERER IMPLEMENTATION")
    print("="*80)
    print()
    
    # Step 1: Extract hyperlinks with v2.0 schema
    print("Step 1: Extracting hyperlinks with coordinates...")
    parser = DOCXParser(INPUT_FILE)
    hyperlinks = parser.extract_hyperlinks()
    
    print(f"Extracted {len(hyperlinks)} hyperlinks")
    print(f"Schema version: {hyperlinks[0].get('schema_version') if hyperlinks else 'N/A'}")
    print()
    
    # Step 2: Create lesson JSON with hyperlinks
    print("Step 2: Creating lesson JSON with hyperlinks...")
    lesson_json = MOCK_LESSON.copy()
    lesson_json['_hyperlinks'] = hyperlinks
    lesson_json['_media_schema_version'] = '2.0'
    
    print(f"Lesson JSON created with {len(hyperlinks)} hyperlinks")
    print(f"Media schema version: 2.0")
    print()
    
    # Step 3: Render with hybrid placement
    print("Step 3: Rendering with hybrid placement...")
    renderer = DOCXRenderer(TEMPLATE_FILE)
    
    success = renderer.render(lesson_json, OUTPUT_FILE)
    
    if success:
        print(f"✅ Rendering successful!")
        print(f"Output: {OUTPUT_FILE}")
        print()
        
        # Step 4: Show placement statistics
        print("="*80)
        print("PLACEMENT STATISTICS:")
        print("="*80)
        print()
        
        total = sum(renderer.placement_stats.values())
        for strategy, count in renderer.placement_stats.items():
            pct = (count / total * 100) if total > 0 else 0
            print(f"  {strategy}: {count} ({pct:.1f}%)")
        
        print()
        inline = (renderer.placement_stats['coordinate'] + 
                 renderer.placement_stats['label_day'] + 
                 renderer.placement_stats['fuzzy'])
        inline_rate = (inline / total * 100) if total > 0 else 0
        
        print(f"  Overall inline rate: {inline_rate:.1f}%")
        print(f"  Fallback rate: {(100 - inline_rate):.1f}%")
        print()
        
        print("="*80)
        print("TEST COMPLETE")
        print("="*80)
        print()
        print("Next steps:")
        print("  1. Open the output file in Word")
        print("  2. Verify hyperlinks are placed correctly")
        print("  3. Check placement statistics")
        
        return True
    else:
        print("❌ Rendering failed")
        return False

if __name__ == '__main__':
    success = test_phase2_renderer()
    sys.exit(0 if success else 1)
