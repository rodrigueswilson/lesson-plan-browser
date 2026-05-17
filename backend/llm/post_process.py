"""
Post-processing for LLM lesson JSON (e.g. punctuation normalization).
"""

from typing import Any, Dict

from backend.telemetry import logger
from backend.wida_eld_format import (
    is_no_school_wida_objective,
    validate_and_normalize_wida_objective,
)


def normalize_wida_objectives_in_lesson_json(
    lesson_json: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Normalize wida_objective ELD codes in all days (Function/Domain slash repair).

    Mutates and returns lesson_json. Skips missing objectives and no-school values.
    On validation failure, logs and leaves the value unchanged (legacy safety net).
    """
    if not lesson_json or "days" not in lesson_json:
        return lesson_json

    days = lesson_json["days"]
    if not isinstance(days, dict):
        return lesson_json

    for day_name, day_data in days.items():
        if not isinstance(day_data, dict):
            continue
        objective = day_data.get("objective")
        if not isinstance(objective, dict):
            continue
        wida = objective.get("wida_objective")
        if not wida or not isinstance(wida, str):
            continue
        if is_no_school_wida_objective(wida):
            continue
        try:
            objective["wida_objective"] = validate_and_normalize_wida_objective(wida)
        except ValueError as exc:
            logger.warning(
                "wida_objective_normalization_skipped",
                extra={"day": day_name, "error": str(exc)},
            )

    return lesson_json


def normalize_sentence_frame_punctuation(lesson_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize sentence frame punctuation based on frame_type.
    - frame/stem: ends with "."
    - open_question: ends with "?"

    Mutates and returns lesson_json. Acts as a safety net if LLM misses prompt instructions.
    """
    if not lesson_json or "days" not in lesson_json:
        return lesson_json

    days = lesson_json["days"]
    for day_name, day_data in days.items():
        if not isinstance(day_data, dict):
            continue

        frames = day_data.get("sentence_frames")
        if not isinstance(frames, list):
            continue

        for frame in frames:
            if not isinstance(frame, dict):
                continue

            frame_type = frame.get("frame_type")

            for lang in ["english", "portuguese"]:
                text = frame.get(lang)
                if not text or not isinstance(text, str):
                    continue

                text = text.strip()
                if not text:
                    continue

                if frame_type in ["frame", "stem"]:
                    if not text.endswith("."):
                        if text[-1] in ["?", "!", ":", ";"]:
                            text = text[:-1] + "."
                        else:
                            text = text + "."
                elif frame_type == "open_question":
                    if not text.endswith("?"):
                        if text[-1] in [".", "!", ":", ";"]:
                            text = text[:-1] + "?"
                        else:
                            text = text + "?"

                frame[lang] = text

    return lesson_json
