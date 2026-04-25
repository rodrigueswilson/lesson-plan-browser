"""
Science curriculum: overview tables with Learning intention / Success criteria by day label,
plus following THE LESSON IN ACTION tables merged per segment as ``lesson_in_action_html``.

Second pass during Science ``ingest_to_curriculum``; see ``merge_science_li_sc_into_lessons``.

Overview LI/SC grids: writers use a **wider** table early in the unit (many day bands, tall grid)
and a **compact** table in many later modules (fewer rows, sometimes only two day labels). Both
are accepted if they expose Learning intention + Success criteria columns and at least two day
labels in the flattened table text (see ``is_science_overview_li_sc_table``).

Writer template (each standalone day or multi-day block under **THE LESSON IN ACTION**):

1. **Lesson Opening** — 5E-aligned phase and guiding questions; strategies; activity list (e.g.
   Module Opener, Page Keeley Probe, phenomenon, inquiry); engagement formats; Do It Now in
   Science (and tips); Launch presentation (learning intentions, success criteria, phenomenon,
   essential question).
2. **During the Lesson** — procedures, vocabulary, reading, digital interactives, investigations;
   often sub-headings (e.g. carry out investigation, Talk About It). Grouped blocks may insert
   explicit **DAY N** callouts inside this section.
3. **Lesson Closing** — standardized routine: grouping formats, revisit essential question,
   interactive science wall, review LI/SC, exit tasks / reflection prompts.
4. **Online Learning Activities** — consistent digital-strategy bullets (collaboration tools,
   prep for in-class work, asynchronous discussion, self/peer assessment).

Ingest keeps the full table as ``lesson_in_action_html`` (lossless). Optional
``experimental_splits`` (opening / during / closing / online HTML) is filled only when
heading-based validation succeeds; see ``try_experimental_lesson_in_action_splits``.

Per-segment JSON (``schema_version`` 2): ``label``, ``learning_intention_html``,
``success_criteria_html``, ``brief_overview`` (Summary of Key Learning HTML when a matching
table appears in the capped pending window before the LI/SC overview),
``lesson_in_action_html``, optional ``experimental_splits``.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple

from docx import Document

import logging

from tools.scraper.science_day_labels import (
    DAY_LABEL_RE,
    day_labels_in_text,
    normalize_day_label_key,
    split_paragraph_on_day_prefix,
)

logger = logging.getLogger(__name__)

_LI_HEADER = re.compile(r"learning\s+intentions?", re.I)
_SC_HEADER = re.compile(r"success\s+criteria", re.I)
_LESSON_NUM_IN_TABLE = re.compile(r"(?i)lesson\s+(\d+)\s*:")
_ACTION = re.compile(r"lesson\s+in\s+action", re.I)
_STAGE1_UBD = re.compile(r"stage\s+1", re.I)
_DESIRED = re.compile(r"desired\s+results", re.I)
_SUMMARY_KEY_LEARNING_RE = re.compile(r"summary\s+of\s+key\s+learning", re.I)

# Tables seen since the prior overview (capped) — Science Summary of Key Learning precedes LI/SC grid.
_PENDING_CONTEXT_MAX = 28


def _xml_local_name(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def _flatten_cell_content(content: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for item in content or []:
        if item.get("type") == "paragraph":
            t = (item.get("text") or "").strip()
            if t:
                parts.append(t)
        elif item.get("type") == "table":
            parts.append(_flatten_table_plain(item))
    return " ".join(parts)


def _flatten_table_plain(table: Dict[str, Any]) -> str:
    chunks: List[str] = []
    for row in table.get("rows", []):
        for cell in row.get("cells", []):
            chunks.append(_flatten_cell_content(cell.get("content", [])))
    return " ".join(chunks)


def _table_shape(table: Dict[str, Any]) -> Tuple[int, int]:
    rows = table.get("rows") or []
    nrows = len(rows)
    ncols = max((len(r.get("cells") or []) for r in rows), default=0)
    return nrows, ncols


def _find_li_sc_header_row_and_cols(table: Dict[str, Any]) -> Optional[Tuple[int, int, int]]:
    # Headers often appear after title/overview rows (row 7+ in Grade 2 Science unit guides).
    for ri, row in enumerate((table.get("rows") or [])[:40]):
        cells = row.get("cells", [])
        li_col: Optional[int] = None
        sc_col: Optional[int] = None
        for ci, cell in enumerate(cells):
            low = re.sub(r"\s+", " ", _flatten_cell_content(cell.get("content", [])).lower())
            if _LI_HEADER.search(low) and not _SC_HEADER.search(low):
                li_col = ci
            if _SC_HEADER.search(low):
                sc_col = ci
        if li_col is not None and sc_col is not None and li_col != sc_col:
            return ri, li_col, sc_col
    return None


def is_science_overview_li_sc_table(table: Dict[str, Any]) -> bool:
    flat = _flatten_table_plain(table)
    if not flat.strip():
        return False
    if _ACTION.search(flat):
        return False
    if _STAGE1_UBD.search(flat) and _DESIRED.search(flat):
        return False
    if not (_LI_HEADER.search(flat) and _SC_HEADER.search(flat)):
        return False
    labels = day_labels_in_text(flat)
    nrows, ncols = _table_shape(table)
    if nrows < 5 or ncols < 1:
        return False
    # Template A: multi-column grids (at least 2 cols); usually 2+ day labels in flat text.
    if ncols >= 2:
        if len(labels) < 2:
            return False
        return True
    # Template B: single-column stack (Learning intention block, then Success criteria block).
    if len(labels) < 1:
        return False
    return True


def _doc_lesson_number_from_table(table: Dict[str, Any]) -> Optional[int]:
    flat = _flatten_table_plain(table)
    m = _LESSON_NUM_IN_TABLE.search(flat)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def _collect_column_elements(
    table: Dict[str, Any], col_idx: int, body_start_row: int
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for ri in range(body_start_row, len(table.get("rows") or [])):
        cells = table["rows"][ri].get("cells", [])
        if col_idx < len(cells):
            out.extend(cells[col_idx].get("content", []))
    return out


def _collect_all_first_column_elements(table: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in table.get("rows") or []:
        cells = row.get("cells") or []
        if cells:
            out.extend(cells[0].get("content") or [])
    return out


def _split_first_column_chain_by_li_sc_headers(
    chain: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Single-column overview tables: writers stack a Learning intention section, then
    Success criteria, each with day-labeled paragraphs.
    """
    li_els: List[Dict[str, Any]] = []
    sc_els: List[Dict[str, Any]] = []
    mode = "seek_li"
    for el in chain:
        if el.get("type") == "paragraph":
            t = (el.get("text") or "").strip()
            low = re.sub(r"\s+", " ", t.lower())
            if mode == "seek_li" and _LI_HEADER.search(low) and not _SC_HEADER.search(low):
                mode = "li"
                continue
            if mode in ("seek_li", "li") and _SC_HEADER.search(low):
                mode = "sc"
                continue
        if mode == "li":
            li_els.append(el)
        elif mode == "sc":
            sc_els.append(el)
    return li_els, sc_els


def _flatten_elements_text(elements: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for el in elements:
        if el.get("type") == "paragraph":
            t = (el.get("text") or "").strip()
            if t:
                parts.append(t)
        elif el.get("type") == "table":
            parts.append(_flatten_table_plain(el))
    return " ".join(parts)


def _split_elements_into_labeled_segments(
    elements: List[Dict[str, Any]],
    json_to_html: Callable[..., str],
) -> List[Tuple[str, str]]:
    segments: List[Tuple[str, str]] = []
    current_label: Optional[str] = None
    bucket: List[Dict[str, Any]] = []

    def emit() -> None:
        nonlocal bucket, current_label
        if current_label is None:
            return
        html = json_to_html(bucket).strip() if bucket else ""
        segments.append((current_label, html))
        bucket = []

    for el in elements:
        if el.get("type") == "paragraph":
            lab, rest = split_paragraph_on_day_prefix(el)
            if lab:
                if current_label is not None:
                    emit()
                current_label = lab
                bucket = []
                if rest is not None:
                    bucket.append(rest)
            else:
                if current_label is None:
                    current_label = ""
                bucket.append(el)
        else:
            if current_label is None:
                current_label = ""
            bucket.append(el)
    if current_label is not None:
        emit()

    merged: List[Tuple[str, str]] = []
    preamble_html = ""
    for lab, html in segments:
        if lab == "" and not merged:
            preamble_html = html
            continue
        if lab == "" and merged:
            prev_lab, prev_h = merged[-1]
            merged[-1] = (prev_lab, (prev_h + " " + html).strip())
            continue
        if preamble_html and not merged:
            html = (preamble_html + " " + html).strip()
            preamble_html = ""
        merged.append((lab, html))
    return [
        (a, b)
        for a, b in merged
        if a or (isinstance(b, str) and b.strip())
    ]


def _per_row_segments(
    table: Dict[str, Any],
    body_start: int,
    li_col: int,
    sc_col: int,
    day_col: int,
    json_to_html: Callable[..., str],
) -> List[Dict[str, str]]:
    rows = table.get("rows") or []
    out: List[Dict[str, str]] = []
    for ri in range(body_start, len(rows)):
        cells = rows[ri].get("cells", [])
        if max(li_col, sc_col, day_col) >= len(cells):
            continue
        day_txt = _flatten_cell_content(cells[day_col].get("content", []))
        labs = day_labels_in_text(day_txt)
        label = normalize_day_label_key(labs[0]) if labs else ""
        if not label:
            m = DAY_LABEL_RE.search(day_txt)
            if m:
                label = normalize_day_label_key(m.group(1))
        if not label:
            continue
        li_html = json_to_html(cells[li_col].get("content", [])).strip()
        sc_html = json_to_html(cells[sc_col].get("content", [])).strip()
        out.append(
            {
                "label": label,
                "learning_intention_html": li_html,
                "success_criteria_html": sc_html,
            }
        )
    return out


def _norm_key(label: str) -> str:
    return normalize_day_label_key(label).lower()


def _norm_day_for_match(label: str) -> str:
    x = normalize_day_label_key(label or "").lower()
    x = re.sub(r"\s+", "", x)
    x = x.replace("&", "and")
    x = x.replace("–", "-")
    return x


def _segment_matches_day(seg_label: str, action_day: str) -> bool:
    a = _norm_day_for_match(seg_label)
    b = _norm_day_for_match(action_day)
    if not a or not b:
        return False
    if a == b:
        return True
    return a.startswith(b) or b.startswith(a)


def is_science_summary_key_learning_table(table: Dict[str, Any]) -> bool:
    """
    Science unit guide: a table whose title mentions Summary of Key Learning, with day labels,
    and which is not the LI/SC overview grid or a THE LESSON IN ACTION block.
    """
    flat = _flatten_table_plain(table)
    if not _SUMMARY_KEY_LEARNING_RE.search(flat):
        return False
    if is_science_overview_li_sc_table(table):
        return False
    if _ACTION.search(flat):
        return False
    if len(day_labels_in_text(flat)) < 1:
        return False
    try:
        from tools.scraper.ela_summary_table import is_summary_key_learning_table

        if is_summary_key_learning_table(table):
            return False
    except Exception:
        pass
    return True


def extract_science_summary_brief_map(
    table: Dict[str, Any],
    doc_lesson_number: int,
    json_to_html: Callable[..., str],
) -> Dict[str, str]:
    """
    Map normalized day label -> HTML for the summary bullets/overview for that block.
    Requires ``Lesson N`` to appear in the table text so we do not attach the wrong module's summary.
    """
    flat = _flatten_table_plain(table)
    if not re.search(rf"(?i)lesson\s+{int(doc_lesson_number)}\b", flat):
        return {}

    out: Dict[str, str] = {}
    rows = table.get("rows") or []
    for row in rows:
        cells = row.get("cells") or []
        if len(cells) < 2:
            continue
        day_txt = _flatten_cell_content(cells[0].get("content", []))
        labs = day_labels_in_text(day_txt)
        label = normalize_day_label_key(labs[0]) if labs else ""
        if not label:
            m = DAY_LABEL_RE.search(day_txt)
            label = normalize_day_label_key(m.group(1)) if m else ""
        if not label:
            continue
        html = json_to_html(cells[1].get("content", [])).strip()
        if html:
            out[label] = html

    if len(out) >= 1:
        return out

    para_el: List[Dict[str, Any]] = []
    for row in rows:
        for cell in row.get("cells") or []:
            for el in cell.get("content", []):
                if el.get("type") == "paragraph":
                    para_el.append(el)
    if not para_el:
        return {}
    parts = _split_elements_into_labeled_segments(para_el, json_to_html)
    merged: Dict[str, str] = {}
    for lab, html in parts:
        if not lab or not (html or "").strip():
            continue
        merged[normalize_day_label_key(lab)] = html.strip()
    return merged


def _extract_brief_map_from_pending(
    pending: List[Dict[str, Any]],
    doc_n: int,
    json_to_html: Callable[..., str],
) -> Dict[str, str]:
    for t in reversed(pending):
        if not is_science_summary_key_learning_table(t):
            continue
        t_dn = _doc_lesson_number_from_table(t)
        if t_dn is not None and t_dn != doc_n:
            continue
        m = extract_science_summary_brief_map(t, doc_n, json_to_html)
        if m:
            return m
    return {}


def _brief_html_for_segment(
    brief_by_label: Dict[str, str],
    seg_label: str,
) -> str:
    if not brief_by_label or not seg_label:
        return ""
    nk = normalize_day_label_key(seg_label)
    if nk in brief_by_label:
        return brief_by_label[nk]
    for k, v in brief_by_label.items():
        if _segment_matches_day(seg_label, k):
            return v
    return ""


def parse_lesson_in_action_title(flat: str) -> Optional[Tuple[int, str]]:
    """
    Parse flattened table text: THE LESSON IN ACTION ... Lesson N ... day span.
    Returns (doc_lesson_number, normalized day label for matching overview segments).
    """
    if not _ACTION.search(flat):
        return None
    s = flat[:900]
    m = re.search(r"(?i)lesson\s+(\d+)", s)
    if not m:
        return None
    n = int(m.group(1))
    rest = s[m.end() :]
    bound = re.search(
        r"(?i)(?:Lessons\s+are\s+designed|In-person\s+lessons)\b",
        rest,
    )
    tail = rest[: bound.start() if bound else len(rest)]
    tail = re.sub(r"^[:\-–;\s]+", "", tail)
    tail = re.sub(r"(?i)^lesson\s+\d+\s*", "", tail)
    tail = tail.strip(" \t:-–;")
    tlow = tail.lower()
    if tlow == "day" or tlow.startswith("day lessons") or re.match(r"^day\s*$", tlow):
        return n, "Day 1"

    labs = day_labels_in_text(tail)
    if labs:
        return n, normalize_day_label_key(labs[0])
    m2 = DAY_LABEL_RE.search(tail)
    if m2:
        return n, normalize_day_label_key(m2.group(1))
    mand = re.search(r"(?i)days?\s+(\d+)\s+and\s+(\d+)", tail)
    if mand:
        return n, normalize_day_label_key(f"Days {mand.group(1)}&{mand.group(2)}")
    m3 = re.search(
        r"(?i)(?:day|days)\s+(\d+)\s*(?:&|and)\s*(\d+)",
        tail,
    )
    if m3:
        return n, normalize_day_label_key(f"Days {m3.group(1)}&{m3.group(2)}")
    md = re.search(r"(?i)^day\s+(\d+)", tail)
    if md:
        return n, normalize_day_label_key(f"Day {md.group(1)}")
    m4 = re.search(r"(?i)days\s+([\d\s\-–&]+?)(?:\s+lessons|\s*$)", tail)
    if m4:
        chunk = m4.group(1).strip()
        return n, normalize_day_label_key(f"Days {chunk}")
    return None


def extract_lesson_in_action_block(
    table: Dict[str, Any],
    parser: Any,
) -> Optional[Dict[str, Any]]:
    flat = _flatten_table_plain(table)
    parsed = parse_lesson_in_action_title(flat)
    if not parsed:
        return None
    doc_n, day_label = parsed
    html = parser.json_to_html(table).strip()
    if not html:
        return None
    return {
        "doc_lesson_number": doc_n,
        "day_label": day_label,
        "html": html,
    }


# Order matters: curriculum writers use these four block titles under THE LESSON IN ACTION.
_LESSON_IN_ACTION_SECTION_MARKERS = (
    "lesson opening",
    "during the lesson",
    "lesson closing",
    "online learning activities",
)

_EXPERIMENTAL_MIN_SECTION_LEN = 40


def try_experimental_lesson_in_action_splits(
    html: str,
) -> Optional[Dict[str, str]]:
    """
    Second-phase split of full THE LESSON IN ACTION HTML into four sections.

    Returns ``opening_html``, ``during_html``, ``closing_html``, ``online_html`` only when
    all markers appear in order and each slice meets a minimum length; otherwise ``None``
    (caller should keep only ``lesson_in_action_html``).
    """
    raw = (html or "").strip()
    if not raw:
        return None
    low = raw.lower()
    idxs: List[int] = []
    pos = 0
    for needle in _LESSON_IN_ACTION_SECTION_MARKERS:
        i = low.find(needle, pos)
        if i < 0:
            return None
        idxs.append(i)
        pos = i + len(needle)

    o0, o1, o2, o3 = idxs
    chunks = {
        "opening_html": raw[o0:o1].strip(),
        "during_html": raw[o1:o2].strip(),
        "closing_html": raw[o2:o3].strip(),
        "online_html": raw[o3:].strip(),
    }
    if any(len(v) < _EXPERIMENTAL_MIN_SECTION_LEN for v in chunks.values()):
        return None
    # Reject if a huge preamble suggests we matched the wrong document slice.
    if o0 > len(raw) * 0.4:
        return None
    return chunks


def _enrich_science_segments_for_storage(
    segments: List[Dict[str, Any]],
    brief_by_label: Optional[Dict[str, str]] = None,
) -> None:
    """Mutates segments: ``brief_overview`` from Summary of Key Learning map, ``experimental_splits``."""
    bb = brief_by_label or {}
    for seg in segments:
        seg["brief_overview"] = _brief_html_for_segment(bb, seg.get("label", ""))
        full = (seg.get("lesson_in_action_html") or "").strip()
        exp = try_experimental_lesson_in_action_splits(full)
        if exp is not None:
            seg["experimental_splits"] = exp
        else:
            seg.pop("experimental_splits", None)


def _attach_action_tables_to_segments(
    segments: List[Dict[str, Any]],
    actions: List[Dict[str, Any]],
) -> None:
    for seg in segments:
        seg.setdefault("lesson_in_action_html", "")
    if not actions:
        return
    for act in actions:
        day = (act.get("day_label") or "").strip()
        html = (act.get("html") or "").strip()
        if not html:
            continue
        matched = False
        for seg in segments:
            if _segment_matches_day(seg.get("label", ""), day):
                prev = (seg.get("lesson_in_action_html") or "").strip()
                seg["lesson_in_action_html"] = (
                    (prev + "\n\n" + html).strip() if prev else html
                )
                matched = True
                break
        if not matched and day.lower() in ("day", "days") and segments:
            seg = segments[0]
            prev = (seg.get("lesson_in_action_html") or "").strip()
            seg["lesson_in_action_html"] = (
                (prev + "\n\n" + html).strip() if prev else html
            )
        elif not matched:
            logger.debug(
                "Science: THE LESSON IN ACTION day %r matched no overview segment",
                day,
            )


def _finalize_overview_payload(
    overview: Dict[str, Any],
    actions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    brief_raw = overview.get("_brief_by_label")
    brief_by_label = brief_raw if isinstance(brief_raw, dict) else {}
    payload = {
        "schema_version": 2,
        "source": overview.get("source", "science_lesson_tables@v1"),
        "doc_lesson_number": overview["doc_lesson_number"],
        "segments": [dict(s) for s in overview.get("segments", [])],
    }
    _attach_action_tables_to_segments(payload["segments"], actions)
    _enrich_science_segments_for_storage(payload["segments"], brief_by_label)
    if actions:
        payload["source"] = "science_lesson_tables@v2"
    return payload


def _merge_li_sc_parts(
    li_parts: List[Tuple[str, str]],
    sc_parts: List[Tuple[str, str]],
) -> List[Dict[str, str]]:
    order_keys: List[str] = []
    seen = set()
    for lab, _ in li_parts:
        k = _norm_key(lab)
        if k not in seen:
            seen.add(k)
            order_keys.append(k)
    for lab, _ in sc_parts:
        k = _norm_key(lab)
        if k not in seen:
            seen.add(k)
            order_keys.append(k)

    li_map = {_norm_key(a): b for a, b in li_parts}
    sc_map = {_norm_key(a): b for a, b in sc_parts}
    display: Dict[str, str] = {}
    for lab, _ in li_parts:
        display.setdefault(_norm_key(lab), lab)
    for lab, _ in sc_parts:
        display.setdefault(_norm_key(lab), lab)

    segments: List[Dict[str, str]] = []
    for k in order_keys:
        segments.append(
            {
                "label": display.get(k, k),
                "learning_intention_html": li_map.get(k, ""),
                "success_criteria_html": sc_map.get(k, ""),
            }
        )
    return segments


def extract_overview_li_sc_payload(
    table: Dict[str, Any],
    json_to_html: Callable[..., str],
    pending_tables: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    if not is_science_overview_li_sc_table(table):
        return None
    doc_n = _doc_lesson_number_from_table(table)
    if doc_n is None and pending_tables:
        for t in reversed(pending_tables[-16:]):
            doc_n = _doc_lesson_number_from_table(t)
            if doc_n is not None:
                break
    if doc_n is None:
        return None
    _, ncols = _table_shape(table)
    found = _find_li_sc_header_row_and_cols(table)

    if ncols == 1:
        chain = _collect_all_first_column_elements(table)
        li_el, sc_el = _split_first_column_chain_by_li_sc_headers(chain)
        if not li_el or not sc_el:
            return None
        li_parts = _split_elements_into_labeled_segments(li_el, json_to_html)
        sc_parts = _split_elements_into_labeled_segments(sc_el, json_to_html)
        if not li_parts and not sc_parts:
            return None
        seg_rows = _merge_li_sc_parts(li_parts, sc_parts)
        if not seg_rows:
            return None
        return {
            "schema_version": 1,
            "source": "science_lesson_tables@v1",
            "doc_lesson_number": doc_n,
            "segments": seg_rows,
        }

    if not found:
        return None
    header_row, li_col, sc_col = found
    body_start = header_row + 1

    li_el = _collect_column_elements(table, li_col, body_start)
    sc_el = _collect_column_elements(table, sc_col, body_start)
    li_txt = _flatten_elements_text(li_el)
    sc_txt = _flatten_elements_text(sc_el)
    use_split = len(day_labels_in_text(li_txt)) >= 2 or len(day_labels_in_text(sc_txt)) >= 2

    if use_split:
        li_parts = _split_elements_into_labeled_segments(li_el, json_to_html)
        sc_parts = _split_elements_into_labeled_segments(sc_el, json_to_html)
        if not li_parts and not sc_parts:
            return None
        seg_rows = _merge_li_sc_parts(li_parts, sc_parts)
    else:
        day_col = 0 if li_col > 0 and ncols >= 3 else None
        if day_col is None:
            col0_text = " ".join(
                _flatten_cell_content(
                    table["rows"][ri]["cells"][0].get("content", []),
                )
                for ri in range(body_start, len(table.get("rows") or []))
                if len(table["rows"][ri].get("cells") or []) > 0
            )
            if len(day_labels_in_text(col0_text)) >= 2:
                day_col = 0
        if day_col is None:
            li_parts = _split_elements_into_labeled_segments(li_el, json_to_html)
            sc_parts = _split_elements_into_labeled_segments(sc_el, json_to_html)
            if not li_parts and not sc_parts:
                return None
            seg_rows = _merge_li_sc_parts(li_parts, sc_parts)
        else:
            seg_rows = _per_row_segments(
                table, body_start, li_col, sc_col, day_col, json_to_html
            )
    if not seg_rows:
        return None
    return {
        "schema_version": 1,
        "source": "science_lesson_tables@v1",
        "doc_lesson_number": doc_n,
        "segments": seg_rows,
    }


def iter_science_teaching_module_payloads(
    docx_path: str, parser: Any
) -> List[Dict[str, Any]]:
    """
    Walk body tables in order. Each overview LI/SC table starts a module; following
    THE LESSON IN ACTION tables for the same doc lesson are merged into that module's
    segments as ``lesson_in_action_html``.

    Tables since the previous overview (capped) are scanned for a Science **Summary of Key
    Learning** grid; when found for the same ``Lesson N``, per-segment ``brief_overview`` HTML
    is filled via ``_extract_brief_map_from_pending``.
    """
    doc = Document(docx_path)
    parser.doc = doc
    out: List[Dict[str, Any]] = []
    current_overview: Optional[Dict[str, Any]] = None
    current_actions: List[Dict[str, Any]] = []
    pending: List[Dict[str, Any]] = []

    def flush() -> None:
        nonlocal current_overview, current_actions
        if current_overview is not None:
            out.append(
                _finalize_overview_payload(current_overview, current_actions),
            )
        current_overview = None
        current_actions = []

    for element in doc.element.body:
        if _xml_local_name(element.tag) != "tbl":
            continue
        table_json = parser._parse_table(element, 0)
        overview = extract_overview_li_sc_payload(
            table_json, parser.json_to_html, pending_tables=pending
        )
        if overview:
            flush()
            doc_n = int(overview["doc_lesson_number"])
            overview["_brief_by_label"] = _extract_brief_map_from_pending(
                pending, doc_n, parser.json_to_html
            )
            current_overview = overview
            current_actions = []
            pending.clear()
            continue
        action = extract_lesson_in_action_block(table_json, parser)
        if action:
            if current_overview is None:
                logger.debug("Science: THE LESSON IN ACTION before any overview; skipped")
            elif action["doc_lesson_number"] != current_overview["doc_lesson_number"]:
                logger.debug(
                    "Science: ACTION doc lesson %s != current overview %s; not attached",
                    action["doc_lesson_number"],
                    current_overview["doc_lesson_number"],
                )
            else:
                current_actions.append(action)
            continue
        pending.append(table_json)
        while len(pending) > _PENDING_CONTEXT_MAX:
            pending.pop(0)

    flush()
    return out


def _science_procedure_html_from_structured_payload(payload: Dict[str, Any]) -> str:
    """
    When the DOCX semantic stream left ``procedure_html`` empty (common for early module
    openers), derive teacher-facing HTML from the Science table pass segments so the lesson
    row still has a primary HTML field alongside ``science_li_sc_day_structured``.
    """
    segments = payload.get("segments") or []
    chunks: List[str] = []
    for seg in segments:
        if not isinstance(seg, dict):
            continue
        parts = [
            (seg.get("brief_overview") or "").strip(),
            (seg.get("learning_intention_html") or "").strip(),
            (seg.get("success_criteria_html") or "").strip(),
            (seg.get("lesson_in_action_html") or "").strip(),
        ]
        block = "\n\n".join(p for p in parts if p)
        if block:
            chunks.append(block)
    return "\n\n".join(chunks).strip()


def merge_science_li_sc_into_lessons(
    parser: Any,
    docx_path: str,
    lessons_data: List[Dict[str, Any]],
    subject: str,
) -> None:
    u = (subject or "").strip().upper()
    if u not in ("SCIENCE", "SCI"):
        return
    try:
        payloads = iter_science_teaching_module_payloads(docx_path, parser)
    except Exception as exc:
        logger.warning("Science LI/SC table pass failed: %s", exc)
        return
    if not payloads:
        return

    # Document order: one overview per writer module appearance. Calendar rows repeat
    # doc_lesson_number 1-4 (and rarely 5) many more times than distinct overview tables.
    # Cycle through the extracted payloads for each doc lesson number in encounter order.
    payloads_by_dn: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for p in payloads:
        n = p.get("doc_lesson_number")
        if isinstance(n, int):
            payloads_by_dn[n].append(p)

    def _payload_cycle(dn: int) -> List[Dict[str, Any]]:
        lst = payloads_by_dn.get(dn)
        if lst:
            return lst
        # Single-row Lesson 5 slot in G2 Science U1 has no dedicated overview in the guide;
        # reuse the nearest module band (Lesson 4) when present.
        if dn == 5:
            for fb in (4, 3, 2, 1):
                alt = payloads_by_dn.get(fb)
                if alt:
                    return alt
        return []

    cycle_index: Dict[int, int] = defaultdict(int)

    science_lessons = [
        le
        for le in lessons_data
        if le.get("science_doc_lesson_number") is not None
    ]
    science_lessons.sort(key=lambda x: int(x.get("lesson_number") or 0))

    for le in science_lessons:
        dn = le.get("science_doc_lesson_number")
        if dn is None:
            continue
        dn_i = int(dn)
        cycle = _payload_cycle(dn_i)
        if not cycle:
            logger.warning(
                "Science: no overview LI/SC payloads for doc lesson %s (lesson row %s)",
                dn_i,
                le.get("lesson_number"),
            )
            continue
        idx = cycle_index[dn_i]
        payload = cycle[idx % len(cycle)]
        cycle_index[dn_i] = idx + 1
        le["science_li_sc_day_structured"] = json.dumps(payload, ensure_ascii=False)
        if not (le.get("procedure_html") or "").strip():
            backfill = _science_procedure_html_from_structured_payload(payload)
            if backfill:
                le["procedure_html"] = backfill
