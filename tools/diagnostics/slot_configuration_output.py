"""Format and print slot configuration suggestions and validation results."""

from typing import Any, Dict


def print_suggestions(suggestions: Dict[str, Any]) -> None:
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


def print_validation(results: Dict[str, Any]) -> None:
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
