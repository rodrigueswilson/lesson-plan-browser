"""
Comprehensive diagnostic to trace hyperlink flow from input to output.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.docx_parser import DOCXParser

print("="*80)
print("HYPERLINK FLOW DIAGNOSTIC")
print("="*80)
print()

# Test 1: Can we extract hyperlinks from input files?
print("TEST 1: Extract hyperlinks from input file")
print("-"*80)

input_file = r'F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W43\Morais 10_20_25 - 10_24_25.docx'

parser = DOCXParser(input_file)
hyperlinks = parser.extract_hyperlinks()

print(f"Input file: {Path(input_file).name}")
print(f"Hyperlinks extracted: {len(hyperlinks)}")

if hyperlinks:
    print(f"Schema version: {hyperlinks[0].get('schema_version')}")
    print(f"Sample link:")
    sample = hyperlinks[0]
    print(f"  Text: '{sample.get('text')[:40]}'")
    print(f"  URL: {sample.get('url')[:60]}")
    print(f"  table_idx: {sample.get('table_idx')}")
    print(f"  row_idx: {sample.get('row_idx')}")
    print(f"  cell_idx: {sample.get('cell_idx')}")
    print(f"  row_label: '{sample.get('row_label')}'")
    print(f"  col_header: '{sample.get('col_header')}'")
    print()
    print("✅ Extraction works!")
else:
    print("❌ No hyperlinks extracted!")

print()

# Test 2: Can we render with hyperlinks?
print("TEST 2: Render with hyperlinks")
print("-"*80)

from tools.docx_renderer import DOCXRenderer

template_file = r"d:\LP\input\Lesson Plan Template SY'25-26.docx"
output_file = r'd:\LP\diagnostic_output.docx'

# Create minimal lesson JSON with hyperlinks
lesson_json = {
    "metadata": {
        "teacher_name": "Diagnostic Test",
        "week_dates": "10/20-10/24",
        "grade": "Test",
        "subject": "Test"
    },
    "days": {
        "monday": {
            "unit_lesson": "Test",
            "objective": {"content": "Test"},
            "anticipatory_set": {"content": "Test"},
            "tailored_instruction": {"content": "Test"},
            "misconceptions": {"content": "Test"},
            "assessment": {"content": "Test"},
            "homework": {"content": "Test"}
        }
    },
    "_hyperlinks": hyperlinks[:5] if hyperlinks else [],  # Use first 5 links
    "_media_schema_version": "2.0"
}

print(f"Lesson JSON:")
print(f"  Hyperlinks: {len(lesson_json['_hyperlinks'])}")
print(f"  Schema version: {lesson_json['_media_schema_version']}")
print()

renderer = DOCXRenderer(template_file)
success = renderer.render(lesson_json, output_file)

print(f"Rendering: {'✅ Success' if success else '❌ Failed'}")
print(f"Output file: {output_file}")
print()

# Check placement stats
if hasattr(renderer, 'placement_stats'):
    print(f"Placement statistics:")
    for strategy, count in renderer.placement_stats.items():
        print(f"  {strategy}: {count}")
print()

# Test 3: Verify output has hyperlinks
print("TEST 3: Verify output has hyperlinks")
print("-"*80)

if Path(output_file).exists():
    output_parser = DOCXParser(output_file)
    output_links = output_parser.extract_hyperlinks()
    
    print(f"Output hyperlinks: {len(output_links)}")
    
    if output_links:
        print("✅ Hyperlinks were inserted!")
        print(f"Sample: '{output_links[0].get('text')[:40]}'")
    else:
        print("❌ No hyperlinks in output!")
else:
    print("❌ Output file not created!")

print()
print("="*80)
print("DIAGNOSTIC COMPLETE")
print("="*80)
print()

if hyperlinks and output_links:
    print("✅ SYSTEM IS WORKING")
    print("   - Extraction: OK")
    print("   - Rendering: OK")
    print("   - Insertion: OK")
    print()
    print("   The issue may be with how the app calls the batch processor.")
elif hyperlinks and not output_links:
    print("⚠️  PARTIAL FAILURE")
    print("   - Extraction: OK")
    print("   - Rendering: ???")
    print("   - Insertion: FAILED")
    print()
    print("   Hyperlinks are extracted but not inserted into output.")
else:
    print("❌ SYSTEM FAILURE")
    print("   - Extraction: FAILED")
