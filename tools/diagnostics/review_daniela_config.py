"""Review and align Daniela Silva's slot configuration with document structures."""

import argparse
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


def get_daniela_user_id(db: SupabaseDatabase) -> str:
    """Find Daniela Silva's user ID."""
    users = db.client.table("users").select("id, first_name, last_name, name").execute()

    for user in users.data:
        name = user.get("name", "").lower()
        first = user.get("first_name", "").lower()
        last = user.get("last_name", "").lower()

        if "daniela" in name or "daniela" in first:
            if "silva" in name or "silva" in last:
                return user["id"]

    return None


def analyze_daniela_documents(week_folder_path: str):
    """Analyze documents in Daniela's week folder."""
    folder = Path(week_folder_path)
    if not folder.exists():
        return None

    analysis = analyze_week_folder(folder)
    if "error" in analysis:
        return None

    # Filter source documents
    source_files = [
        d
        for d in analysis["documents"]
        if d.get("available_slots", 0) > 0
        and "error" not in d
        and not d["file_name"].startswith("Daniela_Silva_Weekly")
    ]

    return source_files


def review_daniela_config():
    """Review and suggest updates for Daniela's configuration."""
    print("=" * 60)
    print("REVIEWING DANIELA SILVA'S CONFIGURATION")
    print("=" * 60)

    # Initialize database
    try:
        db = SupabaseDatabase()
    except Exception as e:
        print(f"ERROR: Could not connect to database: {e}")
        return False

    # Find Daniela's user ID
    print("\n1. Finding Daniela Silva's user ID...")
    user_id = get_daniela_user_id(db)
    if not user_id:
        print("ERROR: Could not find Daniela Silva in database")
        return False

    print(f"   Found user ID: {user_id}")

    # Get user info
    user_info = db.client.table("users").select("*").eq("id", user_id).execute()
    if user_info.data:
        user_data = user_info.data[0]
        print(f"   Name: {user_data.get('name', 'N/A')}")
        base_path = user_data.get("base_path_override")
        print(f"   Base path: {base_path or 'Not set'}")

    # Get current slots
    print("\n2. Retrieving current slot configuration...")
    slots = db.get_user_slots(user_id)
    print(f"   Found {len(slots)} slots configured")

    if not slots:
        print("   No slots configured")
        return False

    # Display current configuration
    print("\n3. Current Slot Configuration:")
    print("-" * 60)
    for slot in sorted(slots, key=lambda x: x.slot_number):
        print(f"\nSlot {slot.slot_number}:")
        print(f"  Subject: {slot.subject}")
        print(f"  Primary Teacher: {slot.primary_teacher_name or 'N/A'}")
        print(f"  File Pattern: {slot.primary_teacher_file_pattern or 'N/A'}")
        print(f"  Grade: {slot.grade}")
        print(f"  Homeroom: {slot.homeroom or 'N/A'}")

    # Analyze documents from W51 (most recent)
    print("\n4. Analyzing document structures...")
    if not base_path:
        print("   ERROR: Base path not configured")
        return False

    base_path_obj = Path(base_path)
    if not base_path_obj.exists():
        print(f"   ERROR: Base path does not exist: {base_path}")
        return False

    # Find W51 folder
    w51_folder = base_path_obj / "25 W51"
    if not w51_folder.exists():
        print(f"   ERROR: Week folder not found: {w51_folder}")
        return False

    print(f"   Analyzing: {w51_folder.name}")
    source_files = analyze_daniela_documents(str(w51_folder))

    if not source_files:
        print("   No source documents found")
        return False

    print(f"   Found {len(source_files)} source documents:")
    for doc in source_files:
        print(f"     - {doc['file_name']}: {doc['available_slots']} slot(s)")

    # Compare configuration with documents
    print("\n5. Comparing configuration with documents:")
    print("-" * 60)

    mismatches = []
    matches = []
    single_slot_mappings = []

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

            # Try multiple matching strategies
            # 1. Full pattern match
            if teacher_pattern.lower() in filename_lower:
                matching_doc = doc
                break

            # 2. Last name matching (most reliable)
            name_parts = teacher_pattern.split()
            if name_parts:
                last_name = name_parts[-1].lower()
                if last_name in filename_lower:
                    matching_doc = doc
                    break

            # 3. First name matching
            if len(name_parts) > 1:
                first_name = name_parts[0].lower()
                if first_name in filename_lower:
                    matching_doc = doc
                    break

        if not matching_doc:
            print(f"\nSlot {slot_num}: {subject} ({teacher_pattern})")
            print("  [WARNING] No matching document found")
            continue

        # Find actual slot in document
        actual_slot = None
        for slot_detail in matching_doc.get("slot_details", []):
            if "error" in slot_detail:
                continue

            slot_subject = slot_detail.get("subject", "").lower()
            req_subject = subject.lower() if subject else ""

            # Check subject match
            if req_subject and (
                req_subject in slot_subject or slot_subject in req_subject
            ):
                # Handle combined subjects
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
            if actual_slot == slot_num:
                print(f"  [MATCH] Found in slot {actual_slot}")
                matches.append({"slot": slot_num, "subject": subject})
            else:
                is_single_slot = matching_doc["available_slots"] == 1
                if is_single_slot:
                    print(
                        "  [INFO] Single-slot file - maps to slot 1 (expected behavior)"
                    )
                    single_slot_mappings.append(
                        {
                            "slot": slot_num,
                            "subject": subject,
                            "file": matching_doc["file_name"],
                        }
                    )
                else:
                    print(
                        f"  [MISMATCH] Found in slot {actual_slot}, not slot {slot_num}"
                    )
                    mismatches.append(
                        {
                            "slot_id": slot.id,
                            "requested": slot_num,
                            "actual": actual_slot,
                            "subject": subject,
                            "file": matching_doc["file_name"],
                        }
                    )
        else:
            print(f"  [WARNING] Subject '{subject}' not found in document")

    # Summary and recommendations
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Total slots: {len(slots)}")
    print(f"Matches: {len(matches)}")
    print(f"Single-slot mappings (expected): {len(single_slot_mappings)}")
    print(f"Multi-slot mismatches: {len(mismatches)}")

    if mismatches:
        print("\n" + "=" * 60)
        print("RECOMMENDED UPDATES")
        print("=" * 60)
        print("\nThe following slots have mismatches with document structure:")
        print(
            "(These are informational - system works correctly via subject-based detection)"
        )
        print()

        for mismatch in mismatches:
            print(f"Slot {mismatch['requested']} ({mismatch['subject']}):")
            print(f"  Current: Slot {mismatch['requested']}")
            print(f"  Document: Slot {mismatch['actual']} in {mismatch['file']}")
            print(f"  Recommendation: Update slot number to {mismatch['actual']}")
            print()

        # Ask if user wants to update (or use command line argument)
        auto_update = getattr(review_daniela_config, "auto_update", None)

        if auto_update is None:
            print("\nOptions:")
            print("1. Update slot numbers to match documents (reduces warnings)")
            print("2. Keep current configuration (system works, just has warnings)")
            print("3. Skip updates for now")
            response = input("\nWould you like to update the slot numbers? (1/2/3): ")
        else:
            response = auto_update
            print(f"\nAuto-update mode: {response}")

        if response == "1" or response == "update":
            print("\nUpdating slot numbers...")
            for mismatch in mismatches:
                try:
                    db.update_class_slot(
                        mismatch["slot_id"], slot_number=mismatch["actual"]
                    )
                    print(
                        f"  [OK] Updated slot {mismatch['requested']} -> {mismatch['actual']} ({mismatch['subject']})"
                    )
                except Exception as e:
                    print(
                        f"  [ERROR] Failed to update slot {mismatch['requested']}: {e}"
                    )
            print("\n[SUCCESS] Updates complete!")
        elif response == "2":
            print(
                "\nKeeping current configuration. System will continue to work correctly."
            )
        else:
            print("\nSkipping updates.")

    else:
        print("\n[SUCCESS] All slots align with document structures!")
        print("(Single-slot mappings are expected behavior)")

    if single_slot_mappings:
        print("\n" + "=" * 60)
        print("SINGLE-SLOT DOCUMENTS (Expected Behavior)")
        print("=" * 60)
        print("The following slots map to single-slot documents (always slot 1):")
        for mapping in single_slot_mappings:
            print(f"  Slot {mapping['slot']} ({mapping['subject']}): {mapping['file']}")
        print("\nThis is expected behavior - warnings are informational only.")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Review and align Daniela Silva's slot configuration"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Automatically update slot numbers to match documents",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep current configuration (no updates)",
    )

    args = parser.parse_args()

    # Set auto_update based on arguments
    if args.update:
        review_daniela_config.auto_update = "1"
    elif args.keep:
        review_daniela_config.auto_update = "2"
    else:
        review_daniela_config.auto_update = None

    success = review_daniela_config()
    sys.exit(0 if success else 1)
