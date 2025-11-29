"""
Fix input/output pairing logic - VALIDATION PREREQUISITE

This is a standalone validation tool with NO runtime impact on production.
Used to verify pairing accuracy before relying on simulation metrics.

Run this BEFORE implementing threshold change to ensure analytics are accurate.
"""

import re
from pathlib import Path
from typing import Optional, Tuple
import json

def normalize_date_component(value: str) -> str:
    """Normalize date component to handle leading zeros."""
    try:
        return str(int(value)).zfill(2)  # Convert to int, then pad with zeros
    except ValueError:
        return value

def extract_teacher(filename: str) -> str:
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
    return 'Unknown'

def extract_date_range(filename: str) -> Optional[str]:
    """
    Extract date range from filename with normalization.
    
    Handles variations like:
    - 9_2-9_5 vs 09_02-09_05
    - 10_20_25-10_24_25 vs 10-20-10-24
    
    Returns normalized format: MM-DD-MM-DD
    """
    # Try MM_DD_YY-MM_DD_YY or MM_DD-MM_DD
    match = re.search(r'(\d{1,2})[_-](\d{1,2})(?:[_-](\d{2,4}))?[_-](\d{1,2})[_-](\d{1,2})', filename)
    if match:
        m1 = normalize_date_component(match.group(1))
        d1 = normalize_date_component(match.group(2))
        m2 = normalize_date_component(match.group(4))
        d2 = normalize_date_component(match.group(5))
        return f"{m1}-{d1}-{m2}-{d2}"
    
    # Try MM-DD-MM-DD format
    match = re.search(r'(\d{1,2})-(\d{1,2})-(\d{1,2})-(\d{1,2})', filename)
    if match:
        m1 = normalize_date_component(match.group(1))
        d1 = normalize_date_component(match.group(2))
        m2 = normalize_date_component(match.group(3))
        d2 = normalize_date_component(match.group(4))
        return f"{m1}-{d1}-{m2}-{d2}"
    
    return None

def find_matching_output(input_file: Path, output_files: list) -> Optional[Path]:
    """Find matching output file for input."""
    input_dates = extract_date_range(input_file.name)
    
    if not input_dates:
        return None
    
    for output_file in output_files:
        output_dates = extract_date_range(output_file.name)
        if output_dates == input_dates:
            return output_file
    
    return None

def validate_pairing(folder_path: str, folder_name: str = "Lesson Plan"):
    """
    Validate pairing logic on all files in a folder.
    
    Args:
        folder_path: Path to folder containing week subfolders
        folder_name: Name of folder (for reporting)
    
    Returns:
        List of pairing results
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"⚠️  Folder not found: {folder}")
        return []
    
    week_folders = [d for d in folder.iterdir() if d.is_dir() and 'W' in d.name]
    
    results = []
    
    print(f"\n{'='*80}")
    print(f"Validating pairing in: {folder_name}")
    print(f"{'='*80}\n")
    
    for week_dir in sorted(week_folders):
        all_files = [f for f in week_dir.glob('*.docx') if not f.name.startswith('~')]
        
        primary_files = []
        bilingual_files = []
        
        for f in all_files:
            name_lower = f.name.lower()
            if 'rodrigues' in name_lower or 'wilson' in name_lower:
                bilingual_files.append(f)
            else:
                primary_files.append(f)
        
        if not primary_files:
            continue
        
        print(f"{week_dir.name}:")
        
        for primary in primary_files:
            match = find_matching_output(primary, bilingual_files)
            
            result = {
                'folder': folder_name,
                'week': week_dir.name,
                'input': primary.name,
                'output': match.name if match else None,
                'teacher': extract_teacher(primary.name),
                'matched': bool(match),
                'input_dates': extract_date_range(primary.name),
                'output_dates': extract_date_range(match.name) if match else None
            }
            
            results.append(result)
            
            if match:
                print(f"  ✓ {primary.name[:40]}... → {match.name[:40]}...")
            else:
                print(f"  ✗ {primary.name[:40]}... → NO MATCH")
    
    return results

def print_summary(all_results: list):
    """Print summary of pairing results."""
    print(f"\n\n{'='*80}")
    print("PAIRING VALIDATION SUMMARY")
    print(f"{'='*80}\n")
    
    # Overall stats
    matched = sum(1 for r in all_results if r['matched'])
    total = len(all_results)
    match_pct = (matched / total * 100) if total > 0 else 0
    
    print(f"Overall Results:")
    print(f"  Total files: {total}")
    print(f"  Matched: {matched} ({match_pct:.1f}%)")
    print(f"  Unmatched: {total - matched}")
    
    # Per-folder breakdown
    folders = {}
    for r in all_results:
        folder = r['folder']
        if folder not in folders:
            folders[folder] = {'matched': 0, 'total': 0}
        folders[folder]['total'] += 1
        if r['matched']:
            folders[folder]['matched'] += 1
    
    print(f"\nPer-Folder Breakdown:")
    for folder, stats in folders.items():
        pct = (stats['matched'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {folder}: {stats['matched']}/{stats['total']} ({pct:.1f}%)")
    
    # Success criteria
    print(f"\n\nSUCCESS CRITERIA:")
    if match_pct >= 80:
        print(f"  ✓ PASS: Match rate {match_pct:.1f}% >= 80%")
        print(f"  → Pairing logic is reliable for simulations")
    else:
        print(f"  ✗ FAIL: Match rate {match_pct:.1f}% < 80%")
        print(f"  → DO NOT trust simulation metrics until pairing is fixed")
    
    # Unmatched files
    if total - matched > 0:
        print(f"\n\nUNMATCHED FILES ({total - matched}):")
        for r in all_results:
            if not r['matched']:
                print(f"  {r['week']}: {r['input'][:60]}")
                print(f"    Dates extracted: {r['input_dates']}")


def main():
    """Run pairing validation on both folders."""
    
    print("="*80)
    print("PAIRING LOGIC VALIDATION - PREREQUISITE CHECK")
    print("="*80)
    print("\nThis is a standalone validation tool with NO runtime impact.")
    print("Used to verify pairing accuracy before relying on simulation metrics.\n")
    
    folders = [
        (r'F:\rodri\Documents\OneDrive\AS\Lesson Plan', 'Lesson Plan'),
        (r'F:\rodri\Documents\OneDrive\AS\Daniela LP', 'Daniela LP')
    ]
    
    all_results = []
    
    for folder_path, folder_name in folders:
        results = validate_pairing(folder_path, folder_name)
        all_results.extend(results)
    
    # Print summary
    print_summary(all_results)
    
    # Save results
    output_path = Path('d:/LP/pairing_validation.json')
    with open(output_path, 'w') as f:
        json.dump({
            'summary': {
                'total': len(all_results),
                'matched': sum(1 for r in all_results if r['matched']),
                'match_percentage': (sum(1 for r in all_results if r['matched']) / len(all_results) * 100) if all_results else 0
            },
            'results': all_results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_path}")
    print(f"\n✅ Validation complete. Review results before proceeding with threshold change.")


if __name__ == '__main__':
    main()
