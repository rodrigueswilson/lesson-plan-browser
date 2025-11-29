"""
Analyze hyperlink placement diagnostics from log files.
Generates summary report of failure patterns.

Usage:
    python tools/analyze_hyperlink_diagnostics.py <log_file>
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
import sys


def parse_log_file(log_path: str):
    """Parse structured log file and extract hyperlink diagnostics."""
    diagnostics = []
    
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if 'hyperlink_placement_diagnostic' in line or 'hyperlink_placement_fallback' in line:
                try:
                    # Extract JSON from structured log
                    # Look for the 'extra' field which contains our diagnostic data
                    if '"extra":' in line:
                        # Find the extra field
                        extra_start = line.find('"extra":')
                        if extra_start != -1:
                            # Extract from extra to end of line
                            json_part = line[extra_start + 8:].strip()
                            # Remove trailing characters
                            if json_part.endswith('}'):
                                json_part = json_part[:-1]  # Remove final }
                            if json_part.startswith('{'):
                                data = json.loads(json_part)
                                diagnostics.append(data)
                except Exception as e:
                    # Try alternative parsing
                    try:
                        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', line)
                        if json_match:
                            data = json.loads(json_match.group())
                            if 'link_text' in data or 'result' in data:
                                diagnostics.append(data)
                    except:
                        pass  # Skip unparseable lines
    
    return diagnostics


def analyze_diagnostics(diagnostics):
    """Analyze diagnostic data and generate report."""
    
    total = len(diagnostics)
    if total == 0:
        print("No diagnostic data found.")
        print("\nTip: Make sure you've processed lesson plans with the updated code.")
        print("Check that logging is enabled and log file path is correct.")
        return
    
    # Count results
    results = Counter(d.get('result', 'unknown') for d in diagnostics)
    
    # Count structure types
    structures = Counter(d.get('structure_type', 'unknown') for d in diagnostics)
    
    # Analyze failures by strategy
    label_day_failures = [d for d in diagnostics if 'label_day' in d.get('strategy_attempted', []) and d.get('result') != 'success_label_day']
    fuzzy_failures = [d for d in diagnostics if 'fuzzy' in d.get('strategy_attempted', []) and d.get('result') != 'success_fuzzy']
    
    # Analyze label lookup failures
    label_lookup_fails = defaultdict(int)
    for d in label_day_failures:
        label = d.get('row_label', 'unknown')
        lookup = d.get('label_lookup')
        if lookup is None:
            label_lookup_fails[label] += 1
    
    # Analyze day lookup failures
    day_lookup_fails = defaultdict(int)
    for d in label_day_failures:
        day = d.get('day_hint', 'unknown')
        lookup = d.get('day_lookup')
        if lookup is None:
            day_lookup_fails[day] += 1
    
    # Generate report
    print("=" * 80)
    print("HYPERLINK PLACEMENT DIAGNOSTIC REPORT")
    print("=" * 80)
    print(f"\nTotal Links Analyzed: {total}")
    
    print(f"\n{'='*80}")
    print("PLACEMENT RESULTS")
    print(f"{'='*80}")
    for result, count in results.most_common():
        pct = (count / total) * 100
        status = "✓" if "success" in result else "✗"
        print(f"  {status} {result:30s}: {count:4d} ({pct:5.1f}%)")
    
    # Calculate overall success rate
    success_count = sum(count for result, count in results.items() if 'success' in result)
    success_rate = (success_count / total) * 100
    print(f"\n  Overall Success Rate: {success_count}/{total} ({success_rate:.1f}%)")
    
    print(f"\n{'='*80}")
    print("STRUCTURE TYPES")
    print(f"{'='*80}")
    for struct, count in structures.most_common():
        pct = (count / total) * 100
        print(f"  {struct:30s}: {count:4d} ({pct:5.1f}%)")
    
    print(f"\n{'='*80}")
    print("STRATEGY ANALYSIS")
    print(f"{'='*80}")
    
    print(f"\nLabel+Day Strategy:")
    print(f"  Attempted: {len([d for d in diagnostics if 'label_day' in d.get('strategy_attempted', [])])}")
    print(f"  Succeeded: {len([d for d in diagnostics if d.get('result') == 'success_label_day'])}")
    print(f"  Failed: {len(label_day_failures)}")
    
    if label_lookup_fails:
        print(f"\n  Top Row Labels Not Found (lookup returned None):")
        for label, count in sorted(label_lookup_fails.items(), key=lambda x: -x[1])[:10]:
            print(f"    '{label}': {count} times")
    
    if day_lookup_fails:
        print(f"\n  Top Day Hints Not Found (lookup returned None):")
        for day, count in sorted(day_lookup_fails.items(), key=lambda x: -x[1])[:10]:
            print(f"    '{day}': {count} times")
    
    print(f"\nFuzzy Match Strategy:")
    print(f"  Attempted: {len([d for d in diagnostics if 'fuzzy' in d.get('strategy_attempted', [])])}")
    print(f"  Succeeded: {len([d for d in diagnostics if d.get('result') == 'success_fuzzy'])}")
    print(f"  Failed: {len(fuzzy_failures)}")
    
    # Sample fallback cases
    fallbacks = [d for d in diagnostics if d.get('result') == 'fallback']
    if fallbacks:
        print(f"\n{'='*80}")
        print(f"FALLBACK CASES (first 5 of {len(fallbacks)})")
        print(f"{'='*80}")
        for i, d in enumerate(fallbacks[:5], 1):
            print(f"\n  {i}. Link: '{d.get('link_text', 'unknown')}'")
            print(f"     URL: {d.get('url', 'unknown')}")
            print(f"     Input Coords: {d.get('input_coords', 'unknown')}")
            print(f"     Row Label: '{d.get('row_label', 'unknown')}'")
            print(f"     Day Hint: '{d.get('day_hint', 'unknown')}'")
            print(f"     Section Hint: '{d.get('section_hint', 'unknown')}'")
            print(f"     Structure Type: {d.get('structure_type', 'unknown')}")
            print(f"     Strategies Tried: {', '.join(d.get('strategy_attempted', []))}")
            print(f"     Label Lookup Result: {d.get('label_lookup', 'N/A')}")
            print(f"     Day Lookup Result: {d.get('day_lookup', 'N/A')}")
            if 'label_day_failure' in d:
                print(f"     Label/Day Failure: {d['label_day_failure']}")
    
    # Recommendations
    print(f"\n{'='*80}")
    print("RECOMMENDATIONS")
    print(f"{'='*80}")
    
    if success_rate < 70:
        print("\n⚠️  Success rate is below 70%. Immediate action needed.")
    elif success_rate < 90:
        print("\n⚠️  Success rate is below 90%. Improvements recommended.")
    else:
        print("\n✓ Success rate is good (>90%).")
    
    if label_lookup_fails:
        print("\n• Fix label normalization - many row labels not being found")
        print("  Consider adding more label variations to ROW_PATTERNS")
    
    if day_lookup_fails:
        print("\n• Fix day extraction - day hints not being found in column headers")
        print("  Check _extract_day_from_header() and _build_col_map()")
    
    if len(fuzzy_failures) > total * 0.3:
        print("\n• Fuzzy matching failing frequently - consider lowering threshold")
        print("  Current threshold: 0.65, try 0.50 for bilingual content")
    
    if structures.get('adaptive', 0) > total * 0.2:
        print("\n• Many unknown structures detected - enhance TableStructureDetector")
        print("  Add support for common teacher table formats")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python tools/analyze_hyperlink_diagnostics.py <log_file>")
        print("\nExample:")
        print("  python tools/analyze_hyperlink_diagnostics.py backend/logs/app.log")
        sys.exit(1)
    
    log_path = sys.argv[1]
    
    if not Path(log_path).exists():
        print(f"Error: Log file not found: {log_path}")
        sys.exit(1)
    
    print(f"Analyzing log file: {log_path}\n")
    diagnostics = parse_log_file(log_path)
    
    if not diagnostics:
        print("No hyperlink diagnostic data found in log file.")
        print("\nPossible reasons:")
        print("  1. No lesson plans have been processed yet")
        print("  2. Log file is from before diagnostic code was added")
        print("  3. Logging level is too high (should be INFO or DEBUG)")
        sys.exit(1)
    
    analyze_diagnostics(diagnostics)
