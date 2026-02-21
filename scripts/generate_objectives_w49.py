#!/usr/bin/env python3
"""
Generate sentence frames PDF, HTML, and DOCX files for all lesson plans in week 50 (25 W50).

This script:
1. Queries the database for all weekly plans with week_of matching "12/8-12/12" (week 50)
2. For each plan, extracts the lesson_json
3. Generates sentence frames PDF, HTML, and DOCX files using the sentence frames generator
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import SQLiteDatabase
from backend.file_manager import get_file_manager
from backend.services.sentence_frames_pdf_generator import (
    generate_sentence_frames_docx,
    generate_sentence_frames_html,
    generate_sentence_frames_pdf,
)
from backend.telemetry import logger


def get_plans_for_week(db: SQLiteDatabase, week_of: str) -> List[Dict[str, Any]]:
    """Get all weekly plans matching the week_of string."""
    from sqlmodel import Session, select

    from backend.schema import WeeklyPlan

    # Query database directly to get all plans matching week_of
    matching_plans = []
    with Session(db.engine) as session:
        statement = select(WeeklyPlan).where(WeeklyPlan.week_of == week_of)
        plans = list(session.exec(statement).all())

        for plan in plans:
            # Parse lesson_json if it's a string
            lesson_json = plan.lesson_json
            if lesson_json and isinstance(lesson_json, str):
                try:
                    lesson_json = json.loads(lesson_json)
                except (json.JSONDecodeError, TypeError):
                    lesson_json = None

            matching_plans.append(
                {
                    "plan_id": plan.id,
                    "user_id": plan.user_id,
                    "week_of": plan.week_of,
                    "output_file": plan.output_file,
                    "week_folder_path": plan.week_folder_path,
                    "lesson_json": lesson_json,
                }
            )

    return matching_plans


def get_lesson_json_from_plan(plan_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get lesson_json from plan info (already extracted)."""
    return plan_info.get("lesson_json")


def generate_sentence_frames_for_plan(
    db: SQLiteDatabase,
    plan_info: Dict[str, Any],
    file_manager: Any,
) -> bool:
    """Generate sentence frames PDF, HTML, and DOCX for a single plan."""
    plan_id = plan_info["plan_id"]
    week_of = plan_info["week_of"]
    user_id = plan_info["user_id"]

    logger.info(
        "generating_sentence_frames_for_plan",
        extra={"plan_id": plan_id, "week_of": week_of, "user_id": user_id},
    )

    # Get lesson_json
    lesson_json = get_lesson_json_from_plan(plan_info)
    if not lesson_json:
        logger.error(
            "no_lesson_json_found_for_sentence_frames", extra={"plan_id": plan_id}
        )
        return False

    # Get user info for file naming
    user = db.get_user(user_id) if user_id else None
    user_name = user.name if user and hasattr(user, "name") else None

    # Determine output directory - FORCE week 50 folder
    # Week 50 folder: F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W50
    week_50_folder = Path(r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W50")

    # Check if the week 50 folder exists, if not try to create it or use file_manager
    if week_50_folder.exists():
        output_dir = week_50_folder
    else:
        # Try to use file_manager to get week folder for week 50
        try:
            # Try different week_of formats for week 50
            week_50_formats = ["12/8-12/12", "12-8-12-12", "12/08-12/12", "12-08-12-12"]
            output_dir = None
            for week_format in week_50_formats:
                try:
                    potential_dir = Path(file_manager.get_week_folder(week_format))
                    if potential_dir.exists():
                        output_dir = potential_dir
                        break
                except Exception:
                    continue

            if not output_dir:
                # Try to create the week 50 folder
                week_50_folder.mkdir(parents=True, exist_ok=True)
                output_dir = week_50_folder
        except Exception:
            # Fallback: try to create week 50 folder directly
            week_50_folder.mkdir(parents=True, exist_ok=True)
            output_dir = week_50_folder

    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    teacher_name = user_name or lesson_json.get("metadata", {}).get(
        "teacher_name", "Teacher"
    )
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Sanitize teacher name for filename
    import re

    teacher_slug = re.sub(r"[^A-Za-z0-9]+", "_", teacher_name).strip("_") or "Teacher"

    sentence_frames_filename = f"{teacher_slug}_SentenceFrames_W50_{timestamp}"
    sentence_frames_pdf_path = output_dir / f"{sentence_frames_filename}.pdf"
    sentence_frames_html_path = output_dir / f"{sentence_frames_filename}.html"
    sentence_frames_docx_path = output_dir / f"{sentence_frames_filename}.docx"

    try:
        # Generate sentence frames PDF (this also creates HTML)
        generate_sentence_frames_pdf(
            lesson_json,
            str(sentence_frames_pdf_path),
            user_name=user_name,
            keep_html=True,  # Keep HTML file
        )

        # Generate sentence frames HTML (if not already created)
        if not sentence_frames_html_path.exists():
            generate_sentence_frames_html(
                lesson_json,
                str(sentence_frames_html_path),
                user_name=user_name,
            )

        # Generate sentence frames DOCX using the proper generator
        docx_generated = False
        try:
            generate_sentence_frames_docx(
                lesson_json,
                str(sentence_frames_docx_path),
                user_name=user_name,
            )
            docx_generated = sentence_frames_docx_path.exists()

            if docx_generated:
                logger.info(
                    "sentence_frames_docx_generated",
                    extra={
                        "plan_id": plan_id,
                        "docx_path": str(sentence_frames_docx_path),
                    },
                )
        except Exception as docx_error:
            logger.warning(
                "sentence_frames_docx_generation_failed",
                extra={"plan_id": plan_id, "error": str(docx_error)},
            )
            docx_generated = False

        logger.info(
            "sentence_frames_generated_successfully",
            extra={
                "plan_id": plan_id,
                "pdf_path": str(sentence_frames_pdf_path),
                "html_path": str(sentence_frames_html_path),
                "docx_path": str(sentence_frames_docx_path) if docx_generated else None,
                "pdf_exists": sentence_frames_pdf_path.exists(),
                "html_exists": sentence_frames_html_path.exists(),
                "docx_exists": sentence_frames_docx_path.exists()
                if docx_generated
                else False,
            },
        )

        print(f"[OK] Generated sentence frames for plan {plan_id}")
        print(f"  PDF: {sentence_frames_pdf_path}")
        print(f"  HTML: {sentence_frames_html_path}")
        if docx_generated and sentence_frames_docx_path.exists():
            print(f"  DOCX: {sentence_frames_docx_path}")

        return True

    except Exception as e:
        logger.error(
            "sentence_frames_generation_failed",
            extra={"plan_id": plan_id, "error": str(e), "error_type": type(e).__name__},
            exc_info=True,
        )
        print(f"[FAILED] Failed to generate sentence frames for plan {plan_id}: {e}")
        return False


def find_plans_in_w50_folder(w50_folder_path: Path) -> List[Dict[str, str]]:
    """Find lesson plan files in the W50 folder and extract identifying information."""
    found_files = []

    if not w50_folder_path.exists():
        print(f"Warning: W50 folder does not exist: {w50_folder_path}")
        return found_files

    # Look for DOCX files (typical lesson plan format)
    for file_path in w50_folder_path.glob("*.docx"):
        # Try to extract teacher name and other info from filename
        filename = file_path.stem
        found_files.append(
            {
                "file_path": str(file_path),
                "filename": filename,
                "full_path": str(file_path.absolute()),
            }
        )

    return found_files


def match_files_with_database(
    files_in_folder: List[Dict[str, str]], db_plans: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Match files in W50 folder with database entries."""
    matched_plans = []
    matched_plan_ids = set()  # Track matched plan IDs to avoid duplicates

    for file_info in files_in_folder:
        file_path = file_info["file_path"]
        filename = file_info["filename"]
        file_path_obj = Path(file_path)

        # Try to match by output_file path
        for db_plan in db_plans:
            plan_id = db_plan.get("plan_id")
            if plan_id in matched_plan_ids:
                continue  # Skip if already matched

            output_file = db_plan.get("output_file", "")
            week_folder_path = db_plan.get("week_folder_path", "")

            # Check if the database plan's output_file matches
            if output_file:
                try:
                    output_path = Path(output_file)
                    if output_path.exists():
                        if str(output_path.absolute()) == file_info["full_path"]:
                            matched_plans.append(db_plan)
                            matched_plan_ids.add(plan_id)
                            print(f"  ✓ Matched: {filename} -> plan_id: {plan_id}")
                            break
                        # Also check if filename matches
                        if (
                            output_path.name == file_path_obj.name
                            or output_path.stem == filename
                        ):
                            matched_plans.append(db_plan)
                            matched_plan_ids.add(plan_id)
                            print(
                                f"  ✓ Matched by filename: {filename} -> plan_id: {plan_id}"
                            )
                            break
                except Exception:
                    pass

            # Check week_folder_path - if it points to W49 folder
            if week_folder_path:
                try:
                    week_path = Path(week_folder_path)
                    if week_path.exists() and str(week_path.absolute()) == str(
                        file_path_obj.parent.absolute()
                    ):
                        matched_plans.append(db_plan)
                        matched_plan_ids.add(plan_id)
                        print(
                            f"  ✓ Matched by folder: {filename} -> plan_id: {plan_id}"
                        )
                        break
                except Exception:
                    pass

    return matched_plans


def main():
    """Main function to generate sentence frames (PDF, HTML, DOCX) for week 50 plans in the W50 folder."""
    # Week 50 folder path
    w50_folder = Path(r"F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W50")

    print("Generating sentence frames (PDF, HTML, DOCX) for week 50 (25 W50)...")
    print("=" * 60)
    print(f"Target folder: {w50_folder}")
    print()

    # Initialize database
    db = SQLiteDatabase(use_ipc=False)
    file_manager = get_file_manager()

    # Step 1: Find all lesson plan files in the W50 folder
    print("Step 1: Scanning W50 folder for lesson plan files...")
    files_in_folder = find_plans_in_w50_folder(w50_folder)

    if not files_in_folder:
        print(f"❌ No lesson plan files found in {w49_folder}")
        print("Please ensure lesson plan DOCX files exist in the W49 folder")
        return

    print(f"Found {len(files_in_folder)} file(s) in W49 folder:")
    for f in files_in_folder:
        print(f"  - {f['filename']}")
    print()

    # Step 2: Query database for week 50 plans with lesson_json
    print("Step 2: Querying database for week 50 plans with lesson_json...")
    from sqlmodel import Session, select

    from backend.schema import WeeklyPlan

    # Week 50 date patterns (December 8-12, 2025)
    week_50_indicators = [
        "12/8",
        "12-8",
        "12/08",
        "12-08",
        "12/12",
        "12-12",
        "w50",
        "week 50",
        "week50",
    ]

    with Session(db.engine) as session:
        # Fetch all plans, then filter for week 50 in Python
        # (SQLite LIKE is case-insensitive for ASCII, but Python filtering is more reliable)
        statement = select(WeeklyPlan)
        all_plans_db = list(session.exec(statement).all())

        plans_with_json = []
        for plan in all_plans_db:
            lesson_json = plan.lesson_json
            if not lesson_json:
                continue

            if isinstance(lesson_json, str):
                try:
                    lesson_json = json.loads(lesson_json)
                except (json.JSONDecodeError, TypeError):
                    continue

            # Check if this is week 50: check both week_of field and lesson_json metadata
            week_of = (plan.week_of or "").lower()
            metadata = lesson_json.get("metadata", {})
            metadata_week = (metadata.get("week_of", "") or "").lower()

            # Verify it's actually week 50
            is_week_50 = any(indicator in week_of for indicator in week_50_indicators)
            if not is_week_50 and metadata_week:
                is_week_50 = any(
                    indicator in metadata_week for indicator in week_50_indicators
                )

            if not is_week_50:
                continue

            plans_with_json.append(
                {
                    "plan_id": plan.id,
                    "user_id": plan.user_id,
                    "week_of": plan.week_of,
                    "output_file": plan.output_file,
                    "week_folder_path": plan.week_folder_path,
                    "lesson_json": lesson_json,
                }
            )

    print(f"Found {len(plans_with_json)} week 50 plan(s) with lesson_json in database")
    print()

    # Step 3: Match files in folder with database entries
    print("Step 3: Matching files with database entries...")
    matched_plans = match_files_with_database(files_in_folder, plans_with_json)
    matched_plan_ids = {
        p.get("plan_id") for p in matched_plans
    }  # Track matched plan IDs

    if not matched_plans:
        print("❌ No matches found between W50 folder files and database entries")
        print("\nTrying alternative matching strategies...")
        print(f"W50 folder path: {w50_folder.absolute()}")
        print(f"W50 folder name: {w50_folder.name}")
        print()

        # Alternative 1: Check if week_folder_path points to W50 folder
        print("Strategy 1: Matching by week_folder_path...")
        w50_folder_str = str(w50_folder.absolute()).lower()
        w50_folder_name = w50_folder.name.lower()
        w50_folder_variants = [
            w50_folder_str,
            w50_folder_name,
            "25 w50",
            "w50",
            "week 50",
        ]

        for plan in plans_with_json:
            plan_id = plan.get("plan_id")
            if plan_id in matched_plan_ids:
                continue

            week_folder = plan.get("week_folder_path", "")
            if week_folder:
                try:
                    week_path = Path(week_folder)
                    week_path_str = str(week_path.absolute()).lower()
                    # Check if any W50 variant is in the week_folder_path
                    if any(variant in week_path_str for variant in w50_folder_variants):
                        matched_plans.append(plan)
                        matched_plan_ids.add(plan_id)
                        print(f"  ✓ Matched by week_folder_path: plan_id: {plan_id}")
                        print(f"    Folder: {week_folder}")
                        print(f"    Week: {plan.get('week_of', 'Unknown')}")
                except Exception:
                    # Try string matching if path doesn't exist
                    week_folder_lower = str(week_folder).lower()
                    if any(
                        variant in week_folder_lower for variant in w50_folder_variants
                    ):
                        matched_plans.append(plan)
                        matched_plan_ids.add(plan_id)
                        print(
                            f"  ✓ Matched by week_folder_path (string): plan_id: {plan_id}"
                        )
                        print(f"    Folder: {week_folder}")

        # Alternative 2: Match by week_of if it's week 50 (December dates)
        if not matched_plans:
            print("\nStrategy 2: Matching by week_of (December 8-12, 2025)...")

            for plan in plans_with_json:
                plan_id = plan.get("plan_id")
                if plan_id in matched_plan_ids:
                    continue

                week_of = plan.get("week_of", "").lower()
                if week_of:
                    # Check if it contains December 8-12 patterns
                    has_dec_8 = any(
                        p in week_of for p in ["12/8", "12-8", "12/08", "12-08"]
                    )
                    has_dec_12 = any(
                        p in week_of for p in ["12/12", "12-12"]
                    )

                    if has_dec_8 or has_dec_12:
                        # More lenient: if it has December dates, consider it a match
                        matched_plans.append(plan)
                        matched_plan_ids.add(plan_id)
                        print(
                            f"  ✓ Matched by week_of: plan_id: {plan_id}, week_of: {plan.get('week_of')}"
                        )

        # Alternative 3: Match by filename similarity (teacher name, dates)
        if not matched_plans:
            print("\nStrategy 3: Matching by filename similarity...")
            for file_info in files_in_folder:
                filename_lower = file_info["filename"].lower()
                print(f"  Checking file: {file_info['filename']}")

                for plan in plans_with_json:
                    plan_id = plan.get("plan_id")
                    if plan_id in matched_plan_ids:
                        continue

                    # Try to match by teacher name from lesson_json
                    lesson_json = plan.get("lesson_json", {})
                    metadata = lesson_json.get("metadata", {})
                    teacher_name = metadata.get("teacher_name", "").lower()

                    if teacher_name:
                        # Extract first and last name parts
                        teacher_parts = teacher_name.split()
                        if teacher_parts:
                            first_name = teacher_parts[0].lower()
                            last_name = (
                                teacher_parts[-1].lower()
                                if len(teacher_parts) > 1
                                else ""
                            )

                            # Check if teacher name appears in filename
                            if first_name in filename_lower or (
                                last_name and last_name in filename_lower
                            ):
                                matched_plans.append(plan)
                                matched_plan_ids.add(plan_id)
                                print(
                                    f"  ✓ Matched by teacher name: {file_info['filename']} -> plan_id: {plan_id}"
                                )
                                print(f"    Teacher: {teacher_name}")
                                break

                    # Try to match by output_file filename (even if path doesn't match)
                    output_file = plan.get("output_file", "")
                    if output_file:
                        try:
                            output_filename = Path(output_file).stem.lower()
                            # More flexible matching
                            if (
                                output_filename in filename_lower
                                or filename_lower in output_filename
                                or any(
                                    word in filename_lower
                                    for word in output_filename.split("_")
                                    if len(word) > 3
                                )
                            ):
                                matched_plans.append(plan)
                                matched_plan_ids.add(plan_id)
                                print(
                                    f"  ✓ Matched by filename similarity: {file_info['filename']} -> plan_id: {plan_id}"
                                )
                                print(f"    Output file: {Path(output_file).name}")
                                break
                        except Exception:
                            pass

                    # Try matching by "Wilson" or "Rodrigues" in filename
                    if "wilson" in filename_lower or "rodrigues" in filename_lower:
                        if teacher_name and (
                            "wilson" in teacher_name or "rodrigues" in teacher_name
                        ):
                            matched_plans.append(plan)
                            matched_plan_ids.add(plan_id)
                            print(
                                f"  ✓ Matched by name pattern: {file_info['filename']} -> plan_id: {plan_id}"
                            )
                            break

    if not matched_plans:
        print("\n❌ No matching plans found")
        print("Please ensure:")
        print("  1. Lesson plan files exist in the W49 folder")
        print("  2. Corresponding database entries exist with lesson_json")
        print(
            "  3. The output_file or week_folder_path in database matches the folder location"
        )
        return

    # Filter matched plans: must have sentence_frames AND be for week 50
    print(f"\n✓ Matched {len(matched_plans)} plan(s)")
    print("Filtering plans with sentence_frames for week 50...")

    # Week 50 date patterns (December 8-12, 2025)
    week_50_indicators = [
        "12/8",
        "12-8",
        "12/08",
        "12-08",
        "12/12",
        "12-12",
        "w50",
        "week 50",
    ]

    plans_with_frames = []
    for plan_info in matched_plans:
        lesson_json = plan_info.get("lesson_json", {})
        if not lesson_json:
            continue

        # First check: Must be week 50 (December dates)
        week_of = plan_info.get("week_of", "").lower()
        metadata_week = lesson_json.get("metadata", {}).get("week_of", "").lower()

        is_week_50 = False
        if week_of:
            is_week_50 = any(indicator in week_of for indicator in week_50_indicators)
        if not is_week_50 and metadata_week:
            is_week_50 = any(
                indicator in metadata_week for indicator in week_50_indicators
            )

        if not is_week_50:
            print(
                f"  ⚠ Skipping plan {plan_info['plan_id']} - not week 50 (week_of: {plan_info.get('week_of', 'Unknown')})"
            )
            continue

        # Second check: Must have sentence_frames
        has_frames = False
        days = lesson_json.get("days", {})
        for day_name in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            day_data = days.get(day_name, {})
            if not day_data:
                continue

            slots = day_data.get("slots", [])
            if isinstance(slots, list) and len(slots) > 0:
                for slot in slots:
                    slot_frames = slot.get("sentence_frames", [])
                    if (
                        slot_frames
                        and isinstance(slot_frames, list)
                        and len(slot_frames) > 0
                    ):
                        has_frames = True
                        break
            else:
                day_frames = day_data.get("sentence_frames", [])
                if day_frames and isinstance(day_frames, list) and len(day_frames) > 0:
                    has_frames = True
                    break

            if has_frames:
                break

        if has_frames:
            plans_with_frames.append(plan_info)
            print(f"  ✓ Plan {plan_info['plan_id']} - week 50 with sentence_frames")
        else:
            print(
                f"  ⚠ Skipping plan {plan_info['plan_id']} - week 50 but no sentence_frames found"
            )

    if not plans_with_frames:
        print("\n❌ No matched plans have sentence_frames data")
        print("Please ensure the lesson plans in the database contain sentence_frames")
        return

    print(
        f"✓ Found {len(plans_with_frames)} plan(s) with sentence_frames for processing"
    )
    print("=" * 60)

    # Step 4: Generate sentence frames for matched plans
    print("\nStep 4: Generating sentence frames files (PDF, HTML, DOCX)...")
    success_count = 0
    fail_count = 0

    for i, plan_info in enumerate(plans_with_frames, 1):
        print(
            f"\n[{i}/{len(plans_with_frames)}] Processing plan {plan_info['plan_id']}..."
        )
        print(f"  Week: {plan_info.get('week_of', 'Unknown')}")
        if plan_info.get("output_file"):
            print(f"  File: {Path(plan_info['output_file']).name}")
        if generate_sentence_frames_for_plan(db, plan_info, file_manager):
            success_count += 1
        else:
            fail_count += 1

    print("\n" + "=" * 60)
    print(f"Summary: {success_count} succeeded, {fail_count} failed")
    print(f"All files saved to: {w50_folder}")
    print("=" * 60)


if __name__ == "__main__":
    main()
