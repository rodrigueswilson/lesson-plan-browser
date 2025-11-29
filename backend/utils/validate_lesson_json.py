"""
Validation utilities for lesson_json structure.

This module provides functions to validate and check lesson_json for required
fields like vocabulary_cognates and sentence_frames.
"""
from typing import Any, Dict, List, Optional, Tuple


def validate_vocabulary_frames_in_lesson_json(
    lesson_json: Dict[str, Any],
    day: Optional[str] = None,
    slot_number: Optional[int] = None,
) -> Tuple[bool, List[str]]:
    """
    Validate that vocabulary_cognates and sentence_frames are present in lesson_json.
    
    Args:
        lesson_json: The lesson_json dictionary to validate
        day: Optional day name to check (e.g., "monday"). If None, checks all days.
        slot_number: Optional slot number to check. If None, checks all slots.
    
    Returns:
        Tuple of (is_valid, warnings) where:
        - is_valid: True if vocabulary/frames are found where expected
        - warnings: List of warning messages about missing or empty vocabulary/frames
    
    Expected structure:
        days[day]["slots"][slot]["vocabulary_cognates"] = [{"english": "...", ...}, ...]
        days[day]["slots"][slot]["sentence_frames"] = [{"english": "...", ...}, ...]
    
    Example:
        >>> lesson_json = {"days": {"monday": {"slots": [{"slot_number": 1, "vocabulary_cognates": []}]}}}
        >>> is_valid, warnings = validate_vocabulary_frames_in_lesson_json(lesson_json, "monday", 1)
        >>> warnings
        ["Monday slot 1 has empty vocabulary_cognates array"]
    """
    warnings: List[str] = []
    days = lesson_json.get("days", {})
    
    if not days:
        warnings.append("lesson_json has no 'days' key")
        return False, warnings
    
    # Determine which days/slots to check
    days_to_check = [day] if day else list(days.keys())
    
    for day_name in days_to_check:
        day_data = days.get(day_name, {})
        if not day_data:
            warnings.append(f"{day_name} has no data in lesson_json")
            continue
        
        slots = day_data.get("slots", [])
        if not slots:
            warnings.append(f"{day_name} has no slots")
            continue
        
        # Determine which slots to check
        slots_to_check = (
            [slot_number] if slot_number is not None else range(1, len(slots) + 1)
        )
        
        for slot_num in slots_to_check:
            slot = next(
                (s for s in slots if s.get("slot_number") == slot_num), None
            )
            if not slot:
                continue
            
            # Check vocabulary_cognates
            vocab = slot.get("vocabulary_cognates")
            if vocab is None:
                warnings.append(
                    f"{day_name} slot {slot_num} missing 'vocabulary_cognates' key "
                    "(vocabulary step will not be created)"
                )
            elif isinstance(vocab, list) and len(vocab) == 0:
                warnings.append(
                    f"{day_name} slot {slot_num} has empty 'vocabulary_cognates' array "
                    "(vocabulary step will not be created)"
                )
            
            # Check sentence_frames
            frames = slot.get("sentence_frames")
            if frames is None:
                warnings.append(
                    f"{day_name} slot {slot_num} missing 'sentence_frames' key "
                    "(sentence frames step will not be created)"
                )
            elif isinstance(frames, list) and len(frames) == 0:
                warnings.append(
                    f"{day_name} slot {slot_num} has empty 'sentence_frames' array "
                    "(sentence frames step will not be created)"
                )
    
    # If we found warnings for specific day/slot, consider it invalid
    is_valid = len(warnings) == 0
    
    return is_valid, warnings


def log_vocabulary_frames_warnings(
    lesson_json: Dict[str, Any],
    plan_id: str,
    logger,
    day: Optional[str] = None,
    slot_number: Optional[int] = None,
) -> None:
    """
    Log warnings about missing vocabulary/frames in lesson_json.
    
    This is a convenience function that calls validate_vocabulary_frames_in_lesson_json
    and logs any warnings using the provided logger.
    
    Args:
        lesson_json: The lesson_json dictionary to validate
        plan_id: Plan ID for logging context
        logger: Logger instance to use for logging warnings
        day: Optional day name to check (e.g., "monday")
        slot_number: Optional slot number to check
    """
    is_valid, warnings = validate_vocabulary_frames_in_lesson_json(
        lesson_json, day=day, slot_number=slot_number
    )
    
    if not is_valid:
        logger.warning(
            "lesson_json_vocabulary_frames_validation",
            extra={
                "plan_id": plan_id,
                "day": day,
                "slot_number": slot_number,
                "warnings": warnings,
                "message": (
                    "lesson_json is missing vocabulary_cognates or sentence_frames. "
                    "Vocabulary/frames steps will not be created. "
                    "If this plan should have vocabulary/frames, check the source JSON "
                    "or use update_plan_supabase.py to fix the plan's lesson_json."
                ),
            },
        )
        
        # Also log individual warnings
        for warning in warnings:
            logger.warning(
                "lesson_json_validation_warning",
                extra={"plan_id": plan_id, "warning": warning},
            )

