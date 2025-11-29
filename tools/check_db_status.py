"""Check database status and user configuration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import get_db


def main():
    db = get_db()
    
    # Check for Wilson Rodrigues
    user = db.get_user_by_name('Wilson Rodrigues')
    
    if not user:
        print("User 'Wilson Rodrigues' not found in database")
        print("\nCreating test user...")
        user_id = db.create_user(
            name='Wilson Rodrigues',
            email='wilson@test.com',
            grade='3'
        )
        user = db.get_user(user_id)
        print(f"Created user: {user['name']} (ID: {user['id']})")
    else:
        print(f"Found user: {user['name']} (ID: {user['id']})")
    
    # Check slots
    slots = db.get_user_slots(user['id'])
    print(f"\nConfigured slots: {len(slots)}")
    
    if slots:
        for slot in slots:
            print(f"  Slot {slot['slot_number']}: {slot['subject']}")
            print(f"    Teacher: {slot.get('primary_teacher_name', 'N/A')}")
            print(f"    File Pattern: {slot.get('primary_teacher_file_pattern', 'N/A')}")
    else:
        print("\nNo slots configured. Creating test slots...")
        
        # Create test slots
        test_slots = [
            {
                'slot_number': 1,
                'subject': 'Language Arts',
                'grade': '3',
                'primary_teacher_name': 'Lang',
                'primary_teacher_file_pattern': 'Lang'
            },
            {
                'slot_number': 2,
                'subject': 'Social Studies',
                'grade': '3',
                'primary_teacher_name': 'Davies',
                'primary_teacher_file_pattern': 'Davies'
            },
            {
                'slot_number': 3,
                'subject': 'Science',
                'grade': '3',
                'primary_teacher_name': 'Savoca',
                'primary_teacher_file_pattern': 'Savoca'
            }
        ]
        
        for slot_data in test_slots:
            slot_id = db.create_class_slot(
                user_id=user['id'],
                slot_number=slot_data['slot_number'],
                subject=slot_data['subject'],
                grade=slot_data['grade'],
                primary_teacher_name=slot_data['primary_teacher_name'],
                primary_teacher_file_pattern=slot_data['primary_teacher_file_pattern']
            )
            print(f"  Created Slot {slot_data['slot_number']}: {slot_data['subject']}")
        
        slots = db.get_user_slots(user['id'])
    
    # Check for input files
    print("\nChecking input files...")
    input_dir = Path('input')
    if input_dir.exists():
        docx_files = list(input_dir.glob('*.docx'))
        print(f"Found {len(docx_files)} DOCX files in input/:")
        for f in docx_files:
            print(f"  - {f.name}")
    else:
        print("Input directory not found")
    
    print("\n" + "="*60)
    print("Database Status Summary:")
    print(f"  User: {user['name']} (ID: {user['id']})")
    print(f"  Slots: {len(slots)}")
    print(f"  Ready for testing: {'YES' if slots and docx_files else 'NO'}")
    print("="*60)


if __name__ == '__main__':
    main()
