"""
Resolve primary file and open DOCX parser for a slot.
Used by slot_flow.process_one_slot.
"""

import asyncio
import traceback
from pathlib import Path
from typing import Any, Optional


async def resolve_primary_file(
    processor: Any,
    slot: dict,
    week_of: str,
    week_folder_path: Optional[str],
    user_base_path: Optional[str],
    plan_id: Optional[str],
) -> Optional[str]:
    """Resolve primary teacher file for the slot. Returns path or None."""

    def _resolve():
        return processor._resolve_primary_file(
            slot, week_of, week_folder_path, user_base_path
        )

    if plan_id:

        def _resolve_with_tracking():
            try:
                with processor.tracker.track_operation(
                    plan_id,
                    "parse_resolve_file",
                    metadata={
                        "slot_number": slot.get("slot_number"),
                        "subject": slot["subject"],
                        "week_of": week_of,
                    },
                ):
                    return _resolve()
            except Exception as e:
                print(f"DEBUG: Error in _resolve_with_tracking: {e}")
                traceback.print_exc()
                raise

        primary_file = await asyncio.to_thread(_resolve_with_tracking)
    else:
        primary_file = await asyncio.to_thread(_resolve)
    return primary_file


def raise_no_primary_file_error(
    processor: Any,
    slot: dict,
    week_of: str,
    week_folder_path: Optional[str],
    user_base_path: Optional[str],
) -> None:
    """Build and raise ValueError when no primary file is found."""
    if week_folder_path:
        week_folder = Path(week_folder_path)
    else:
        file_mgr = processor.get_file_manager(base_path=user_base_path)
        week_folder = file_mgr.get_week_folder(week_of)

    teacher_pattern = (
        slot.get("primary_teacher_file_pattern")
        or slot.get("primary_teacher_name")
        or (
            f"{slot.get('primary_teacher_first_name', '')} {slot.get('primary_teacher_last_name', '')}".strip()
            if slot.get("primary_teacher_first_name")
            or slot.get("primary_teacher_last_name")
            else None
        )
    )

    error_msg = (
        f"No primary teacher file found for slot {slot['slot_number']} (subject: '{slot['subject']}').\n"
        f"Week folder: {week_folder} (exists: {week_folder.exists()})\n"
    )
    if not teacher_pattern:
        error_msg += (
            f"\nCONFIGURATION MISSING: Slot {slot['slot_number']} needs primary teacher information.\n"
            f"Please configure one of the following:\n"
            f"  - primary_teacher_file_pattern (e.g., 'Davies', 'Savoca')\n"
            f"  - primary_teacher_name\n"
            f"  - primary_teacher_first_name + primary_teacher_last_name\n"
        )
    else:
        error_msg += f"\nSearched for pattern: '{teacher_pattern}'\n"
        if week_folder.exists():
            docx_files = list(week_folder.glob("*.docx"))
            error_msg += f"Available files ({len(docx_files)} total):\n"
            for f in docx_files[:10]:
                error_msg += f"  - {f.name}\n"
            if len(docx_files) > 10:
                error_msg += f"  ... and {len(docx_files) - 10} more files\n"
            error_msg += (
                "\nTROUBLESHOOTING:\n"
                "1. Check if the teacher's name appears in any filename\n"
                "2. Verify the filename format matches the pattern\n"
                "3. Ensure files are in the correct week folder\n"
            )
        else:
            error_msg += "\nWeek folder does not exist. Please create it or check the path.\n"
    raise ValueError(error_msg)


async def open_parser_for_slot(
    processor: Any,
    primary_file: str,
    plan_id: Optional[str],
    slot_number: int,
    subject: str,
) -> Any:
    """Open DOCX and return parser. Raises on failure."""
    parser = await processor._open_docx_with_retry(
        primary_file,
        plan_id=plan_id,
        slot_number=slot_number,
        subject=subject,
    )
    return parser
