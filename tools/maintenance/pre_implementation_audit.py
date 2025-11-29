"""
Pre-Implementation Audit: Validate assumptions before coding.
Addresses Other AI's concerns about row labels and pairing.
"""

from pathlib import Path
import sys
import json
from collections import Counter, defaultdict
import re

sys.path.insert(0, str(Path(__file__).parent))
from tools.docx_parser import DOCXParser
from docx import Document

class PreImplementationAuditor:
    """Audit actual data before implementing changes."""
    
    def __init__(self):
        self.results = {
            'row_labels': Counter(),
            'row_labels_by_teacher': defaultdict(Counter),
            'pairing_validation': [],
            'missing_hint_patterns': Counter(),
            'template_structures': []
        }
    
    def audit_row_labels(self, file_paths):
        """
        Audit 1: What row labels actually exist?
        Need this to write accurate regex patterns.
        """
        print(f"\n{'='*80}")
        print("AUDIT 1: Actual Row Labels in Files")
        print(f"{'='*80}\n")
        
        for file_path in file_paths:
            if not file_path.exists():
                continue
            
            try:
                doc = Document(str(file_path))
                teacher = self._extract_teacher_name(file_path.name)
                
                for table in doc.tables:
                    for row in table.rows:
                        if row.cells:
                            label = row.cells[0].text.strip()
                            if label and len(label) < 100:  # Skip long content
                                self.results['row_labels'][label] += 1
                                self.results['row_labels_by_teacher'][teacher][label] += 1
                
            except Exception as e:
                print(f"❌ Error reading {file_path.name}: {e}")
        
        # Print results
        print(f"Total unique row labels: {len(self.results['row_labels'])}\n")
        
        print("TOP 30 MOST COMMON ROW LABELS:")
        print(f"{'Count':<8} {'Label':<60}")
        print(f"{'-'*70}")
        
        for label, count in self.results['row_labels'].most_common(30):
            print(f"{count:<8} {label[:60]}")
        
        # Identify curriculum/resource patterns
        print(f"\n\nCURRICULUM-RELATED LABELS:")
        curriculum_labels = [
            (label, count) for label, count in self.results['row_labels'].items()
            if re.search(r'lesson|unit|curriculum|guide|standard', label, re.I)
        ]
        for label, count in sorted(curriculum_labels, key=lambda x: x[1], reverse=True)[:20]:
            print(f"  [{count:3d}] {label[:70]}")
        
        print(f"\n\nRESOURCE-RELATED LABELS:")
        resource_labels = [
            (label, count) for label, count in self.results['row_labels'].items()
            if re.search(r'resource|material|link|reference|media', label, re.I)
        ]
        for label, count in sorted(resource_labels, key=lambda x: x[1], reverse=True)[:20]:
            print(f"  [{count:3d}] {label[:70]}")
        
        # Per-teacher breakdown
        print(f"\n\nPER-TEACHER LABEL VARIATIONS:")
        for teacher, labels in self.results['row_labels_by_teacher'].items():
            print(f"\n{teacher}:")
            for label, count in labels.most_common(10):
                print(f"  [{count:3d}] {label[:60]}")
    
    def validate_pairing(self, folder_path):
        """
        Audit 2: Validate input/output pairing logic.
        Check if we're matching the right files.
        """
        print(f"\n\n{'='*80}")
        print("AUDIT 2: Input/Output Pairing Validation")
        print(f"{'='*80}\n")
        
        folder = Path(folder_path)
        week_folders = [d for d in folder.iterdir() if d.is_dir() and 'W' in d.name]
        
        for week_dir in sorted(week_folders):
            print(f"\n{week_dir.name}:")
            
            # Find all files
            all_files = [f for f in week_dir.glob('*.docx') if not f.name.startswith('~')]
            
            # Categorize
            primary_files = []
            bilingual_files = []
            
            for f in all_files:
                name_lower = f.name.lower()
                if 'rodrigues' in name_lower or 'wilson' in name_lower:
                    bilingual_files.append(f)
                else:
                    primary_files.append(f)
            
            print(f"  Primary files: {len(primary_files)}")
            for f in primary_files:
                print(f"    - {f.name}")
            
            print(f"  Bilingual files: {len(bilingual_files)}")
            for f in bilingual_files:
                print(f"    - {f.name}")
            
            # Attempt smart pairing
            print(f"\n  Suggested pairings:")
            for primary in primary_files:
                teacher = self._extract_teacher_name(primary.name)
                date_range = self._extract_date_range(primary.name)
                
                # Find matching bilingual file
                best_match = None
                for bilingual in bilingual_files:
                    bil_date = self._extract_date_range(bilingual.name)
                    if date_range and bil_date and date_range == bil_date:
                        best_match = bilingual
                        break
                
                if best_match:
                    print(f"    ✓ {primary.name[:40]}... → {best_match.name[:40]}...")
                    self.results['pairing_validation'].append({
                        'week': week_dir.name,
                        'primary': primary.name,
                        'bilingual': best_match.name,
                        'teacher': teacher,
                        'confidence': 'high'
                    })
                else:
                    print(f"    ⚠️  {primary.name[:40]}... → NO MATCH FOUND")
                    self.results['pairing_validation'].append({
                        'week': week_dir.name,
                        'primary': primary.name,
                        'bilingual': None,
                        'teacher': teacher,
                        'confidence': 'none'
                    })
    
    def analyze_missing_hints(self, file_paths):
        """
        Audit 3: What patterns exist in links with missing section_hint?
        """
        print(f"\n\n{'='*80}")
        print("AUDIT 3: Missing Section Hint Patterns")
        print(f"{'='*80}\n")
        
        missing_hint_links = []
        
        for file_path in file_paths:
            if not file_path.exists():
                continue
            
            try:
                parser = DOCXParser(str(file_path))
                hyperlinks = parser.extract_hyperlinks()
                
                for link in hyperlinks:
                    if not link.get('section_hint'):
                        missing_hint_links.append({
                            'text': link['text'],
                            'context': link.get('context_snippet', '')[:100],
                            'file': file_path.name
                        })
                        
                        # Categorize by pattern
                        text_upper = link['text'].upper()
                        if re.search(r'LESSON|UNIT', text_upper):
                            self.results['missing_hint_patterns']['curriculum_lesson'] += 1
                        elif re.search(r'GUIDE|TEACHER', text_upper):
                            self.results['missing_hint_patterns']['curriculum_guide'] += 1
                        elif re.search(r'ACTIVITY|WORKSHEET', text_upper):
                            self.results['missing_hint_patterns']['activity'] += 1
                        elif re.search(r'ASSESSMENT|TEST|QUIZ', text_upper):
                            self.results['missing_hint_patterns']['assessment'] += 1
                        elif re.search(r'STANDARD|CCSS|NGSS', text_upper):
                            self.results['missing_hint_patterns']['standards'] += 1
                        elif re.search(r'STAGE|LEVEL|CHAPTER', text_upper):
                            self.results['missing_hint_patterns']['curriculum_other'] += 1
                        else:
                            self.results['missing_hint_patterns']['other'] += 1
                
            except Exception as e:
                pass
        
        print(f"Total links missing section_hint: {len(missing_hint_links)}\n")
        
        print("PATTERN BREAKDOWN:")
        for pattern, count in self.results['missing_hint_patterns'].most_common():
            pct = (count / len(missing_hint_links) * 100) if missing_hint_links else 0
            print(f"  {pattern:<25} {count:4d} ({pct:5.1f}%)")
        
        print(f"\n\nEXAMPLES (first 20):")
        for i, link in enumerate(missing_hint_links[:20], 1):
            print(f"\n[{i}] {link['text'][:60]}")
            print(f"    Context: {link['context'][:80]}")
            print(f"    File: {link['file'][:50]}")
    
    def _extract_teacher_name(self, filename):
        """Extract teacher name from filename."""
        name_lower = filename.lower()
        if 'davies' in name_lower:
            return 'Davies'
        elif 'lang' in name_lower:
            return 'Lang'
        elif 'savoca' in name_lower:
            return 'Savoca'
        elif 'piret' in name_lower:
            return 'Piret'
        else:
            return 'Unknown'
    
    def _extract_date_range(self, filename):
        """Extract date range from filename."""
        # Try MM_DD_YY-MM_DD_YY format
        match = re.search(r'(\d{1,2})[_-](\d{1,2})[_-](\d{2,4})[_-](\d{1,2})[_-](\d{1,2})[_-](\d{2,4})', filename)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(4)}-{match.group(5)}"
        
        # Try MM-DD-MM-DD format
        match = re.search(r'(\d{1,2})-(\d{1,2})-(\d{1,2})-(\d{1,2})', filename)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)}-{match.group(4)}"
        
        return None
    
    def print_summary(self):
        """Print summary and recommendations."""
        print(f"\n\n{'='*80}")
        print("PRE-IMPLEMENTATION AUDIT SUMMARY")
        print(f"{'='*80}\n")
        
        print("1. ROW LABELS:")
        print(f"   Total unique labels: {len(self.results['row_labels'])}")
        print(f"   Teachers analyzed: {len(self.results['row_labels_by_teacher'])}")
        
        print("\n2. PAIRING:")
        successful = sum(1 for p in self.results['pairing_validation'] if p['bilingual'])
        total = len(self.results['pairing_validation'])
        print(f"   Successful pairings: {successful}/{total}")
        if successful < total:
            print(f"   ⚠️  {total - successful} files couldn't be paired!")
        
        print("\n3. MISSING HINTS:")
        total_missing = sum(self.results['missing_hint_patterns'].values())
        print(f"   Total missing: {total_missing}")
        print(f"   Top pattern: {self.results['missing_hint_patterns'].most_common(1)[0] if self.results['missing_hint_patterns'] else 'N/A'}")
        
        print("\n\n✅ RECOMMENDATIONS:")
        print("\n1. Parser regex patterns should include:")
        curriculum_labels = [l for l in self.results['row_labels'] if re.search(r'lesson|unit|guide', l, re.I)]
        for label in curriculum_labels[:5]:
            print(f"   - {label}")
        
        print("\n2. Pairing logic needs:")
        if successful < total:
            print(f"   - Better date extraction (currently missing {total-successful} matches)")
            print(f"   - Teacher name matching")
            print(f"   - Week validation")
        else:
            print(f"   ✓ Current logic works well")
        
        print("\n3. Parser enhancement will fix:")
        fixable = sum(count for pattern, count in self.results['missing_hint_patterns'].items() 
                     if pattern != 'other')
        print(f"   - {fixable}/{total_missing} missing hints ({fixable/total_missing*100:.1f}%)")


def main():
    """Run pre-implementation audits."""
    
    print("="*80)
    print("PRE-IMPLEMENTATION AUDIT")
    print("Validating assumptions before coding")
    print("="*80)
    
    # Collect files
    base_dir = Path(r'F:\rodri\Documents\OneDrive\AS\Lesson Plan')
    
    input_files = []
    week_folders = [d for d in base_dir.iterdir() if d.is_dir() and 'W' in d.name]
    
    for week_dir in week_folders:
        files = [f for f in week_dir.glob('*.docx') if not f.name.startswith('~')]
        input_files.extend(files)
    
    print(f"\nFound {len(input_files)} files across {len(week_folders)} weeks\n")
    
    # Run audits
    auditor = PreImplementationAuditor()
    
    auditor.audit_row_labels(input_files)
    auditor.validate_pairing(base_dir)
    auditor.analyze_missing_hints(input_files)
    auditor.print_summary()
    
    # Save results
    results_path = Path('d:/LP/pre_implementation_audit_results.json')
    with open(results_path, 'w') as f:
        # Simplify for JSON
        json_results = {
            'row_labels': dict(auditor.results['row_labels'].most_common(50)),
            'missing_hint_patterns': dict(auditor.results['missing_hint_patterns']),
            'pairing_validation': auditor.results['pairing_validation']
        }
        json.dump(json_results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_path}")


if __name__ == '__main__':
    main()
