"""Tests for curriculum vocabulary token filtering and vocab-section escape (table_extractor)."""

from tools.scraper.subject_config import SubjectConfig
from tools.scraper.table_extractor import (
    _extract_vocab_terms,
    _normalize_anchor_text,
    _resolve_field_from_anchors,
    _resolve_section_header_after_false_vocab_run,
    _should_drop_vocab_token,
)


def test_should_drop_vocab_instructional_fragments():
    assert _should_drop_vocab_token("Article: Memory Quilts")
    assert _should_drop_vocab_token("Daily Instructional Task: Culminating Task")
    assert _should_drop_vocab_token("Anticipatory Set: Think aloud")
    assert _should_drop_vocab_token("students will complete the task")
    assert _should_drop_vocab_token("and techniques?")
    assert _should_drop_vocab_token("preservation)")
    assert _should_drop_vocab_token("materials")
    assert _should_drop_vocab_token("storytelling")
    assert _should_drop_vocab_token("Editing")
    assert _should_drop_vocab_token("cultural meaning")
    assert _should_drop_vocab_token("Correct spelling and punctuation")
    assert _should_drop_vocab_token("Use correct spelling and punctuation")
    assert _should_drop_vocab_token("if working with a peer")
    assert _should_drop_vocab_token("Who is responsible for creating each?")
    assert not _should_drop_vocab_token("Constitution")
    assert not _should_drop_vocab_token("protest")
    assert not _should_drop_vocab_token("representatives")


def test_extract_vocab_terms_keeps_real_terms_drops_prose():
    s = (
        "Constitution, protest, Article: Memory Quilts, Winter Counts, "
        "materials, storytelling, Correct spelling and punctuation"
    )
    out = _extract_vocab_terms(s)
    assert "Constitution" in out
    assert "protest" in out
    assert "Winter Counts" in out
    assert "Article: Memory Quilts" not in out
    assert "materials" not in out
    assert "storytelling" not in out
    assert "Correct spelling and punctuation" not in out


def test_resolve_section_header_escapes_long_daily_instructional_line():
    cfg = SubjectConfig.get_config("ELA")
    field_map = {}
    for field, anchors in cfg["anchors"].items():
        for a in anchors:
            field_map[_normalize_anchor_text(a)] = field
    field_map[_normalize_anchor_text("vocabulary")] = "_vocab_temp"

    body = "x" * 90
    long_line = f"daily instructional task: culminating comparison composition {body}"
    low = _normalize_anchor_text(long_line)
    assert len(low) > 120
    assert _resolve_field_from_anchors(low, field_map) is None
    r = _resolve_section_header_after_false_vocab_run(low, field_map)
    assert r == "daily_instructional_task"
