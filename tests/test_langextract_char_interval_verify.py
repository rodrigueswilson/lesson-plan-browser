"""Unit tests for spike char_interval grounding checks (no langextract dependency)."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

_SPIKE_DIR = Path(__file__).resolve().parents[1] / "docs/research/spikes/langextract_curriculum_smoke"
sys.path.insert(0, str(_SPIKE_DIR))

from char_interval_verify import (  # noqa: E402
    slice_for_char_interval,
    verify_grounded_extractions,
)


class _Status:
    """Mimics langextract AlignmentStatus .value strings."""

    def __init__(self, value: str) -> None:
        self.value = value


def test_slice_for_char_interval_tuple():
    assert slice_for_char_interval("abcde", (2, 5)) == "cde"


def test_slice_for_char_interval_object():
    ci = SimpleNamespace(start_pos=1, end_pos=3)
    assert slice_for_char_interval("abcde", ci) == "bc"


def test_verify_passes_when_slices_match():
    src = "Lesson 2: Hello. Procedure: Do the thing."
    ex = [
        SimpleNamespace(
            extraction_class="lesson_number",
            extraction_text="Lesson 2",
            char_interval=SimpleNamespace(start_pos=0, end_pos=8),
        ),
        SimpleNamespace(
            extraction_class="procedure",
            extraction_text="Do the thing.",
            char_interval=SimpleNamespace(start_pos=28, end_pos=41),
        ),
    ]
    assert verify_grounded_extractions(src, ex) == []


def test_verify_whitespace_fallback_without_status():
    src = "a  b  c"
    ex = [
        SimpleNamespace(
            extraction_class="x",
            extraction_text="a b c",
            char_interval=SimpleNamespace(start_pos=0, end_pos=7),
        )
    ]
    assert verify_grounded_extractions(src, ex) == []


def test_verify_skips_ungrounded():
    src = "abc"
    ex = [SimpleNamespace(extraction_class="x", extraction_text="nope", char_interval=None)]
    assert verify_grounded_extractions(src, ex) == []


def test_verify_fails_on_mismatch_no_status():
    src = "abcdef"
    ex = [
        SimpleNamespace(
            extraction_class="bad",
            extraction_text="wrong",
            char_interval=SimpleNamespace(start_pos=0, end_pos=3),
        )
    ]
    errs = verify_grounded_extractions(src, ex)
    assert len(errs) == 1
    assert "whitespace-normalized" in errs[0]


def test_verify_match_exact_fails_when_slice_wrong():
    src = "Activity 1 done"
    ex = [
        SimpleNamespace(
            extraction_class="lesson_number",
            extraction_text="Activity 1",
            alignment_status=_Status("match_exact"),
            char_interval=SimpleNamespace(start_pos=0, end_pos=8),
        )
    ]
    errs = verify_grounded_extractions(src, ex)
    assert len(errs) == 1
    assert "match_exact" in errs[0]


def test_verify_match_lesser_allows_shorter_slice():
    """Library partial token match: span in source shorter than extraction_text."""
    src = "prefix activity suffix"
    pos = src.index("activity")
    ex = [
        SimpleNamespace(
            extraction_class="lesson_number",
            extraction_text="Activity 1",
            alignment_status=_Status("match_lesser"),
            char_interval=SimpleNamespace(start_pos=pos, end_pos=pos + len("activity")),
        )
    ]
    assert verify_grounded_extractions(src, ex) == []


def test_verify_require_all_exact_rejects_match_lesser():
    src = "activity"
    ex = [
        SimpleNamespace(
            extraction_class="x",
            extraction_text="Activity 1",
            alignment_status=_Status("match_lesser"),
            char_interval=SimpleNamespace(start_pos=0, end_pos=8),
        )
    ]
    errs = verify_grounded_extractions(src, ex, require_all_exact=True)
    assert len(errs) == 1
    assert "require_all_exact" in errs[0]


def test_verify_fails_out_of_range():
    src = "hi"
    ex = [
        SimpleNamespace(
            extraction_class="x",
            extraction_text="x",
            char_interval=SimpleNamespace(start_pos=0, end_pos=99),
        )
    ]
    errs = verify_grounded_extractions(src, ex)
    assert len(errs) == 1
    assert "out of range" in errs[0]


def test_unicode_match_exact():
    src = "Minus sign: \u2212 and café"
    needle = "\u2212"
    pos = src.index(needle)
    ex = [
        SimpleNamespace(
            extraction_class="sym",
            extraction_text=needle,
            alignment_status=_Status("match_exact"),
            char_interval=SimpleNamespace(start_pos=pos, end_pos=pos + len(needle)),
        )
    ]
    assert verify_grounded_extractions(src, ex) == []
