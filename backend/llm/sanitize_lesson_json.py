"""
Sanitize lesson_json string values for XML/encoding safety.

Recursively walks lesson_json and removes NULL bytes and control characters
from every string value, using the same rules as tools.docx_renderer.style.sanitize_xml_text.
Preserves valid Unicode (e.g. accented characters, apostrophes).
"""

from typing import Any, Dict, List

from tools.docx_renderer.style import sanitize_xml_text


def sanitize_lesson_json_strings(lesson_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitize all string values in lesson_json in place.

    Removes NULL bytes and XML-invalid control characters from every string.
    Does not alter keys or structure. Returns the same dict (mutated).

    Args:
        lesson_json: Lesson plan dict (may contain nested dicts, lists, strings).

    Returns:
        The same lesson_json with all string values sanitized.
    """
    if not lesson_json:
        return lesson_json

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    obj[key] = sanitize_xml_text(value)
                else:
                    walk(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str):
                    obj[i] = sanitize_xml_text(item)
                else:
                    walk(item)

    walk(lesson_json)
    return lesson_json
