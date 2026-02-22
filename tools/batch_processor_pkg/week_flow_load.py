"""
Load user and slots for week-level batch processing; enrich slots with schedule.
"""
import asyncio
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple, Union

from backend.telemetry import logger


def _slot_obj_to_dict(slot_obj: Any) -> dict:
    """Convert a slot object (ORM/Pydantic/dict) to a safe dictionary."""
    slot_dict = None
    if hasattr(slot_obj, "model_dump"):
        try:
            slot_dict = slot_obj.model_dump(mode="python")
        except Exception:
            try:
                slot_dict = slot_obj.model_dump()
            except Exception:
                slot_dict = None
    if slot_dict is None and hasattr(slot_obj, "dict"):
        try:
            slot_dict = slot_obj.dict()
        except Exception:
            slot_dict = None
    if slot_dict is None and isinstance(slot_obj, dict):
        slot_dict = {}
        for key, value in slot_obj.items():
            if hasattr(value, "__class__") and "ModelPrivateAttr" in str(type(value)):
                try:
                    slot_dict[key] = getattr(slot_obj, key, None)
                except Exception:
                    slot_dict[key] = None
            else:
                slot_dict[key] = value
    if slot_dict is None:
        slot_dict = {
            "id": str(getattr(slot_obj, "id", "")) if hasattr(slot_obj, "id") else "",
            "user_id": str(getattr(slot_obj, "user_id", "")) if hasattr(slot_obj, "user_id") else "",
            "slot_number": int(getattr(slot_obj, "slot_number", 0)) if hasattr(slot_obj, "slot_number") else 0,
            "subject": str(getattr(slot_obj, "subject", "")) if hasattr(slot_obj, "subject") else "",
            "grade": str(getattr(slot_obj, "grade", "")) if hasattr(slot_obj, "grade") else "",
            "homeroom": str(getattr(slot_obj, "homeroom", "")) if hasattr(slot_obj, "homeroom") else None,
            "plan_group_label": str(getattr(slot_obj, "plan_group_label", "")) if hasattr(slot_obj, "plan_group_label") else None,
            "proficiency_levels": str(getattr(slot_obj, "proficiency_levels", "")) if hasattr(slot_obj, "proficiency_levels") else None,
            "primary_teacher_file": str(getattr(slot_obj, "primary_teacher_file", "")) if hasattr(slot_obj, "primary_teacher_file") else None,
            "primary_teacher_name": str(getattr(slot_obj, "primary_teacher_name", "")) if hasattr(slot_obj, "primary_teacher_name") else None,
            "primary_teacher_first_name": str(getattr(slot_obj, "primary_teacher_first_name", "")) if hasattr(slot_obj, "primary_teacher_first_name") else None,
            "primary_teacher_last_name": str(getattr(slot_obj, "primary_teacher_last_name", "")) if hasattr(slot_obj, "primary_teacher_last_name") else None,
            "primary_teacher_file_pattern": str(getattr(slot_obj, "primary_teacher_file_pattern", "")) if hasattr(slot_obj, "primary_teacher_file_pattern") else None,
            "display_order": int(getattr(slot_obj, "display_order", 0)) if hasattr(slot_obj, "display_order") else 0,
        }
    for key in list(slot_dict.keys()):
        value = slot_dict[key]
        if hasattr(value, "__class__") and "ModelPrivateAttr" in str(type(value)):
            slot_dict[key] = None
        elif not isinstance(value, (str, int, float, bool, type(None), list, dict)):
            try:
                slot_dict[key] = str(value)
            except Exception:
                slot_dict[key] = None
    return slot_dict


async def load_user_slots(
    processor: Any,
    user_id: str,
    slot_ids: Optional[list] = None,
) -> Union[Tuple[Dict[str, Any], List[Dict[str, Any]], Any], Dict[str, Any]]:
    """
    Load user and slots for the given user_id; enrich slots with schedule.
    Returns (user, slots, db) on success, or {"success": False, "error": "..."} on failure.
    """
    db = processor.get_db(user_id=user_id)
    user_raw = await asyncio.to_thread(db.get_user, user_id)
    if not user_raw:
        return {"success": False, "error": f"User not found: {user_id}"}

    if hasattr(user_raw, "model_dump"):
        user = user_raw.model_dump()
    elif hasattr(user_raw, "dict"):
        user = user_raw.dict()
    else:
        user = dict(user_raw)

    slots_raw = await asyncio.to_thread(db.get_user_slots, user_id)
    if not slots_raw:
        return {
            "success": False,
            "error": f"No class slots configured for user: {user.get('name', 'Unknown')}",
        }

    slots = [_slot_obj_to_dict(slot_obj) for slot_obj in slots_raw]

    schedule_entries = await asyncio.to_thread(db.get_user_schedule, user_id)
    schedule_entries_dict = []
    for entry in schedule_entries:
        if hasattr(entry, "model_dump"):
            entry_dict = entry.model_dump()
        elif hasattr(entry, "dict"):
            entry_dict = entry.dict()
        else:
            entry_dict = {
                "slot_number": getattr(entry, "slot_number", None),
                "is_active": getattr(entry, "is_active", True),
                "start_time": getattr(entry, "start_time", None),
                "end_time": getattr(entry, "end_time", None),
            }
        schedule_entries_dict.append(entry_dict)

    def normalize_subj(s):
        if not s:
            return ""
        return re.sub(r"[^a-z0-9]", "", s.lower())

    for slot in slots:
        slot_subj_norm = normalize_subj(slot.get("subject", ""))
        slot_num = slot.get("slot_number")
        matching_entries = [
            e
            for e in schedule_entries_dict
            if normalize_subj(e.get("subject", "")) == slot_subj_norm
            and e.get("slot_number") == slot_num
            and e.get("is_active", True)
        ]
        if not matching_entries:
            matching_entries = [
                e
                for e in schedule_entries_dict
                if normalize_subj(e.get("subject", "")) == slot_subj_norm
                and e.get("is_active", True)
            ]
        if not matching_entries:
            matching_entries = [
                e
                for e in schedule_entries_dict
                if e.get("slot_number") == slot_num and e.get("is_active", True)
            ]
        if matching_entries:
            day_times = {}
            for e in matching_entries:
                day = e.get("day_of_week", "").lower()
                if day:
                    day_times[day] = {
                        "start_time": e.get("start_time"),
                        "end_time": e.get("end_time"),
                    }
            slot["day_times"] = day_times
            times = [(e.get("start_time"), e.get("end_time")) for e in matching_entries]
            most_common_time = Counter(times).most_common(1)[0][0]
            slot["start_time"] = most_common_time[0]
            slot["end_time"] = most_common_time[1]

    if slot_ids:
        slot_ids_set = set()
        for sid in slot_ids:
            if isinstance(sid, str):
                slot_ids_set.add(sid)
            elif hasattr(sid, "id"):
                slot_ids_set.add(str(sid.id))
            else:
                slot_ids_set.add(str(sid))
        slots = [slot for slot in slots if slot.get("id") in slot_ids_set]
        if not slots:
            error_msg = (
                f"No matching slots found for provided slot_ids. Requested: {slot_ids_set}, "
                f"Available: {[getattr(s, 'id', s.get('id') if isinstance(s, dict) else None) for s in slots_raw]}"
            )
            logger.error("week_flow_load_no_matching_slots", extra={"error": error_msg})
            return {"success": False, "error": error_msg}

    return (user, slots, db)
