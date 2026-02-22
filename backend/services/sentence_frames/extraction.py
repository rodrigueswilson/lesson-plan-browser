"""Extract sentence frame payloads from lesson JSON."""

from __future__ import annotations

from typing import Any, Dict, List

from backend.services.sorting_utils import sort_slots
from backend.telemetry import logger
from backend.utils.metadata_utils import (
    get_homeroom,
    get_subject,
    get_teacher_name,
)


def extract_sentence_frames(lesson_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract sentence frame payloads from lesson JSON, ordered by schedule (day and slot).

    Each item is a dict with metadata and three level buckets:
    - levels_1_2: list of 3 frames
    - levels_3_4: list of 3 frames
    - levels_5_6: list of 2 frames

    Frames are ordered by day (Monday-Friday) and then by start_time (chronological) to follow schedule order.
    """
    results: List[Dict[str, Any]] = []

    days = lesson_json.get("days") or {}
    if not isinstance(days, dict):
        return results

    metadata = lesson_json.get("metadata", {})
    week_of = metadata.get("week_of", "Unknown")
    default_grade = metadata.get("grade", "Unknown")
    default_room = metadata.get("room", "")
    default_teacher_name = get_teacher_name(metadata)

    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]

    for day_name in day_names:
        day_data = days.get(day_name)
        if not isinstance(day_data, dict):
            continue

        slots = day_data.get("slots") or []
        if isinstance(slots, list) and len(slots) > 0:
            sorted_slots = sort_slots(slots)
            logger.debug(
                f"Extracting sentence frames for {day_name}: {len(sorted_slots)} slots found (slot_numbers: {[s.get('slot_number', 0) for s in sorted_slots]})"
            )

            for slot in sorted_slots:
                if not isinstance(slot, dict):
                    continue

                slot_num = slot.get("slot_number", 0)
                slot_unit_lesson = slot.get("unit_lesson", "")

                if (
                    slot_unit_lesson
                    and slot_unit_lesson.strip().lower() == "no school"
                ):
                    logger.debug(
                        f"Skipping slot {slot_num} ({day_name}) - No School entry"
                    )
                    continue

                slot_frames = slot.get("sentence_frames") or []
                if not isinstance(slot_frames, list) or len(slot_frames) == 0:
                    logger.debug(
                        f"Slot {slot_num} ({day_name}) has no sentence frames - including with empty frames"
                    )
                    slot_frames = []
                else:
                    logger.debug(
                        f"Processing slot {slot_num} ({day_name}) for sentence frames extraction ({len(slot_frames)} frames)"
                    )

                slot_grade = slot.get("grade", default_grade)
                slot_subject = get_subject(metadata, slot=slot)
                slot_homeroom = get_homeroom(metadata, slot=slot)
                slot_room = slot.get("room")
                if slot_room is None:
                    slot_room = default_room
                slot_teacher = get_teacher_name(metadata, slot=slot)

                levels_1_2: List[Dict[str, Any]] = []
                levels_3_4: List[Dict[str, Any]] = []
                levels_5_6: List[Dict[str, Any]] = []

                for frame in slot_frames:
                    if not isinstance(frame, dict):
                        continue
                    level = frame.get("proficiency_level")
                    if level == "levels_1_2":
                        levels_1_2.append(frame)
                    elif level == "levels_3_4":
                        levels_3_4.append(frame)
                    elif level == "levels_5_6":
                        levels_5_6.append(frame)

                final_room = slot_room
                if (
                    not final_room
                    or final_room == "N/A"
                    or final_room.strip() == ""
                ):
                    if default_room and default_room != "Unknown":
                        final_room = default_room
                    else:
                        final_room = ""

                results.append(
                    {
                        "week_of": week_of,
                        "day": day_name.capitalize(),
                        "grade": slot_grade
                        if slot_grade and slot_grade != "N/A"
                        else default_grade,
                        "subject": slot_subject,
                        "homeroom": slot_homeroom,
                        "room": final_room,
                        "teacher_name": slot_teacher
                        if slot_teacher != "Unknown"
                        else default_teacher_name,
                        "unit_lesson": slot_unit_lesson,
                        "slot_number": slot.get("slot_number", 0),
                        "start_time": slot.get("start_time", ""),
                        "levels_1_2": levels_1_2,
                        "levels_3_4": levels_3_4,
                        "levels_5_6": levels_5_6,
                    }
                )
        else:
            day_unit_lesson = day_data.get("unit_lesson", "")

            if day_unit_lesson and day_unit_lesson.strip().lower() == "no school":
                continue

            day_level_frames = day_data.get("sentence_frames") or []
            if not isinstance(day_level_frames, list) or len(day_level_frames) == 0:
                continue

            levels_1_2 = []
            levels_3_4 = []
            levels_5_6 = []

            for frame in day_level_frames:
                if not isinstance(frame, dict):
                    continue
                level = frame.get("proficiency_level")
                if level == "levels_1_2":
                    levels_1_2.append(frame)
                elif level == "levels_3_4":
                    levels_3_4.append(frame)
                elif level == "levels_5_6":
                    levels_5_6.append(frame)

            if not (levels_1_2 or levels_3_4 or levels_5_6):
                continue

            results.append(
                {
                    "week_of": week_of,
                    "day": day_name.capitalize(),
                    "grade": default_grade,
                    "subject": get_subject(metadata),
                    "homeroom": get_homeroom(metadata),
                    "room": default_room if default_room else "",
                    "teacher_name": get_teacher_name(metadata),
                    "unit_lesson": day_data.get("unit_lesson", ""),
                    "slot_number": 0,
                    "levels_1_2": levels_1_2,
                    "levels_3_4": levels_3_4,
                    "levels_5_6": levels_5_6,
                }
            )

    day_order = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4}

    def get_result_sort_key(result: Dict[str, Any]) -> tuple:
        day = result.get("day", "")
        day_idx = day_order.get(day, 99)
        start_time = result.get("start_time", "") or ""
        slot_num = result.get("slot_number", 0)

        time_sort = 0
        if start_time:
            try:
                parts = str(start_time).split(":")
                if len(parts) >= 2:
                    time_sort = int(parts[0]) * 60 + int(parts[1])
            except (ValueError, TypeError):
                pass

        return (day_idx, time_sort, slot_num)

    results.sort(key=get_result_sort_key)
    return results
