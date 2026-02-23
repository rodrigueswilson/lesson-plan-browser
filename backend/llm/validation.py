"""
Retry and validation logic for LLM responses.
Parse validation errors, pre-validate JSON, analyze JSON errors, validate structure.
"""

import json
from typing import Any, Dict, List, Optional, Tuple

from backend.llm.error_analysis import (
    analyze_characters_around_error,
    detect_error_type,
    detect_truncation,
    extract_problematic_snippet,
    find_complete_days_before_error,
    identify_day_at_position,
    identify_field_at_position,
)
from backend.llm.json_pre_validation import pre_validate_json
from backend.llm.validation_error_parser import parse_validation_errors
from backend.telemetry import logger
from tools.json_repair import repair_json


def analyze_json_error(
    json_string: str, error: json.JSONDecodeError
) -> Dict[str, Any]:
    """
    Analyze JSON parsing error to extract comprehensive context.
    Returns structured error information for logging and retry prompts.
    """
    error_pos = getattr(error, "pos", len(json_string))
    error_line = getattr(error, "lineno", None)
    error_col = getattr(error, "colno", None)

    context_before = json_string[max(0, error_pos - 500) : error_pos]
    context_after = json_string[error_pos : min(len(json_string), error_pos + 500)]

    day_being_generated = identify_day_at_position(json_string, error_pos)
    field_being_generated = identify_field_at_position(json_string, error_pos)
    error_type = detect_error_type(error, json_string, error_pos)
    char_analysis = analyze_characters_around_error(json_string, error_pos)
    complete_days = find_complete_days_before_error(json_string, error_pos)

    return {
        "error_type": error_type,
        "error_position": error_pos,
        "error_position_percent": round((error_pos / len(json_string)) * 100, 2)
        if len(json_string) > 0
        else 0,
        "error_line": error_line,
        "error_column": error_col,
        "context_before": context_before,
        "context_after": context_after,
        "problematic_snippet": extract_problematic_snippet(json_string, error_pos),
        "day_being_generated": day_being_generated,
        "field_being_generated": field_being_generated,
        "response_length": len(json_string),
        "was_truncated": detect_truncation(json_string),
        "complete_days_before_error": complete_days,
        "character_analysis": char_analysis,
    }


def parse_llm_response(response_text: str) -> Dict[str, Any]:
    """
    Parse LLM response text to JSON. Strips markdown fences, pre-validates,
    and on JSONDecodeError attempts repair using error analysis.
    """
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    is_valid, pre_validation_error, pre_validation_fixes = pre_validate_json(cleaned)
    if (
        not is_valid
        and pre_validation_fixes
        and pre_validation_fixes.get("fixed_string")
    ):
        cleaned = pre_validation_fixes["fixed_string"]
        logger.info(
            "json_pre_validation_fixes_applied",
            extra={
                "pre_validation_error": pre_validation_error,
                "fixes_applied": pre_validation_fixes.get("fix_attempts", []),
            },
        )

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        original_error = str(e)
        error_analysis = analyze_json_error(cleaned, e)
        logger.warning(
            "json_parse_error_attempting_repair",
            extra={
                "error": original_error,
                "response_preview": cleaned[:500],
                "response_length": len(cleaned),
                "error_position": getattr(e, "pos", None),
                "error_type": error_analysis.get("error_type"),
                "error_position_percent": error_analysis.get("error_position_percent"),
                "day_being_generated": error_analysis.get("day_being_generated"),
                "field_being_generated": error_analysis.get("field_being_generated"),
                "complete_days_before_error": error_analysis.get(
                    "complete_days_before_error"
                ),
                "was_truncated": error_analysis.get("was_truncated"),
                "problematic_snippet": error_analysis.get("problematic_snippet"),
                "character_analysis": error_analysis.get("character_analysis"),
            },
        )
        error_pos = error_analysis.get("error_position")
        success, repaired, repair_error = repair_json(cleaned, error_pos, error_analysis)
        if success and repaired:
            logger.info(
                "json_repair_successful",
                extra={
                    "repair_message": repair_error,
                    "original_length": len(cleaned),
                    "repaired_length": len(repaired) if repaired else 0,
                },
            )
            try:
                parsed = json.loads(repaired)
                logger.info(
                    "json_repair_parse_success",
                    extra={
                        "salvaged_days": list(parsed.get("days", {}).keys())
                        if isinstance(parsed, dict)
                        else [],
                    },
                )
                return parsed
            except json.JSONDecodeError as e2:
                logger.error(
                    "json_repair_failed_to_parse",
                    extra={
                        "repair_error": str(e2),
                        "original_error": original_error,
                        "repaired_preview": repaired[:500] if repaired else None,
                    },
                )
        logger.error(
            "json_parse_error_repair_failed",
            extra={
                "original_error": original_error,
                "repair_error": repair_error,
                "response_preview": cleaned[:500],
                "response_length": len(cleaned),
                "error_analysis": error_analysis,
            },
        )
        error_with_analysis = ValueError(f"Failed to parse JSON: {original_error}")
        error_with_analysis.error_analysis = error_analysis  # type: ignore[attr-defined]
        raise error_with_analysis


def validate_structure(
    lesson_json: Dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    """
    Validate JSON structure matches schema. Fills missing days with placeholders.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if "metadata" not in lesson_json or "days" not in lesson_json:
        error_msg = "Missing root keys: 'metadata' or 'days'"
        logger.error("schema_validation_failed", extra={"reason": error_msg})
        return False, error_msg

    metadata = lesson_json["metadata"]
    required_metadata = ["week_of", "grade", "subject"]
    for field in required_metadata:
        if field not in metadata:
            error_msg = f"Missing metadata.{field}"
            logger.error("schema_validation_failed", extra={"reason": error_msg})
            return False, error_msg

    days = lesson_json["days"]
    required_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    missing_days = []
    for day in required_days:
        if day not in days:
            missing_days.append(day)
            logger.warning(
                "schema_validation_missing_day",
                extra={"day": day, "action": "Adding placeholder"},
            )

    no_school_placeholder = {
        "unit_lesson": "No School",
        "objective": {
            "content_objective": "No School",
            "student_goal": "No School",
            "wida_objective": "No School",
        },
        "anticipatory_set": {
            "original_content": "No School",
            "bilingual_bridge": "No School",
        },
        "vocabulary_cognates": [],
        "sentence_frames": [],
        "tailored_instruction": {
            "original_content": "No School",
            "co_teaching_model": {},
            "ell_support": [],
            "special_needs_support": [],
            "materials": [],
        },
        "misconceptions": {
            "original_content": "No School",
            "linguistic_note": {},
        },
        "assessment": {
            "primary_assessment": "No School",
            "bilingual_overlay": {},
        },
        "homework": {
            "original_content": "No School",
            "family_connection": "No School",
        },
    }

    if missing_days:
        for day in missing_days:
            days[day] = no_school_placeholder.copy()

        for day_name in required_days:
            if day_name not in days:
                continue
            day_data = days[day_name]
            if day_data.get("unit_lesson") == "No School":
                tailored_instruction = day_data.get("tailored_instruction", {})
                if isinstance(tailored_instruction, dict):
                    original_content = tailored_instruction.get("original_content", "")
                    if (
                        original_content
                        and original_content.strip()
                        and original_content.strip() != "No School"
                    ):
                        logger.info(
                            "preserving_tailored_instruction_content",
                            extra={"day": day_name, "has_content": True},
                        )
                    co_teaching = tailored_instruction.get("co_teaching_model", {})
                    if isinstance(co_teaching, dict) and co_teaching:
                        has_co_teaching_content = (
                            co_teaching.get("model_name")
                            or co_teaching.get("rationale")
                            or (
                                isinstance(co_teaching.get("phase_plan"), list)
                                and len(co_teaching.get("phase_plan", [])) > 0
                            )
                        )
                        if has_co_teaching_content:
                            logger.info(
                                "preserving_co_teaching_model",
                                extra={"day": day_name, "has_content": True},
                            )
                    for field in ["ell_support", "special_needs_support", "materials"]:
                        field_value = tailored_instruction.get(field, [])
                        if isinstance(field_value, list) and len(field_value) > 0:
                            logger.info(
                                "preserving_tailored_instruction_field",
                                extra={
                                    "day": day_name,
                                    "field": field,
                                    "count": len(field_value),
                                },
                            )

                objective = day_data.get("objective", {})
                if isinstance(objective, dict):
                    for obj_field in [
                        "content_objective",
                        "student_goal",
                        "wida_objective",
                    ]:
                        obj_value = objective.get(obj_field, "")
                        if (
                            obj_value
                            and obj_value.strip()
                            and obj_value.strip() != "No School"
                        ):
                            logger.info(
                                "preserving_objective_content",
                                extra={"day": day_name, "field": obj_field},
                            )

                anticipatory_set = day_data.get("anticipatory_set", {})
                if isinstance(anticipatory_set, dict):
                    for as_field in ["original_content", "bilingual_bridge"]:
                        as_value = anticipatory_set.get(as_field, "")
                        if (
                            as_value
                            and as_value.strip()
                            and as_value.strip() != "No School"
                        ):
                            logger.info(
                                "preserving_anticipatory_set_content",
                                extra={"day": day_name, "field": as_field},
                            )

        logger.info(
            "schema_validation_missing_days_filled",
            extra={"missing_days": missing_days, "filled_count": len(missing_days)},
        )

    monday = days["monday"]
    if "unit_lesson" not in monday:
        error_msg = "Missing monday.unit_lesson"
        logger.error("schema_validation_failed", extra={"reason": error_msg})
        return False, error_msg

    missing_fields = []
    for day_name in required_days:
        day_data = days.get(day_name, {})
        if not day_data or day_data.get("unit_lesson") == "No School":
            continue

        vocab = day_data.get("vocabulary_cognates")
        if vocab is None:
            missing_fields.append(f"{day_name}.vocabulary_cognates (missing)")
        elif not isinstance(vocab, list):
            missing_fields.append(f"{day_name}.vocabulary_cognates (not a list)")
        elif len(vocab) == 0:
            missing_fields.append(
                f"{day_name}.vocabulary_cognates (empty array - must have exactly 6 items)"
            )
        elif len(vocab) > 6:
            day_data["vocabulary_cognates"] = vocab[:6]
        elif len(vocab) != 6:
            missing_fields.append(
                f"{day_name}.vocabulary_cognates (has {len(vocab)} items, need exactly 6)"
            )

        frames = day_data.get("sentence_frames")
        if frames is None:
            missing_fields.append(f"{day_name}.sentence_frames (missing)")
        elif not isinstance(frames, list):
            missing_fields.append(f"{day_name}.sentence_frames (not a list)")
        elif len(frames) != 8:
            missing_fields.append(
                f"{day_name}.sentence_frames (has {len(frames)} items, need exactly 8)"
            )

    if missing_fields:
        error_msg = f"Missing or invalid required fields: {', '.join(missing_fields)}. vocabulary_cognates (exactly 6 items) and sentence_frames (exactly 8 items) are MANDATORY for all lesson days."
        logger.error(
            "schema_validation_missing_fields",
            extra={"missing_fields": missing_fields},
        )
        return False, error_msg

    logger.info("schema_validation_success")
    return True, None
