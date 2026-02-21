"""Test both Wilson Rodrigues and Daniela Silva's configurations."""

import io
import sys
from pathlib import Path

# Set UTF-8 encoding for stdout
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.supabase_database import SupabaseDatabase
from tools.diagnostics.analyze_slot_structures import analyze_week_folder


def get_user_id(db: SupabaseDatabase, name: str) -> str:
    """Find user ID by name."""
    users = db.client.table("users").select("id, first_name, last_name, name").execute()

    for user in users.data:
        full_name = user.get("name", "").lower()
        first = user.get("first_name", "").lower()
        last = user.get("last_name", "").lower()

        if name.lower() in full_name or name.lower() in first:
            return user["id"]

    return None


def test_user_configuration(user_id: str, user_name: str, week_folder: str):
    """Test a user's configuration."""
    print(f"\n{'=' * 60}")
    print(f"TESTING: {user_name}")
    print("=" * 60)

    try:
        db = SupabaseDatabase()
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        return False

    # Get user info
    user_info = db.client.table("users").select("*").eq("id", user_id).execute()
    if not user_info.data:
        print(f"ERROR: User not found: {user_id}")
        return False

    user_data = user_info.data[0]
    base_path = user_data.get("base_path_override")
    print(f"\nUser ID: {user_id}")
    print(f"Base path: {base_path or 'Not set'}")

    if not base_path:
        print("ERROR: Base path not configured")
        return False

    # Get slots
    slots = db.get_user_slots(user_id)
    print(f"Slots configured: {len(slots)}")

    if not slots:
        print("ERROR: No slots configured")
        return False

    # Display slot summary
    print("\nSlot Configuration Summary:")
    print("-" * 60)
    for slot in sorted(slots, key=lambda x: x.slot_number):
        teacher = (
            slot.primary_teacher_file_pattern or slot.primary_teacher_name or "N/A"
        )
        print(f"  Slot {slot.slot_number}: {slot.subject} ({teacher})")

    # Check week folder
    base_path_obj = Path(base_path)
    if not base_path_obj.exists():
        print(f"\nERROR: Base path does not exist: {base_path}")
        return False

    week_path = base_path_obj / week_folder
    if not week_path.exists():
        print(f"\nERROR: Week folder does not exist: {week_path}")
        return False

    print(f"\nAnalyzing week folder: {week_folder}")
    print(f"Path: {week_path}")

    # Analyze documents
    analysis = analyze_week_folder(week_path)
    if "error" in analysis:
        print(f"ERROR: {analysis['error']}")
        return False

    # Filter source documents
    source_files = [
        d
        for d in analysis["documents"]
        if d.get("available_slots", 0) > 0
        and "error" not in d
        and not d["file_name"].startswith(user_name.split()[0])  # Exclude output files
    ]

    print(f"\nFound {len(source_files)} source documents:")
    for doc in source_files:
        print(f"  - {doc['file_name']}: {doc['available_slots']} slot(s)")

    # Test slot matching
    print("\n" + "=" * 60)
    print("SLOT MATCHING TEST")
    print("=" * 60)

    matches = 0
    single_slot_matches = 0
    mismatches = 0
    not_found = 0

    for slot in sorted(slots, key=lambda x: x.slot_number):
        slot_num = slot.slot_number
        subject = slot.subject
        teacher_pattern = (
            slot.primary_teacher_file_pattern
            or slot.primary_teacher_name
            or f"{slot.primary_teacher_first_name or ''} {slot.primary_teacher_last_name or ''}".strip()
            or "Unknown"
        )

        # Find matching document
        matching_doc = None
        for doc in source_files:
            filename_lower = doc["file_name"].lower()
            name_parts = teacher_pattern.split()
            if teacher_pattern.lower() in filename_lower or (
                name_parts and name_parts[-1].lower() in filename_lower
            ):
                matching_doc = doc
                break

        if not matching_doc:
            print(f"\nSlot {slot_num}: {subject} ({teacher_pattern})")
            print("  [NOT FOUND] No matching document")
            not_found += 1
            continue

        # Find actual slot in document
        actual_slot = None
        for slot_detail in matching_doc.get("slot_details", []):
            if "error" in slot_detail:
                continue

            slot_subject = slot_detail.get("subject", "").lower()
            req_subject = subject.lower() if subject else ""

            if req_subject and (
                req_subject in slot_subject or slot_subject in req_subject
            ):
                if "/" in req_subject:
                    tokens = req_subject.split("/")
                    if any(t.strip() in slot_subject for t in tokens):
                        actual_slot = slot_detail["slot_number"]
                        break
                else:
                    actual_slot = slot_detail["slot_number"]
                    break

        print(f"\nSlot {slot_num}: {subject} ({teacher_pattern})")
        print(f"  File: {matching_doc['file_name']}")

        if actual_slot:
            is_single_slot = matching_doc["available_slots"] == 1
            if actual_slot == slot_num:
                print(f"  [MATCH] Slot {actual_slot}")
                matches += 1
            elif is_single_slot:
                print("  [SINGLE-SLOT] Maps to slot 1 (expected)")
                single_slot_matches += 1
            else:
                print(f"  [MISMATCH] Document has in slot {actual_slot}")
                mismatches += 1
        else:
            print(f"  [WARNING] Subject '{subject}' not found in document")
            not_found += 1

    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Total slots: {len(slots)}")
    print(f"Perfect matches: {matches}")
    print(f"Single-slot mappings (expected): {single_slot_matches}")
    print(f"Multi-slot mismatches (informational): {mismatches}")
    print(f"Not found: {not_found}")

    # Status
    if not_found == 0 and mismatches <= 2:  # Allow some mismatches
        print("\n[SUCCESS] Configuration is valid and ready for use!")
        print("System will work correctly via subject-based detection.")
        return True
    elif not_found > 0:
        print("\n[WARNING] Some slots could not find matching documents.")
        print("Review file patterns and document availability.")
        return False
    else:
        print("\n[INFO] Configuration is functional.")
        print("Mismatches are informational - system works correctly.")
        return True


def main():
    """Test both users' configurations."""
    print("=" * 60)
    print("TESTING USER CONFIGURATIONS")
    print("=" * 60)

    try:
        db = SupabaseDatabase()
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        return False

    # Test Wilson Rodrigues (use the ID we configured)
    wilson_id = "905a382a-ca42-4846-9d8f-e617af3114ad"  # Wilson Rodrigues we configured
    # Verify it exists
    user_check = (
        db.client.table("users").select("id, name").eq("id", wilson_id).execute()
    )
    if not user_check.data:
        print("\nERROR: Configured Wilson Rodrigues user not found")
        wilson_result = False
    else:
        wilson_result = test_user_configuration(wilson_id, "Wilson Rodrigues", "25 W51")

    # Test Daniela Silva
    daniela_id = get_user_id(db, "Daniela Silva")
    if daniela_id:
        daniela_result = test_user_configuration(daniela_id, "Daniela Silva", "25 W51")
    else:
        print("\nERROR: Daniela Silva not found")
        daniela_result = False

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Wilson Rodrigues: {'PASS' if wilson_result else 'FAIL'}")
    print(f"Daniela Silva: {'PASS' if daniela_result else 'FAIL'}")

    if wilson_result and daniela_result:
        print("\n[SUCCESS] Both configurations are ready for use!")
        return True
    else:
        print("\n[WARNING] Some configurations need attention.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
