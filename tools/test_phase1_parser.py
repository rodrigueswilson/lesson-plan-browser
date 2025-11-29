"""
Test Phase 1 parser implementation with actual DOCXParser class.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.docx_parser import DOCXParser

TEST_FILE = r'F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W43\10_20-10_24 Davies Lesson Plans.docx'

def test_parser():
    print("="*80)
    print("TESTING PHASE 1 PARSER IMPLEMENTATION")
    print("="*80)
    print()
    
    parser = DOCXParser(TEST_FILE)
    hyperlinks = parser.extract_hyperlinks()
    
    print(f"Total hyperlinks extracted: {len(hyperlinks)}")
    print()
    
    # Check schema version
    with_v2 = [h for h in hyperlinks if h.get('schema_version') == '2.0']
    print(f"Links with schema v2.0: {len(with_v2)}/{len(hyperlinks)}")
    
    # Check coordinates
    table_links = [h for h in hyperlinks if h.get('table_idx') is not None]
    para_links = [h for h in hyperlinks if h.get('table_idx') is None]
    
    print(f"Table links (with coordinates): {len(table_links)}")
    print(f"Paragraph links (no coordinates): {len(para_links)}")
    print()
    
    # Show sample
    print("="*80)
    print("SAMPLE LINKS:")
    print("="*80)
    print()
    
    for i, link in enumerate(hyperlinks[:3], 1):
        print(f"{i}. {link['text'][:50]}")
        print(f"   Schema: {link.get('schema_version')}")
        print(f"   Type: {link.get('context_type')}")
        
        if link.get('table_idx') is not None:
            print(f"   Coordinates: table={link['table_idx']}, row={link['row_idx']}, cell={link['cell_idx']}")
            print(f"   Row label: '{link['row_label'][:40]}'")
            print(f"   Col header: '{link['col_header']}'")
            print(f"   Day hint: {link.get('day_hint')}")
        else:
            print(f"   Coordinates: None (paragraph link)")
        
        print(f"   Section hint: {link.get('section_hint')}")
        print()
    
    # Validation
    print("="*80)
    print("VALIDATION:")
    print("="*80)
    print()
    
    errors = []
    
    # Check all have schema_version
    if len(with_v2) != len(hyperlinks):
        errors.append(f"Not all links have schema v2.0: {len(with_v2)}/{len(hyperlinks)}")
    
    # Check table links have coordinates
    for link in table_links:
        if link['table_idx'] is None or link['row_idx'] is None or link['cell_idx'] is None:
            errors.append(f"Table link '{link['text']}' missing coordinates")
    
    # Check paragraph links don't have coordinates
    for link in para_links:
        if link['table_idx'] is not None:
            errors.append(f"Paragraph link '{link['text']}' has table_idx")
    
    if errors:
        print("❌ ERRORS:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ All validation checks passed!")
    
    print()
    print("="*80)
    print("PHASE 1 PARSER TEST COMPLETE")
    print("="*80)
    
    return len(errors) == 0

if __name__ == '__main__':
    success = test_parser()
    sys.exit(0 if success else 1)
