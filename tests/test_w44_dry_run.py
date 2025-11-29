"""
Dry run test of W44 files through batch processor with LLM disabled.

This validates slot-aware extraction counts before involving OpenAI.
"""

import asyncio
from pathlib import Path
from tools.docx_parser import DOCXParser
from backend.telemetry import logger
import json


async def dry_run_slot_extraction(file_path: str, slots_config: list):
    """
    Simulate batch processor slot extraction without LLM calls.
    
    Args:
        file_path: Path to lesson plan file
        slots_config: List of slot configurations (slot_number, subject, grade)
    """
    print(f"\n{'='*80}")
    print(f"DRY RUN: {Path(file_path).name}")
    print(f"{'='*80}")
    
    parser = DOCXParser(file_path)
    
    results = []
    
    for slot in slots_config:
        slot_num = slot['slot_number']
        subject = slot['subject']
        grade = slot['grade']
        
        print(f"\n--- Slot {slot_num}: {subject} (Grade {grade}) ---")
        
        try:
            # Extract hyperlinks (slot-aware)
            hyperlinks = parser.extract_hyperlinks_for_slot(slot_num)
            
            # Extract images (slot-aware)
            images = parser.extract_images_for_slot(slot_num)
            
            # Analyze hyperlink distribution
            table_indices = set(link['table_idx'] for link in hyperlinks)
            context_types = {}
            for link in hyperlinks:
                ctx_type = link.get('context_type', 'unknown')
                context_types[ctx_type] = context_types.get(ctx_type, 0) + 1
            
            # Analyze image distribution
            image_table_indices = set(img['table_idx'] for img in images if img.get('table_idx') is not None)
            
            result = {
                'slot_number': slot_num,
                'subject': subject,
                'grade': grade,
                'hyperlinks': {
                    'total': len(hyperlinks),
                    'table_indices': sorted(table_indices),
                    'context_types': context_types
                },
                'images': {
                    'total': len(images),
                    'table_indices': sorted(image_table_indices)
                }
            }
            
            results.append(result)
            
            # Print summary
            print(f"  Hyperlinks: {len(hyperlinks)}")
            print(f"    Table indices: {sorted(table_indices)}")
            print(f"    Context types: {context_types}")
            print(f"  Images: {len(images)}")
            if image_table_indices:
                print(f"    Table indices: {sorted(image_table_indices)}")
            
            # Sample hyperlinks
            if hyperlinks:
                print(f"\n  Sample hyperlinks (first 3):")
                for i, link in enumerate(hyperlinks[:3]):
                    print(f"    {i+1}. '{link['text'][:50]}' -> {link['url'][:50]}")
                    print(f"       Table {link['table_idx']}, Row {link['row_idx']}, Cell {link['cell_idx']}")
            
            # Validate no cross-contamination
            expected_tables = {slot_num * 2 - 2, slot_num * 2 - 1}  # e.g., slot 1 = {0, 1}
            if table_indices and not table_indices.issubset(expected_tables):
                print(f"\n  ⚠️  WARNING: Unexpected table indices!")
                print(f"     Expected: {expected_tables}")
                print(f"     Got: {table_indices}")
            else:
                print(f"\n  ✅ No cross-contamination detected")
            
        except Exception as e:
            print(f"  ❌ Error: {type(e).__name__}: {e}")
            result = {
                'slot_number': slot_num,
                'subject': subject,
                'grade': grade,
                'error': str(e)
            }
            results.append(result)
    
    print(f"\n{'='*80}\n")
    
    return results


async def main():
    """Run dry run tests on W44 files."""
    
    input_dir = Path("F:/rodri/Documents/OneDrive/AS/Daniela LP/25 W44")
    
    # Test configurations for Daniela W44 files
    test_cases = [
        {
            'file': "Morais 10_27-31.docx",
            'slots': [
                {'slot_number': 1, 'subject': 'ELA', 'grade': '3'},
                {'slot_number': 2, 'subject': 'Math', 'grade': '3'},
                {'slot_number': 3, 'subject': 'Science', 'grade': '3'},
                {'slot_number': 4, 'subject': 'Social Studies', 'grade': '3'},
            ]
        },
        {
            'file': "Mrs. Grande Science 10_27- 10_31.docx",
            'slots': [
                {'slot_number': 1, 'subject': 'Science', 'grade': '4'},
            ]
        },
        {
            'file': "Santiago SS Plans 10_27-10_31.docx",
            'slots': [
                {'slot_number': 1, 'subject': 'Social Studies', 'grade': '5'},
            ]
        }
    ]
    
    all_results = {}
    
    for test_case in test_cases:
        file_path = input_dir / test_case['file']
        if not file_path.exists():
            print(f"⚠️  File not found: {test_case['file']}")
            continue
        
        results = await dry_run_slot_extraction(str(file_path), test_case['slots'])
        all_results[test_case['file']] = results
    
    # Summary report
    print("\n" + "="*80)
    print("SUMMARY REPORT")
    print("="*80)
    
    for filename, results in all_results.items():
        print(f"\n{filename}:")
        total_hyperlinks = sum(r['hyperlinks']['total'] for r in results if 'hyperlinks' in r)
        total_images = sum(r['images']['total'] for r in results if 'images' in r)
        
        print(f"  Total hyperlinks across all slots: {total_hyperlinks}")
        print(f"  Total images across all slots: {total_images}")
        
        for result in results:
            if 'error' in result:
                print(f"    Slot {result['slot_number']}: ERROR - {result['error']}")
            else:
                print(f"    Slot {result['slot_number']} ({result['subject']}): "
                      f"{result['hyperlinks']['total']} hyperlinks, "
                      f"{result['images']['total']} images")
    
    # Save detailed results
    output_file = Path("d:/LP/w44_dry_run_results.json")
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n✅ Detailed results saved to: {output_file}")
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(main())
