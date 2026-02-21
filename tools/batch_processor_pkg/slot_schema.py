"""
Slot and schema mapping for batch processor: sanitize values/slots, convert formats, map to original schema.
"""

from typing import Any, Dict, List, Optional

from backend.original_lesson_schema_models import (
    OriginalAnticipatorySet,
    OriginalAssessment,
    OriginalDayPlanSingleSlot,
    OriginalHomework,
    OriginalHyperlink,
    OriginalHyperlinks,
    OriginalInstruction,
    OriginalMaterials,
    OriginalMisconceptions,
    OriginalObjective,
    OriginalTailoredInstruction,
)
from backend.telemetry import logger


def sanitize_value(value: Any) -> Any:
    """Recursively sanitize a value to remove ModelPrivateAttr objects."""
    if hasattr(value, "__class__") and "ModelPrivateAttr" in str(type(value)):
        return None

    if isinstance(value, list):
        return [sanitize_value(item) for item in value]

    if isinstance(value, dict):
        return {k: sanitize_value(v) for k, v in value.items()}

    if hasattr(value, "model_dump") and callable(value.model_dump):
        try:
            return sanitize_value(value.model_dump())
        except Exception:
            pass

    if hasattr(value, "dict") and callable(value.dict):
        try:
            return sanitize_value(value.dict())
        except Exception:
            pass

    return value


def sanitize_slot(slot: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure slot dictionary contains no ModelPrivateAttr objects."""
    print(f"DEBUG: _sanitize_slot called for slot type {type(slot)}")
    if not isinstance(slot, dict):
        if hasattr(slot, "model_dump"):
            try:
                slot = slot.model_dump()
            except Exception:
                pass
        elif hasattr(slot, "dict"):
            try:
                slot = slot.dict()
            except Exception:
                pass
        else:
            try:
                slot = dict(slot)
            except Exception:
                pass

    if not isinstance(slot, dict):
        return slot

    return {k: sanitize_value(v) for k, v in slot.items()}


def convert_single_slot_to_slots_format(
    lesson_json: Dict[str, Any], slot_number: int, subject: str
) -> Dict[str, Any]:
    """
    Convert a single-slot lesson_json (old format) to the new slots format.

    Old format: days = { "monday": { "unit_lesson": ..., "objective": ..., ... } }
    New format: days = { "monday": { "slots": [{ "slot_number": 1, "subject": "...", ... }] } }
    """
    if not lesson_json or not isinstance(lesson_json, dict):
        return lesson_json

    days = lesson_json.get("days", {})
    if not days:
        return lesson_json

    is_already_in_slots_format = any(
        isinstance(day_data, dict)
        and "slots" in day_data
        and isinstance(day_data["slots"], list)
        for day_data in days.values()
    )

    if is_already_in_slots_format:
        return lesson_json

    converted_days = {}
    for day_name, day_data in days.items():
        if not isinstance(day_data, dict):
            converted_days[day_name] = day_data
            continue

        slot = {
            "slot_number": slot_number,
            "subject": subject,
        }
        for key, value in day_data.items():
            slot[key] = value

        metadata = lesson_json.get("metadata", {})
        if "grade" in metadata and "grade" not in slot:
            slot["grade"] = metadata.get("grade")
        if "homeroom" in metadata and "homeroom" not in slot:
            slot["homeroom"] = metadata.get("homeroom")
        if "teacher_name" in metadata and "teacher_name" not in slot:
            slot["teacher_name"] = metadata.get("teacher_name")

        converted_days[day_name] = {"slots": [slot]}

    return {**lesson_json, "days": converted_days}


def map_day_content_to_schema(
    day_content: Dict[str, str],
    slot_info: Dict[str, Any],
    day_hyperlinks: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Map raw extracted string content to OriginalDayPlanSingleSlot schema.

    Args:
        day_content: Dictionary of {row_label: cell_text}
        slot_info: Slot metadata (subject, grade, etc.)
        day_hyperlinks: Optional list of {text, url} for the day

    Returns:
        Dictionary representation of OriginalDayPlanSingleSlot
    """
    normalized_content = {k.lower().strip(): v for k, v in day_content.items()}

    def find_text(keywords: List[str]) -> Optional[str]:
        for k, v in normalized_content.items():
            if any(kw in k for kw in keywords):
                return v.strip()
        return None

    unit_lesson = find_text(["unit", "lesson", "module"]) or "N/A"

    objective_text = find_text(["objective", "goal", "target", "swbat"])
    objective = (
        OriginalObjective(content_objective=objective_text) if objective_text else None
    )

    ant_set_text = find_text(["anticipatory", "do now", "warm up", "entry"])
    anticipatory_set = (
        OriginalAnticipatorySet(original_content=ant_set_text) if ant_set_text else None
    )

    instruction_text = find_text(["activity", "procedure", "instruction", "lesson"])
    tailored_text = find_text(["tailored", "differentiation", "scaffold"])
    tailored_instruction = (
        OriginalTailoredInstruction(content=tailored_text) if tailored_text else None
    )

    if not instruction_text and tailored_text:
        instruction_text = f"[Tailored Instruction provided]: {tailored_text}"

    instruction = (
        OriginalInstruction(activities=instruction_text) if instruction_text else None
    )

    misconception_text = find_text(["misconception", "pitfall", "error"])
    misconceptions = (
        OriginalMisconceptions(content=misconception_text)
        if misconception_text
        else None
    )

    materials_text = find_text(["material", "resource", "supplies"])
    materials = (
        OriginalMaterials(
            root=[m.strip() for m in materials_text.split("\n") if m.strip()]
        )
        if materials_text
        else None
    )

    assessment_text = find_text(["assessment", "evaluate", "exit ticket", "check"])
    assessment = (
        OriginalAssessment(primary_assessment=assessment_text)
        if assessment_text
        else None
    )

    homework_text = find_text(["homework", "assignment"])
    homework = (
        OriginalHomework(original_content=homework_text) if homework_text else None
    )

    try:
        plan = OriginalDayPlanSingleSlot(
            unit_lesson=unit_lesson,
            objective=objective,
            anticipatory_set=anticipatory_set,
            instruction=instruction,
            tailored_instruction=tailored_instruction,
            misconceptions=misconceptions,
            materials=materials,
            assessment=assessment,
            homework=homework,
            hyperlinks=(
                OriginalHyperlinks(
                    root=[
                        OriginalHyperlink(text=h["text"], url=h["url"])
                        for h in day_hyperlinks
                        if h.get("text") and h.get("url")
                    ]
                )
                if day_hyperlinks
                else None
            ),
        )
        return plan.model_dump()
    except Exception as e:
        logger.warning(
            "original_schema_mapping_failed",
            extra={"error": str(e), "slot": slot_info.get("slot_number")},
        )
        return {
            "unit_lesson": unit_lesson,
            "objective": objective.model_dump() if objective else None,
            "anticipatory_set": anticipatory_set.model_dump() if anticipatory_set else None,
            "instruction": instruction.model_dump() if instruction else None,
            "tailored_instruction": tailored_instruction.model_dump()
            if tailored_instruction
            else None,
            "misconceptions": misconceptions.model_dump() if misconceptions else None,
            "materials": materials.model_dump() if materials else None,
            "assessment": assessment.model_dump() if assessment else None,
            "homework": homework.model_dump() if homework else None,
            "hyperlinks": {"root": day_hyperlinks} if day_hyperlinks else None,
        }
