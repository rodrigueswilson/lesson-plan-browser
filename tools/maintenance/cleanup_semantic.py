"""Remove semantic matching solution files."""
import os

files_to_remove = [
    'tools/semantic_matcher.py',
    'test_semantic_matcher.py',
    'test_backend_check.py',
    'test_import.py',
    'SESSION_9_COMPLETE.md',
    'SESSION_9_SUMMARY.md',
    'PYTORCH_TROUBLESHOOTING.md',
    'SEMANTIC_MATCHING_QUICKSTART.md'
]

for file in files_to_remove:
    if os.path.exists(file):
        os.remove(file)
        print(f"Removed: {file}")
    else:
        print(f"Not found: {file}")

print("\nCleanup complete!")
