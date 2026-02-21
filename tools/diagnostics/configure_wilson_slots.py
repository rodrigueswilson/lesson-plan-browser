"""Configure Wilson Rodrigues' slots and base path based on document analysis."""

import io
import sys
from pathlib import Path

# Set UTF-8 encoding for stdout
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.supabase_database import SupabaseDatabase


def configure_wilson():
    """Configure Wilson Rodrigues' base path and slots."""
    print("=" * 60)
    print("CONFIGURING WILSON RODRIGUES")
    print("=" * 60)

    # Initialize database
    try:
        db = SupabaseDatabase()
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        return False

    # Wilson's user ID (from previous analysis)
    user_id = "905a382a-ca42-4846-9d8f-e617af3114ad"

    print(f"\nUser ID: {user_id}")

    # Step 1: Set base path
    print("\n1. Setting base path...")
    base_path = r"F:\rodri\Documents\OneDrive\AS\Lesson Plan"

    try:
        success = db.update_user_base_path(user_id, base_path)
        if success:
            print(f"   [OK] Base path set: {base_path}")
        else:
            print("   [ERROR] Failed to set base path")
            return False
    except Exception as e:
        print(f"   [ERROR] Error setting base path: {e}")
        return False

    # Step 2: Get existing slots (to check if any exist)
    print("\n2. Checking existing slots...")
    existing_slots = db.get_user_slots(user_id)
    print(f"   Found {len(existing_slots)} existing slots")

    if existing_slots:
        print("   WARNING: Slots already exist. Review before proceeding.")
        response = input("   Delete existing slots and create new ones? (yes/no): ")
        if response.lower() == "yes":
            # Delete existing slots
            for slot in existing_slots:
                try:
                    db.delete_class_slot(slot.id)
                    print(f"   [OK] Deleted slot {slot.slot_number}")
                except Exception as e:
                    print(f"   [ERROR] Error deleting slot {slot.slot_number}: {e}")
        else:
            print("   Keeping existing slots. Add new slots only.")

    # Step 3: Create slot configurations based on document analysis
    print("\n3. Creating slot configurations...")

    # Slot configurations based on document analysis
    # From W50 analysis:
    # - Savoca: 4 slots (ELA/SS, Math, Science, Health) - Grade 2, Homeroom 209
    # - Lang: 4 slots (ELA, Math, Social Studies, Science) - Need grade/homeroom
    # - Davies: 4 slots (ELA, Math, Social Studies, Science) - Grade 3, Homeroom T2

    slots_to_create = [
        # Savoca slots (Grade 2, Homeroom 209)
        {
            "slot_number": 1,
            "subject": "ELA/SS",
            "grade": "2",
            "homeroom": "209",
            "primary_teacher_file_pattern": "Savoca",
            "primary_teacher_name": "Donna Savoca",
            "plan_group_label": "Savoca Grade 2",
        },
        {
            "slot_number": 2,
            "subject": "Math",
            "grade": "2",
            "homeroom": "209",
            "primary_teacher_file_pattern": "Savoca",
            "primary_teacher_name": "Donna Savoca",
            "plan_group_label": "Savoca Grade 2",
        },
        {
            "slot_number": 3,
            "subject": "Science",
            "grade": "2",
            "homeroom": "209",
            "primary_teacher_file_pattern": "Savoca",
            "primary_teacher_name": "Donna Savoca",
            "plan_group_label": "Savoca Grade 2",
        },
        {
            "slot_number": 4,
            "subject": "Health",
            "grade": "2",
            "homeroom": "209",
            "primary_teacher_file_pattern": "Savoca",
            "primary_teacher_name": "Donna Savoca",
            "plan_group_label": "Savoca Grade 2",
        },
        # Lang slots (Grade 3, Homeroom T2 - from document analysis)
        {
            "slot_number": 5,
            "subject": "ELA",
            "grade": "3",
            "homeroom": "T2",
            "primary_teacher_file_pattern": "Lang",
            "primary_teacher_name": "Kelsey Lang",
            "plan_group_label": "Lang Grade 3",
        },
        {
            "slot_number": 6,
            "subject": "Math",
            "grade": "3",
            "homeroom": "T2",
            "primary_teacher_file_pattern": "Lang",
            "primary_teacher_name": "Kelsey Lang",
            "plan_group_label": "Lang Grade 3",
        },
        {
            "slot_number": 7,
            "subject": "Social Studies",
            "grade": "3",
            "homeroom": "T2",
            "primary_teacher_file_pattern": "Lang",
            "primary_teacher_name": "Kelsey Lang",
            "plan_group_label": "Lang Grade 3",
        },
        {
            "slot_number": 8,
            "subject": "Science",
            "grade": "3",
            "homeroom": "T2",
            "primary_teacher_file_pattern": "Lang",
            "primary_teacher_name": "Kelsey Lang",
            "plan_group_label": "Lang Grade 3",
        },
        # Davies slots (Grade 3, Homeroom T2)
        {
            "slot_number": 9,
            "subject": "ELA",
            "grade": "3",
            "homeroom": "T2",
            "primary_teacher_file_pattern": "Davies",
            "primary_teacher_name": "Caitlin Davies",
            "plan_group_label": "Davies Grade 3",
        },
        {
            "slot_number": 10,
            "subject": "Math",
            "grade": "3",
            "homeroom": "T2",
            "primary_teacher_file_pattern": "Davies",
            "primary_teacher_name": "Caitlin Davies",
            "plan_group_label": "Davies Grade 3",
        },
        {
            "slot_number": 11,
            "subject": "Social Studies",
            "grade": "3",
            "homeroom": "T2",
            "primary_teacher_file_pattern": "Davies",
            "primary_teacher_name": "Caitlin Davies",
            "plan_group_label": "Davies Grade 3",
        },
        {
            "slot_number": 12,
            "subject": "Science",
            "grade": "3",
            "homeroom": "T2",
            "primary_teacher_file_pattern": "Davies",
            "primary_teacher_name": "Caitlin Davies",
            "plan_group_label": "Davies Grade 3",
        },
    ]

    created_count = 0
    error_count = 0

    for slot_config in slots_to_create:
        try:
            # Create slot with basic fields
            slot_id = db.create_class_slot(
                user_id=user_id,
                slot_number=slot_config["slot_number"],
                subject=slot_config["subject"],
                grade=slot_config["grade"],
                homeroom=slot_config.get("homeroom") or None,
                plan_group_label=slot_config.get("plan_group_label"),
                primary_teacher_first_name=slot_config.get(
                    "primary_teacher_name", ""
                ).split()[0]
                if slot_config.get("primary_teacher_name")
                else None,
                primary_teacher_last_name=" ".join(
                    slot_config.get("primary_teacher_name", "").split()[1:]
                )
                if slot_config.get("primary_teacher_name")
                and len(slot_config.get("primary_teacher_name", "").split()) > 1
                else None,
            )

            # Update slot with file pattern and name
            update_fields = {}
            if slot_config.get("primary_teacher_file_pattern"):
                update_fields["primary_teacher_file_pattern"] = slot_config[
                    "primary_teacher_file_pattern"
                ]
            if slot_config.get("primary_teacher_name"):
                update_fields["primary_teacher_name"] = slot_config[
                    "primary_teacher_name"
                ]

            if update_fields:
                db.update_class_slot(slot_id, **update_fields)

            print(
                f"   [OK] Created slot {slot_config['slot_number']}: {slot_config['subject']} ({slot_config.get('primary_teacher_name', 'N/A')})"
            )
            created_count += 1
        except Exception as e:
            print(f"   [ERROR] Error creating slot {slot_config['slot_number']}: {e}")
            error_count += 1

    # Summary
    print("\n" + "=" * 60)
    print("CONFIGURATION SUMMARY")
    print("=" * 60)
    print(f"Base path: {base_path}")
    print(f"Slots created: {created_count}")
    print(f"Errors: {error_count}")
    print(f"Total slots configured: {len(slots_to_create)}")

    if error_count == 0:
        print("\n[SUCCESS] Configuration complete!")
        print("\nNext steps:")
        print("1. Verify slots in the application")
        print("2. Update Lang slots' grade/homeroom if needed (currently placeholders)")
        print("3. Test with one week (W50 or W51)")
    else:
        print(f"\n[WARNING] Configuration completed with {error_count} error(s)")

    return error_count == 0


if __name__ == "__main__":
    success = configure_wilson()
    sys.exit(0 if success else 1)
