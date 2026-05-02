"""
Detect instructional vs non-instructional weekdays from extracted primary-plan text.

Used to derive per-slot available_days without treating exam/testing or empty cells
as reasons to generate five full bilingual lessons.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from tools.docx_parser.no_school import is_day_no_school

NON_INSTRUCTIONAL_UNIT_LESSON = "Non-instructional (assessment)"


def _day_text_for_instructional_inference(day_content: Any) -> str:
    """Build text used to classify instructional vs assessment for one weekday.

    Prefer Unit/Lesson and Objective-style columns (matches extractors in
    slot_flow_extract.get_original_unit_lessons_and_objectives) so district notes,
    testing banners, or extra columns do not override a normal lesson line.

    If no such columns have text, fall back to joining all cell values (legacy).
    """
    if not isinstance(day_content, dict):
        return str(day_content) if day_content is not None else ""

    primary_parts: List[str] = []
    for label, text in day_content.items():
        if text is None or not str(text).strip():
            continue
        label_lower = str(label).lower().strip()
        if (
            ("unit" in label_lower and ("lesson" in label_lower or "module" in label_lower))
            or label_lower.startswith("unit")
            or label_lower.startswith("lesson")
            or label_lower.startswith("objective")
        ):
            primary_parts.append(str(text).strip())

    if primary_parts:
        return " ".join(primary_parts)

    return " ".join(
        str(v).strip() for v in day_content.values() if v is not None and str(v).strip()
    )

# Phrases indicating assessments / testing (school open, no regular lesson).
_ASSESSMENT_PATTERNS = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bstaar\b",
        r"\bstate\s+(test|testing|assessment|exam)\b",
        r"\bstandardized\s+test\b",
        r"\bbenchmark(\s+(test|assessment))?\b",
        r"\bmap\s+(test|testing)\b",
        r"\bnwea\b",
        r"\biready\b",
        r"\bstudents?\s+(are\s+)?testing\b",
        r"\btesting\s+days?\b",
        r"\bexam\s+days?\b",
        r"\btest\s+days?\b",
        r"\bmock\s+staar\b",
        r"\bdistrict\s+assessment\b",
        r"\bnj[-\s]?sla\b",
        r"\bexam\s+period\b",
        r"\bmid[-\s]?year\s+exam\b",
    )
)

# Cell is only the word "exam" or "exam day" (avoids matching "exam" inside long lesson prose).
_STANDALONE_EXAM_OR_EXAM_DAY = re.compile(
    r"^\s*exam(?:\s+day)?\s*$",
    re.IGNORECASE,
)


def substantive_day_text(day_text: str) -> bool:
    """True if joined cell text looks like real lesson content, not placeholders."""
    if not day_text or not str(day_text).strip():
        return False
    stripped = str(day_text).strip()
    lowered = stripped.lower()
    if lowered in ("-", "—", "n/a", "na", ".", "..", "none", "tbd"):
        return False
    words = re.findall(r"[A-Za-z0-9']{2,}", stripped)
    if len(words) >= 2:
        return True
    return len(words) >= 1 and len(stripped) >= 15


def is_testing_or_assessment_day(day_text: str) -> bool:
    """True when primary text indicates assessments rather than a teachable lesson."""
    if not day_text or not str(day_text).strip():
        return False
    text = str(day_text).strip()
    if _STANDALONE_EXAM_OR_EXAM_DAY.match(text):
        return True
    return any(p.search(text) for p in _ASSESSMENT_PATTERNS)


def is_instructional_lesson_day(day_text: str) -> bool:
    """
    True if this weekday column should receive bilingual lesson generation.

    No-school and assessment markers are checked before the substantive-text gate
    so short labels (e.g. NJ-SLA, exam) still classify correctly.
    """
    if not day_text or not str(day_text).strip():
        return False
    text = str(day_text).strip()
    if text.lower() in ("-", "—", "n/a", "na", ".", "..", "none", "tbd"):
        return False
    if is_day_no_school(text):
        return False
    if is_testing_or_assessment_day(text):
        return False
    if not substantive_day_text(text):
        return False
    return True


def infer_instructional_weekdays_from_table_content(
    table_content: Dict[str, Any],
) -> List[str]:
    """Return lowercase weekdays with instructional primary content.

    ``All Days`` keys keep legacy behavior: always ``[\"monday\"]``.
    """
    weekdays = ("monday", "tuesday", "wednesday", "thursday", "friday")
    available: List[str] = []

    for day, day_content in table_content.items():
        day_lower = day.lower().strip()
        if day_lower == "all days":
            # Match legacy extractors: single-lesson docs map to Monday-only generation.
            return ["monday"]

        if day_lower in weekdays:
            day_text = _day_text_for_instructional_inference(day_content)
            lowered = day_text.strip().lower()
            if lowered in ("no school", "n/a", ""):
                continue
            if is_instructional_lesson_day(day_text):
                available.append(day_lower)

    return available
