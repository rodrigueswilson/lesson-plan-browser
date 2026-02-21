"""Comprehensive analysis of Wilson Rodrigues' documents across multiple weeks."""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.diagnostics.analyze_slot_structures import analyze_week_folder


def analyze_multiple_weeks(base_path: str, week_names: list):
    """Analyze multiple week folders."""
    base_path_obj = Path(base_path)

    all_results = {}
    all_problems = []

    for week_name in week_names:
        week_folder = base_path_obj / week_name

        if not week_folder.exists():
            print(f"\nWeek folder not found: {week_name}")
            continue

        print(f"\n{'=' * 60}")
        print(f"ANALYZING: {week_name}")
        print("=" * 60)

        analysis = analyze_week_folder(week_folder)

        if "error" in analysis:
            print(f"ERROR: {analysis['error']}")
            continue

        # Filter source documents
        source_files = [
            d
            for d in analysis["documents"]
            if d.get("available_slots", 0) > 0
            and "error" not in d
            and not d["file_name"].startswith("Wilson")
        ]

        print(f"\nFound {len(source_files)} source documents:")

        for doc in source_files:
            print(f"\n  {doc['file_name']}")
            print(f"    Slots: {doc['available_slots']}")
            for slot in doc.get("slot_details", []):
                if "error" not in slot:
                    print(
                        f"      Slot {slot['slot_number']}: {slot.get('subject', 'N/A')} ({slot.get('teacher', 'N/A')})"
                    )

        all_results[week_name] = analysis

        # Identify problems
        problems = identify_problems_for_week(week_name, source_files)
        all_problems.extend(problems)

    return all_results, all_problems


def identify_problems_for_week(week_name: str, source_files: list):
    """Identify problems for a specific week."""
    problems = []

    # Group by teacher
    by_teacher = {}
    for doc in source_files:
        for slot in doc.get("slot_details", []):
            if "error" not in slot:
                teacher = slot.get("teacher", "Unknown").split("/")[0].strip()
                if teacher not in by_teacher:
                    by_teacher[teacher] = []
                by_teacher[teacher].append(
                    {
                        "file": doc["file_name"],
                        "slot": slot["slot_number"],
                        "subject": slot.get("subject", "N/A"),
                    }
                )

    # Problem: Multiple files for same teacher
    for teacher, slots in by_teacher.items():
        files = set(s["file"] for s in slots)
        if len(files) > 1:
            problems.append(
                {
                    "type": "multiple_files_same_teacher",
                    "week": week_name,
                    "teacher": teacher,
                    "files": list(files),
                    "description": f"Teacher {teacher} has content in {len(files)} different files",
                }
            )

    # Problem: Single-slot files
    single_slot_files = [d for d in source_files if d["available_slots"] == 1]
    if single_slot_files:
        problems.append(
            {
                "type": "single_slot_files",
                "week": week_name,
                "count": len(single_slot_files),
                "files": [d["file_name"] for d in single_slot_files],
                "description": f"{len(single_slot_files)} file(s) contain only 1 slot",
            }
        )

    # Problem: Inconsistent slot structures
    slot_counts = {}
    for doc in source_files:
        count = doc["available_slots"]
        if count not in slot_counts:
            slot_counts[count] = []
        slot_counts[count].append(doc["file_name"])

    if len(slot_counts) > 1:
        problems.append(
            {
                "type": "inconsistent_slot_structures",
                "week": week_name,
                "structures": {str(k): v for k, v in slot_counts.items()},
                "description": f"Documents have different slot counts: {list(slot_counts.keys())}",
            }
        )

    return problems


def generate_summary_report(all_results: dict, all_problems: list):
    """Generate a comprehensive summary report."""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE ANALYSIS SUMMARY")
    print("=" * 60)

    # Count documents by type
    total_docs = 0
    single_slot_count = 0
    multi_slot_count = 0

    all_teachers = set()
    all_subjects = set()

    for week_name, analysis in all_results.items():
        source_files = [
            d
            for d in analysis["documents"]
            if d.get("available_slots", 0) > 0
            and "error" not in d
            and not d["file_name"].startswith("Wilson")
        ]

        total_docs += len(source_files)

        for doc in source_files:
            if doc["available_slots"] == 1:
                single_slot_count += 1
            else:
                multi_slot_count += 1

            for slot in doc.get("slot_details", []):
                if "error" not in slot:
                    teacher = slot.get("teacher", "").split("/")[0].strip()
                    if teacher:
                        all_teachers.add(teacher)
                    subject = slot.get("subject", "")
                    if subject:
                        all_subjects.add(subject)

    print(f"\nTotal documents analyzed: {total_docs}")
    print(f"  Single-slot documents: {single_slot_count}")
    print(f"  Multi-slot documents: {multi_slot_count}")
    print(f"\nTeachers found: {len(all_teachers)}")
    for teacher in sorted(all_teachers):
        print(f"  - {teacher}")
    print(f"\nSubjects found: {len(all_subjects)}")
    for subject in sorted(all_subjects):
        print(f"  - {subject}")

    # Group problems by type
    print("\n" + "=" * 60)
    print("PROBLEMS IDENTIFIED")
    print("=" * 60)

    problems_by_type = {}
    for problem in all_problems:
        ptype = problem["type"]
        if ptype not in problems_by_type:
            problems_by_type[ptype] = []
        problems_by_type[ptype].append(problem)

    for ptype, problems in problems_by_type.items():
        print(f"\n{ptype.replace('_', ' ').title()}: {len(problems)} occurrence(s)")
        for problem in problems[:5]:  # Show first 5
            print(f"  - {problem['description']}")
            if "week" in problem:
                print(f"    Week: {problem['week']}")
        if len(problems) > 5:
            print(f"  ... and {len(problems) - 5} more")

    # Common patterns
    print("\n" + "=" * 60)
    print("COMMON PATTERNS")
    print("=" * 60)

    # Pattern 1: Single-slot files are common
    single_slot_problems = [p for p in all_problems if p["type"] == "single_slot_files"]
    if single_slot_problems:
        print("\n1. Single-Slot Files (Common Pattern):")
        print("   - Many teachers provide separate files for each subject")
        print("   - Each file contains only 1 slot")
        print("   - This is EXPECTED behavior, but user config must account for it")
        print("   - System correctly maps any slot number to slot 1 for these files")

    # Pattern 2: Multi-slot files
    if multi_slot_count > 0:
        print("\n2. Multi-Slot Files:")
        print("   - Some teachers provide consolidated files with multiple slots")
        print("   - User slot configuration MUST match document slot numbers")
        print("   - Subject-based detection helps, but slot numbers should align")

    # Pattern 3: Multiple files per teacher
    multi_file_problems = [
        p for p in all_problems if p["type"] == "multiple_files_same_teacher"
    ]
    if multi_file_problems:
        print("\n3. Multiple Files Per Teacher:")
        print("   - Some teachers have content split across multiple files")
        print("   - Each file may have different slot structures")
        print("   - User config needs to specify correct file pattern for each slot")

    # Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS FOR WILSON RODRIGUES")
    print("=" * 60)

    print("\n1. Slot Configuration:")
    print("   - Configure slots to match actual document structures")
    print("   - For single-slot files: any slot number works (system maps to slot 1)")
    print("   - For multi-slot files: slot numbers must match document structure")

    print("\n2. File Pattern Configuration:")
    print("   - Ensure primary_teacher_file_pattern matches actual filenames")
    print("   - Common patterns: 'Savoca', 'Davies', 'Lang'")

    print("\n3. Subject Matching:")
    print("   - System uses subject-based detection as fallback")
    print("   - Ensure subject names match exactly (case-insensitive)")
    print("   - Combined subjects like 'ELA/SS' are handled correctly")

    print("\n4. Base Path Configuration:")
    print("   - Set base_path_override in user settings")
    print("   - Path should point to: F:\\rodri\\Documents\\OneDrive\\AS\\Lesson Plan")

    return {
        "total_documents": total_docs,
        "single_slot_count": single_slot_count,
        "multi_slot_count": multi_slot_count,
        "teachers": sorted(all_teachers),
        "subjects": sorted(all_subjects),
        "problems": all_problems,
        "problems_by_type": {k: len(v) for k, v in problems_by_type.items()},
    }


if __name__ == "__main__":
    base_path = r"F:\rodri\Documents\OneDrive\AS\Lesson Plan"

    # Analyze multiple weeks
    week_names = ["25 W50", "25 W51"]

    print("=" * 60)
    print("WILSON RODRIGUES - COMPREHENSIVE DOCUMENT ANALYSIS")
    print("=" * 60)
    print(f"\nBase path: {base_path}")
    print(f"Analyzing weeks: {', '.join(week_names)}")

    all_results, all_problems = analyze_multiple_weeks(base_path, week_names)

    summary = generate_summary_report(all_results, all_problems)

    # Save results
    output_file = Path("logs/wilson_comprehensive_analysis.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    results = {"analysis": all_results, "problems": all_problems, "summary": summary}

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n\nResults saved to: {output_file}")
