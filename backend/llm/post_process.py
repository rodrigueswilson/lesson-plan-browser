"""
Post-processing for LLM lesson JSON (e.g. punctuation normalization).
"""

from typing import Any, Dict


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
