"""Analyze Wilson Rodrigues' source documents to identify slot structures and problems."""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.diagnostics.analyze_slot_structures import analyze_week_folder


def analyze_wilson_week_folder(week_folder_path: str):
    """Analyze a specific week folder for Wilson."""
    folder = Path(week_folder_path)

    if not folder.exists():
        print(f"ERROR: Week folder does not exist: {week_folder_path}")
        return None

    print(f"\nAnalyzing week folder: {folder.name}")
    print(f"Path: {week_folder_path}")

    analysis = analyze_week_folder(folder)

    if "error" in analysis:
        print(f"ERROR: {analysis['error']}")
        return None

    # Filter source documents (exclude output files)
    source_files = [
        d
        for d in analysis["documents"]
        if d.get("available_slots", 0) > 0
        and "error" not in d
        and not d["file_name"].startswith("Wilson")  # Exclude output files
    ]

    print(f"\nFound {len(source_files)} source documents:")
    print("-" * 60)

    for doc in source_files:
        print(f"\n{doc['file_name']}")
        print(f"  Total slots: {doc['available_slots']}")
        print(
            f"  Tables: {doc['total_tables']} (has signature: {doc['has_signature']})"
        )
        print("  Slot structure:")
        for slot in doc.get("slot_details", []):
            if "error" not in slot:
                print(f"    Slot {slot['slot_number']}: {slot['subject']}")
                print(f"      Teacher: {slot.get('teacher', 'N/A')}")
                print(
                    f"      Homeroom: {slot.get('homeroom', 'N/A')}, Grade: {slot.get('grade', 'N/A')}"
                )

    return analysis


def identify_common_problems(analysis: dict):
    """Identify common problems across documents."""
    if not analysis or "error" in analysis:
        return

    source_files = [
        d
        for d in analysis["documents"]
        if d.get("available_slots", 0) > 0
        and "error" not in d
        and not d["file_name"].startswith("Wilson")
    ]

    print("\n" + "=" * 60)
    print("COMMON PROBLEMS IDENTIFIED")
    print("=" * 60)

    # Problem 1: Single-slot documents
    single_slot_files = [d for d in source_files if d["available_slots"] == 1]
    if single_slot_files:
        print("\n1. Single-Slot Documents (Expected Behavior):")
        print(
            "   These files contain only one slot, so any slot request maps to slot 1."
        )
        print(
            "   This is expected behavior, but may cause warnings if user config uses different slot numbers."
        )
        for doc in single_slot_files:
            slot = doc["slot_details"][0] if doc["slot_details"] else {}
            print(f"   - {doc['file_name']}")
            print(f"     Subject: {slot.get('subject', 'N/A')}")
            print(f"     Teacher: {slot.get('teacher', 'N/A')}")

    # Problem 2: Multi-slot documents with inconsistent numbering
    multi_slot_files = [d for d in source_files if d["available_slots"] > 1]
    if multi_slot_files:
        print("\n2. Multi-Slot Documents:")
        print(
            "   These files contain multiple slots. User configuration must match document structure."
        )
        for doc in multi_slot_files:
            print(f"   - {doc['file_name']} ({doc['available_slots']} slots):")
            for slot in doc.get("slot_details", []):
                if "error" not in slot:
                    print(
                        f"     Slot {slot['slot_number']}: {slot.get('subject', 'N/A')}"
                    )

    # Problem 3: Missing or incomplete metadata
    incomplete_metadata = []
    for doc in source_files:
        for slot in doc.get("slot_details", []):
            if "error" not in slot:
                missing = []
                if not slot.get("subject"):
                    missing.append("subject")
                if not slot.get("teacher"):
                    missing.append("teacher")
                if missing:
                    incomplete_metadata.append(
                        {
                            "file": doc["file_name"],
                            "slot": slot["slot_number"],
                            "missing": missing,
                        }
                    )

    if incomplete_metadata:
        print("\n3. Incomplete Metadata:")
        print("   Some slots are missing critical metadata fields.")
        for item in incomplete_metadata:
            print(
                f"   - {item['file']}, Slot {item['slot']}: Missing {', '.join(item['missing'])}"
            )

    # Problem 4: Document structure inconsistencies
    print("\n4. Document Structure Analysis:")
    table_counts = {}
    for doc in source_files:
        count = doc["total_tables"]
        if count not in table_counts:
            table_counts[count] = []
        table_counts[count].append(doc["file_name"])

    if len(table_counts) > 1:
        print("   WARNING: Documents have inconsistent table counts:")
        for count, files in sorted(table_counts.items()):
            slots = (count - 1) // 2 if count % 2 == 1 else count // 2
            print(f"     {count} tables ({slots} slots): {len(files)} file(s)")
            for f in files[:3]:  # Show first 3
                print(f"       - {f}")
            if len(files) > 3:
                print(f"       ... and {len(files) - 3} more")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total source documents: {len(source_files)}")
    print(f"Single-slot documents: {len(single_slot_files)}")
    print(f"Multi-slot documents: {len(multi_slot_files)}")
    print(f"Documents with incomplete metadata: {len(incomplete_metadata)}")

    # Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)

    if single_slot_files:
        print("\n1. For single-slot documents:")
        print(
            "   - User slot configuration can use any slot number (system will map to slot 1)"
        )
        print("   - Warnings about slot mismatches are informational only")
        print("   - Consider standardizing to slot 1 in user config for clarity")

    if multi_slot_files:
        print("\n2. For multi-slot documents:")
        print("   - User slot configuration MUST match document slot numbers")
        print(
            "   - Review each document's slot structure and update user config accordingly"
        )
        print(
            "   - Consider using subject-based detection (already implemented) as fallback"
        )

    if incomplete_metadata:
        print("\n3. For incomplete metadata:")
        print(
            "   - Review source documents and ensure all slots have complete metadata"
        )
        print("   - Subject and teacher fields are critical for proper slot detection")


if __name__ == "__main__":
    # Based on logs, Wilson's files are in:
    # F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W50
    base_path = r"F:\rodri\Documents\OneDrive\AS\Lesson Plan"

    print("=" * 60)
    print("WILSON RODRIGUES DOCUMENT ANALYSIS")
    print("=" * 60)
    print(f"\nBase path: {base_path}")

    base_path_obj = Path(base_path)
    if not base_path_obj.exists():
        print(f"\nERROR: Base path does not exist: {base_path}")
        print("\nTrying alternative paths...")

        # Try alternative
        alt_paths = [
            r"F:\rodri\Documents\OneDrive\AS\Wilson LP",
            r"F:\rodri\Documents\OneDrive\AS\Lesson Plan",
        ]

        for alt_path in alt_paths:
            if Path(alt_path).exists():
                base_path = alt_path
                base_path_obj = Path(alt_path)
                print(f"Found: {alt_path}")
                break

    if not base_path_obj.exists():
        print("\nCould not find base path. Please check the path manually.")
        sys.exit(1)

    # Find week folders
    print("\nSearching for week folders...")
    week_folders = []
    for item in base_path_obj.iterdir():
        if item.is_dir():
            name = item.name.lower()
            if any(keyword in name for keyword in ["w", "week", "25"]):
                week_folders.append(item)

    week_folders.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    if not week_folders:
        print("No week folders found")
        sys.exit(1)

    print(f"Found {len(week_folders)} week folder(s)")

    # Analyze most recent week folder
    recent_folder = week_folders[0]
    print(f"\nAnalyzing most recent: {recent_folder.name}")

    analysis = analyze_wilson_week_folder(str(recent_folder))

    if analysis:
        identify_common_problems(analysis)

        # Save results
        output_file = Path("logs/wilson_document_analysis.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, default=str)

        print(f"\n\nResults saved to: {output_file}")
