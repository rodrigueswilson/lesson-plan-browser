"""List files in Daniela's W43 folder."""
from pathlib import Path

folder = Path(r'F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W43')

if folder.exists():
    print(f"📁 Folder: {folder}")
    print("=" * 80)
    
    docx_files = list(folder.glob('*.docx'))
    print(f"\nFound {len(docx_files)} DOCX files:\n")
    
    for file in sorted(docx_files):
        size_kb = file.stat().st_size / 1024
        print(f"  • {file.name}")
        print(f"    Size: {size_kb:.1f} KB")
        print(f"    Modified: {file.stat().st_mtime}")
        print()
else:
    print(f"❌ Folder not found: {folder}")
