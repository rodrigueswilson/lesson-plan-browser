"""
Shared day-label patterns for Grade 2+ Science curriculum DOCX tables.

Used by diagnose_science_g2_unit1_tables.py and science_lesson_tables.py (SSOT).
"""

from __future__ import annotations

import re
from typing import List, Set

# Flexible day headers: Day 1:, Days 2&3:, Days 4-7:, Days 10 & 11:, Days 1 & 2:, etc.
DAY_LABEL_RE = re.compile(
    r"(?i)\b("
    r"day\s+\d+"
    r"|"
    r"days\s+(?:\d+\s*[-–]\s*\d+|\d+\s*&\s*\d+|\d+\s+&\s+\d+)"
    r")\s*:?",
)

# Paragraph-anchored: optional bullet + day label + optional colon + rest of line
_PARA_DAY_PREFIX = re.compile(
    r"(?i)^(?:(?:\u2022|•|\*)\s*)?("
    r"day\s+\d+"
    r"|"
    r"days\s+(?:\d+\s*[-–]\s*\d+|\d+\s*&\s*\d+|\d+\s+&\s+\d+)"
    r")\s*:?\s*(.*)$",
    re.DOTALL,
)


def day_labels_in_text(text: str) -> List[str]:
    """Unique day labels in first-seen document order."""
    seen: Set[str] = set()
    ordered: List[str] = []
    for m in DAY_LABEL_RE.finditer(text or ""):
        raw = m.group(1).strip()
        key = raw.lower()
        if key not in seen:
            seen.add(key)
            ordered.append(raw)
    return ordered


def normalize_day_label_key(label: str) -> str:
    s = (label or "").strip()
    s = re.sub(r"\s*:\s*$", "", s)
    return re.sub(r"\s+", " ", s)


def split_paragraph_on_day_prefix(
    para_json: dict,
) -> tuple[str | None, dict | None]:
    """
    If paragraph opens with a day label, return (label, remainder_paragraph_json_or_none).
    Remainder is None if the whole line was only the label.
    """
    text = (para_json.get("text") or "").strip()
    if not text:
        return None, None
    m = _PARA_DAY_PREFIX.match(text)
    if not m:
        return None, None
    label = normalize_day_label_key(m.group(1))
    rest = (m.group(2) or "").strip()
    if not rest:
        return label, None
    out = dict(para_json)
    out["text"] = rest
    return label, out
