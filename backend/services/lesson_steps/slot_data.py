"""
Extract day/slot data and phase_plan from lesson_json for lesson step generation.
"""
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException

from backend.telemetry import logger


def extract_slot_data(
    lesson_json: Dict[str, Any],
    plan_id: str,
    day: str,
    slot: int,
) -> Optional[Tuple[Dict[str, Any], Dict[str, Any], List[Any], Dict[str, Any]]]:
    """
    Extract day_data, slot_data, phase_plan, and tailored_instruction from lesson_json.
    Returns None if this is a "No School" slot (caller should return []).
    Raises HTTPException if day or slot not found.
    """
    days = lesson_json.get("days", {})
    logger.info(
        "extracting_day_data",
        extra={
            "plan_id": plan_id,
            "day": day,
            "available_days": list(days.keys()),
            "day_lower": day.lower(),
        },
    )
    day_data = days.get(day.lower())
    if not day_data:
        logger.error(
            "day_not_found_in_plan",
            extra={
                "plan_id": plan_id,
                "requested_day": day,
                "available_days": list(days.keys()),
            },
        )
        raise HTTPException(status_code=404, detail=f"Day {day} not found in plan")

    slot_data = day_data
    slots_for_day = day_data.get("slots") or []

    if isinstance(slots_for_day, list) and slots_for_day:
        matching = None
        for s in slots_for_day:
            if not isinstance(s, dict):
                continue
            s_num = s.get("slot_number", 0)
            if int(s_num) == int(slot):
                matching = s
                break
        if matching:
            slot_data = matching
        else:
            available_slots = [
                s.get("slot_number") for s in slots_for_day if isinstance(s, dict)
            ]
            logger.error(
                "slot_not_found_in_plan",
                extra={
                    "plan_id": plan_id,
                    "requested_slot": slot,
                    "requested_day": day,
                    "available_slots": available_slots,
                },
            )
            raise HTTPException(
                status_code=404,
                detail=f"Slot {slot} not found in {day}. Available slots: {available_slots}",
            )

        unit_lesson = slot_data.get("unit_lesson", "")
        if unit_lesson and "no school" in unit_lesson.lower():
            logger.info(
                "skipping_step_generation_for_no_school",
                extra={
                    "plan_id": plan_id,
                    "day": day,
                    "slot": slot,
                    "unit_lesson": unit_lesson,
                },
            )
            return None

        if not slot_data.get("vocabulary_cognates"):
            logger.info(
                "vocabulary_cognates_not_found_in_slot",
                extra={
                    "plan_id": plan_id,
                    "day": day,
                    "slot": slot,
                    "message": "vocabulary_cognates not found in slot_data. This may mean the plan was generated before vocabulary_cognates was added to the schema. Consider regenerating the plan to include vocabulary data.",
                },
            )

        if day_data.get("vocabulary_cognates") and not slot_data.get(
            "vocabulary_cognates"
        ):
            slot_data["vocabulary_cognates"] = day_data.get("vocabulary_cognates")

    slot_tailored_instruction = slot_data.get("tailored_instruction", {})
    day_tailored_instruction = day_data.get("tailored_instruction", {})

    tailored_instruction = (
        slot_tailored_instruction
        if slot_tailored_instruction
        else day_tailored_instruction
    )

    logger.info(
        "tailored_instruction_extracted",
        extra={
            "plan_id": plan_id,
            "day": day,
            "slot": slot,
            "has_tailored_instruction": bool(tailored_instruction),
            "tailored_instruction_keys": list(tailored_instruction.keys())
            if tailored_instruction
            else [],
            "has_day_tailored_instruction": bool(day_tailored_instruction),
            "day_tailored_instruction_keys": list(day_tailored_instruction.keys())
            if day_tailored_instruction
            else [],
        },
    )

    phase_plan = None
    co_teaching_model = slot_tailored_instruction.get("co_teaching_model", {})

    if co_teaching_model:
        phase_plan = co_teaching_model.get("phase_plan")
        if phase_plan:
            logger.info(
                "phase_plan_found_in_slot_co_teaching_model",
                extra={
                    "plan_id": plan_id,
                    "day": day,
                    "slot": slot,
                    "location": "slot_data.tailored_instruction.co_teaching_model.phase_plan",
                    "phase_plan_count": len(phase_plan)
                    if isinstance(phase_plan, list)
                    else 0,
                },
            )

    if not phase_plan:
        phase_plan = slot_tailored_instruction.get("phase_plan")
        if phase_plan:
            logger.info(
                "phase_plan_found_in_slot_direct",
                extra={
                    "plan_id": plan_id,
                    "day": day,
                    "slot": slot,
                    "location": "slot_data.tailored_instruction.phase_plan",
                    "phase_plan_count": len(phase_plan)
                    if isinstance(phase_plan, list)
                    else 0,
                },
            )

    if not phase_plan:
        day_co_teaching_model = day_tailored_instruction.get(
            "co_teaching_model", {}
        )
        if day_co_teaching_model:
            phase_plan = day_co_teaching_model.get("phase_plan")
            if phase_plan:
                logger.info(
                    "phase_plan_found_in_day_co_teaching_model",
                    extra={
                        "plan_id": plan_id,
                        "day": day,
                        "slot": slot,
                        "location": "day_data.tailored_instruction.co_teaching_model.phase_plan",
                        "phase_plan_count": len(phase_plan)
                        if isinstance(phase_plan, list)
                        else 0,
                    },
                )

    if not phase_plan:
        phase_plan = day_tailored_instruction.get("phase_plan")
        if phase_plan:
            logger.info(
                "phase_plan_found_in_day_direct",
                extra={
                    "plan_id": plan_id,
                    "day": day,
                    "slot": slot,
                    "location": "day_data.tailored_instruction.phase_plan",
                    "phase_plan_count": len(phase_plan)
                    if isinstance(phase_plan, list)
                    else 0,
                },
            )

    if phase_plan is None:
        phase_plan = []

    logger.info(
        "co_teaching_model_extracted",
        extra={
            "plan_id": plan_id,
            "has_co_teaching_model": bool(co_teaching_model),
            "co_teaching_model_keys": list(co_teaching_model.keys())
            if co_teaching_model
            else [],
        },
    )

    logger.info(
        "phase_plan_extracted",
        extra={
            "plan_id": plan_id,
            "day": day,
            "slot": slot,
            "phase_plan_count": len(phase_plan) if phase_plan else 0,
            "phase_plan_is_list": isinstance(phase_plan, list),
            "phase_plan_is_none": phase_plan is None,
        },
    )

    return (day_data, slot_data, phase_plan, tailored_instruction)
