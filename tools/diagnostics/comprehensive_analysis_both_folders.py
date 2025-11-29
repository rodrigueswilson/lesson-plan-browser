"""
Comprehensive Analysis: Both Lesson Plan Folders
Extended data collection, diagnosis, and simulation for complete picture.
"""

from pathlib import Path
import sys
import json
from collections import defaultdict
from rapidfuzz import fuzz

sys.path.insert(0, str(Path(__file__).parent))
from tools.docx_parser import DOCXParser
from docx import Document
from docx.oxml.ns import qn

class ComprehensiveAnalyzer:
    """Analyze both folders comprehensively."""
    
    def __init__(self):
        self.results = {
            'folders': {},
            'aggregate': {
                'total_files': 0,
                'total_hyperlinks': 0,
                'baseline_inline': 0,
                'phase2_inline': 0,
                'false_positives': 0
            },
            'per_file_results': []
        }
    
    def find_input_output_pairs(self, folder_path):
        """Find all input/output pairs in a folder."""
        folder = Path(folder_path)
        pairs = []
        
        print(f"\nScanning folder: {folder}")
        
        # Find all week folders
        week_folders = [d for d in folder.iterdir() if d.is_dir() and 'W' in d.name]
        
        for week_dir in sorted(week_folders):
            # Find primary teacher files (input)
            primary_files = []
            for pattern in ['Davies', 'Lang Lesson', 'Savoca', 'Piret']:
                primary_files.extend(week_dir.glob(f'*{pattern}*.docx'))
            
            # Find bilingual output files
            output_files = list(week_dir.glob('*Rodrigues*.docx')) + list(week_dir.glob('Wilson*.docx'))
            
            # Match pairs
            for primary in primary_files:
                if primary.name.startswith('~'):
                    continue
                
                # Find corresponding output
                for output in output_files:
                    if output.name.startswith('~'):
                        continue
                    
                    # Simple heuristic: same week folder
                    pairs.append({
                        'input': primary,
                        'output': output,
                        'week': week_dir.name,
                        'folder': folder.name
                    })
                    break  # One output per input
        
        print(f"  Found {len(pairs)} input/output pairs")
        return pairs
    
    def analyze_pair(self, pair):
        """Analyze one input/output pair."""
        input_path = pair['input']
        output_path = pair['output']
        
        try:
            # Extract input hyperlinks
            parser = DOCXParser(str(input_path))
            input_links = parser.extract_hyperlinks()
            
            if not input_links:
                return None
            
            # Extract output cells
            output_doc = Document(str(output_path))
            output_cells = self._extract_all_cells(output_doc)
            
            # Simulate baseline
            baseline = self._simulate_baseline(input_links, output_cells)
            
            # Simulate Phase 2
            phase2 = self._simulate_phase2(input_links, output_cells)
            
            # Detect false positives
            false_positives = self._detect_false_positives(phase2['placements'])
            
            return {
                'folder': pair['folder'],
                'week': pair['week'],
                'input_file': input_path.name,
                'output_file': output_path.name,
                'total_links': len(input_links),
                'baseline_inline': baseline['inline'],
                'baseline_pct': baseline['inline_pct'],
                'phase2_inline': phase2['inline'],
                'phase2_pct': phase2['inline_pct'],
                'improvement': phase2['inline'] - baseline['inline'],
                'improvement_pct': phase2['inline_pct'] - baseline['inline_pct'],
                'false_positives': len(false_positives)
            }
            
        except Exception as e:
            print(f"  ❌ Error analyzing {input_path.name}: {e}")
            return None
    
    def _extract_all_cells(self, doc):
        """Extract all cells with their text and location."""
        cells = []
        
        for table_idx, table in enumerate(doc.tables):
            for row_idx, row in enumerate(table.rows):
                for cell_idx, cell in enumerate(row.cells):
                    cells.append({
                        'text': cell.text,
                        'location': f"T{table_idx}R{row_idx}C{cell_idx}",
                        'table_idx': table_idx,
                        'row_idx': row_idx,
                        'cell_idx': cell_idx
                    })
        
        return cells
    
    def _simulate_baseline(self, links, cells):
        """Simulate current matching logic (threshold 0.65)."""
        inline = 0
        placements = []
        
        for link in links:
            link_text = link['text']
            context = link.get('context_snippet', '')
            
            # Try exact match
            for cell in cells:
                if link_text in cell['text']:
                    inline += 1
                    placements.append({
                        'link': link,
                        'cell': cell,
                        'strategy': 'exact',
                        'confidence': 1.0
                    })
                    break
            else:
                # Try fuzzy match with threshold 0.65
                best_score = 0
                best_cell = None
                
                for cell in cells:
                    if context:
                        score = fuzz.partial_ratio(context, cell['text']) / 100.0
                        if score > best_score:
                            best_score = score
                            best_cell = cell
                
                if best_score >= 0.65:
                    inline += 1
                    placements.append({
                        'link': link,
                        'cell': best_cell,
                        'strategy': 'fuzzy_0.65',
                        'confidence': best_score
                    })
        
        return {
            'inline': inline,
            'fallback': len(links) - inline,
            'inline_pct': (inline / len(links) * 100) if links else 0,
            'placements': placements
        }
    
    def _simulate_phase2(self, links, cells):
        """Simulate Phase 2: lower threshold to 0.55."""
        inline = 0
        placements = []
        
        for link in links:
            link_text = link['text']
            context = link.get('context_snippet', '')
            
            # Try exact match
            matched = False
            for cell in cells:
                if link_text in cell['text']:
                    inline += 1
                    placements.append({
                        'link': link,
                        'cell': cell,
                        'strategy': 'exact',
                        'confidence': 1.0
                    })
                    matched = True
                    break
            
            if matched:
                continue
            
            # Try fuzzy match with LOWERED threshold 0.55
            best_score = 0
            best_cell = None
            
            for cell in cells:
                if context:
                    score = fuzz.partial_ratio(context, cell['text']) / 100.0
                    if score > best_score:
                        best_score = score
                        best_cell = cell
            
            if best_score >= 0.55:  # LOWERED from 0.65
                inline += 1
                placements.append({
                    'link': link,
                    'cell': best_cell,
                    'strategy': f'fuzzy_0.55',
                    'confidence': best_score
                })
        
        return {
            'inline': inline,
            'fallback': len(links) - inline,
            'inline_pct': (inline / len(links) * 100) if links else 0,
            'placements': placements
        }
    
    def _detect_false_positives(self, placements):
        """Detect potential false positives."""
        false_positives = []
        
        # Group by link text
        by_text = defaultdict(list)
        for p in placements:
            by_text[p['link']['text']].append(p)
        
        # Check for duplicate link texts with different URLs
        for link_text, group in by_text.items():
            urls = set(p['link']['url'] for p in group)
            if len(urls) > 1:
                # Same text, different URLs - potential false positive
                for p in group:
                    if p['confidence'] < 0.70:  # Low confidence + duplicate text
                        false_positives.append({
                            'link_text': link_text,
                            'url': p['link']['url'],
                            'cell_location': p['cell']['location'],
                            'confidence': p['confidence'],
                            'strategy': p['strategy']
                        })
        
        return false_positives
    
    def print_summary(self):
        """Print comprehensive summary."""
        print(f"\n\n{'='*80}")
        print("COMPREHENSIVE ANALYSIS SUMMARY")
        print(f"{'='*80}\n")
        
        agg = self.results['aggregate']
        
        print(f"Total files analyzed: {agg['total_files']}")
        print(f"Total hyperlinks: {agg['total_hyperlinks']}")
        print()
        
        if agg['total_hyperlinks'] > 0:
            baseline_pct = (agg['baseline_inline'] / agg['total_hyperlinks']) * 100
            phase2_pct = (agg['phase2_inline'] / agg['total_hyperlinks']) * 100
            improvement = phase2_pct - baseline_pct
            fp_pct = (agg['false_positives'] / agg['total_hyperlinks']) * 100
            
            print(f"BASELINE (current threshold 0.65):")
            print(f"  Inline: {agg['baseline_inline']} ({baseline_pct:.1f}%)")
            print()
            
            print(f"PHASE 2 (lower threshold to 0.55):")
            print(f"  Inline: {agg['phase2_inline']} ({phase2_pct:.1f}%)")
            print(f"  Improvement: +{agg['phase2_inline'] - agg['baseline_inline']} (+{improvement:.1f}%)")
            print()
            
            print(f"FALSE POSITIVES:")
            print(f"  Count: {agg['false_positives']} ({fp_pct:.1f}%)")
            print()
            
            # Per-folder breakdown
            print(f"\nPER-FOLDER BREAKDOWN:")
            for folder_name, folder_data in self.results['folders'].items():
                print(f"\n{folder_name}:")
                print(f"  Files: {folder_data['files']}")
                print(f"  Hyperlinks: {folder_data['total_links']}")
                print(f"  Baseline: {folder_data['baseline_pct']:.1f}%")
                print(f"  Phase 2: {folder_data['phase2_pct']:.1f}%")
                print(f"  Improvement: +{folder_data['improvement_pct']:.1f}%")
            
            # Top improvements
            print(f"\n\nTOP 5 FILES BY IMPROVEMENT:")
            sorted_files = sorted(self.results['per_file_results'], 
                                key=lambda x: x['improvement'], reverse=True)
            
            for i, result in enumerate(sorted_files[:5], 1):
                print(f"\n{i}. {result['output_file'][:60]}")
                print(f"   Baseline: {result['baseline_pct']:.1f}% → Phase 2: {result['phase2_pct']:.1f}%")
                print(f"   Improvement: +{result['improvement']} links (+{result['improvement_pct']:.1f}%)")
            
            # Files needing attention
            print(f"\n\nFILES WITH LOWEST BASELINE (<60%):")
            low_baseline = [r for r in self.results['per_file_results'] if r['baseline_pct'] < 60]
            
            for result in sorted(low_baseline, key=lambda x: x['baseline_pct'])[:5]:
                print(f"\n- {result['output_file'][:60]}")
                print(f"  Baseline: {result['baseline_pct']:.1f}% → Phase 2: {result['phase2_pct']:.1f}%")
                print(f"  {result['total_links']} links, {result['false_positives']} false positives")
            
            # Final verdict
            print(f"\n\n{'='*80}")
            print("FINAL VERDICT")
            print(f"{'='*80}\n")
            
            if improvement >= 10:
                print(f"✅ PROCEED: Improvement ({improvement:.1f}%) is significant")
            elif improvement >= 5:
                print(f"⚠️  CONSIDER: Improvement ({improvement:.1f}%) is moderate")
            else:
                print(f"❌ REJECT: Improvement ({improvement:.1f}%) is minimal")
            
            if fp_pct > 5:
                print(f"⚠️  WARNING: High false positive rate ({fp_pct:.1f}%)")
                print(f"   → Need safeguards before implementing")
            else:
                print(f"✅ False positive rate acceptable ({fp_pct:.1f}%)")


def main():
    """Run comprehensive analysis on both folders."""
    
    folders = [
        r'F:\rodri\Documents\OneDrive\AS\Lesson Plan',
        r'F:\rodri\Documents\OneDrive\AS\Daniela LP'
    ]
    
    analyzer = ComprehensiveAnalyzer()
    
    print("="*80)
    print("COMPREHENSIVE ANALYSIS: BOTH FOLDERS")
    print("="*80)
    
    for folder_path in folders:
        folder = Path(folder_path)
        if not folder.exists():
            print(f"\n⚠️  Folder not found: {folder}")
            continue
        
        # Find pairs
        pairs = analyzer.find_input_output_pairs(folder_path)
        
        # Analyze each pair
        folder_results = {
            'files': 0,
            'total_links': 0,
            'baseline_inline': 0,
            'phase2_inline': 0,
            'false_positives': 0
        }
        
        print(f"\nAnalyzing {len(pairs)} pairs from {folder.name}...")
        
        for i, pair in enumerate(pairs, 1):
            print(f"  [{i}/{len(pairs)}] {pair['week']} - {pair['input'].name[:40]}...", end=' ')
            
            result = analyzer.analyze_pair(pair)
            
            if result:
                print(f"✓ ({result['total_links']} links, {result['baseline_pct']:.0f}% → {result['phase2_pct']:.0f}%)")
                
                analyzer.results['per_file_results'].append(result)
                
                folder_results['files'] += 1
                folder_results['total_links'] += result['total_links']
                folder_results['baseline_inline'] += result['baseline_inline']
                folder_results['phase2_inline'] += result['phase2_inline']
                folder_results['false_positives'] += result['false_positives']
                
                analyzer.results['aggregate']['total_files'] += 1
                analyzer.results['aggregate']['total_hyperlinks'] += result['total_links']
                analyzer.results['aggregate']['baseline_inline'] += result['baseline_inline']
                analyzer.results['aggregate']['phase2_inline'] += result['phase2_inline']
                analyzer.results['aggregate']['false_positives'] += result['false_positives']
            else:
                print("✗ (skipped)")
        
        # Calculate folder percentages
        if folder_results['total_links'] > 0:
            folder_results['baseline_pct'] = (folder_results['baseline_inline'] / folder_results['total_links']) * 100
            folder_results['phase2_pct'] = (folder_results['phase2_inline'] / folder_results['total_links']) * 100
            folder_results['improvement_pct'] = folder_results['phase2_pct'] - folder_results['baseline_pct']
        
        analyzer.results['folders'][folder.name] = folder_results
    
    # Print summary
    analyzer.print_summary()
    
    # Save results
    results_path = Path('d:/LP/comprehensive_analysis_results.json')
    with open(results_path, 'w') as f:
        # Simplify for JSON
        json_results = {
            'aggregate': analyzer.results['aggregate'],
            'folders': analyzer.results['folders'],
            'per_file': analyzer.results['per_file_results']
        }
        json.dump(json_results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_path}")


if __name__ == '__main__':
    main()
