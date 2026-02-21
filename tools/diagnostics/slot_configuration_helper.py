"""Slot Configuration Helper Tool

Analyzes documents and suggests slot configurations for users.
Can validate existing configurations and generate new ones.
"""

import io
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Set UTF-8 encoding for stdout
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.supabase_database import SupabaseDatabase
from tools.diagnostics.analyze_slot_structures import analyze_week_folder


class SlotConfigurationHelper:
    """Helper class for slot configuration analysis and suggestions."""

    def __init__(self, db: Optional[SupabaseDatabase] = None):
        """Initialize helper with database connection."""
        self.db = db or SupabaseDatabase()

    def analyze_week_folder(self, week_folder_path: str) -> Dict[str, Any]:
        """Analyze documents in a week folder and extract slot structures."""
        folder = Path(week_folder_path)
        if not folder.exists():
            return {"error": f"Week folder does not exist: {week_folder_path}"}

        analysis = analyze_week_folder(folder)
        if "error" in analysis:
            return analysis

        # Filter source documents
        source_files = [
            d
            for d in analysis["documents"]
            if d.get("available_slots", 0) > 0
            and "error" not in d
            and not any(
                d["file_name"].startswith(prefix)
                for prefix in ["Wilson", "Daniela", "Weekly"]
            )  # Exclude output files
        ]

        return {
            "week_folder": week_folder_path,
            "source_files": source_files,
            "total_files": len(source_files),
        }

    def suggest_slot_configuration(
        self, week_folder_path: str, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Suggest slot configuration based on document analysis."""
        analysis = self.analyze_week_folder(week_folder_path)
        if "error" in analysis:
            return analysis

        source_files = analysis["source_files"]
        suggestions = []

        # Group by teacher
        by_teacher = {}
        for doc in source_files:
            for slot in doc.get("slot_details", []):
                if "error" in slot:
                    continue

                teacher = slot.get("teacher", "Unknown").split("/")[0].strip()
                if teacher not in by_teacher:
                    by_teacher[teacher] = {
                        "teacher": teacher,
                        "file": doc["file_name"],
                        "slots": [],
                        "is_single_slot": doc["available_slots"] == 1,
                    }

                by_teacher[teacher]["slots"].append(
                    {
                        "slot_number": slot["slot_number"],
                        "subject": slot.get("subject", "N/A"),
                        "grade": slot.get("grade", ""),
                        "homeroom": slot.get("homeroom", ""),
                    }
                )

        # Generate suggestions
        slot_counter = 1
        for teacher, info in sorted(by_teacher.items()):
            # Extract file pattern from filename
            file_pattern = self._extract_file_pattern(info["file"], teacher)

            if info["is_single_slot"]:
                # Single-slot document - suggest one slot
                slot = info["slots"][0]
                suggestions.append(
                    {
                        "slot_number": slot_counter,
                        "subject": slot["subject"],
                        "grade": slot["grade"],
                        "homeroom": slot["homeroom"],
                        "primary_teacher_name": teacher,
                        "primary_teacher_file_pattern": file_pattern,
                        "document_slot": slot["slot_number"],
                        "is_single_slot": True,
                        "file": info["file"],
                    }
                )
                slot_counter += 1
            else:
                # Multi-slot document - suggest slots matching document structure
                for slot in sorted(info["slots"], key=lambda x: x["slot_number"]):
                    suggestions.append(
                        {
                            "slot_number": slot_counter,
                            "subject": slot["subject"],
                            "grade": slot["grade"],
                            "homeroom": slot["homeroom"],
                            "primary_teacher_name": teacher,
                            "primary_teacher_file_pattern": file_pattern,
                            "document_slot": slot["slot_number"],
                            "is_single_slot": False,
                            "file": info["file"],
                        }
                    )
                    slot_counter += 1

        return {
            "suggestions": suggestions,
            "total_slots": len(suggestions),
            "teachers": list(by_teacher.keys()),
            "analysis": analysis,
        }

    def _extract_file_pattern(self, filename: str, teacher_name: str) -> str:
        """Extract file pattern from filename and teacher name."""
        # Try last name first
        last_name = teacher_name.split()[-1] if teacher_name else ""
        if last_name and last_name.lower() in filename.lower():
            return last_name

        # Try first name
        first_name = teacher_name.split()[0] if teacher_name else ""
        if first_name and first_name.lower() in filename.lower():
            return first_name

        # Try common patterns
        filename_lower = filename.lower()
        if "savoca" in filename_lower:
            return "Savoca"
        if "davies" in filename_lower:
            return "Davies"
        if "lang" in filename_lower:
            return "Lang"
        if "morais" in filename_lower:
            return "Morais"
        if "santiago" in filename_lower:
            return "Santiago"
        if "grande" in filename_lower:
            return "Grande"

        # Fallback to last name
        return last_name or teacher_name

    def validate_configuration(
        self, user_id: str, week_folder_path: str
    ) -> Dict[str, Any]:
        """Validate existing slot configuration against documents."""
        # Get user slots
        slots = self.db.get_user_slots(user_id)
        if not slots:
            return {"error": "No slots configured for user"}

        # Analyze documents
        analysis = self.analyze_week_folder(week_folder_path)
        if "error" in analysis:
            return analysis

        source_files = analysis["source_files"]

        # Compare
        results = {
            "total_slots": len(slots),
            "matches": [],
            "mismatches": [],
            "not_found": [],
            "single_slot_mappings": [],
        }

        for slot in sorted(slots, key=lambda x: x.slot_number):
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
                results["not_found"].append(
                    {
                        "slot": slot.slot_number,
                        "subject": slot.subject,
                        "teacher": teacher_pattern,
                    }
                )
                continue

            # Find actual slot in document
            actual_slot = None
            for slot_detail in matching_doc.get("slot_details", []):
                if "error" in slot_detail:
                    continue

                slot_subject = slot_detail.get("subject", "").lower()
                req_subject = slot.subject.lower() if slot.subject else ""

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

            if actual_slot:
                is_single_slot = matching_doc["available_slots"] == 1
                if actual_slot == slot.slot_number:
                    results["matches"].append(
                        {
                            "slot": slot.slot_number,
                            "subject": slot.subject,
                            "teacher": teacher_pattern,
                            "file": matching_doc["file_name"],
                        }
                    )
                elif is_single_slot:
                    results["single_slot_mappings"].append(
                        {
                            "slot": slot.slot_number,
                            "subject": slot.subject,
                            "teacher": teacher_pattern,
                            "file": matching_doc["file_name"],
                            "document_slot": 1,
                        }
                    )
                else:
                    results["mismatches"].append(
                        {
                            "slot": slot.slot_number,
                            "subject": slot.subject,
                            "teacher": teacher_pattern,
                            "file": matching_doc["file_name"],
                            "requested_slot": slot.slot_number,
                            "actual_slot": actual_slot,
                        }
                    )
            else:
                results["not_found"].append(
                    {
                        "slot": slot.slot_number,
                        "subject": slot.subject,
                        "teacher": teacher_pattern,
                        "file": matching_doc["file_name"],
                    }
                )

        return results

    def generate_configuration_json(
        self, week_folder_path: str, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate slot configuration JSON ready for database insertion."""
        suggestions = self.suggest_slot_configuration(week_folder_path, user_id)
        if "error" in suggestions:
            return []

        config = []
        for suggestion in suggestions["suggestions"]:
            config.append(
                {
                    "slot_number": suggestion["slot_number"],
                    "subject": suggestion["subject"],
                    "grade": suggestion["grade"],
                    "homeroom": suggestion["homeroom"] or None,
                    "primary_teacher_name": suggestion["primary_teacher_name"],
                    "primary_teacher_file_pattern": suggestion[
                        "primary_teacher_file_pattern"
                    ],
                    "plan_group_label": f"{suggestion['primary_teacher_name']} {suggestion['grade']}"
                    if suggestion["grade"]
                    else suggestion["primary_teacher_name"],
                }
            )

        return config


def print_suggestions(suggestions: Dict[str, Any]):
    """Print formatted suggestions."""
    if "error" in suggestions:
        print(f"ERROR: {suggestions['error']}")
        return

    print("\n" + "=" * 60)
    print("SLOT CONFIGURATION SUGGESTIONS")
    print("=" * 60)
    print(f"\nTotal slots suggested: {suggestions['total_slots']}")
    print(f"Teachers found: {len(suggestions['teachers'])}")
    for teacher in suggestions["teachers"]:
        print(f"  - {teacher}")

    print("\nSuggested Configuration:")
    print("-" * 60)
    for slot in suggestions["suggestions"]:
        slot_type = "Single-slot" if slot["is_single_slot"] else "Multi-slot"
        print(f"\nSlot {slot['slot_number']}: {slot['subject']}")
        print(f"  Teacher: {slot['primary_teacher_name']}")
        print(f"  File Pattern: {slot['primary_teacher_file_pattern']}")
        print(f"  Grade: {slot['grade']}, Homeroom: {slot['homeroom']}")
        print(f"  Document: {slot['file']}")
        print(f"  Type: {slot_type} (document slot {slot['document_slot']})")


def print_validation(results: Dict[str, Any]):
    """Print formatted validation results."""
    if "error" in results:
        print(f"ERROR: {results['error']}")
        return

    print("\n" + "=" * 60)
    print("CONFIGURATION VALIDATION RESULTS")
    print("=" * 60)

    print(f"\nTotal slots: {results['total_slots']}")
    print(f"Perfect matches: {len(results['matches'])}")
    print(f"Single-slot mappings (expected): {len(results['single_slot_mappings'])}")
    print(f"Multi-slot mismatches: {len(results['mismatches'])}")
    print(f"Not found: {len(results['not_found'])}")

    if results["matches"]:
        print("\n[MATCHES]")
        for match in results["matches"]:
            print(
                f"  Slot {match['slot']}: {match['subject']} ({match['teacher']}) - {match['file']}"
            )

    if results["single_slot_mappings"]:
        print("\n[SINGLE-SLOT MAPPINGS] (Expected Behavior)")
        for mapping in results["single_slot_mappings"]:
            print(
                f"  Slot {mapping['slot']}: {mapping['subject']} ({mapping['teacher']}) - {mapping['file']}"
            )

    if results["mismatches"]:
        print("\n[MISMATCHES] (Informational)")
        for mismatch in results["mismatches"]:
            print(
                f"  Slot {mismatch['slot']}: {mismatch['subject']} ({mismatch['teacher']})"
            )
            print(f"    Requested: Slot {mismatch['requested_slot']}")
            print(f"    Document: Slot {mismatch['actual_slot']} in {mismatch['file']}")
            print(
                f"    Suggestion: Update slot {mismatch['slot']} to slot {mismatch['actual_slot']}"
            )

    if results["not_found"]:
        print("\n[NOT FOUND]")
        for item in results["not_found"]:
            print(
                f"  Slot {item['slot']}: {item['subject']} ({item['teacher']}) - No matching document"
            )


def main():
    """Main CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Slot Configuration Helper Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Suggest configuration for a week folder
  python slot_configuration_helper.py suggest --week "F:\\path\\to\\week\\folder"

  # Validate existing configuration
  python slot_configuration_helper.py validate --user-id <id> --week "F:\\path\\to\\week\\folder"

  # Generate configuration JSON
  python slot_configuration_helper.py generate --week "F:\\path\\to\\week\\folder" --output config.json
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Suggest command
    suggest_parser = subparsers.add_parser("suggest", help="Suggest slot configuration")
    suggest_parser.add_argument(
        "--week", required=True, help="Path to week folder to analyze"
    )
    suggest_parser.add_argument("--user-id", help="User ID (optional, for context)")

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate existing configuration"
    )
    validate_parser.add_argument("--user-id", required=True, help="User ID to validate")
    validate_parser.add_argument(
        "--week", required=True, help="Path to week folder to analyze"
    )

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate", help="Generate configuration JSON"
    )
    generate_parser.add_argument(
        "--week", required=True, help="Path to week folder to analyze"
    )
    generate_parser.add_argument(
        "--output", help="Output JSON file path (default: stdout)"
    )
    generate_parser.add_argument("--user-id", help="User ID (optional, for context)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    helper = SlotConfigurationHelper()

    if args.command == "suggest":
        suggestions = helper.suggest_slot_configuration(args.week, args.user_id)
        print_suggestions(suggestions)

    elif args.command == "validate":
        results = helper.validate_configuration(args.user_id, args.week)
        print_validation(results)

    elif args.command == "generate":
        config = helper.generate_configuration_json(args.week, args.user_id)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            print(f"\nConfiguration saved to: {args.output}")
        else:
            print(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()
