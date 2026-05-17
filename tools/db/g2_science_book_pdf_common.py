"""
Shared helpers for Grade 2 Inspire student workbook PDF alignment (seed + ingest).

Not imported by the FastAPI app at runtime; tools/db scripts only.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Must match seed_g2_science_book_lesson_supplement._SOURCE_LABEL for traceability.
SOURCE_PDF_LABEL = "Inspire_G2_StudentWorkbook_9780021344871"

BOOK_EXTRACT_PARSER_VERSION = "g2_book_extract@v1"

_TITLE_ALIASES: Dict[str, Tuple[str, ...]] = {
    "Forest and Grasslands": ("Forests and Grasslands", "Forest and Grasslands"),
}


def norm_apostrophe(s: str) -> str:
    return (
        (s or "")
        .replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("`", "'")
    )


def title_variants(canonical_title: str) -> Tuple[str, ...]:
    t = norm_apostrophe(canonical_title).strip()
    extra = _TITLE_ALIASES.get(canonical_title, ())
    merged = (t,) + tuple(norm_apostrophe(x).strip() for x in extra if x)
    # unique preserve order
    seen: set[str] = set()
    out: List[str] = []
    for x in merged:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return tuple(out)


def head_limit_for_title(title: str) -> int:
    longest = max(title_variants(title), key=len) if title else ""
    return 520 if len(longest) >= 14 else 360


def sha256_text(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def load_page_overrides(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    arr = obj.get("overrides")
    if not isinstance(arr, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in arr:
        if isinstance(item, dict) and item.get("lesson_id"):
            out.append(item)
    return out


def override_lesson_for_page(page_number: int, overrides: Sequence[Dict[str, Any]]) -> Optional[str]:
    for o in overrides:
        lid = o.get("lesson_id")
        if not lid or not isinstance(lid, str):
            continue
        if o.get("page") == page_number:
            return lid
        ps, pe = o.get("page_start"), o.get("page_end")
        if isinstance(ps, int) and isinstance(pe, int) and ps <= page_number <= pe:
            return lid
    return None


def match_titles_in_head(
    page_text: str,
    lessons: Sequence[Tuple[str, str]],
) -> Tuple[Optional[str], str, int]:
    """
    Returns (lesson_id, confidence, ambiguous_flag_int).
    confidence: high | low | none
    ambiguous: 1 if two+ same-length winning matches
    """
    raw = norm_apostrophe(page_text)
    candidates: List[Tuple[str, str, int]] = []
    for lesson_id, title in lessons:
        best_len = 0
        best_variant = ""
        for v in title_variants(title):
            hl = head_limit_for_title(title)
            head = raw[:hl]
            if v and v in head:
                if len(v) > best_len:
                    best_len = len(v)
                    best_variant = v
        if best_len > 0:
            candidates.append((lesson_id, title, best_len))

    if not candidates:
        return None, "none", 0

    max_len = max(c[2] for c in candidates)
    winners = [c for c in candidates if c[2] == max_len]
    ambiguous = 1 if len(winners) > 1 else 0

    if ambiguous:
        winners.sort(key=lambda c: c[0])
        chosen = winners[0][0]
        conf = "low"
    else:
        chosen = winners[0][0]
        conf = "high" if max_len >= 14 else "low"

    return chosen, conf, ambiguous
