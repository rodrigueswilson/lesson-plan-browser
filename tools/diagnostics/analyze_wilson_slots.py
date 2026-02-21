"""Analyze Wilson Rodrigues' slot configurations and identify problems."""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.supabase_database import SupabaseDatabase
from tools.diagnostics.analyze_slot_structures import analyze_week_folder


def get_wilson_user_id(db: SupabaseDatabase) -> str:
    """Find Wilson Rodrigues' user ID."""
    # Try to find user by name
    users = db.client.table("users").select("id, first_name, last_name, name").execute()

    for user in users.data:
        name = user.get("name", "").lower()
        first = user.get("first_name", "").lower()
        last = user.get("last_name", "").lower()

        if "wilson" in name or "wilson" in first:
            if "rodrigues" in name or "rodrigues" in last:
                return user["id"]

    return None


def get_user_slots(db: SupabaseDatabase, user_id: str) -> list:
    """Get all slots for a user."""
    slots = (
        db.client.table("class_slots")
        .select("*")
        .eq("user_id", user_id)
        .order("slot_number")
        .execute()
    )
    return slots.data


def get_user_base_path(db: SupabaseDatabase, user_id: str) -> str:
    """Get user's base path override."""
    user = (
        db.client.table("users")
        .select("base_path_override")
        .eq("id", user_id)
        .execute()
    )
    if user.data:
        return user.data[0].get("base_path_override")
    return None


def analyze_wilson_slots():
    """Main analysis function."""
    print("=" * 60)
    print("WILSON RODRIGUES SLOT ANALYSIS")
    print("=" * 60)

    # Initialize database
    try:
        db = SupabaseDatabase()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return

    # Find Wilson's user ID
    print("\n1. Finding Wilson Rodrigues' user ID...")
    user_id = get_wilson_user_id(db)
    if not user_id:
        print("ERROR: Could not find Wilson Rodrigues in database")
        return

    print(f"   Found user ID: {user_id}")

    # Get user info
    user_info = db.client.table("users").select("*").eq("id", user_id).execute()
    if user_info.data:
        user_data = user_info.data[0]
        print(f"   Name: {user_data.get('name', 'N/A')}")
        print(f"   Base path: {user_data.get('base_path_override', 'Not set')}")

    # Get slots
    print("\n2. Retrieving slot configurations...")
    slots = get_user_slots(db, user_id)
    print(f"   Found {len(slots)} slots")

    if not slots:
        print("   No slots configured")
        return

    # Display slot configuration
    print("\n3. Slot Configuration:")
    print("-" * 60)
    for slot in slots:
        print(f"\nSlot {slot.get('slot_number')}:")
        print(f"  Subject: {slot.get('subject', 'N/A')}")
        print(f"  Primary Teacher: {slot.get('primary_teacher_name', 'N/A')}")
        print(f"  File Pattern: {slot.get('primary_teacher_file_pattern', 'N/A')}")
        print(f"  Grade: {slot.get('grade', 'N/A')}")
        print(f"  Homeroom: {slot.get('homeroom', 'N/A')}")

    # Get base path
    base_path = get_user_base_path(db, user_id)
    if not base_path:
        print("\n4. Base path not configured - cannot analyze documents")
        return

    print(f"\n4. Base path: {base_path}")

    # Find recent week folders
    print("\n5. Finding recent week folders...")
    base_path_obj = Path(base_path)
    if not base_path_obj.exists():
        print(f"   ERROR: Base path does not exist: {base_path}")
        return

    # Look for week folders (common patterns)
    week_folders = []
    for item in base_path_obj.iterdir():
        if item.is_dir():
            # Check if it looks like a week folder
            name = item.name.lower()
            if any(keyword in name for keyword in ["w", "week", "12", "11", "10"]):
                week_folders.append(item)

    week_folders.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    if not week_folders:
        print("   No week folders found")
        return

    print(f"   Found {len(week_folders)} potential week folders")
    print(f"   Analyzing most recent: {week_folders[0].name}")

    # Analyze the most recent week folder
    print("\n6. Analyzing document structures...")
    analysis = analyze_week_folder(week_folders[0])

    if "error" in analysis:
        print(f"   ERROR: {analysis['error']}")
        return

    # Filter source documents
    source_files = [
        d
        for d in analysis["documents"]
        if d.get("available_slots", 0) > 0
        and "error" not in d
        and not d["file_name"].startswith("Wilson")  # Exclude output files
    ]

    print(f"\n   Found {len(source_files)} source documents:")
    for doc in source_files:
        print(f"     - {doc['file_name']}: {doc['available_slots']} slot(s)")

    # Compare slots with documents
    print("\n7. Comparing slot configuration with documents:")
    print("-" * 60)

    mismatches = []
    matches = []

    for slot in slots:
        slot_num = slot.get("slot_number")
        subject = slot.get("subject")
        teacher_pattern = (
            slot.get("primary_teacher_file_pattern")
            or slot.get("primary_teacher_name")
            or "Unknown"
        )

        # Find matching document
        matching_doc = None
        for doc in source_files:
            # Check if teacher pattern matches filename
            if teacher_pattern.lower() in doc["file_name"].lower():
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
                print(f"  [MISMATCH] Found in slot {actual_slot}, not slot {slot_num}")
                mismatches.append(
                    {
                        "requested": slot_num,
                        "actual": actual_slot,
                        "subject": subject,
                        "file": matching_doc["file_name"],
                    }
                )
        else:
            print(f"  [WARNING] Subject '{subject}' not found in document")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total slots configured: {len(slots)}")
    print(f"Matches: {len(matches)}")
    print(f"Mismatches: {len(mismatches)}")

    if mismatches:
        print("\nCommon Problems Identified:")
        print("-" * 60)

        # Group by problem type
        single_slot_files = {}
        multi_slot_mismatches = []

        for mismatch in mismatches:
            # Check if it's a single-slot file
            for doc in source_files:
                if mismatch["file"] in doc["file_name"]:
                    if doc["available_slots"] == 1:
                        single_slot_files[mismatch["subject"]] = mismatch["file"]
                    else:
                        multi_slot_mismatches.append(mismatch)

        if single_slot_files:
            print("\n1. Single-Slot Documents (Expected Behavior):")
            for subject, file in single_slot_files.items():
                print(f"   - {subject}: {file}")
                print("     -> Always maps to slot 1 (this is expected)")

        if multi_slot_mismatches:
            print("\n2. Slot Numbering Mismatches:")
            for mismatch in multi_slot_mismatches:
                print(f"   - Slot {mismatch['requested']} ({mismatch['subject']}):")
                print(f"     Found in slot {mismatch['actual']} in {mismatch['file']}")
                print("     -> User config doesn't match document structure")

    # Save results
    output_file = Path("logs/wilson_slot_analysis.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    results = {
        "user_id": user_id,
        "base_path": base_path,
        "week_folder": str(week_folders[0]) if week_folders else None,
        "slot_configuration": slots,
        "document_analysis": analysis,
        "matches": matches,
        "mismatches": mismatches,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    analyze_wilson_slots()
