"""Check the last processing run to see what happened."""
import json
from pathlib import Path

# Find the most recent output file
output_dir = Path(r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\Output")
if output_dir.exists():
    files = sorted(output_dir.glob("Wilson_Rodrigues_W44_*.docx"), key=lambda f: f.stat().st_mtime, reverse=True)
    if files:
        latest = files[0]
        print(f"Latest output file: {latest.name}")
        print(f"Created: {latest.stat().st_mtime}")
        print()

# Check if there are any cached JSON files
cache_dir = Path(r"D:\LP\cache")
if cache_dir.exists():
    json_files = list(cache_dir.glob("*.json"))
    print(f"Found {len(json_files)} cached JSON files")
    for f in json_files:
        print(f"  - {f.name}")
else:
    print("No cache directory found")

# Check temp directory
import tempfile
temp_dir = Path(tempfile.gettempdir())
temp_files = list(temp_dir.glob("*lesson*.json"))
print(f"\nFound {len(temp_files)} temp JSON files")
for f in temp_files[:5]:  # Show first 5
    print(f"  - {f.name}")
