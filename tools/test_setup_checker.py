"""
Test setup checker for Day 7 end-to-end testing.
Verifies database configuration, test data, and system readiness.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import get_db
import json

def check_database_setup():
    """Check database for test users and slots."""
    print("=" * 60)
    print("DATABASE SETUP CHECKER - DAY 7")
    print("=" * 60)
    
    db = get_db()
    
    # Check users
    users = db.list_users()
    print(f"\n📊 Users in database: {len(users)}")
    
    if not users:
        print("⚠️  No users found. Creating test user...")
        user_id = db.create_user("Wilson Rodrigues", "wilson@example.com")
        print(f"✅ Created test user: Wilson Rodrigues (ID: {user_id})")
        users = [db.get_user(user_id)]
    
    # Display user details
    for user in users:
        print(f"\n👤 User: {user['name']}")
        print(f"   ID: {user['id']}")
        print(f"   Email: {user.get('email', 'N/A')}")
        
        # Check slots for this user
        slots = db.get_user_slots(user['id'])
        print(f"   Class Slots: {len(slots)}")
        
        if slots:
            for slot in slots:
                print(f"      Slot {slot['slot_number']}: {slot['subject']} (Grade {slot['grade']})")
                print(f"         Teacher: {slot.get('primary_teacher_name', 'N/A')}")
                print(f"         File Pattern: {slot.get('primary_teacher_file_pattern', 'N/A')}")
        else:
            print("      ⚠️  No slots configured")
    
    return users

def check_input_files():
    """Check available input files."""
    print("\n" + "=" * 60)
    print("INPUT FILES CHECK")
    print("=" * 60)
    
    input_dir = Path("input")
    if not input_dir.exists():
        print("❌ Input directory not found!")
        return []
    
    docx_files = list(input_dir.glob("*.docx"))
    print(f"\n📁 DOCX files in input/: {len(docx_files)}")
    
    for file in docx_files:
        size_kb = file.stat().st_size / 1024
        print(f"   - {file.name} ({size_kb:.1f} KB)")
    
    return docx_files

def check_test_data():
    """Check if test data exists."""
    print("\n" + "=" * 60)
    print("TEST DATA CHECK")
    print("=" * 60)
    
    output_dir = Path("output")
    test_files = [
        "test_merged.json",
        "test_merged.docx"
    ]
    
    for file in test_files:
        file_path = output_dir / file
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"   ✅ {file} ({size_kb:.1f} KB)")
        else:
            print(f"   ❌ {file} (not found)")

def suggest_test_configuration():
    """Suggest test configuration based on available files."""
    print("\n" + "=" * 60)
    print("SUGGESTED TEST CONFIGURATION")
    print("=" * 60)
    
    input_files = list(Path("input").glob("*.docx"))
    template_files = [f for f in input_files if "template" in f.name.lower()]
    lesson_files = [f for f in input_files if "template" not in f.name.lower()]
    
    print(f"\n📋 Available lesson plan files: {len(lesson_files)}")
    
    # Map files to potential subjects
    file_mapping = []
    for file in lesson_files:
        name = file.stem.lower()
        if "lang" in name or "ela" in name:
            file_mapping.append(("ELA", file.name, "Lang"))
        elif "savoca" in name or "science" in name:
            file_mapping.append(("Science", file.name, "Savoca"))
        elif "davies" in name or "math" in name:
            file_mapping.append(("Math", file.name, "Davies"))
        elif "piret" in name:
            file_mapping.append(("Social Studies", file.name, "Piret"))
        else:
            file_mapping.append(("Unknown", file.name, "Unknown"))
    
    print("\n💡 Recommended slot configuration:")
    for i, (subject, filename, teacher) in enumerate(file_mapping, 1):
        print(f"   Slot {i}: {subject} - {teacher}")
        print(f"      File: {filename}")
    
    return file_mapping

def create_test_slots(user_id: str, file_mapping: list):
    """Create test slots based on file mapping."""
    print("\n" + "=" * 60)
    print("CREATE TEST SLOTS")
    print("=" * 60)
    
    db = get_db()
    
    # Delete existing slots
    deleted = db.delete_user_slots(user_id)
    if deleted > 0:
        print(f"🗑️  Deleted {deleted} existing slots")
    
    # Create new slots
    for i, (subject, filename, teacher) in enumerate(file_mapping, 1):
        if subject != "Unknown":
            slot_id = db.create_class_slot(
                user_id=user_id,
                slot_number=i,
                subject=subject,
                grade="3",
                homeroom=f"3-{i}",
                proficiency_levels=json.dumps(["Entering", "Emerging", "Developing"]),
                primary_teacher_file=f"input/{filename}"
            )
            # Update with teacher name and pattern
            db.update_class_slot(
                slot_id,
                primary_teacher_name=teacher,
                primary_teacher_file_pattern=filename
            )
            print(f"✅ Created Slot {i}: {subject} ({teacher})")
    
    print(f"\n✅ Test slots created successfully!")

def main():
    """Main test setup checker."""
    users = check_database_setup()
    check_input_files()
    check_test_data()
    file_mapping = suggest_test_configuration()
    
    print("\n" + "=" * 60)
    print("SETUP OPTIONS")
    print("=" * 60)
    
    if users:
        user = users[0]
        slots = get_db().get_user_slots(user['id'])
        
        if not slots and file_mapping:
            print("\n❓ Would you like to create test slots? (y/n): ", end="")
            response = input().strip().lower()
            if response == 'y':
                create_test_slots(user['id'], file_mapping)
                print("\n✅ Setup complete! Ready for testing.")
            else:
                print("\n⏭️  Skipped slot creation.")
        elif slots:
            print(f"\n✅ User '{user['name']}' has {len(slots)} slots configured")
            print("   Ready for testing!")
        else:
            print("\n⚠️  No lesson files found to configure slots")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("\n1. Run Test 1: python main.py --user-id <user_id> --week-of '10/06-10/10'")
    print("2. Or use batch processor directly")
    print("3. Check output/ directory for results")
    print("\n")

if __name__ == "__main__":
    main()
