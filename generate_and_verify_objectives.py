"""Generate objectives DOCX and verify both sections fit on one page."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tools.diagnostics.analyze_objectives_layout import analyze_docx_layout
from backend.services.objectives_printer import ObjectivesPrinter
from backend.services.objectives_utils import normalize_objectives_in_lesson


def main():
    """Generate objectives DOCX and verify layout."""
    # Path to JSON file
    json_file = Path(
        r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W47\Wilson_Rodrigues_Weekly_W47_11-17-11-21_20251116_213107.json"
    )

    if not json_file.exists():
        print(f"ERROR: JSON file not found: {json_file}")
        return

    print("=" * 80)
    print("GENERATING OBJECTIVES DOCX")
    print("=" * 80)
    print(f"Loading lesson plan from: {json_file.name}\n")

    # Load JSON
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            lesson_json = json.load(f)
        normalize_objectives_in_lesson(lesson_json)
        print("[OK] Successfully loaded lesson JSON")
    except Exception as e:
        print(f"ERROR: Failed to load JSON file: {e}")
        return

    # Get metadata
    metadata = lesson_json.get("metadata", {})
    week_of = metadata.get("week_of", "11-17-11-21").replace("/", "-")

    user_name = metadata.get("teacher_name", "Wilson Rodrigues")
    if "/" in user_name:
        names = [n.strip() for n in user_name.split("/")]
        if "Wilson Rodrigues" in names:
            user_name = "Wilson Rodrigues"
        else:
            user_name = names[0]

    print(f"Week: {week_of}")
    print(f"User: {user_name}\n")

    # Generate output path with timestamp to avoid file locks
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = json_file.parent
    output_filename = (
        f"{user_name.replace(' ', '_')}_W47_{week_of}_objectives_{timestamp}.docx"
    )
    output_path = output_folder / output_filename

    print("Generating objectives DOCX with precise 75%/25% layout...")
    print("  - Student Goal: 75% of objectives area (top-aligned)")
    print("  - WIDA Objective: 25% of objectives area (bottom-aligned)")
    print()

    # Generate objectives DOCX
    printer = ObjectivesPrinter()

    try:
        result_path = printer.generate_docx(
            lesson_json, str(output_path), user_name=user_name, week_of=week_of
        )

        print("[OK] Objectives DOCX generated successfully!")
        print(f"File: {result_path}\n")

        # Copy to local for analysis
        local_path = Path("test_objectives_verified.docx")
        import shutil

        shutil.copy2(result_path, local_path)
        print(f"Copied to local: {local_path}\n")

        # Analyze the generated file
        print("=" * 80)
        print("VERIFYING LAYOUT")
        print("=" * 80)
        print()

        analyze_docx_layout(str(local_path))

        return result_path

    except Exception as e:
        print(f"ERROR: Failed to generate objectives DOCX: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
