"""
Metadata Audit: Verify section_hint and day_hint extraction accuracy.
Implements the other AI's recommendations.
"""

from pathlib import Path
import sys
import json
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from tools.docx_parser import DOCXParser

class MetadataAudit:
    """Audit hyperlink metadata extraction accuracy."""
    
    def __init__(self):
        self.results = {
            'total_hyperlinks': 0,
            'with_section_hint': 0,
            'with_day_hint': 0,
            'with_both_hints': 0,
            'missing_section': 0,
            'missing_day': 0,
            'missing_both': 0,
            'hint_values': defaultdict(int),
            'extraction_failures': []
        }
    
    def audit_file(self, input_path):
        """Audit metadata extraction for one file."""
        print(f"\n{'='*80}")
        print(f"Auditing: {Path(input_path).name}")
        print(f"{'='*80}\n")
        
        parser = DOCXParser(str(input_path))
        hyperlinks = parser.extract_hyperlinks()
        
        print(f"📥 Total hyperlinks: {len(hyperlinks)}\n")
        
        self.results['total_hyperlinks'] += len(hyperlinks)
        
        # Analyze each hyperlink's metadata
        for i, link in enumerate(hyperlinks, 1):
            section_hint = link.get('section_hint')
            day_hint = link.get('day_hint')
            
            # Count presence
            if section_hint:
                self.results['with_section_hint'] += 1
                self.results['hint_values'][f"section:{section_hint}"] += 1
            else:
                self.results['missing_section'] += 1
            
            if day_hint:
                self.results['with_day_hint'] += 1
                self.results['hint_values'][f"day:{day_hint}"] += 1
            else:
                self.results['missing_day'] += 1
            
            if section_hint and day_hint:
                self.results['with_both_hints'] += 1
            elif not section_hint and not day_hint:
                self.results['missing_both'] += 1
                self.results['extraction_failures'].append({
                    'text': link['text'],
                    'url': link['url'][:60],
                    'context': link.get('context_snippet', '')[:100]
                })
            
            # Show first 10 examples
            if i <= 10:
                print(f"[{i}] {link['text'][:50]}")
                print(f"    Section: {section_hint or 'MISSING'}")
                print(f"    Day: {day_hint or 'MISSING'}")
                print(f"    Context: {link.get('context_snippet', '')[:80]}...")
                print()
    
    def print_summary(self):
        """Print audit summary."""
        print(f"\n\n{'='*80}")
        print("📊 METADATA AUDIT SUMMARY")
        print(f"{'='*80}\n")
        
        total = self.results['total_hyperlinks']
        
        print(f"Total hyperlinks analyzed: {total}\n")
        
        print(f"Metadata Coverage:")
        print(f"  With section_hint: {self.results['with_section_hint']} ({self.results['with_section_hint']/total*100:.1f}%)")
        print(f"  With day_hint: {self.results['with_day_hint']} ({self.results['with_day_hint']/total*100:.1f}%)")
        print(f"  With BOTH hints: {self.results['with_both_hints']} ({self.results['with_both_hints']/total*100:.1f}%)")
        print(f"  Missing section: {self.results['missing_section']} ({self.results['missing_section']/total*100:.1f}%)")
        print(f"  Missing day: {self.results['missing_day']} ({self.results['missing_day']/total*100:.1f}%)")
        print(f"  Missing BOTH: {self.results['missing_both']} ({self.results['missing_both']/total*100:.1f}%)")
        
        print(f"\n🔍 Hint Value Distribution:")
        for hint, count in sorted(self.results['hint_values'].items(), key=lambda x: x[1], reverse=True)[:15]:
            print(f"  {hint}: {count}")
        
        if self.results['extraction_failures']:
            print(f"\n⚠️  Extraction Failures (first 5):")
            for failure in self.results['extraction_failures'][:5]:
                print(f"  Text: {failure['text']}")
                print(f"  URL: {failure['url']}")
                print(f"  Context: {failure['context']}")
                print()
        
        # Key findings
        print(f"\n💡 KEY FINDINGS:")
        
        both_pct = self.results['with_both_hints'] / total * 100 if total > 0 else 0
        if both_pct < 80:
            print(f"  ⚠️  Only {both_pct:.1f}% of hyperlinks have both section AND day hints!")
            print(f"      → This explains why structural placement fails")
        else:
            print(f"  ✓ {both_pct:.1f}% of hyperlinks have both hints (good coverage)")
        
        if self.results['missing_both'] > 0:
            print(f"  ⚠️  {self.results['missing_both']} hyperlinks have NO hints at all")
            print(f"      → These will always fail structural placement")


def main():
    """Run metadata audit on input files."""
    
    # Audit multiple input files
    input_dir = Path(r'F:\rodri\Documents\OneDrive\AS\Lesson Plan')
    
    input_files = [
        input_dir / '25 W43' / 'Lang Lesson Plans 10_20_25-10_24_25.docx',
        input_dir / '25 W43' / '10_20-10_24 Davies Lesson Plans.docx',
        input_dir / '25 W43' / 'Ms. Savoca-10_20_25-10_25_25 Lesson plans.docx',
        input_dir / '25 W42' / 'Lang Lesson Plans 10_13_25-10_17_25.docx',
        input_dir / '25 W41' / 'Lang Lesson Plans 10_6_25-10_10_25.docx',
    ]
    
    audit = MetadataAudit()
    
    for file_path in input_files:
        if file_path.exists():
            try:
                audit.audit_file(str(file_path))
            except Exception as e:
                print(f"❌ Error auditing {file_path.name}: {e}\n")
    
    audit.print_summary()
    
    # Save results
    results_path = Path('d:/LP/metadata_audit_results.json')
    with open(results_path, 'w') as f:
        # Convert defaultdict to dict
        results_json = {
            **audit.results,
            'hint_values': dict(audit.results['hint_values'])
        }
        json.dump(results_json, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_path}")


if __name__ == '__main__':
    main()
