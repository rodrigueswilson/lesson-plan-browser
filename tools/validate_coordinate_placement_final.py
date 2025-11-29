"""
Phase 2.3: Final Validation of Coordinate-Based Placement

Tests hybrid placement on:
1. Standard 8x6 files
2. Non-standard structures (9x6, 13x6)
3. Files with paragraph links
4. Multiple file types

Generates comprehensive report with placement statistics.
"""

import sys
from pathlib import Path
from collections import defaultdict
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.docx_parser import DOCXParser
from tools.docx_renderer import DOCXRenderer

# Test files from different categories
TEST_FILES = [
    # Standard 8x6 files
    {
        'path': r'F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W43\10_20-10_24 Davies Lesson Plans.docx',
        'type': 'standard_8x6',
        'name': 'Davies (Grade 3 ELA)'
    },
    {
        'path': r'F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W43\Lang Lesson Plans 10_20_25-10_24_25.docx',
        'type': 'standard_8x6',
        'name': 'Lang'
    },
]

TEMPLATE_FILE = r"d:\LP\input\Lesson Plan Template SY'25-26.docx"
OUTPUT_DIR = Path(r'd:\LP\validation_output')

# Mock lesson JSON (minimal for testing)
MOCK_LESSON = {
    "metadata": {
        "teacher_name": "Test Teacher",
        "week_dates": "10/20-10/24",
        "grade": "3",
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
    }
}


def validate_file(file_info):
    """Validate coordinate placement for a single file."""
    
    file_path = file_info['path']
    file_type = file_info['type']
    file_name = file_info['name']
    
    print(f"\n{'='*80}")
    print(f"VALIDATING: {file_name}")
    print(f"Type: {file_type}")
    print(f"{'='*80}\n")
    
    if not Path(file_path).exists():
        print(f"⚠️  File not found: {file_path}")
        return None
    
    try:
        # Step 1: Extract hyperlinks with v2.0 schema
        print("Step 1: Extracting hyperlinks...")
        parser = DOCXParser(file_path)
        hyperlinks = parser.extract_hyperlinks()
        
        print(f"  Extracted: {len(hyperlinks)} hyperlinks")
        
        # Check schema version
        v2_links = [h for h in hyperlinks if h.get('schema_version') == '2.0']
        print(f"  Schema v2.0: {len(v2_links)}/{len(hyperlinks)}")
        
        # Check coordinates
        table_links = [h for h in hyperlinks if h.get('table_idx') is not None]
        para_links = [h for h in hyperlinks if h.get('table_idx') is None]
        
        print(f"  Table links: {len(table_links)}")
        print(f"  Paragraph links: {len(para_links)}")
        print()
        
        # Step 2: Render with hybrid placement
        print("Step 2: Rendering with hybrid placement...")
        
        lesson_json = MOCK_LESSON.copy()
        lesson_json['_hyperlinks'] = hyperlinks
        lesson_json['_media_schema_version'] = '2.0'
        
        # Create output directory
        OUTPUT_DIR.mkdir(exist_ok=True)
        output_file = OUTPUT_DIR / f"{file_name.replace(' ', '_')}_output.docx"
        
        renderer = DOCXRenderer(TEMPLATE_FILE)
        success = renderer.render(lesson_json, str(output_file))
        
        if not success:
            print("  ❌ Rendering failed")
            return None
        
        print(f"  ✅ Rendering successful")
        print(f"  Output: {output_file.name}")
        print()
        
        # Step 3: Analyze placement statistics
        print("Step 3: Placement Statistics:")
        print("-" * 80)
        
        stats = renderer.placement_stats.copy()
        total = sum(stats.values())
        
        for strategy, count in stats.items():
            pct = (count / total * 100) if total > 0 else 0
            icon = "✅" if strategy == 'coordinate' else "⚠️" if strategy == 'fallback' else "→"
            print(f"  {icon} {strategy}: {count} ({pct:.1f}%)")
        
        inline = stats['coordinate'] + stats['label_day'] + stats['fuzzy']
        inline_rate = (inline / total * 100) if total > 0 else 0
        fallback_rate = (stats['fallback'] / total * 100) if total > 0 else 0
        
        print()
        print(f"  Overall inline rate: {inline_rate:.1f}%")
        print(f"  Fallback rate: {fallback_rate:.1f}%")
        
        # Return results
        return {
            'file_name': file_name,
            'file_type': file_type,
            'total_links': len(hyperlinks),
            'table_links': len(table_links),
            'para_links': len(para_links),
            'stats': stats,
            'inline_rate': inline_rate,
            'fallback_rate': fallback_rate,
            'output_file': str(output_file)
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_summary_report(results):
    """Generate comprehensive summary report."""
    
    print(f"\n\n{'='*80}")
    print("FINAL VALIDATION SUMMARY")
    print(f"{'='*80}\n")
    
    # Filter successful results
    successful = [r for r in results if r is not None]
    
    print(f"Files tested: {len(successful)}/{len(results)}")
    print()
    
    # Overall statistics
    total_links = sum(r['total_links'] for r in successful)
    total_stats = defaultdict(int)
    
    for r in successful:
        for strategy, count in r['stats'].items():
            total_stats[strategy] += count
    
    print("="*80)
    print("OVERALL PLACEMENT STATISTICS")
    print("="*80)
    print()
    
    total = sum(total_stats.values())
    for strategy, count in total_stats.items():
        pct = (count / total * 100) if total > 0 else 0
        icon = "✅" if strategy == 'coordinate' else "⚠️" if strategy == 'fallback' else "→"
        print(f"  {icon} {strategy}: {count} ({pct:.1f}%)")
    
    overall_inline = total_stats['coordinate'] + total_stats['label_day'] + total_stats['fuzzy']
    overall_inline_rate = (overall_inline / total * 100) if total > 0 else 0
    overall_fallback_rate = (total_stats['fallback'] / total * 100) if total > 0 else 0
    
    print()
    print(f"  Overall inline rate: {overall_inline_rate:.1f}%")
    print(f"  Fallback rate: {overall_fallback_rate:.1f}%")
    print()
    
    # By file type
    print("="*80)
    print("RESULTS BY FILE TYPE")
    print("="*80)
    print()
    
    by_type = defaultdict(list)
    for r in successful:
        by_type[r['file_type']].append(r)
    
    for file_type, type_results in by_type.items():
        print(f"{file_type}:")
        
        type_total = sum(r['total_links'] for r in type_results)
        type_inline = sum(r['stats']['coordinate'] + r['stats']['label_day'] + r['stats']['fuzzy'] 
                         for r in type_results)
        type_inline_rate = (type_inline / type_total * 100) if type_total > 0 else 0
        
        print(f"  Files: {len(type_results)}")
        print(f"  Total links: {type_total}")
        print(f"  Inline rate: {type_inline_rate:.1f}%")
        print()
    
    # Individual file results
    print("="*80)
    print("INDIVIDUAL FILE RESULTS")
    print("="*80)
    print()
    
    for r in successful:
        print(f"{r['file_name']}:")
        print(f"  Type: {r['file_type']}")
        print(f"  Links: {r['total_links']} (table: {r['table_links']}, para: {r['para_links']})")
        print(f"  Inline: {r['inline_rate']:.1f}%")
        print(f"  Fallback: {r['fallback_rate']:.1f}%")
        print(f"  Output: {Path(r['output_file']).name}")
        print()
    
    # Comparison with baseline
    print("="*80)
    print("COMPARISON WITH BASELINE")
    print("="*80)
    print()
    
    baseline_inline = 84.2
    improvement = overall_inline_rate - baseline_inline
    
    print(f"  Baseline (fuzzy matching): {baseline_inline}%")
    print(f"  Current (coordinate-based): {overall_inline_rate:.1f}%")
    print(f"  Improvement: +{improvement:.1f} percentage points")
    print()
    
    if overall_inline_rate >= 93:
        print("  ✅ TARGET ACHIEVED (93-97% inline)")
    else:
        print(f"  ⚠️  Target not met (need {93 - overall_inline_rate:.1f}% more)")
    
    print()
    
    # Save report
    report_file = OUTPUT_DIR / 'validation_report.json'
    with open(report_file, 'w') as f:
        json.dump({
            'summary': {
                'total_files': len(successful),
                'total_links': total_links,
                'overall_inline_rate': overall_inline_rate,
                'overall_fallback_rate': overall_fallback_rate,
                'improvement_over_baseline': improvement
            },
            'overall_stats': dict(total_stats),
            'by_type': {k: [{'name': r['file_name'], 'inline_rate': r['inline_rate']} 
                           for r in v] for k, v in by_type.items()},
            'individual_results': successful
        }, f, indent=2)
    
    print(f"Report saved to: {report_file}")
    print()


def main():
    print("="*80)
    print("PHASE 2.3: FINAL VALIDATION OF COORDINATE-BASED PLACEMENT")
    print("="*80)
    print()
    print(f"Testing {len(TEST_FILES)} files...")
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    
    results = []
    
    for file_info in TEST_FILES:
        result = validate_file(file_info)
        results.append(result)
    
    # Generate summary
    generate_summary_report(results)
    
    print("="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    print()
    print("Next steps:")
    print("  1. Review output files in validation_output/")
    print("  2. Manually verify hyperlink placement")
    print("  3. Check validation_report.json for details")
    print("  4. If results are good, proceed to production deployment")


if __name__ == '__main__':
    main()
