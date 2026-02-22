"""
Enrich lesson plan JSON with start_time and end_time from the schedules table.
"""
from typing import Any, Dict

from backend.database import get_db
from backend.services.sorting_utils import sort_slots


def enrich_lesson_json_with_times(lesson_json: Dict[str, Any], user_id: str) -> None:
    """Enrich lesson_json with start_time and end_time from schedules table.

    Matches slots to schedule entries by (day, subject, grade, homeroom) since schedule
    slot_numbers may differ from class slot_numbers. This ensures correct chronological
    ordering for each day based on the actual schedule, considering all three attributes:
    subject, grade, and room (homeroom).
    """
    if not lesson_json or "days" not in lesson_json:
        return

    db = get_db(user_id=user_id)
    schedule = db.get_user_schedule(user_id=user_id)

    # Build maps for flexible matching
    # Map (day, subject, grade, homeroom) -> list of (start_time, end_time, slot_number)
    # This allows matching by all three attributes even if slot_numbers don't match
    full_match_map = {}
    # Map (day, subject, grade) -> list of (start_time, end_time, slot_number, homeroom)
    # Fallback if homeroom doesn't match
    subject_grade_map = {}
    # Map (day, subject) -> list of (start_time, end_time, slot_number, grade, homeroom)
    # Fallback if grade/homeroom don't match
    subject_time_map = {}
    # Map (day, slot_number, subject) -> (start_time, end_time) for exact slot matches
    exact_map = {}

    def normalize_value(val):
        """Normalize a value for comparison (lowercase, strip, handle None)."""
        if val is None:
            return None
        return str(val).lower().strip() if str(val).strip() else None

    for entry in schedule:
        day = entry.day_of_week.lower()
        slot_num = entry.slot_number
        subject = normalize_value(entry.subject)
        grade = normalize_value(entry.grade)
        homeroom = normalize_value(entry.homeroom)

        # Exact match map (day, slot_number, subject)
        exact_map[(day, slot_num, subject)] = (entry.start_time, entry.end_time)

        # Full match: (day, subject, grade, homeroom)
        key_full = (day, subject, grade, homeroom)
        if key_full not in full_match_map:
            full_match_map[key_full] = []
        full_match_map[key_full].append((entry.start_time, entry.end_time, slot_num))

        # Subject + Grade match: (day, subject, grade)
        key_sg = (day, subject, grade)
        if key_sg not in subject_grade_map:
            subject_grade_map[key_sg] = []
        subject_grade_map[key_sg].append(
            (entry.start_time, entry.end_time, slot_num, homeroom)
        )

        # Subject only match: (day, subject)
        key_subj = (day, subject)
        if key_subj not in subject_time_map:
            subject_time_map[key_subj] = []
        subject_time_map[key_subj].append(
            (entry.start_time, entry.end_time, slot_num, grade, homeroom)
        )

    # Sort all map entries by time
    for key in full_match_map:
        full_match_map[key].sort(key=lambda x: x[0])
    for key in subject_grade_map:
        subject_grade_map[key].sort(key=lambda x: x[0])
    for key in subject_time_map:
        subject_time_map[key].sort(key=lambda x: x[0])

    for day_name, day_data in lesson_json["days"].items():
        day_lower = day_name.lower()
        slots = day_data.get("slots", [])

        if not isinstance(slots, list):
            if isinstance(slots, dict):
                slots = list(slots.values())
            else:
                continue

        # Track which schedule entries we've already used for each subject
        # This ensures we match slots to schedule entries in chronological order
        used_entries = {}  # (day, subject) -> list of used indices

        def get_times(slot_dict, slot_index_in_day):
            """Get times for a slot, trying multiple matching strategies.

            Tries matching in order of specificity:
            1. Exact match by (day, slot_number, subject)
            2. Full match by (day, subject, grade, homeroom)
            3. Match by (day, subject, grade)
            4. Match by (day, subject) - fallback
            """
            slot_num = slot_dict.get("slot_number")
            subject = normalize_value(slot_dict.get("subject"))
            grade = normalize_value(slot_dict.get("grade"))
            homeroom = normalize_value(slot_dict.get("homeroom"))

            if not subject:
                return None

            # Strategy 1: Exact match by (day, slot_number, subject)
            if slot_num is not None:
                times = exact_map.get((day_lower, slot_num, subject))
                if times:
                    return times

            # Strategy 2: Full match by (day, subject, grade, homeroom)
            key_full = (day_lower, subject, grade, homeroom)
            candidates = full_match_map.get(key_full, [])
            if candidates:
                key = key_full
                if key not in used_entries:
                    used_entries[key] = []
                existing_time = slot_dict.get("start_time")
                if existing_time:
                    for idx, (start_time, end_time, _) in enumerate(candidates):
                        if start_time == existing_time and idx not in used_entries[key]:
                            used_entries[key].append(idx)
                            return (start_time, end_time)
                for idx, (start_time, end_time, _) in enumerate(candidates):
                    if idx not in used_entries[key]:
                        used_entries[key].append(idx)
                        return (start_time, end_time)

            # Strategy 3: Match by (day, subject, grade)
            if grade:
                key_sg = (day_lower, subject, grade)
                candidates = subject_grade_map.get(key_sg, [])
                if candidates:
                    key = key_sg
                    if key not in used_entries:
                        used_entries[key] = []
                    existing_time = slot_dict.get("start_time")
                    if existing_time:
                        for idx, (start_time, end_time, _, _) in enumerate(candidates):
                            if (
                                start_time == existing_time
                                and idx not in used_entries[key]
                            ):
                                used_entries[key].append(idx)
                                return (start_time, end_time)
                    for idx, (start_time, end_time, _, _) in enumerate(candidates):
                        if idx not in used_entries[key]:
                            used_entries[key].append(idx)
                            return (start_time, end_time)

            # Strategy 4: Match by (day, subject) - fallback
            key_subj = (day_lower, subject)
            candidates = subject_time_map.get(key_subj, [])
            if not candidates:
                return None

            if key_subj not in used_entries:
                used_entries[key_subj] = []

            existing_time = slot_dict.get("start_time")
            if existing_time:
                for idx, (start_time, end_time, _, _, _) in enumerate(candidates):
                    if (
                        start_time == existing_time
                        and idx not in used_entries[key_subj]
                    ):
                        used_entries[key_subj].append(idx)
                        return (start_time, end_time)

            for idx, (start_time, end_time, _, _, _) in enumerate(candidates):
                if idx not in used_entries[key_subj]:
                    used_entries[key_subj].append(idx)
                    return (start_time, end_time)

            return None

        # Sort slots by their current start_time (if available) or slot_number
        # This ensures we match them to schedule entries in the right order
        def get_slot_sort_key(slot):
            start_time = slot.get("start_time", "")
            slot_num = slot.get("slot_number", 0)
            try:
                slot_num = int(slot_num)
            except (ValueError, TypeError):
                slot_num = 0

            if start_time:
                try:
                    parts = str(start_time).split(":")
                    if len(parts) >= 2:
                        time_sort = int(parts[0]) * 60 + int(parts[1])
                        return (0, time_sort, slot_num)
                except (ValueError, TypeError):
                    pass
            return (1, 0, slot_num)

        # Sort slots to match them in chronological order
        sorted_slots = sorted(
            [s for s in slots if isinstance(s, dict)], key=get_slot_sort_key
        )

        # Now match each slot to schedule entries
        for slot in sorted_slots:
            times = get_times(slot, None)
            if times:
                slot["start_time"] = times[0]
                slot["end_time"] = times[1]

        # Re-sort slots after updating times to ensure chronological order
        final_slots = sort_slots(sorted_slots)

        # Update the original slots list with correctly sorted order
        # Always update day_data["slots"] with enriched and sorted slots
        day_data["slots"] = final_slots
