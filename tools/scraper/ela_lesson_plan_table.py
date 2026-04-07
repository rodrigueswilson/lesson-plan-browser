"""
Detect and parse ELA per-lesson detailed plan tables from DOCX table JSON.

Typical layout (Grade 2+ teacher guide tabs):
- Row 0: "Lesson N: <title>" (often column 0 only).
- Optional blank row(s) between title and headers (Grade 2 Unit 8 tab exports).
- Headers: "Learning Intention" | "Success Criteria" (row located by scanning).
- Next row: body cells for those columns.
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


def _row_is_li_sc_header(row: Dict[str, Any]) -> bool:
    """True when this row looks like Learning Intention | Success Criteria column headers."""
    t0, t1 = _row_plain_cells(row)
    n0, n1 = _norm(t0), _norm(t1)
    if "learning intention" not in n0:
        return False
    if "success criteria" not in n1:
        return False
    return True


def find_ela_lesson_plan_anchor(
    rows: List[Dict[str, Any]],
    max_scan: int = 12,
) -> Optional[Tuple[int, int]]:
    """
    Locate the LI|SC header row and the lesson title row above it.

    Google Docs / district exports sometimes insert blank or spacer rows between
    the \"Lesson N:\" title and the two-column headers (Grade 2 Unit 8 tab).

    Returns:
        (header_row_index, lesson_title_row_index) or None if not a lesson plan grid.
    """
    limit = min(len(rows), max_scan)
    for hi in range(limit):
        cells = rows[hi].get("cells") or []
        if len(cells) < 2:
            continue
        if not _row_is_li_sc_header(rows[hi]):
            continue
        for ti in range(hi - 1, -1, -1):
            lnum, _ = _parse_lesson_title_row(rows[ti])
            if lnum is not None:
                return (hi, ti)
        return None
    return None


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


def _bold_label_prefix(line: str) -> str:
    """
    Emphasize leading section label prefixes like 'Anticipatory Set:' when DOCX export
    flattened style metadata. Skips lines that already contain bold tags.
    """
    if not line or "<b>" in line.lower() or "<strong>" in line.lower():
        return line
    m = re.match(r"^\s*([A-Za-z][A-Za-z0-9/&\-\s]{1,90}:)\s*(.*)$", line)
    if not m:
        return line
    label = (m.group(1) or "").strip()
    rest = (m.group(2) or "").strip()
    # Keep this conservative to avoid bolding arbitrary long sentence prefixes.
    if len(label.split()) > 9:
        return line
    if rest:
        return f"<b>{label}</b> {rest}"
    return f"<b>{label}</b>"


def _looks_like_heading_prefix(line: str) -> bool:
    plain = re.sub(r"<[^>]+>", "", line or "").strip()
    m = re.match(r"^([A-Za-z][A-Za-z0-9/&\-\s]{1,90}:)\s*(.*)$", plain)
    if not m:
        return False
    label = (m.group(1) or "").strip()
    if len(label.split()) > 9:
        return False
    return True


_STANDARDS_TOKEN_RE = re.compile(
    r"\b(?:[A-Z]{1,4}\.[A-Z]{1,4}\.[0-9A-Za-z\.]+|[0-9]+\.[0-9]+\.[0-9A-Za-z\.]+)\b"
)


def _split_heading_plus_standards_line(line: str) -> List[str]:
    """
    Split flattened lines that merged a heading with standards codes.
    Example:
      "Read Aloud and Text Dependent Questions RI.IT.2.3, ...:"
    =>
      ["Read Aloud and Text Dependent Questions:", "RI.IT.2.3, ...:"]
    """
    plain = re.sub(r"<[^>]+>", "", line or "").strip()
    if not plain:
        return [line]
    # "Daily Instructional Task: Partner Discussions RI...." should keep only
    # the section title as heading and move the rest to a normal bullet line.
    m_daily = re.match(r"^Daily Instructional Task\s*:\s*(.+)$", plain, flags=re.IGNORECASE)
    if m_daily:
        rest = m_daily.group(1).strip()
        if rest and _STANDARDS_TOKEN_RE.search(rest):
            return ["Daily Instructional Task:", rest]
    m = _STANDARDS_TOKEN_RE.search(plain)
    if not m:
        return [line]
    idx = m.start()
    if idx < 8:
        return [line]
    head = plain[:idx].strip().rstrip(":")
    tail = plain[idx:].strip()
    # Avoid splitting short labels or obvious full-sentence content.
    if len(head.split()) < 2 or len(head) > 120:
        return [line]
    head_low = head.lower()
    # Keep scope conservative: this normalization is intended for long instructional
    # lines where a heading and standards list were flattened into one line.
    allowed_heads = (
        "read aloud",
        "text dependent questions",
        "daily instructional task",
    )
    if not any(h in head_low for h in allowed_heads):
        return [line]
    if "," not in tail and "." not in tail:
        return [line]
    return [f"{head}:", tail]


def _normalize_docx_export_html(html: str) -> str:
    """
    Normalize flattened DOCX HTML:
    - preserve/emphasize heading-like prefixes ending with ':'
    - recover bullets from lines starting with '*' or '-' within paragraph <br> blocks
    """
    raw = (html or "").strip()
    if not raw:
        return raw

    def _rewrite_paragraph(match: re.Match[str]) -> str:
        inner = match.group(1) or ""
        lines0 = [x.strip() for x in re.split(r"<br\s*/?>", inner, flags=re.IGNORECASE)]
        lines0 = [ln for ln in lines0 if ln]
        lines: List[str] = []
        for ln in lines0:
            lines.extend(_split_heading_plus_standards_line(ln))
        if not lines:
            return "<p></p>"

        normal_lines: List[str] = []
        bullets: List[str] = []
        heading_context = False
        for ln in lines:
            ln2 = _bold_label_prefix(ln)
            b = re.match(r"^[\*\-]\s+(.+)$", ln2)
            if b:
                bullets.append((b.group(1) or "").strip())
                heading_context = True
            else:
                if _looks_like_heading_prefix(ln2):
                    # New section heading in long flattened cells: keep heading as a line and
                    # treat following lines as list items for readability.
                    if bullets:
                        lis = "".join(f"<li>{item}</li>" for item in bullets if item)
                        if lis:
                            normal_lines.append(f"<ul>{lis}</ul>")
                        bullets = []
                    normal_lines.append(ln2)
                    heading_context = True
                elif heading_context and len(ln2) > 0:
                    bullets.append(ln2)
                else:
                    normal_lines.append(ln2)

        chunks: List[str] = []
        if bullets:
            lis = "".join(f"<li>{item}</li>" for item in bullets if item)
            if lis:
                normal_lines.append(f"<ul>{lis}</ul>")
        if normal_lines:
            # Don't wrap block-level lists in <p>.
            if any(x.startswith("<ul>") for x in normal_lines):
                buf: List[str] = []
                for item in normal_lines:
                    if item.startswith("<ul>"):
                        if buf:
                            chunks.append(f"<p>{'<br>'.join(buf)}</p>")
                            buf = []
                        chunks.append(item)
                    else:
                        buf.append(item)
                if buf:
                    chunks.append(f"<p>{'<br>'.join(buf)}</p>")
            else:
                chunks.append(f"<p>{'<br>'.join(normal_lines)}</p>")
        return "".join(chunks) if chunks else "<p></p>"

    # Rebuild each paragraph independently so list recovery remains local.
    return re.sub(
        r"<p>(.*?)</p>",
        _rewrite_paragraph,
        raw,
        flags=re.IGNORECASE | re.DOTALL,
    )


def is_ela_lesson_plan_table(table_json: Dict[str, Any]) -> bool:
    """True if the table matches the ELA detailed lesson plan grid (Lesson N: title + LI/SC headers)."""
    rows = table_json.get("rows") or []
    if len(rows) < 3:
        return False
    anchor = find_ela_lesson_plan_anchor(rows)
    if anchor is None:
        return False
    hi, _ti = anchor
    # Need header row plus at least one content row (LI/SC body).
    return hi + 1 < len(rows)


def parse_ela_lesson_plan_table(
    table_json: Dict[str, Any],
    json_to_html: Callable[[List[Dict[str, Any]]], str],
) -> Optional[Dict[str, Any]]:
    """
    Parse a detected ELA lesson plan table into a JSON-serializable dict.
    Returns None if the lesson title or header anchor cannot be resolved.
    Permissive: after LI/SC cells are captured, remaining sections are best-effort.
    """
    rows = table_json.get("rows") or []
    if len(rows) < 3:
        return None

    anchor = find_ela_lesson_plan_anchor(rows)
    if anchor is None:
        return None
    hi, ti = anchor
    lesson_number, lesson_title = _parse_lesson_title_row(rows[ti])
    if lesson_number is None:
        return None

    out: Dict[str, Any] = {
        "schema_version": 1,
        "lesson_number": lesson_number,
        "lesson_title": lesson_title,
    }

    # Skip rows from after the title through the LI|SC header; next row is the body pair.
    i = hi + 1
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
        # Some exports label this row as "NJSLS Priority Standards".
        if n0.startswith("njsls standards") or n0.startswith("njsls priority standards"):
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
        if n0.startswith("key instructional practices") and len(t0) < 200 and _second_empty():
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

    # Post-process all rich cells with a single formatter for heading/bullet readability.
    for k, v in list(out.items()):
        if isinstance(v, str) and k.endswith("_html") and v.strip():
            out[k] = _normalize_docx_export_html(v)
    return out
