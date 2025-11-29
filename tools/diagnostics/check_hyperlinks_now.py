"""
Quick diagnostic: Check if hyperlinks exist in Daniela's input files.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.docx_parser import DOCXParser

# Daniela's input files - use Path to handle spaces correctly
from pathlib import Path as P
input_files = [
    P(r'F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W43') / 'Morais 10_20_25 - 10_24_25.docx',
    P(r'F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W43') / 'Mrs. Grande Science 10_20- 10_24.docx'
]

print("=" * 80)
print("HYPERLINK EXTRACTION DIAGNOSTIC")
print("=" * 80)

for file_path in input_files:
    if not Path(file_path).exists():
        print(f"\n❌ File not found: {file_path}")
        continue
    
    print(f"\n📄 File: {Path(file_path).name}")
    print("-" * 80)
    
    try:
        parser = DOCXParser(file_path)
        hyperlinks = parser.extract_hyperlinks()
        
        print(f"✅ Found {len(hyperlinks)} hyperlinks")
        
        if hyperlinks:
            print("\nFirst 5 hyperlinks:")
            for i, link in enumerate(hyperlinks[:5], 1):
                print(f"\n  {i}. Text: {link.get('text', 'N/A')[:50]}")
                print(f"     URL: {link.get('url', 'N/A')[:60]}")
                print(f"     Location: {link.get('location_type', 'N/A')}")
                if link.get('table_idx') is not None:
                    print(f"     Coordinates: table={link.get('table_idx')}, row={link.get('row_idx')}, cell={link.get('cell_idx')}")
                    print(f"     Row label: {link.get('row_label', 'N/A')}")
                    print(f"     Col header: {link.get('col_header', 'N/A')}")
        else:
            print("⚠️  No hyperlinks found in this file")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
