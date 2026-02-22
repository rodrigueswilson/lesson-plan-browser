"""
Convert OriginalLessonPlan lists to/from multi-slot lesson JSON.
Extracted from combine.py for single responsibility; used by combine and orchestrator.
"""

import copy
from typing import Any, Dict, List

from backend.schema import OriginalLessonPlan


def convert_originals_to_json(
    plans: List[OriginalLessonPlan],
) -> Dict[str, Any]:
    """
    Convert a list of OriginalLessonPlan objects to a multi-slot lesson JSON.
    This allows reusing the standard DOCXRenderer for original plans.
    """
    if not plans:
        return {}

    first = plans[0]
    is_single_plan = len(plans) == 1

    metadata = {
        "primary_teacher_name": first.primary_teacher_name,
        "week_of": first.week_of,
        "grade": first.grade or "Unknown",
        "subject": first.subject,
        "slot_number": first.slot_number if is_single_plan else None,
        "homeroom": first.homeroom,
        "source_type": "originals",
    }

    days_data = {}
    all_hyperlinks = []

    for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
        slots = []
        for plan in plans:
            content = getattr(plan, f"{day}_content", None)
            if content:
                enriched = content.copy()

                if "hyperlinks" in enriched and enriched["hyperlinks"]:
                    links = enriched["hyperlinks"]
                    if isinstance(links, dict) and "root" in links:
                        links = links["root"]

                    if isinstance(links, list):
                        for link in links:
                            if isinstance(link, dict):
                                link_copy = link.copy()
                                link_copy["_source_slot"] = plan.slot_number
                                link_copy["_source_subject"] = plan.subject
                                link_copy["table_idx"] = 1
                                all_hyperlinks.append(link_copy)

                orig_instruction = enriched.get("instruction") or {}
                orig_tailored = enriched.get("tailored_instruction") or {}

                instr_parts = []
                activities = (
                    orig_instruction.get("activities")
                    if isinstance(orig_instruction, dict)
                    else None
                )
                if activities:
                    instr_parts.append(activities)

                tailored = (
                    orig_tailored.get("content")
                    if isinstance(orig_tailored, dict)
                    else None
                )
                if tailored:
                    is_duplicate = any(
                        tailored in part or part in tailored for part in instr_parts
                    )
                    if not is_duplicate:
                        instr_parts.append(tailored)

                materials_list = []
                materials_data = enriched.get("materials")
                if materials_data:
                    if isinstance(materials_data, list):
                        materials_list = materials_data
                    elif (
                        isinstance(materials_data, dict)
                        and "root" in materials_data
                    ):
                        materials_list = materials_data["root"]

                enriched["tailored_instruction"] = {
                    "original_content": "\n\n".join(instr_parts),
                    "materials": materials_list,
                }

                misconceptions = enriched.get("misconceptions")
                if (
                    misconceptions
                    and isinstance(misconceptions, dict)
                    and "content" in misconceptions
                ):
                    misconceptions["original_content"] = misconceptions["content"]

                enriched["slot_number"] = plan.slot_number
                enriched["subject"] = plan.subject
                slots.append(enriched)

        if slots:
            if len(plans) == 1:
                days_data[day] = slots[0]
            else:
                days_data[day] = {"slots": slots}

    return {
        "metadata": metadata,
        "days": days_data,
        "_hyperlinks": all_hyperlinks,
        "_media_schema_version": "2.0",
    }


def reconstruct_slots_from_json(
    lesson_json: Dict[str, Any],
) -> Dict[int, Dict[str, Any]]:
    """
    Reconstruct individual slot lesson plans from a multi-slot lesson JSON.
    Returns a mapping of slot_number -> lesson_entry.

    CRITICAL: Uses deep copies to prevent shared state in parallel processing.
    """
    if not lesson_json or "days" not in lesson_json:
        return {}

    existing_slots_by_number = {}

    for day_name, day_data in lesson_json.get("days", {}).items():
        day_slots = day_data.get("slots", [])
        if not day_slots and any(
            k in day_data for k in ["unit_lesson", "objective"]
        ):
            day_slots = [{**day_data}]

        for slot_data in day_slots:
            slot_num = slot_data.get("slot_number")
            if slot_num is not None:
                if slot_num not in existing_slots_by_number:
                    existing_slots_by_number[slot_num] = {
                        "slot_number": slot_num,
                        "subject": slot_data.get("subject", "Unknown"),
                        "lesson_json": {
                            "metadata": copy.deepcopy(
                                lesson_json.get("metadata", {})
                            ),
                            "days": {
                                d: {}
                                for d in [
                                    "monday",
                                    "tuesday",
                                    "wednesday",
                                    "thursday",
                                    "friday",
                                ]
                            },
                        },
                    }
                    existing_slots_by_number[slot_num]["lesson_json"][
                        "metadata"
                    ]["slot_number"] = slot_num
                    existing_slots_by_number[slot_num]["lesson_json"][
                        "metadata"
                    ]["subject"] = slot_data.get("subject", "Unknown")

                day_content = slot_data.copy()
                for field in [
                    "slot_number",
                    "subject",
                    "teacher_name",
                    "grade",
                    "homeroom",
                    "start_time",
                    "end_time",
                ]:
                    day_content.pop(field, None)

                existing_slots_by_number[slot_num]["lesson_json"]["days"][
                    day_name
                ] = day_content

    all_existing_images = lesson_json.get("_images", [])
    all_existing_links = lesson_json.get("_hyperlinks", [])

    has_source_metadata = any(
        link.get("_source_slot") is not None for link in all_existing_links
    )
    is_effectively_single_slot = len(existing_slots_by_number) == 1

    for slot_num, lesson_entry in existing_slots_by_number.items():
        lesson_entry["lesson_json"]["_media_schema_version"] = "2.0"

        if not has_source_metadata and is_effectively_single_slot:
            images_with_meta = []
            for img in all_existing_images:
                img_copy = img.copy()
                img_copy["_source_slot"] = slot_num
                images_with_meta.append(img_copy)
            lesson_entry["lesson_json"]["_images"] = images_with_meta

            links_with_meta = []
            for link in all_existing_links:
                link_copy = link.copy()
                link_copy["_source_slot"] = slot_num
                links_with_meta.append(link_copy)
            lesson_entry["lesson_json"]["_hyperlinks"] = links_with_meta
        else:
            lesson_entry["lesson_json"]["_images"] = [
                img
                for img in all_existing_images
                if img.get("_source_slot") == slot_num
            ]
            lesson_entry["lesson_json"]["_hyperlinks"] = [
                link
                for link in all_existing_links
                if link.get("_source_slot") == slot_num
            ]

    return existing_slots_by_number
