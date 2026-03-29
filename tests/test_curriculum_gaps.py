"""Unit tests for curriculum gap detection helpers."""

import json
from pathlib import Path

from backend.services.curriculum_gaps import (
    extract_metadata,
    load_scrapped_doc_ids,
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


def test_load_scrapped_doc_ids_dict(tmp_path: Path):
    p = tmp_path / "scrapped.json"
    p.write_text(
        json.dumps({"doc_one": "note", "doc_two": "other"}),
        encoding="utf-8",
    )
    ids = load_scrapped_doc_ids(str(p))
    assert ids == {"doc_one", "doc_two"}


def test_load_scrapped_doc_ids_missing_file():
    assert load_scrapped_doc_ids("") == set()
    assert load_scrapped_doc_ids("/nonexistent/path/scrapped.json") == set()
