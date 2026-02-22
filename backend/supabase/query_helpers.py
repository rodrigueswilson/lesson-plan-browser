"""Serialization, deserialization, and row hydration for Supabase payloads."""

import json
from datetime import datetime
from typing import Any, Dict, Optional


def normalize_day(day: Optional[str]) -> Optional[str]:
    """Normalize day_of_week to lowercase."""
    if isinstance(day, str):
        return day.lower()
    return day


def serialize_json_field(value: Any) -> Any:
    """Serialize dict/list to JSON string for storage."""
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return value


def deserialize_json_field(value: Any) -> Any:
    """Deserialize JSON string from storage to dict/list."""
    if value is None or isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return value


LESSON_STEP_JSON_KEYS = ("hidden_content", "sentence_frames", "materials_needed", "vocabulary_cognates")


def prepare_lesson_step_payload(step_data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare lesson step dict for insert/update: normalize day and serialize JSON fields."""
    payload = step_data.copy()
    if "day_of_week" in payload:
        payload["day_of_week"] = normalize_day(payload.get("day_of_week"))
    for key in LESSON_STEP_JSON_KEYS:
        if key in payload:
            payload[key] = serialize_json_field(payload.get(key))
    return payload


def hydrate_lesson_step_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Hydrate lesson step row from DB: normalize day and deserialize JSON fields."""
    hydrated = payload.copy()
    hydrated["day_of_week"] = normalize_day(hydrated.get("day_of_week"))
    for key in LESSON_STEP_JSON_KEYS:
        hydrated[key] = deserialize_json_field(hydrated.get(key))
    return hydrated


def hydrate_session_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    """Hydrate lesson_mode_sessions row: booleans, adjusted_durations JSON, datetime fields."""
    for bool_field in ["is_running", "is_paused", "is_synced"]:
        if bool_field in row and isinstance(row[bool_field], int):
            row[bool_field] = bool(row[bool_field])

    if "adjusted_durations" in row and isinstance(row["adjusted_durations"], str):
        try:
            row["adjusted_durations"] = json.loads(row["adjusted_durations"])
        except (json.JSONDecodeError, TypeError):
            row["adjusted_durations"] = None

    for dt_field in ["timer_start_time", "session_start_time", "last_updated", "ended_at"]:
        if dt_field in row and row[dt_field] is not None and isinstance(row[dt_field], str):
            try:
                row[dt_field] = datetime.fromisoformat(
                    row[dt_field].replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                pass

    return row
