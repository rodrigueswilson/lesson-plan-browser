"""
Detect and parse the ELA unit-level "Summary of Key Learning" matrix from table JSON.

Table shape (SSOT strings in tools.scraper.subject_config.SubjectConfig.ELA_SUMMARY_TABLE):
- Row 0: one logical title cell (merged) containing "Summary of Key Learning".
- Row 1: four headers — Lesson | Learning Intentions and Success Criteria |
         Daily Instructional Task | Content and Learning Strategies.
- Row 2+: one row per lesson; column A = lesson number; B/C/D = rich text.

Used by table_extractor.ingest_to_curriculum for subject ELA only; the matched table is
omitted from the semantic stream to avoid duplicating this content in procedure_html.
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List

from tools.scraper.cell_content_format import split_leading_bold_title_and_rest_from_cell
from tools.scraper.subject_config import SubjectConfig


def _norm(s: str) -> str:
    t = (s or "").lower().strip()
    t = re.sub(r"\s+", " ", t)
    return t


def _clean_header(s: str) -> str:
    return _norm(s).rstrip(":").strip()


def _cell_plain_text(content: List[Dict[str, Any]]) -> str:
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


def _cell_paragraphs(content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Top-level paragraph dicts only (no recursion into nested tables)."""
    return [x for x in content if x.get("type") == "paragraph"]


def _header_cell_matches(cell_text: str, expected: str) -> bool:
    c, e = _clean_header(cell_text), _clean_header(expected)
    if not e:
        return False
    if c == e:
        return True
    if e in ("lesson",):
        return c == e or c.startswith(e + " ")
    return c.startswith(e) or e in c


def is_summary_key_learning_table(table_json: Dict[str, Any]) -> bool:
    """True if this table matches the ELA Summary of Key Learning layout."""
    rows = table_json.get("rows") or []
    if len(rows) < 3:
        return False

    meta = SubjectConfig.ELA_SUMMARY_TABLE
    title_needle = meta["title"]
    expected_headers: List[str] = meta["headers"]

    r0_cells = rows[0].get("cells") or []
    if not r0_cells:
        return False

    texts0 = [_cell_plain_text(c.get("content", [])) for c in r0_cells]
    non_empty0 = [t for t in texts0 if t.strip()]
    title_ok = False
    if len(non_empty0) == 1:
        title_ok = _clean_header(non_empty0[0]) == _clean_header(title_needle) or title_needle in _norm(
            non_empty0[0]
        )
    elif texts0 and texts0[0].strip():
        first, rest = texts0[0], texts0[1:]
        title_ok = (
            _clean_header(first) == _clean_header(title_needle) or title_needle in _norm(first)
        ) and all(not (t or "").strip() for t in rest)

    if not title_ok:
        return False

    r1_cells = rows[1].get("cells") or []
    if len(r1_cells) < 4:
        return False

    for i, exp in enumerate(expected_headers):
        ct = _cell_plain_text(r1_cells[i].get("content", []))
        if not _header_cell_matches(ct, exp):
            return False

    return True


def _normalize_plain_for_standards_findall(plain: str) -> str:
    """
    Collapse stray spaces around dots in code-like text (e.g. 'L .VL.2..2' from Word)
    so standards_summary_mentions can match without widening regex false positives.
    """
    if not plain:
        return plain
    t = plain
    for _ in range(8):
        nt = re.sub(r"([A-Za-z0-9])\s+\.", r"\1.", t)
        nt = re.sub(r"\.\s+([A-Za-z0-9])", r".\1", nt)
        if nt == t:
            break
        t = nt
    t = re.sub(r"(\d)\.{2,}(\d)", r"\1.\2", t)
    return t


def _split_learning_intention_success(plain: str) -> tuple[str, str]:
    """Split column B on Learning Intention(s): and Success Criteria: labels."""
    text = (plain or "").strip()
    if not text:
        return "", ""

    li_m = re.search(r"(?i)learning\s+intentions?\s*:", text)
    sc_m = re.search(r"(?i)success\s+criteria\s*:", text)

    if not li_m:
        return "", text

    li_start = li_m.end()
    if sc_m and sc_m.start() > li_m.start():
        intention = text[li_start : sc_m.start()].strip()
        criteria = text[sc_m.end() :].strip()
        return intention, criteria

    intention = text[li_start:].strip()
    return intention, ""


def _daily_task_title_body_with_fallback(
    content: List[Dict[str, Any]],
    htmlize: Callable[[List[Dict[str, Any]]], str],
) -> tuple[str, str]:
    """Column C: bold-based title + body, or first plain line as title if no bold title."""
    title, body = split_leading_bold_title_and_rest_from_cell(content, htmlize)
    if title.strip():
        return title.strip(), body

    paras = _cell_paragraphs(content)
    plain = _cell_plain_text(content)
    full_html = htmlize(paras) if paras else ""
    if not plain.strip():
        return "", full_html

    lines = [ln.strip() for ln in plain.splitlines() if ln.strip()]
    if not lines:
        return "", full_html

    first = lines[0]
    if len(first) > 200:
        first = first[:200].rstrip() + "..."
    if not body.strip() and len(paras) > 1:
        return first, htmlize(paras[1:])
    if not body.strip() and len(paras) == 1 and len(lines) > 1:
        rest_plain = "\n".join(lines[1:])
        return first, f"<p>{rest_plain}</p>" if rest_plain else full_html
    return first, full_html if not body.strip() else body


def parse_summary_rows(
    table_json: Dict[str, Any],
    htmlize: Callable[[List[Dict[str, Any]]], str],
    standards_mention_pattern: re.Pattern[str],
) -> Dict[int, Dict[str, Any]]:
    """
    Parse data rows (from index 2) into lesson_number -> summary payload dicts.
    Values are suitable for JSON serialization (schema_version added by caller).
    """
    out: Dict[int, Dict[str, Any]] = {}
    rows = table_json.get("rows") or []
    for row in rows[2:]:
        cells = row.get("cells") or []
        if len(cells) < 4:
            continue

        lesson_txt = _cell_plain_text(cells[0].get("content", []))
        m = re.search(r"\d+", lesson_txt)
        if not m:
            continue
        lesson_num = int(m.group(0))

        b_content = cells[1].get("content", [])
        c_content = cells[2].get("content", [])
        d_content = cells[3].get("content", [])

        plain_b = _cell_plain_text(b_content)
        intention, criteria = _split_learning_intention_success(plain_b)
        learning_html = htmlize(_cell_paragraphs(b_content)) if b_content else ""

        daily_title, daily_body = _daily_task_title_body_with_fallback(c_content, htmlize)
        content_html = htmlize(d_content) if d_content else ""
        plain_d = _cell_plain_text(d_content)
        plain_d_norm = _normalize_plain_for_standards_findall(plain_d)
        mentions = list(dict.fromkeys(standards_mention_pattern.findall(plain_d_norm)))

        out[lesson_num] = {
            "learning_intention": intention,
            "success_criteria": criteria,
            "learning_intentions_success_html": learning_html,
            "daily_task_title": daily_title,
            "daily_task_body": daily_body,
            "content_and_strategies": content_html,
            "standards_mentions": mentions,
        }
    return out
