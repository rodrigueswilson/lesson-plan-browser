"""Check exact filenames and test hyperlink extraction."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from tools.docx_parser import DOCXParser

folder = Path(r'F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W43')

# Get all input DOCX files (not output files)
all_files = list(folder.glob('*.docx'))
input_files = [f for f in all_files if not f.name.startswith('Daniela_Silva_Weekly')]

print("=" * 80)
print(f"INPUT FILES IN: {folder.name}")
print("=" * 80)

for file in sorted(input_files):
    print(f"\n📄 {file.name}")
    print(f"   Path: {file}")
    print(f"   Exists: {file.exists()}")
    print(f"   Size: {file.stat().st_size / 1024:.1f} KB")
    
    try:
        parser = DOCXParser(str(file))
        hyperlinks = parser.extract_hyperlinks()
        print(f"   ✅ Hyperlinks: {len(hyperlinks)}")
        
        if hyperlinks:
            print(f"\n   First 3 hyperlinks:")
            for i, link in enumerate(hyperlinks[:3], 1):
                print(f"     {i}. {link.get('text', 'N/A')[:40]}...")
                print(f"        URL: {link.get('url', 'N/A')[:50]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
