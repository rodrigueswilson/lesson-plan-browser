"""
Simulate Phase 1+2 improvements WITHOUT modifying any code.
Answers: What will the ACTUAL inline rate be after changes?
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

class ImprovementSimulator:
    """Simulate improvements and measure actual impact."""
    
    def __init__(self):
        self.results = {
            'baseline': {},
            'phase1': {},
            'phase2': {},
            'false_positives': [],
            'duplicate_url_risks': [],
            'per_file_breakdown': []
        }
    
    def simulate_on_file(self, input_path, output_path):
        """
        Simulate improvements on one input/output pair.
        Returns: baseline vs. improved inline rates
        """
        print(f"\n{'='*80}")
        print(f"Simulating: {Path(output_path).name}")
        print(f"{'='*80}\n")
        
        # Extract input hyperlinks
        parser = DOCXParser(str(input_path))
        input_links = parser.extract_hyperlinks()
        
        # Extract output cells
        output_doc = Document(output_path)
        output_cells = self._extract_all_cells(output_doc)
        
        print(f"Input: {len(input_links)} hyperlinks")
        print(f"Output: {len(output_cells)} cells\n")
        
        # Simulate baseline (current logic)
        baseline_results = self._simulate_baseline(input_links, output_cells)
        
        # Simulate Phase 1 (case-insensitive + whitespace)
        phase1_results = self._simulate_phase1(input_links, output_cells)
        
        # Simulate Phase 2 (lower threshold)
        phase2_results = self._simulate_phase2(input_links, output_cells)
        
        # Print results
        print(f"BASELINE (current):")
        print(f"  Inline: {baseline_results['inline']} ({baseline_results['inline_pct']:.1f}%)")
        print(f"  Fallback: {baseline_results['fallback']}")
        
        print(f"\nPHASE 1 (case-insensitive + whitespace):")
        print(f"  Inline: {phase1_results['inline']} ({phase1_results['inline_pct']:.1f}%)")
        print(f"  Improvement: +{phase1_results['inline'] - baseline_results['inline']} (+{phase1_results['inline_pct'] - baseline_results['inline_pct']:.1f}%)")
        
        print(f"\nPHASE 2 (+ lower threshold to 0.55):")
        print(f"  Inline: {phase2_results['inline']} ({phase2_results['inline_pct']:.1f}%)")
        print(f"  Improvement: +{phase2_results['inline'] - baseline_results['inline']} (+{phase2_results['inline_pct'] - baseline_results['inline_pct']:.1f}%)")
        
        # Check for false positives
        false_positives = self._detect_false_positives(phase2_results['placements'])
        if false_positives:
            print(f"\n⚠️  Potential false positives: {len(false_positives)}")
            for fp in false_positives[:3]:
                print(f"  - {fp['link_text'][:40]} → {fp['cell_location']}")
        
        return {
            'file': Path(output_path).name,
            'baseline': baseline_results,
            'phase1': phase1_results,
            'phase2': phase2_results,
            'false_positives': false_positives
        }
    
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
        """Simulate current matching logic."""
        inline = 0
        placements = []
        
        for link in links:
            link_text = link['text']
            context = link.get('context_snippet', '')
            
            # Try exact match (current logic)
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
    
    def _simulate_phase1(self, links, cells):
        """Simulate Phase 1: case-insensitive + whitespace normalization."""
        inline = 0
        placements = []
        
        for link in links:
            link_text = link['text']
            context = link.get('context_snippet', '')
            
            # Normalize link text
            link_norm = ' '.join(link_text.split()).strip().lower()
            
            # Try exact match (case-sensitive)
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
            
            # Try case-insensitive match
            for cell in cells:
                cell_norm = ' '.join(cell['text'].split()).strip().lower()
                if link_norm in cell_norm:
                    inline += 1
                    placements.append({
                        'link': link,
                        'cell': cell,
                        'strategy': 'case_insensitive',
                        'confidence': 0.95
                    })
                    matched = True
                    break
            
            if matched:
                continue
            
            # Try fuzzy match with threshold 0.65 (unchanged)
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
        """Simulate Phase 2: Phase 1 + lower threshold to 0.55."""
        inline = 0
        placements = []
        
        for link in links:
            link_text = link['text']
            context = link.get('context_snippet', '')
            link_norm = ' '.join(link_text.split()).strip().lower()
            
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
            
            # Try case-insensitive
            for cell in cells:
                cell_norm = ' '.join(cell['text'].split()).strip().lower()
                if link_norm in cell_norm:
                    inline += 1
                    placements.append({
                        'link': link,
                        'cell': cell,
                        'strategy': 'case_insensitive',
                        'confidence': 0.95
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
    
    def print_aggregate_summary(self):
        """Print summary across all files."""
        print(f"\n\n{'='*80}")
        print("AGGREGATE RESULTS ACROSS ALL FILES")
        print(f"{'='*80}\n")
        
        # Aggregate totals
        baseline_total = sum(r['baseline']['inline'] for r in self.results['per_file_breakdown'])
        baseline_count = sum(r['baseline']['inline'] + r['baseline']['fallback'] for r in self.results['per_file_breakdown'])
        
        phase1_total = sum(r['phase1']['inline'] for r in self.results['per_file_breakdown'])
        phase2_total = sum(r['phase2']['inline'] for r in self.results['per_file_breakdown'])
        
        print(f"Total hyperlinks: {baseline_count}")
        print(f"\nBASELINE (current):")
        print(f"  Inline: {baseline_total} ({baseline_total/baseline_count*100:.1f}%)")
        
        print(f"\nPHASE 1 (case-insensitive + whitespace):")
        print(f"  Inline: {phase1_total} ({phase1_total/baseline_count*100:.1f}%)")
        print(f"  Improvement: +{phase1_total - baseline_total} (+{(phase1_total - baseline_total)/baseline_count*100:.1f}%)")
        
        print(f"\nPHASE 2 (+ lower threshold to 0.55):")
        print(f"  Inline: {phase2_total} ({phase2_total/baseline_count*100:.1f}%)")
        print(f"  Improvement: +{phase2_total - baseline_total} (+{(phase2_total - baseline_total)/baseline_count*100:.1f}%)")
        
        # False positives
        total_fp = sum(len(r['false_positives']) for r in self.results['per_file_breakdown'])
        if total_fp > 0:
            print(f"\n⚠️  POTENTIAL FALSE POSITIVES: {total_fp}")
            print(f"   ({total_fp/baseline_count*100:.1f}% of total links)")
        
        # Per-file breakdown
        print(f"\n\nPER-FILE BREAKDOWN:")
        print(f"{'File':<50} {'Baseline':<10} {'Phase1':<10} {'Phase2':<10} {'Gain':<10}")
        print(f"{'-'*90}")
        
        for r in self.results['per_file_breakdown']:
            file_name = r['file'][:48]
            baseline_pct = r['baseline']['inline_pct']
            phase1_pct = r['phase1']['inline_pct']
            phase2_pct = r['phase2']['inline_pct']
            gain = phase2_pct - baseline_pct
            
            print(f"{file_name:<50} {baseline_pct:>6.1f}%   {phase1_pct:>6.1f}%   {phase2_pct:>6.1f}%   +{gain:>5.1f}%")
        
        # Final recommendation
        print(f"\n\n{'='*80}")
        print("FINAL VERDICT")
        print(f"{'='*80}\n")
        
        actual_improvement = (phase2_total - baseline_total) / baseline_count * 100
        projected_min = 50
        projected_max = 60
        
        if actual_improvement >= projected_min:
            print(f"✅ PROCEED: Actual improvement ({actual_improvement:.1f}%) meets projection ({projected_min}-{projected_max}%)")
        else:
            print(f"⚠️  CAUTION: Actual improvement ({actual_improvement:.1f}%) below projection ({projected_min}-{projected_max}%)")
        
        if total_fp / baseline_count > 0.05:  # >5% false positives
            print(f"⚠️  WARNING: High false positive rate ({total_fp/baseline_count*100:.1f}%)")
            print(f"   → Need safeguards before implementing")
        else:
            print(f"✅ False positive rate acceptable ({total_fp/baseline_count*100:.1f}%)")


def main():
    """Run simulation on multiple files."""
    
    # Input/output pairs
    base_dir = Path(r'F:\rodri\Documents\OneDrive\AS\Lesson Plan')
    
    pairs = [
        (
            base_dir / '25 W43' / 'Lang Lesson Plans 10_20_25-10_24_25.docx',
            base_dir / '25 W43' / 'Wilson_Rodrigues_Weekly_W43_10-20-10-24_20251019_025901.docx'
        ),
        (
            base_dir / '25 W42' / 'Lang Lesson Plans 10_13_25-10_17_25.docx',
            base_dir / '25 W42' / 'Wilson_Rodrigues_Weekly_W42_10-13-10-17.docx'
        ),
        (
            base_dir / '25 W41' / 'Lang Lesson Plans 10_6_25-10_10_25.docx',
            base_dir / '25 W41' / 'Wilson_Rodrigues_Weekly_W41_10-06-10-10.docx'
        ),
    ]
    
    simulator = ImprovementSimulator()
    
    for input_path, output_path in pairs:
        if input_path.exists() and output_path.exists():
            try:
                result = simulator.simulate_on_file(str(input_path), str(output_path))
                simulator.results['per_file_breakdown'].append(result)
            except Exception as e:
                print(f"❌ Error: {e}\n")
    
    simulator.print_aggregate_summary()
    
    # Save results
    results_path = Path('d:/LP/simulation_results.json')
    with open(results_path, 'w') as f:
        # Simplify for JSON
        json_results = {
            'per_file': [
                {
                    'file': r['file'],
                    'baseline_pct': r['baseline']['inline_pct'],
                    'phase1_pct': r['phase1']['inline_pct'],
                    'phase2_pct': r['phase2']['inline_pct'],
                    'false_positives': len(r['false_positives'])
                }
                for r in simulator.results['per_file_breakdown']
            ]
        }
        json.dump(json_results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_path}")


if __name__ == '__main__':
    main()
