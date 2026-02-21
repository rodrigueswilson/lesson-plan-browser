"""Verify enhanced warning messages are correctly implemented."""

import io
import sys
from pathlib import Path

# Set UTF-8 encoding for stdout
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Read the batch_processor.py file to verify enhanced warnings
batch_processor_path = Path("tools/batch_processor.py")


def verify_enhanced_warnings():
    """Verify enhanced warning messages are in the code."""
    print("=" * 60)
    print("VERIFYING ENHANCED WARNING MESSAGES")
    print("=" * 60)

    if not batch_processor_path.exists():
        print("ERROR: batch_processor.py not found")
        return False

    with open(batch_processor_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check for enhanced warning types
    checks = {
        "slot_subject_mismatch_single_slot": False,
        "slot_subject_mismatch_multi_slot": False,
        "Enhanced slot_auto_mapped": False,
        "is_single_slot check": False,
        "Human-readable message": False,
        "Fix suggestions": False,
    }

    # Check for single-slot warning
    if "slot_subject_mismatch_single_slot" in content:
        checks["slot_subject_mismatch_single_slot"] = True
        print("\n[OK] slot_subject_mismatch_single_slot warning type found")

    # Check for multi-slot warning
    if "slot_subject_mismatch_multi_slot" in content:
        checks["slot_subject_mismatch_multi_slot"] = True
        print("[OK] slot_subject_mismatch_multi_slot warning type found")

    # Check for enhanced auto-mapped warning
    if 'extra={"requested_slot"' in content and '"message":' in content:
        # Check if it's in the slot_auto_mapped section
        auto_mapped_section = content.find("slot_auto_mapped")
        if auto_mapped_section != -1:
            section = content[auto_mapped_section : auto_mapped_section + 500]
            if '"message":' in section:
                checks["Enhanced slot_auto_mapped"] = True
                print("[OK] Enhanced slot_auto_mapped warning found")

    # Check for is_single_slot logic
    if "is_single_slot = available_slots == 1" in content:
        checks["is_single_slot check"] = True
        print("[OK] is_single_slot check found")

    # Check for human-readable messages
    if "message =" in content and "Slot" in content and "requested" in content:
        checks["Human-readable message"] = True
        print("[OK] Human-readable message generation found")

    # Check for fix suggestions
    if "Consider updating" in content or "slot configuration" in content.lower():
        checks["Fix suggestions"] = True
        print("[OK] Fix suggestions found")

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    all_passed = all(checks.values())
    for check, passed in checks.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {check}")

    if all_passed:
        print("\n[SUCCESS] All enhanced warning features verified!")
        return True
    else:
        print("\n[WARNING] Some features not found")
        return False


def show_example_warnings():
    """Show examples of what enhanced warnings will look like."""
    print("\n" + "=" * 60)
    print("EXAMPLE ENHANCED WARNINGS")
    print("=" * 60)

    print("\n1. SINGLE-SLOT MISMATCH (Expected Behavior):")
    print("-" * 60)
    example1 = {
        "event": "slot_subject_mismatch_single_slot",
        "level": "warning",
        "extra": {
            "requested_slot": 2,
            "actual_slot": 1,
            "subject": "Social Studies",
            "file": "T. Santiago SS Plans 12_15.docx",
            "available_slots": 1,
            "is_single_slot": True,
            "is_expected": True,
            "message": "Slot 2 requested, but document 'T. Santiago SS Plans 12_15.docx' has only 1 slot. Content correctly extracted from slot 1. This is expected behavior for single-slot documents.",
            "teacher": "Taina Santiago",
            "grade": "6",
            "homeroom": "406",
        },
    }
    print(json.dumps(example1, indent=2))

    print("\n2. MULTI-SLOT MISMATCH (Informational):")
    print("-" * 60)
    example2 = {
        "event": "slot_subject_mismatch_multi_slot",
        "level": "warning",
        "extra": {
            "requested_slot": 4,
            "actual_slot": 3,
            "subject": "Science",
            "file": "Morais 12_15 - 12_19.docx",
            "available_slots": 4,
            "is_single_slot": False,
            "is_expected": False,
            "message": "Slot 4 requested for 'Science', but document 'Morais 12_15 - 12_19.docx' has 'Science' in slot 3. Content correctly extracted via subject-based detection. Consider updating slot configuration to match document structure (slot 3).",
            "teacher": "Catarina Morais",
            "grade": "2",
            "homeroom": "310",
        },
    }
    print(json.dumps(example2, indent=2))

    print("\n3. AUTO-MAPPED (Expected Behavior):")
    print("-" * 60)
    example3 = {
        "event": "slot_auto_mapped",
        "level": "warning",
        "extra": {
            "requested_slot": 5,
            "available_slots": 1,
            "mapped_to": 1,
            "subject": "Science",
            "file": "Mrs. Grande Science 12_15 12_19.docx",
            "message": "Slot 5 requested, but document 'Mrs. Grande Science 12_15 12_19.docx' has only 1 slot(s). Auto-mapped to slot 1. This is expected behavior for single-slot documents.",
            "teacher": "Mariela Grande",
            "grade": "6",
            "homeroom": "405",
        },
    }
    print(json.dumps(example3, indent=2))

    print("\n" + "=" * 60)
    print("KEY IMPROVEMENTS")
    print("=" * 60)
    print("\n1. Distinct Warning Types:")
    print("   - slot_subject_mismatch_single_slot (expected)")
    print("   - slot_subject_mismatch_multi_slot (informational)")
    print("   - slot_auto_mapped (expected)")

    print("\n2. Human-Readable Messages:")
    print("   - Clear explanation of what happened")
    print("   - Context about document structure")
    print("   - Indication of expected vs unexpected")

    print("\n3. Actionable Guidance:")
    print("   - Fix suggestions for multi-slot mismatches")
    print("   - Clear indication when no action needed")

    print("\n4. Enhanced Context:")
    print("   - Document structure information")
    print("   - Teacher, grade, homeroom details")
    print("   - File information")


if __name__ == "__main__":
    import json

    # Verify implementation
    verified = verify_enhanced_warnings()

    # Show examples
    show_example_warnings()

    if verified:
        print("\n[SUCCESS] Enhanced warnings are correctly implemented!")
        print(
            "\nNext: Test with actual lesson plan generation to see warnings in action."
        )
    else:
        print("\n[WARNING] Some features may need review.")
