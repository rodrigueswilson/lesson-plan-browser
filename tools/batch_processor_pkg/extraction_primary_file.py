"""
Resolve primary teacher file for a slot (hybrid: explicit path, pattern, fallback).
"""

from pathlib import Path
from typing import Any, Dict, Optional

from backend.file_manager import get_file_manager
from backend.telemetry import logger


def _safe_get(d: Dict[str, Any], key: str, default=None):
    """Get value from dict; return default if value is ModelPrivateAttr."""
    val = d.get(key, default)
    if hasattr(val, "__class__") and "ModelPrivateAttr" in str(type(val)):
        return default
    return val


def resolve_primary_file(
    slot: Dict[str, Any],
    week_of: str,
    week_folder_path: Optional[str] = None,
    user_base_path: Optional[str] = None,
    get_file_manager_fn: Any = None,
) -> Optional[str]:
    """
    Resolve primary teacher file using hybrid approach.
    get_file_manager_fn: optional; if provided (e.g. from facade for test patching), use it instead of backend default.
    """
    _get_fm = get_file_manager_fn or get_file_manager
    if week_folder_path:
        week_folder = Path(week_folder_path)
    else:
        file_mgr = _get_fm(base_path=user_base_path)
        week_folder = file_mgr.get_week_folder(week_of)

    logger.debug(
        "primary_file_resolve_start",
        extra={
            "slot_number": slot.get("slot_number"),
            "week_folder": str(week_folder),
            "week_folder_exists": week_folder.exists(),
            "primary_teacher_file": slot.get("primary_teacher_file"),
            "primary_teacher_name": slot.get("primary_teacher_name"),
            "primary_teacher_file_pattern": slot.get("primary_teacher_file_pattern"),
        },
    )

    if slot.get("primary_teacher_file"):
        file_path = Path(slot["primary_teacher_file"])
        if file_path.is_absolute() and file_path.exists():
            logger.debug(
                "primary_file_resolve_absolute",
                extra={"slot_number": slot.get("slot_number"), "path": str(file_path)},
            )
            return str(file_path)
        if week_folder.exists():
            relative_path = week_folder / file_path.name
            if relative_path.exists():
                logger.debug(
                    "primary_file_resolve_relative",
                    extra={
                        "slot_number": slot.get("slot_number"),
                        "path": str(relative_path),
                    },
                )
                return str(relative_path)

    teacher_pattern = _safe_get(slot, "primary_teacher_file_pattern")
    primary_name = _safe_get(slot, "primary_teacher_name")
    first_name = _safe_get(slot, "primary_teacher_first_name", "")
    last_name = _safe_get(slot, "primary_teacher_last_name", "")

    if teacher_pattern:
        print(f"DEBUG: Using primary_teacher_file_pattern: '{teacher_pattern}'")
    elif primary_name:
        teacher_pattern = primary_name
        print(f"DEBUG: Using primary_teacher_name: '{teacher_pattern}'")
    elif first_name or last_name:
        teacher_pattern = f"{first_name} {last_name}".strip()
        print(f"DEBUG: Using first_name + last_name: '{teacher_pattern}'")
    else:
        teacher_pattern = None
        print("DEBUG: No teacher pattern available")

    if teacher_pattern and week_folder.exists():
        print(f"DEBUG: Searching for pattern '{teacher_pattern}' in week folder")
        logger.debug(
            "primary_file_resolve_pattern",
            extra={"slot_number": slot.get("slot_number"), "pattern": teacher_pattern},
        )
        if week_folder.exists():
            docx_files = list(week_folder.glob("*.docx"))
            file_names = [f.name for f in docx_files[:10]]
            print(f"DEBUG: Found {len(docx_files)} DOCX files in week folder: {file_names}")
            logger.debug(
                "primary_file_candidates",
                extra={
                    "slot_number": slot.get("slot_number"),
                    "candidate_count": len(docx_files),
                    "candidates": file_names,
                },
            )
        file_mgr = _get_fm(base_path=user_base_path)
        patterns_to_try = []
        if teacher_pattern:
            patterns_to_try.append(teacher_pattern)
        if last_name and last_name not in (patterns_to_try or []):
            patterns_to_try.append(last_name)
        if primary_name and primary_name not in patterns_to_try:
            patterns_to_try.append(primary_name)
        elif (first_name and last_name) and f"{first_name} {last_name}".strip() not in patterns_to_try:
            patterns_to_try.append(f"{first_name} {last_name}".strip())
        found = None
        for pattern in patterns_to_try:
            print(f"DEBUG: Trying pattern '{pattern}' for subject '{slot['subject']}'")
            found = file_mgr.find_primary_teacher_file(
                week_folder, pattern, slot["subject"]
            )
            if found:
                print(f"DEBUG: Found primary file using pattern '{pattern}': {found}")
                logger.debug(
                    "primary_file_resolve_pattern_success",
                    extra={
                        "slot_number": slot.get("slot_number"),
                        "pattern": pattern,
                        "path": found,
                    },
                )
                return found
        print(f"DEBUG: None of the patterns matched: {patterns_to_try}")
        all_files = list(week_folder.glob("*.docx"))
        skipped_files = [f.name for f in all_files if file_mgr._should_skip_file(f.name)]
        available_files = [
            f.name for f in all_files if not file_mgr._should_skip_file(f.name)
        ]
        print(f"DEBUG: Available files (not skipped): {available_files}")
        if skipped_files:
            print(f"DEBUG: Skipped files: {skipped_files}")
        logger.debug(
            "primary_file_resolve_pattern_failed",
            extra={
                "slot_number": slot.get("slot_number"),
                "patterns_tried": patterns_to_try,
                "available_files": available_files,
                "skipped_files": skipped_files,
            },
        )
    else:
        if not teacher_pattern:
            print(
                f"DEBUG: Slot {slot.get('slot_number')} has no teacher pattern or name configured"
            )
            logger.debug(
                "primary_file_no_pattern",
                extra={
                    "slot_number": slot.get("slot_number"),
                    "primary_teacher_file_pattern": slot.get(
                        "primary_teacher_file_pattern"
                    ),
                    "primary_teacher_name": slot.get("primary_teacher_name"),
                },
            )
        if not week_folder.exists():
            print(f"DEBUG: Week folder does not exist: {week_folder}")
            logger.debug(
                "primary_file_week_folder_missing",
                extra={
                    "slot_number": slot.get("slot_number"),
                    "week_folder": str(week_folder),
                },
            )

    if slot.get("primary_teacher_file"):
        fallback = Path("input") / Path(slot["primary_teacher_file"]).name
        if fallback.exists():
            logger.debug(
                "primary_file_resolve_fallback",
                extra={"slot_number": slot.get("slot_number"), "path": str(fallback)},
            )
            return str(fallback)

    print(f"DEBUG: PRIMARY FILE NOT FOUND for slot {slot.get('slot_number')}")
    logger.warning(
        "primary_file_not_found",
        extra={
            "slot_number": slot.get("slot_number"),
            "week_folder": str(week_folder),
            "week_folder_exists": week_folder.exists(),
            "primary_teacher_file": slot.get("primary_teacher_file"),
            "primary_teacher_file_pattern": slot.get("primary_teacher_file_pattern"),
            "primary_teacher_name": slot.get("primary_teacher_name"),
            "available_files": (
                [f.name for f in list(week_folder.glob("*.docx"))[:20]]
                if week_folder.exists()
                else []
            ),
        },
    )
    return None
