"""Test DOCXParser class directly."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.docx_parser import DOCXParser

folder = Path(r'F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W43')
morais_file = folder / 'Morais 10_20_25 - 10_24_25.docx'

print("=" * 80)
print(f"Testing DOCXParser on: {morais_file.name}")
print("=" * 80)

try:
    parser = DOCXParser(str(morais_file))
    print("✅ DOCXParser initialized")
    
    hyperlinks = parser.extract_hyperlinks()
    print(f"\n📊 Extracted {len(hyperlinks)} hyperlinks")
    
    if hyperlinks:
        print("\nFirst 5 hyperlinks:")
        for i, link in enumerate(hyperlinks[:5], 1):
            print(f"\n{i}. Text: {link.get('text', 'N/A')}")
            print(f"   URL: {link.get('url', 'N/A')[:60]}")
            print(f"   Location: {link.get('context_type', 'N/A')}")
            print(f"   Schema: {link.get('schema_version', 'N/A')}")
            if link.get('table_idx') is not None:
                print(f"   Coordinates: table={link.get('table_idx')}, row={link.get('row_idx')}, cell={link.get('cell_idx')}")
    else:
        print("\n⚠️  No hyperlinks extracted!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
