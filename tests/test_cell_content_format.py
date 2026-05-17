"""Tests for tools.scraper.cell_content_format (cross-subject cell JSON helpers)."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRAPER_DIR = str(_REPO_ROOT / "tools" / "scraper")
if _SCRAPER_DIR not in sys.path:
    sys.path.insert(0, _SCRAPER_DIR)
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.scraper.cell_content_format import (  # noqa: E402
    collect_hyperlinks_from_buffer,
    extract_google_doc_id,
    split_leading_bold_runs_for_paragraph,
    split_leading_bold_title_and_rest_from_cell,
    summarize_structure,
)


def _p(text: str, bold: bool = False) -> dict:
    style = {"bold": True} if bold else None
    return {
        "type": "paragraph",
        "text": text,
        "is_bullet": False,
        "ilvl": 0,
        "runs": [{"type": "run", "text": text, "style": style}],
    }


def _plink(text: str, url: str, google_id: str | None = None) -> dict:
    st: dict = {"link": True, "url": url}
    if google_id:
        st["google_id"] = google_id
    return {
        "type": "paragraph",
        "text": text,
        "is_bullet": False,
        "ilvl": 0,
        "runs": [{"type": "run", "text": text, "style": st}],
    }


def test_split_leading_bold_runs_for_paragraph() -> None:
    p = _p("Hello", bold=True)
    p["runs"].append({"type": "run", "text": " world", "style": None})
    lead, tail = split_leading_bold_runs_for_paragraph(p)
    assert len(lead) == 1
    assert len(tail) == 1
    assert tail[0]["text"] == " world"


def test_split_leading_bold_title_and_rest_from_cell_matches_summary_semantics() -> None:
    def htmlize(parts: list) -> str:
        return "".join(f"<p>{(x.get('text') or '')}</p>" for x in parts)

    body_para = {
        "type": "paragraph",
        "text": "Body para.",
        "is_bullet": False,
        "ilvl": 0,
        "runs": [{"type": "run", "text": "Body para.", "style": None}],
    }
    content = [_p("TitleBit", bold=True), body_para]
    title, body = split_leading_bold_title_and_rest_from_cell(content, htmlize)
    assert title == "TitleBit"
    assert "Body" in body


def test_collect_hyperlinks_from_buffer() -> None:
    buf = [
        _plink("Doc", "https://docs.google.com/document/d/abc123/edit", "abc123"),
        {"type": "paragraph", "text": "x", "runs": []},
    ]
    links = collect_hyperlinks_from_buffer(buf)
    assert len(links) == 1
    assert links[0]["google_id"] == "abc123"
    assert "abc123" in links[0]["url"]


def test_summarize_structure_counts_bullets() -> None:
    content = [_p("a"), {"type": "paragraph", "text": "b", "is_bullet": True, "ilvl": 0, "runs": []}]
    s = summarize_structure(content)
    assert s["paragraphs"] == 1
    assert s["bullets"] == 1


def test_extract_google_doc_id() -> None:
    assert extract_google_doc_id("https://docs.google.com/document/d/XYZ-1_/edit") == "XYZ-1_"
    assert extract_google_doc_id("https://example.com") is None


def test_json_to_html_enriches_first_paragraph_label() -> None:
    from tools.scraper.table_extractor import RecursiveTableParser

    parser = RecursiveTableParser()
    parser.enrich_leading_cell_labels = True
    html = parser.json_to_html(
        [
            {
                "type": "paragraph",
                "text": "Label body",
                "is_bullet": False,
                "ilvl": 0,
                "runs": [
                    {"type": "run", "text": "Label", "style": {"bold": True}},
                    {"type": "run", "text": " body", "style": None},
                ],
            }
        ]
    )
    assert 'class="rich-cell-label"' in html
    assert "<b>Label</b>" in html


def test_json_to_html_paragraph_newlines_become_br() -> None:
    from tools.scraper.table_extractor import RecursiveTableParser

    parser = RecursiveTableParser()
    html = parser.json_to_html(
        [
            {
                "type": "paragraph",
                "text": "Line one\nLine two",
                "is_bullet": False,
                "ilvl": 0,
                "runs": [
                    {"type": "run", "text": "Line one\nLine two", "style": None},
                ],
            }
        ]
    )
    assert "<br>" in html
    assert "Line one" in html and "Line two" in html
