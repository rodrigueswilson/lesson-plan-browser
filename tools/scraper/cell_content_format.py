"""
Cross-subject helpers for DOCX-derived table cell JSON (paragraphs, runs, nested tables).

SSOT: operate on the same structure produced by RecursiveTableParser._parse_paragraph /
_parse_table — not on HTML strings. Used by ELA summary parsing, table_extractor link
aggregation, and optional display enrichment.
"""
from __future__ import annotations

import re
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

__all__ = [
    "collect_hyperlinks_from_buffer",
    "extract_google_doc_id",
    "iter_paragraphs_deep",
    "split_leading_bold_runs_for_paragraph",
    "split_leading_bold_title_and_rest_from_cell",
    "summarize_structure",
    "top_level_paragraphs",
]


def top_level_paragraphs(content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Paragraph dicts at the top of a cell content list (no recursion into nested tables)."""
    return [x for x in content if x.get("type") == "paragraph"]


def iter_paragraphs_deep(items: List[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
    """Depth-first paragraph nodes including nested table cells."""
    for item in items:
        if item.get("type") == "paragraph":
            yield item
        elif item.get("type") == "table":
            for row in item.get("rows") or []:
                for cell in row.get("cells") or []:
                    yield from iter_paragraphs_deep(cell.get("content") or [])


def collect_hyperlinks_from_buffer(buffer: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract link runs from a semantic buffer (paragraphs only, same shape as flush_buffer).

    Matches legacy flush_buffer behavior: one entry per hyperlink run with url, google_id, text.
    """
    out: List[Dict[str, Any]] = []
    for b in buffer:
        if b.get("type") != "paragraph":
            continue
        for run in b.get("runs") or []:
            style = run.get("style") or {}
            if style.get("link"):
                out.append(
                    {
                        "url": style.get("url"),
                        "google_id": style.get("google_id"),
                        "text": run.get("text") or "",
                    }
                )
    return out


def split_leading_bold_runs_for_paragraph(
    p_json: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Split runs of a single paragraph into leading bold segment vs remainder.

    Used for optional <span class="rich-cell-label"> wrapping in HTML emission.
    """
    runs = list(p_json.get("runs") or [])
    if not runs:
        return [], []

    leading: List[Dict[str, Any]] = []
    split_idx: Optional[int] = None

    for i, run in enumerate(runs):
        st = run.get("style") or {}
        t = run.get("text") or ""
        bold = bool(st.get("bold"))
        if split_idx is not None:
            break
        if bold and t.strip():
            leading.append(run)
        elif leading and (not bold) and t.strip():
            split_idx = i
            break
        elif not leading and t.strip() and not bold:
            return [], runs

    if split_idx is not None:
        return leading, runs[split_idx:]
    if leading:
        return leading, []
    return [], runs


def split_leading_bold_title_and_rest_from_cell(
    content: List[Dict[str, Any]],
    htmlize: Callable[[List[Dict[str, Any]]], str],
) -> Tuple[str, str]:
    """
    Consecutive bold runs from the start of the first affected paragraph through
    paragraph boundaries = title; first non-bold run with text closes the title (ELA column C).
    """
    paras = top_level_paragraphs(content)
    if not paras:
        return "", ""

    title_chunks: List[str] = []
    title_closed = False
    split_pi: Optional[int] = None
    split_ri: Optional[int] = None

    for pi, p in enumerate(paras):
        runs = p.get("runs") or []
        for ri, run in enumerate(runs):
            st = run.get("style") or {}
            t = run.get("text") or ""
            bold = bool(st.get("bold"))
            if not title_closed:
                if bold and t.strip():
                    title_chunks.append(t)
                elif title_chunks and (not bold) and t.strip():
                    title_closed = True
                    split_pi, split_ri = pi, ri
                    break
        if title_closed:
            break

    title = "".join(title_chunks).strip()
    if not title_closed:
        if title:
            return title, ""
        return "", htmlize(content)

    rem: List[Dict[str, Any]] = []
    for pi, p in enumerate(paras):
        runs = list(p.get("runs") or [])
        if split_pi is None or split_ri is None:
            break
        if pi < split_pi:
            continue
        if pi == split_pi:
            tail = runs[split_ri:]
            if any((r.get("text") or "").strip() for r in tail):
                rem.append({**p, "runs": tail})
        else:
            rem.append(p)

    body_html = htmlize(rem) if rem else ""
    return title, body_html


def summarize_structure(content: List[Dict[str, Any]]) -> Dict[str, int]:
    """Lightweight counts for ingest diagnostics (paragraphs vs bullets)."""
    bullets = 0
    plain = 0
    for p in iter_paragraphs_deep(content):
        if p.get("is_bullet"):
            bullets += 1
        else:
            plain += 1
    return {"paragraphs": plain, "bullets": bullets}


def extract_google_doc_id(url: str) -> Optional[str]:
    """Return Google Doc id from a /document/d/<id>/ URL, or None."""
    if not url:
        return None
    m = re.search(r"/document/d/([a-zA-Z0-9_-]+)", url)
    return m.group(1) if m else None
