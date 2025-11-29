"""Clear Python cache files."""
import shutil
from pathlib import Path

cache_dir = Path("d:/LP/tools/__pycache__")

if cache_dir.exists():
    print(f"Deleting: {cache_dir}")
    shutil.rmtree(cache_dir)
    print("✅ Cache deleted!")
else:
    print("No cache directory found")
