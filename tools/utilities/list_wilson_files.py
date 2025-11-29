"""List files in Wilson's folder."""
from pathlib import Path
import time

folder = Path(r'F:\rodri\Documents\OneDrive\AS\Wilson LP\25 W43')

print(f"📁 Folder: {folder}")
print("=" * 80)

if not folder.exists():
    print("❌ Folder does not exist!")
    exit(1)

docx_files = sorted(
    [f for f in folder.glob('*.docx')],
    key=lambda f: f.stat().st_mtime,
    reverse=True
)

if not docx_files:
    print("❌ No DOCX files found!")
    exit(1)

print(f"\nFound {len(docx_files)} DOCX files:\n")

for f in docx_files:
    size_kb = f.stat().st_size / 1024
    mtime = f.stat().st_mtime
    print(f"  • {f.name}")
    print(f"    Size: {size_kb:.1f} KB")
    print(f"    Modified: {mtime}")
    print()
