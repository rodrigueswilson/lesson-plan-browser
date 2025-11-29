from backend.file_manager import FileManager
from pathlib import Path

week_folder = Path(r"F:\rodri\Documents\OneDrive\AS\Daniela LP\25 W44")
file_mgr = FileManager()

# Test different patterns
patterns = [
    ("Catarina Morais", "Math"),
    ("Morais", "Math"),
    ("Catarina", "Math"),
]

print("Testing file matching patterns:\n")
for pattern, subject in patterns:
    result = file_mgr.find_primary_teacher_file(week_folder, pattern, subject)
    print(f"Pattern: '{pattern}', Subject: '{subject}'")
    print(f"  Result: {result}")
    print()
