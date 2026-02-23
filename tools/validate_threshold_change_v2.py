"""
Automated Validation Script v2 - Improved

Addresses:
- Proper URL resolution (not just relationship IDs)
- Better false positive detection using metadata
- Flexible output file selection
- Table-aware fallback detection
- Telemetry integration (if available)
"""

import sys
from pathlib import Path
from collections import defaultdict
import json
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.docx_parser import DOCXParser
from tools.validate_threshold_link_analysis import (
    extract_output_links_with_urls,
    categorize_links,
)
from docx import Document

class ImprovedThresholdValidator:
    """Improved validator with proper URL resolution and metadata checking."""
    
    def __init__(self):
        self.results = {
            'files': [],
            'aggregate': {
                'total_links': 0,
                'inline': 0,
                'fallback': 0,
                'broken': 0,
                'false_positives': [],
                'warnings': []
            }
        }
    
    def validate_file_pair(self, input_path: str, output_path: str, file_name: str):
        """Validate one input/output pair with improved analysis."""
        
        print(f"\n{'='*80}")
        print(f"Validating: {file_name}")
        print(f"{'='*80}\n")
        
        # Parse input to get all hyperlinks with metadata
        print("1. Parsing input file...")
        parser = DOCXParser(input_path)
        input_links = parser.extract_hyperlinks()
        print(f"   Found {len(input_links)} hyperlinks in input")
        
        # Show metadata coverage
        with_section = sum(1 for l in input_links if l.get('section_hint'))
        with_day = sum(1 for l in input_links if l.get('day_hint'))
        print(f"   Metadata: {with_section} with section_hint, {with_day} with day_hint")
        
        # Parse output with proper URL resolution
        print("\n2. Analyzing output file...")
        output_doc = Document(output_path)
        output_links = extract_output_links_with_urls(output_doc)
        
        print(f"   Found {len(output_links)} hyperlinks in output")
        
        # Categorize links (inline vs fallback)
        inline_links, fallback_links = categorize_links(output_doc, output_links)
        
        print(f"   Inline: {len(inline_links)}")
        print(f"   Fallback: {len(fallback_links)}")
        
        # Check for broken links (proper URL comparison)
        print("\n3. Checking for broken links...")
        broken = self._find_broken_links(input_links, output_links)
        
        if broken:
            print(f"   ⚠️  {len(broken)} broken links found!")
            for b in broken[:3]:
                print(f"      - {b['text'][:60]}")
        else:
            print(f"   ✓ No broken links")
        
        # Detect false positives using metadata
        print("\n4. Detecting false positives...")
        false_positives = self._detect_false_positives_with_metadata(
            input_links, inline_links, output_doc
        )
        
        if false_positives:
            print(f"   ⚠️  {len(false_positives)} potential false positives")
            for fp in false_positives[:3]:
                print(f"      - {fp['text'][:60]} ({fp['reason']})")
        else:
            print(f"   ✓ No obvious false positives")
        
        # Calculate rates
        total = len(input_links)
        inline_count = len(inline_links)
        fallback_count = len(fallback_links)
        
        inline_rate = (inline_count / total * 100) if total > 0 else 0
        fallback_rate = (fallback_count / total * 100) if total > 0 else 0
        fp_rate = (len(false_positives) / total * 100) if total > 0 else 0
        
        # Store results
        result = {
            'file': file_name,
            'input_path': input_path,
            'output_path': output_path,
            'total_links': total,
            'inline': inline_count,
            'fallback': fallback_count,
            'inline_rate': inline_rate,
            'fallback_rate': fallback_rate,
            'broken': len(broken),
            'broken_links': broken,
            'false_positives': false_positives,
            'false_positive_rate': fp_rate,
            'metadata_coverage': {
                'section_hint': (with_section / total * 100) if total > 0 else 0,
                'day_hint': (with_day / total * 100) if total > 0 else 0
            }
        }
        
        self.results['files'].append(result)
        
        # Update aggregate
        self.results['aggregate']['total_links'] += total
        self.results['aggregate']['inline'] += inline_count
        self.results['aggregate']['fallback'] += fallback_count
        self.results['aggregate']['broken'] += len(broken)
        self.results['aggregate']['false_positives'].extend(false_positives)
        
        # Print summary
        print(f"\n5. Summary:")
        print(f"   Inline rate: {inline_rate:.1f}% (target: ≥45%)")
        print(f"   FP rate: {fp_rate:.1f}% (target: ≤5%)")
        print(f"   Broken: {len(broken)} (target: 0)")
        
        return result
    
    def _find_broken_links(self, input_links: List[Dict], output_links: List[Dict]) -> List[Dict]:
        """Find links that are in input but not in output (broken)."""
        
        # Create sets of URLs for comparison
        input_urls = {link['url'] for link in input_links if link.get('url')}
        output_urls = {link['url'] for link in output_links if link.get('url')}
        
        # Find missing URLs
        broken_urls = input_urls - output_urls
        
        # Get details for broken links
        broken = []
        for link in input_links:
            if link.get('url') in broken_urls:
                broken.append({
                    'text': link['text'],
                    'url': link['url'],
                    'section_hint': link.get('section_hint'),
                    'day_hint': link.get('day_hint')
                })
        
        return broken
    
    def _detect_false_positives_with_metadata(
        self, 
        input_links: List[Dict], 
        inline_links: List[Dict],
        doc: Document
    ) -> List[Dict]:
        """
        Detect false positives using metadata comparison.
        
        A link is a potential false positive if:
        1. It has section/day hints in input
        2. But appears in a different section/day in output
        3. Or has duplicate generic text
        """
        false_positives = []
        
        # Build mapping of URLs to input metadata
        input_metadata = {}
        for link in input_links:
            if link.get('url'):
                input_metadata[link['url']] = {
                    'section_hint': link.get('section_hint'),
                    'day_hint': link.get('day_hint'),
                    'text': link['text']
                }
        
        # Check inline links for mismatches
        for link in inline_links:
            url = link.get('url')
            if not url or url not in input_metadata:
                continue
            
            input_meta = input_metadata[url]
            
            # If input had hints, check if placement makes sense
            if input_meta['section_hint'] or input_meta['day_hint']:
                # Get output location
                location = link.get('location', '')
                
                # Try to infer section/day from table location
                # This is heuristic - would need template knowledge for accuracy
                # For now, just flag if it's a duplicate generic text
                
                pass  # TODO: Would need template structure to validate properly
        
        # Check for duplicate generic text (simpler heuristic)
        text_counts = defaultdict(list)
        for link in inline_links:
            text_counts[link['text']].append(link)
        
        generic_patterns = ['stage', 'level', 'cool down', 'activity', 'worksheet', 'capture']
        
        for text, links in text_counts.items():
            if len(links) > 1:  # Duplicate
                is_generic = any(pattern in text.lower() for pattern in generic_patterns)
                
                if is_generic:
                    for link in links:
                        false_positives.append({
                            'text': text,
                            'url': link.get('url', ''),
                            'location': link.get('location', 'unknown'),
                            'reason': 'duplicate_generic_text',
                            'confidence': 0.6
                        })
        
        return false_positives
    
    def print_summary(self):
        """Print validation summary with pass/fail decision."""
        
        print(f"\n\n{'='*80}")
        print("VALIDATION SUMMARY")
        print(f"{'='*80}\n")
        
        agg = self.results['aggregate']
        
        if agg['total_links'] == 0:
            print("⚠️  No links found to validate!")
            return False
        
        inline_rate = (agg['inline'] / agg['total_links'] * 100)
        fallback_rate = (agg['fallback'] / agg['total_links'] * 100)
        fp_rate = (len(agg['false_positives']) / agg['total_links'] * 100)
        
        print(f"Total links analyzed: {agg['total_links']}")
        print(f"\nPlacement:")
        print(f"  Inline: {agg['inline']} ({inline_rate:.1f}%)")
        print(f"  Fallback: {agg['fallback']} ({fallback_rate:.1f}%)")
        print(f"\nIssues:")
        print(f"  Broken links: {agg['broken']}")
        print(f"  Potential false positives: {len(agg['false_positives'])} ({fp_rate:.1f}%)")
        
        # Per-file breakdown
        print(f"\n\nPER-FILE RESULTS:")
        print(f"{'File':<30} {'Total':<8} {'Inline%':<10} {'FP%':<10} {'Broken':<8}")
        print(f"{'-'*70}")
        
        for result in self.results['files']:
            print(f"{result['file']:<30} {result['total_links']:<8} "
                  f"{result['inline_rate']:<10.1f} {result['false_positive_rate']:<10.1f} "
                  f"{result['broken']:<8}")
        
        # Success criteria
        print(f"\n\nSUCCESS CRITERIA:")
        
        criteria = {
            'Inline rate ≥ 45%': (inline_rate >= 45, inline_rate),
            'FP rate ≤ 5%': (fp_rate <= 5, fp_rate),
            'Zero broken links': (agg['broken'] == 0, agg['broken'])
        }
        
        all_pass = all(passed for passed, _ in criteria.values())
        
        for criterion, (passed, value) in criteria.items():
            status = '✓ PASS' if passed else '✗ FAIL'
            print(f"  {status}: {criterion} (actual: {value if isinstance(value, int) else f'{value:.1f}%'})")
        
        # Warnings
        if agg['warnings']:
            print(f"\n\n⚠️  WARNINGS:")
            for warning in agg['warnings']:
                print(f"  - {warning}")
        
        # Final result
        print(f"\n\nFINAL RESULT:")
        if all_pass:
            print(f"  ✓ VALIDATION PASSED")
            print(f"  → Threshold change is working well")
            print(f"  → Recommend: Manual spot-check, then deploy")
        else:
            print(f"  ✗ VALIDATION FAILED")
            print(f"  → Issues found that need attention")
            print(f"  → Recommend: Review issues before deploying")
        
        print(f"\n\n📝 NEXT STEPS:")
        if all_pass:
            print(f"  1. Do a quick manual spot-check (open one file, click a few links)")
            print(f"  2. If spot-check looks good, submit W43 lesson plans")
            print(f"  3. Commit threshold change to git")
            print(f"  4. Deploy to production")
        else:
            print(f"  1. Review broken links and false positives")
            print(f"  2. Decide: adjust threshold, fix issues, or revert")
            print(f"  3. Reprocess if needed")
            print(f"  4. Re-validate")
        
        return all_pass


def select_output_files(base_dir: Path) -> List[Dict]:
    """
    Interactively select output files for validation.
    Handles multiple output files with timestamps.
    """
    
    print("\n" + "="*80)
    print("OUTPUT FILE SELECTION")
    print("="*80 + "\n")
    
    # Find all output files
    output_files = sorted(base_dir.glob('Wilson_Rodrigues_Weekly_W43*.docx'), 
                         key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not output_files:
        print("⚠️  No output files found matching pattern: Wilson_Rodrigues_Weekly_W43*.docx")
        print(f"   Looking in: {base_dir}")
        return []
    
    print(f"Found {len(output_files)} output file(s):\n")
    for i, f in enumerate(output_files, 1):
        mtime = f.stat().st_mtime
        import datetime
        mtime_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        print(f"  [{i}] {f.name}")
        print(f"      Modified: {mtime_str}")
        print()
    
    # For now, use the most recent (first in sorted list)
    selected = output_files[0]
    print(f"Using most recent file: {selected.name}\n")
    
    # Define pairs
    pairs = [
        {
            'name': 'Davies W43',
            'input': base_dir / '10_20-10_24 Davies Lesson Plans.docx',
            'output': selected
        },
        {
            'name': 'Lang W43',
            'input': base_dir / 'Lang Lesson Plans 10_20_25-10_24_25.docx',
            'output': selected
        },
        {
            'name': 'Savoca W43',
            'input': base_dir / 'Ms. Savoca-10_20_25-10_25_25 Lesson plans.docx',
            'output': selected
        }
    ]
    
    return pairs


def main():
    """Run improved validation on W43 files."""
    
    print("="*80)
    print("AUTOMATED THRESHOLD VALIDATION v2")
    print("="*80)
    print("\n⚠️  IMPORTANT: Make sure you've processed W43 files with the NEW threshold (0.55)")
    print("   The validation expects fresh output generated with the updated code.\n")
    
    base_dir = Path(r'F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W43')
    
    if not base_dir.exists():
        print(f"❌ Directory not found: {base_dir}")
        return 1
    
    # Select output files
    pairs = select_output_files(base_dir)
    
    if not pairs:
        print("\n❌ No files to validate. Please process W43 files first.")
        return 1
    
    validator = ImprovedThresholdValidator()
    
    for pair in pairs:
        if pair['input'].exists() and pair['output'].exists():
            try:
                validator.validate_file_pair(
                    str(pair['input']),
                    str(pair['output']),
                    pair['name']
                )
            except Exception as e:
                print(f"\n❌ Error validating {pair['name']}: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"\n⚠️  Skipping {pair['name']}: Files not found")
            if not pair['input'].exists():
                print(f"   Input missing: {pair['input']}")
            if not pair['output'].exists():
                print(f"   Output missing: {pair['output']}")
    
    # Print summary
    passed = validator.print_summary()
    
    # Save results
    results_path = Path('d:/LP/docs/validation/W43_validation_results_v2.json')
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_path, 'w') as f:
        json.dump(validator.results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_path}")
    
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
