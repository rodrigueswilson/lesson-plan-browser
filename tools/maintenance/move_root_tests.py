"""
Move root-level test files to tests/ directory.

Part of Phase 3.1 - Test File Consolidation
"""

import shutil
from pathlib import Path


def move_root_tests():
    """Move all test_*.py files from root to tests/ directory."""
    
    root_dir = Path(__file__).resolve().parent.parent.parent
    tests_dir = root_dir / "tests"
    
    # Ensure tests directory exists
    tests_dir.mkdir(exist_ok=True)
    
    # Find all test files at root level
    root_test_files = list(root_dir.glob("test_*.py"))
    
    print(f"Found {len(root_test_files)} test files at root level")
    print()
    
    moved = []
    skipped = []
    errors = []
    
    for test_file in sorted(root_test_files):
        target = tests_dir / test_file.name
        
        # Check if file already exists in tests/
        if target.exists():
            print(f"⚠️  SKIP: {test_file.name} (already exists in tests/)")
            skipped.append(test_file.name)
            continue
        
        try:
            # Move the file
            shutil.move(str(test_file), str(target))
            print(f"✅ MOVED: {test_file.name} → tests/{test_file.name}")
            moved.append(test_file.name)
        except Exception as e:
            print(f"❌ ERROR: {test_file.name} - {e}")
            errors.append((test_file.name, str(e)))
    
    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✅ Moved: {len(moved)} files")
    print(f"⚠️  Skipped: {len(skipped)} files (already in tests/)")
    print(f"❌ Errors: {len(errors)} files")
    print()
    
    if moved:
        print("Moved files:")
        for name in moved:
            print(f"  - {name}")
        print()
    
    if skipped:
        print("Skipped files (duplicates):")
        for name in skipped:
            print(f"  - {name}")
        print()
    
    if errors:
        print("Errors:")
        for name, error in errors:
            print(f"  - {name}: {error}")
        print()
    
    print("Next steps:")
    print("1. Run: pytest --collect-only --quiet")
    print("2. Verify all tests are discovered")
    print("3. Run: pytest tests/ -v")
    print("4. Fix any import errors")
    
    return len(moved), len(skipped), len(errors)


if __name__ == "__main__":
    move_root_tests()
