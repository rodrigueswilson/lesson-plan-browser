"""Unit tests for curriculum gap detection helpers."""

from backend.services.curriculum_gaps import (
    extract_metadata,
    normalize_grade,
    normalize_subject,
)


def test_normalize_grade_kindergarten():
    assert normalize_grade("k") == "Kindergarten"
    assert normalize_grade("K") == "Kindergarten"


def test_normalize_grade_numeric():
    assert normalize_grade("Grade 2") == "Grade 2"
    assert normalize_grade("2") == "Grade 2"


def test_normalize_subject_splits_slash():
    assert normalize_subject("ELA/SS") == "ELA"


def test_extract_metadata_finds_doc_id():
    text = "Unit: 1\nLesson: 2\nSee [Title](https://docs.google.com/document/d/abc123xyz/edit)"
    out = extract_metadata(text)
    assert len(out) == 1
    assert out[0]["id"] == "abc123xyz"
    assert out[0]["unit"] == "1"
    assert out[0]["lesson"] == "2"
