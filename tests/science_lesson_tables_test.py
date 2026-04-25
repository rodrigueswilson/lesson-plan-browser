"""Unit tests for science overview LI/SC table extraction (synthetic table_json)."""

from __future__ import annotations

from tools.scraper.science_lesson_tables import (
    _finalize_overview_payload,
    _science_procedure_html_from_structured_payload,
    extract_lesson_in_action_block,
    extract_overview_li_sc_payload,
    extract_science_summary_brief_map,
    is_science_overview_li_sc_table,
    is_science_summary_key_learning_table,
    merge_science_li_sc_into_lessons,
    parse_lesson_in_action_title,
    try_experimental_lesson_in_action_splits,
)


def _run(text: str) -> dict:
    return {
        "type": "run",
        "text": text,
        "style": None,
    }


def _para(text: str) -> dict:
    return {
        "type": "paragraph",
        "text": text,
        "is_bullet": False,
        "ilvl": 0,
        "runs": [_run(text)],
    }


def _cell(*paragraphs: dict) -> dict:
    return {
        "type": "table-cell",
        "grid_span": None,
        "v_merge": None,
        "content": list(paragraphs),
    }


def _row(*cells: dict) -> dict:
    return {"type": "table-row", "cells": list(cells)}


def _table(rows: list, depth: int = 0) -> dict:
    return {"type": "table", "rows": rows, "depth": depth}


def _json_to_html_mock(elements: list) -> str:
    """Minimal HTML for tests (no RecursiveTableParser)."""
    if isinstance(elements, dict):
        elements = [elements]
    parts = []
    for el in elements:
        if el.get("type") == "paragraph":
            t = (el.get("text") or "").strip()
            if t:
                parts.append(f"<p>{t}</p>")
    return "".join(parts)


class _ParserJsonToHtml:
    """Parser-like object: json_to_html supports full table dicts."""

    @staticmethod
    def json_to_html(elements):
        if isinstance(elements, dict) and elements.get("type") == "table":
            return "<table>action-block</table>"
        return _json_to_html_mock(elements)


def test_action_table_not_overview():
    rows = [
        _row(
            _cell(_para("THE LESSON IN ACTION")),
            _cell(_para("Learning intention")),
            _cell(_para("Success criteria Lesson 1: Mod")),
        ),
    ]
    for i in range(1, 10):
        rows.append(
            _row(
                _cell(_para(f"Day {i}")),
                _cell(_para("li")),
                _cell(_para("sc")),
            )
        )
    assert is_science_overview_li_sc_table(_table(rows)) is False


def test_overview_split_extracts_segments():
    """10+ rows, 3 cols, LI/SC headers, Lesson 1, multiple day labels in columns."""
    header = _row(
        _cell(_para("Lesson 1: Properties of Matter: Describe Matter")),
        _cell(_para("Learning intention")),
        _cell(_para("Success criteria")),
    )
    body = []
    body.append(
        _row(
            _cell(_para("")),
            _cell(
                _para("Day 1: First LI"),
                _para("More LI"),
            ),
            _cell(
                _para("Day 1: First SC"),
            ),
        )
    )
    body.append(
        _row(
            _cell(_para("")),
            _cell(_para("Days 2&3: Second LI")),
            _cell(_para("Days 2&3: Second SC")),
        )
    )
    body.append(
        _row(
            _cell(_para("")),
            _cell(_para("Days 4-7: Third LI")),
            _cell(_para("Days 4-7: Third SC")),
        )
    )
    # Pad to >= 10 rows total
    while len(body) < 9:
        body.append(
            _row(
                _cell(_para("")),
                _cell(_para("extra li")),
                _cell(_para("extra sc")),
            )
        )
    tbl = _table([header] + body)
    assert is_science_overview_li_sc_table(tbl) is True
    payload = extract_overview_li_sc_payload(tbl, _json_to_html_mock)
    assert payload is not None
    assert payload["doc_lesson_number"] == 1
    assert payload["schema_version"] == 1
    segs = payload["segments"]
    labels = [s["label"] for s in segs]
    assert "Day 1" in labels
    assert any("2" in lb and "3" in lb for lb in labels)
    assert any("4" in lb for lb in labels)


def test_parse_lesson_in_action_title_truncated_day():
    flat = "THE LESSON IN ACTION Lesson 1 - Day In-person lessons"
    assert parse_lesson_in_action_title(flat) == (1, "Day 1")


def test_parse_lesson_in_action_title_days_2_3():
    flat = "THE LESSON IN ACTION: Lesson 1: Days 2&3 Lessons are designed"
    r = parse_lesson_in_action_title(flat)
    assert r is not None
    assert r[0] == 1
    assert "2" in r[1] and "3" in r[1]


def test_extract_lesson_in_action_block_parses_table():
    rows = [
        _row(
            _cell(
                _para("THE LESSON IN ACTION: Lesson 1: Days 2&3"),
                _para("Some body"),
            ),
        ),
    ]
    tbl = _table(rows)
    block = extract_lesson_in_action_block(tbl, _ParserJsonToHtml())
    assert block is not None
    assert block["doc_lesson_number"] == 1
    assert block["html"] == "<table>action-block</table>"


def test_finalize_attaches_action_html_to_matching_segments():
    overview = {
        "schema_version": 1,
        "source": "science_lesson_tables@v1",
        "doc_lesson_number": 1,
        "segments": [
            {
                "label": "Day 1",
                "learning_intention_html": "<p>a</p>",
                "success_criteria_html": "<p>b</p>",
            },
            {
                "label": "Days 2&3",
                "learning_intention_html": "<p>c</p>",
                "success_criteria_html": "<p>d</p>",
            },
        ],
    }
    actions = [
        {"doc_lesson_number": 1, "day_label": "Day 1", "html": "<table>x</table>"},
        {
            "doc_lesson_number": 1,
            "day_label": "Days 2 and 3",
            "html": "<table>y</table>",
        },
    ]
    fin = _finalize_overview_payload(overview, actions)
    assert fin["source"] == "science_lesson_tables@v2"
    assert fin["schema_version"] == 2
    segs = fin["segments"]
    assert segs[0]["lesson_in_action_html"] == "<table>x</table>"
    assert segs[1]["lesson_in_action_html"] == "<table>y</table>"
    assert segs[0].get("brief_overview") == ""
    assert "experimental_splits" not in segs[0]


def test_try_experimental_lesson_in_action_splits_success():
    pad = "x" * 60
    html = (
        f"<p>Preamble</p><p>Lesson Opening</p><p>{pad}</p>"
        f"<p>During the Lesson</p><p>{pad}</p>"
        f"<p>Lesson Closing</p><p>{pad}</p>"
        f"<p>Online Learning Activities</p><p>{pad}</p>"
    )
    exp = try_experimental_lesson_in_action_splits(html)
    assert exp is not None
    assert set(exp) == {
        "opening_html",
        "during_html",
        "closing_html",
        "online_html",
    }
    assert all(len(exp[k]) >= 40 for k in exp)


def test_try_experimental_lesson_in_action_splits_none_if_marker_missing():
    exp = try_experimental_lesson_in_action_splits("<p>Lesson Opening</p><p>" + "z" * 80)
    assert exp is None


def test_finalize_populates_experimental_splits_when_action_html_valid():
    pad = "y" * 60
    action_html = (
        f"<div>THE LESSON IN ACTION</div><p>Lesson Opening</p><p>{pad}</p>"
        f"<p>During the Lesson</p><p>{pad}</p>"
        f"<p>Lesson Closing</p><p>{pad}</p>"
        f"<p>Online Learning Activities</p><p>{pad}</p>"
    )
    overview = {
        "schema_version": 1,
        "source": "science_lesson_tables@v1",
        "doc_lesson_number": 1,
        "segments": [
            {
                "label": "Day 1",
                "learning_intention_html": "<p>li</p>",
                "success_criteria_html": "<p>sc</p>",
            },
        ],
    }
    actions = [{"doc_lesson_number": 1, "day_label": "Day 1", "html": action_html}]
    fin = _finalize_overview_payload(overview, actions)
    es = fin["segments"][0].get("experimental_splits")
    assert es is not None
    assert "opening_html" in es and len(es["opening_html"]) >= 40


def test_extract_science_summary_brief_map_two_column():
    rows = [
        _row(_cell(_para("Summary of Key Learning Lesson 1: Describe Matter"))),
        _row(
            _cell(_para("Day 1:")),
            _cell(_para("Bullet one"), _para("Bullet two")),
        ),
        _row(
            _cell(_para("Days 2&3:")),
            _cell(_para("Shared block tasks")),
        ),
    ]
    tbl = _table(rows)
    assert is_science_summary_key_learning_table(tbl) is True
    m = extract_science_summary_brief_map(tbl, 1, _json_to_html_mock)
    assert "Day 1" in m
    assert "Days 2&3" in m or any("2" in k and "3" in k for k in m)


def test_finalize_applies_brief_by_label_to_segments():
    overview = {
        "schema_version": 1,
        "source": "science_lesson_tables@v1",
        "doc_lesson_number": 1,
        "segments": [
            {
                "label": "Day 1",
                "learning_intention_html": "<p>li</p>",
                "success_criteria_html": "<p>sc</p>",
            },
        ],
        "_brief_by_label": {"Day 1": "<p>summary bullets</p>"},
    }
    fin = _finalize_overview_payload(overview, [])
    assert fin["segments"][0]["brief_overview"] == "<p>summary bullets</p>"


def test_overview_requires_min_day_labels():
    rows = [
        _row(
            _cell(_para("Learning intention")),
            _cell(_para("Success criteria")),
            _cell(_para("Lesson 1: X")),
        ),
    ]
    for _ in range(9):
        rows.append(_row(_cell(_para("")), _cell(_para("only")), _cell(_para("text"))))
    assert is_science_overview_li_sc_table(_table(rows)) is False


def test_single_column_overview_stacked_li_sc():
    """Template B: one column; Learning intention / Success criteria as section headers."""
    rows = [
        _row(_cell(_para("Lesson 2: Module title"))),
        _row(_cell(_para("Learning intention"))),
        _row(_cell(_para("Days 4&5: LI body here"))),
        _row(_cell(_para("Success criteria"))),
        _row(_cell(_para("Days 4&5: SC body here"))),
        _row(_cell(_para("Notes row"))),
    ]
    tbl = _table(rows)
    assert is_science_overview_li_sc_table(tbl) is True
    payload = extract_overview_li_sc_payload(tbl, _json_to_html_mock)
    assert payload is not None
    assert payload["doc_lesson_number"] == 2
    segs = payload["segments"]
    assert len(segs) >= 1
    assert any("4" in s["label"] and "5" in s["label"] for s in segs)


def test_compact_overview_two_day_labels_template_b():
    """Later Science modules: smaller LI/SC grid with only two day bands (not three+)."""
    header = _row(
        _cell(_para("Lesson 12: Example topic line")),
        _cell(_para("Learning intention")),
        _cell(_para("Success criteria")),
    )
    body = [
        _row(
            _cell(_para("")),
            _cell(_para("Day 1: Short LI")),
            _cell(_para("Day 1: Short SC")),
        ),
        _row(
            _cell(_para("")),
            _cell(_para("Days 2&3: Block LI")),
            _cell(_para("Days 2&3: Block SC")),
        ),
        _row(
            _cell(_para("")),
            _cell(_para("continuation")),
            _cell(_para("more sc")),
        ),
        _row(
            _cell(_para("")),
            _cell(_para("notes")),
            _cell(_para("rubric")),
        ),
    ]
    tbl = _table([header] + body)
    assert is_science_overview_li_sc_table(tbl) is True
    payload = extract_overview_li_sc_payload(tbl, _json_to_html_mock)
    assert payload is not None
    assert payload["doc_lesson_number"] == 12
    labels = [s["label"] for s in payload["segments"]]
    assert "Day 1" in labels
    assert any("2" in lb and "3" in lb for lb in labels)


def test_merge_cycles_payloads_when_calendar_rows_exceed_doc_tables():
    """Fewer overview tables than lesson rows: reuse payloads in order (cycle)."""

    class _P:
        def __init__(self) -> None:
            self.called = False

        def science_pass(self, *_a, **_k):
            self.called = True
            return [
                {
                    "schema_version": 2,
                    "doc_lesson_number": 1,
                    "segments": [{"label": "Day 1", "learning_intention_html": "<p>a</p>"}],
                },
                {
                    "schema_version": 2,
                    "doc_lesson_number": 1,
                    "segments": [{"label": "Day 1", "learning_intention_html": "<p>b</p>"}],
                },
            ]

    p = _P()
    lessons = [
        {"lesson_number": 1, "science_doc_lesson_number": 1},
        {"lesson_number": 2, "science_doc_lesson_number": 2},
        {"lesson_number": 5, "science_doc_lesson_number": 1},
        {"lesson_number": 6, "science_doc_lesson_number": 1},
    ]
    import json

    import tools.scraper.science_lesson_tables as slt

    orig = slt.iter_science_teaching_module_payloads
    try:
        slt.iter_science_teaching_module_payloads = p.science_pass  # type: ignore[method-assign]
        merge_science_li_sc_into_lessons(None, "x.docx", lessons, "Science")
    finally:
        slt.iter_science_teaching_module_payloads = orig

    assert p.called
    assert "science_li_sc_day_structured" in lessons[0]
    assert "science_li_sc_day_structured" not in lessons[1]
    j0 = json.loads(lessons[0]["science_li_sc_day_structured"])
    j5 = json.loads(lessons[2]["science_li_sc_day_structured"])
    j6 = json.loads(lessons[3]["science_li_sc_day_structured"])
    assert j0["segments"][0]["learning_intention_html"] == "<p>a</p>"
    assert j5["segments"][0]["learning_intention_html"] == "<p>b</p>"
    assert j6["segments"][0]["learning_intention_html"] == "<p>a</p>"


def test_science_procedure_html_from_structured_payload_orders_blocks():
    html = _science_procedure_html_from_structured_payload(
        {
            "segments": [
                {
                    "brief_overview": "<p>overview</p>",
                    "learning_intention_html": "<p>li</p>",
                    "success_criteria_html": "<p>sc</p>",
                    "lesson_in_action_html": "<p>action</p>",
                }
            ]
        }
    )
    assert html.index("<p>overview</p>") < html.index("<p>li</p>")
    assert html.index("<p>li</p>") < html.index("<p>sc</p>")
    assert html.index("<p>sc</p>") < html.index("<p>action</p>")


def test_merge_science_backfills_procedure_html_when_empty(tmp_path):
    """merge attaches structured JSON and fills procedure_html from segments when blank."""

    class P:
        called = False

        def science_pass(self, _path, _parser):
            P.called = True
            return [
                {
                    "doc_lesson_number": 1,
                    "schema_version": 2,
                    "source": "t",
                    "segments": [
                        {
                            "label": "Day 1",
                            "learning_intention_html": "<p>L</p>",
                            "lesson_in_action_html": "<p>A</p>",
                        }
                    ],
                }
            ]

    p = P()
    lessons = [
        {
            "lesson_number": 1,
            "science_doc_lesson_number": 1,
            "procedure_html": "",
            "title": "t",
        }
    ]
    import tools.scraper.science_lesson_tables as slt

    orig = slt.iter_science_teaching_module_payloads
    try:
        slt.iter_science_teaching_module_payloads = p.science_pass  # type: ignore[method-assign]
        merge_science_li_sc_into_lessons(None, str(tmp_path / "x.docx"), lessons, "Science")
    finally:
        slt.iter_science_teaching_module_payloads = orig

    assert "<p>L</p>" in lessons[0]["procedure_html"]
    assert "<p>A</p>" in lessons[0]["procedure_html"]
