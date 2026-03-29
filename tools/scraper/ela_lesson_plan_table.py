"""
Detect and parse ELA per-lesson detailed plan tables from DOCX table JSON.

Typical layout (Grade 2+ teacher guide tabs):
- Row 0: "Lesson N: <title>" (often column 0 only).
- Row 1: headers "Learning Intention" | "Success Criteria".
- Row 2: body cells for those columns.
- Section rows for NJSLS Standards, Key Instructional Practices (then sub-row with
  key questions | instructional routines), Vocabulary | Instructional Resources,
  a large procedures / engagement / DIT cell, and Differentiation | Addressing Misconceptions.

Used by table_extractor.ingest_to_curriculum for subject ELA. Parsed tables are still
flattened into the semantic stream; this module adds structured JSON on the lesson row.
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Optional, Tuple

# Ordered paragraph-level section labels inside the large "procedures" cell.
_PROCEDURE_SECTIONS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("anticipatory_set_html", ("anticipatory set:",)),
    ("learning_procedures_html", ("learning procedures:",)),
    ("engagement_with_content_html", ("engagement with the content",)),
    ("daily_instructional_task_html", ("daily instructional task:",)),
)


def _norm(s: str) -> str:
    t = (s or "").lower().strip()
    t = re.sub(r"\s+", " ", t)
    return t


def _cell_plain(content: List[Dict[str, Any]]) -> str:
    parts: List[str] = []

    def walk(items: List[Dict[str, Any]]) -> None:
        for item in items:
            if item.get("type") == "paragraph":
                parts.append(item.get("text") or "")
            elif item.get("type") == "table":
                for row in item.get("rows", []):
                    for cell in row.get("cells", []):
                        walk(cell.get("content", []))

    walk(content)
    return "\n".join(p for p in parts if p).strip()


def _row_plain_cells(row: Dict[str, Any]) -> Tuple[str, str]:
    cells = row.get("cells") or []
    if not cells:
        return "", ""
    t0 = _cell_plain(cells[0].get("content", []))
    if len(cells) >= 2:
        t1 = _cell_plain(cells[1].get("content", []))
    else:
        t1 = ""
    return t0, t1


def _merge_row_html(row: Dict[str, Any], json_to_html: Callable[[List[Dict[str, Any]]], str]) -> str:
    chunks: List[str] = []
    for cell in row.get("cells") or []:
        h = json_to_html(cell.get("content", []))
        if h and h.strip():
            chunks.append(h.strip())
    return "\n".join(chunks)


def _parse_lesson_title_row(row: Dict[str, Any]) -> Tuple[Optional[int], str]:
    cells = row.get("cells") or []
    combined = " ".join(_cell_plain(c.get("content", [])) for c in cells).strip()
    m = re.match(
        r"^\s*Lesson\s+(\d+)\s*(?:[:\.\-]\s*(.+))?$",
        combined,
        re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return None, ""
    rest = (m.group(2) or "").strip()
    title = re.sub(r"\s+", " ", rest) if rest else ""
    return int(m.group(1)), title


def _cell_top_paragraphs(content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [x for x in content if x.get("type") == "paragraph"]


def _bucket_procedure_paragraphs(
    content: List[Dict[str, Any]],
    json_to_html: Callable[[List[Dict[str, Any]]], str],
) -> Dict[str, str]:
    paras = _cell_top_paragraphs(content)
    if not paras:
        return {}

    buckets: Dict[str, List[Dict[str, Any]]] = {key: [] for key, _ in _PROCEDURE_SECTIONS}
    preamble: List[Dict[str, Any]] = []
    current: Optional[str] = None

    for p in paras:
        pt = (p.get("text") or "").strip()
        pt_low = pt.lower()
        matched: Optional[str] = None
        for key, prefixes in _PROCEDURE_SECTIONS:
            for pref in prefixes:
                if pt_low.startswith(pref):
                    matched = key
                    break
            if matched:
                break
        if matched:
            current = matched
            buckets[current].append(p)
        elif current:
            buckets[current].append(p)
        else:
            preamble.append(p)

    out: Dict[str, str] = {}
    if preamble:
        h = json_to_html(preamble)
        if h.strip():
            out["procedures_preamble_html"] = h
    for key, _ in _PROCEDURE_SECTIONS:
        block = buckets[key]
        if block:
            h = json_to_html(block)
            if h.strip():
                out[key] = h
    return out


def is_ela_lesson_plan_table(table_json: Dict[str, Any]) -> bool:
    """True if the table matches the ELA detailed lesson plan grid (Lesson N: title + LI/SC headers)."""
    rows = table_json.get("rows") or []
    if len(rows) < 4:
        return False
    lnum, _title = _parse_lesson_title_row(rows[0])
    if lnum is None:
        return False
    r1 = rows[1].get("cells") or []
    if len(r1) < 2:
        return False
    h0 = _norm(_cell_plain(r1[0].get("content", [])))
    h1 = _norm(_cell_plain(r1[1].get("content", [])))
    if "learning intention" not in h0:
        return False
    if "success criteria" not in h1:
        return False
    return True


def parse_ela_lesson_plan_table(
    table_json: Dict[str, Any],
    json_to_html: Callable[[List[Dict[str, Any]]], str],
) -> Optional[Dict[str, Any]]:
    """
    Parse a detected ELA lesson plan table into a JSON-serializable dict.
    Returns None if the title row cannot be parsed.
    """
    rows = table_json.get("rows") or []
    if len(rows) < 3:
        return None

    lesson_number, lesson_title = _parse_lesson_title_row(rows[0])
    if lesson_number is None:
        return None

    out: Dict[str, Any] = {
        "schema_version": 1,
        "lesson_number": lesson_number,
        "lesson_title": lesson_title,
    }

    i = 1
    # Learning Intention | Success Criteria
    if i < len(rows):
        t0, t1 = _row_plain_cells(rows[i])
        if "learning intention" in _norm(t0) and "success criteria" in _norm(t1):
            i += 1
            if i < len(rows):
                cells = rows[i].get("cells") or []
                if len(cells) >= 2:
                    out["learning_intention_html"] = json_to_html(cells[0].get("content", []))
                    out["success_criteria_html"] = json_to_html(cells[1].get("content", []))
                i += 1

    while i < len(rows):
        t0, t1 = _row_plain_cells(rows[i])
        n0, n1 = _norm(t0), _norm(t1)
        cells = rows[i].get("cells") or []

        def _second_empty() -> bool:
            return len(t1.strip()) == 0

        # Section: NJSLS Standards (short label row + body row, or one merged cell)
        if n0.startswith("njsls standards"):
            short_label = len(t0.strip()) < 50 and _second_empty()
            if short_label and i + 1 < len(rows):
                i += 1
                out["njsls_standards_html"] = _merge_row_html(rows[i], json_to_html)
                i += 1
            else:
                out["njsls_standards_html"] = json_to_html(cells[0].get("content", []))
                i += 1
            continue

        # Body-only standards row: some lessons omit the "NJSLS Standards" label row (empty merged
        # row above) and start directly with "Priority Standards:" in a full-width cell.
        if (
            "njsls_standards_html" not in out
            and len(cells) >= 1
            and _second_empty()
            and len(t0.strip()) > 8
        ):
            head = n0[:100]
            if head.startswith("priority standard") or (
                "priority standard" in head[:50] and not n0.startswith("key instructional")
            ):
                out["njsls_standards_html"] = json_to_html(cells[0].get("content", []))
                i += 1
                continue

        # Section: Key Instructional Practices (label) then sub-row
        if n0.startswith("key instructional practices") and len(t0) < 120 and _second_empty():
            i += 1
            if i < len(rows):
                c2 = rows[i].get("cells") or []
                if len(c2) >= 2:
                    out["key_questions_html"] = json_to_html(c2[0].get("content", []))
                    out["instructional_routines_assessments_html"] = json_to_html(c2[1].get("content", []))
                i += 1
            continue

        # Differentiation | Addressing Misconceptions
        if "differentiation" in n0[:80] and "addressing misconceptions" in n1[:120]:
            if len(cells) >= 2:
                out["differentiation_html"] = json_to_html(cells[0].get("content", []))
                out["addressing_misconceptions_html"] = json_to_html(cells[1].get("content", []))
            i += 1
            continue

        # Large procedures / engagement cell (starts with Anticipatory Set, etc.)
        if cells and (
            n0.startswith("anticipatory set")
            or n0.startswith("learning procedures")
            or n0.startswith("engagement with the content")
        ):
            c0 = cells[0].get("content", [])
            out.update(_bucket_procedure_paragraphs(c0, json_to_html))
            combined = json_to_html(c0)
            if combined.strip():
                out["procedures_full_html"] = combined
            i += 1
            continue

        # Vocabulary | Instructional Resources (labels in the same row as content)
        if n0.startswith("vocabulary") and "instructional resources" in n1:
            if len(cells) >= 2:
                out["vocabulary_cell_html"] = json_to_html(cells[0].get("content", []))
                out["instructional_resources_cell_html"] = json_to_html(cells[1].get("content", []))
            i += 1
            continue

        i += 1

    return out
