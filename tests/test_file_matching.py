"""
Test file matching with real Week 41 files.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.file_manager import FileManager

def test_file_matching():
    """Test file matching with real files from Week 41."""
    
    print("="*70)
    print("TESTING FILE MATCHING - Week 41 (10/6-10/10)")
    print("="*70)
    print()
    
    # Initialize file manager
    base_path = "F:/rodri/Documents/OneDrive/AS/Lesson Plan"
    file_mgr = FileManager(base_path)
    
    # Test 1: Validate base path
    print("1. Base Path Validation")
    print(f"   Path: {file_mgr.base_path}")
    print(f"   Valid: {file_mgr.validate_base_path()}")
    print()
    
    # Test 2: Get week folder
    week_of = "10/06-10/10"
    week_folder = file_mgr.get_week_folder(week_of)
    print(f"2. Week Folder")
    print(f"   Week: {week_of}")
    print(f"   Folder: {week_folder}")
    print(f"   Exists: {week_folder.exists()}")
    print()
    
    # Test 3: List all primary teacher files
    print("3. Available Primary Teacher Files")
    files = file_mgr.list_primary_teacher_files(week_folder)
    for i, file in enumerate(files, 1):
        print(f"   {i}. {file['name']}")
        print(f"      Size: {file['size']/1024:.1f} KB")
        print(f"      Modified: {file['modified']}")
    print()
    
    # Test 4: Find specific teacher files
    print("4. Teacher File Matching Tests")
    print()
    
    test_cases = [
        ("Davies", "Math", "Should find: 10_6-10_10 Davies Lesson Plans.docx"),
        ("Lang", "ELA", "Should find: Lang Lesson Plans 10_6_25-10_10_25.docx"),
        ("Savoca", "Science", "Should find: Ms. Savoca-10_6_25-10_10_25 Lesson plans.docx"),
        ("Savoca", "Social Studies", "Should find: Ms. Savoca-10_6_25-10_10_25 Lesson plans.docx"),
        ("Smith", "Math", "Should find: None (teacher doesn't exist)"),
    ]
    
    for teacher, subject, expected in test_cases:
        result = file_mgr.find_primary_teacher_file(week_folder, teacher, subject)
        
        print(f"   Teacher: {teacher}, Subject: {subject}")
        print(f"   Expected: {expected}")
        
        if result:
            filename = Path(result).name
            print(f"   ✅ Found: {filename}")
        else:
            print(f"   ❌ Not found")
        print()
    
    # Test 5: Output path generation
    print("5. Output Path Generation")
    user_name = "Maria Rodriguez"
    output_path = file_mgr.get_output_path(week_folder, user_name, week_of)
    print(f"   User: {user_name}")
    print(f"   Week: {week_of}")
    print(f"   Output: {output_path}")
    print(f"   Filename: {Path(output_path).name}")
    print()
    
    # Test 6: Available weeks
    print("6. Available Week Folders")
    weeks = file_mgr.get_available_weeks(limit=5)
    for week in weeks:
        print(f"   {week['folder_name']}: {week['file_count']} files")
    print()
    
    print("="*70)
    print("TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    test_file_matching()
