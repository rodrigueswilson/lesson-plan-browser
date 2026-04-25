"""Grade 2 workbook PDF extract table, alignment helpers, and curriculum routes."""

from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

from backend.api import app
from backend.database.curriculum import CurriculumDatabase
from tools.db.g2_science_book_pdf_common import (
    override_lesson_for_page,
    match_titles_in_head,
)


def _minimal_db_with_extract(tmp_path, *, long_body: bool = False) -> str:
    db_path = tmp_path / "g2_extract.db"
    body = ("x" * 13000) if long_body else "Page one text for lesson."
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE units (
            id TEXT PRIMARY KEY,
            grade INTEGER,
            subject TEXT,
            unit_number INTEGER,
            title TEXT
        );
        CREATE TABLE lessons (
            id TEXT PRIMARY KEY,
            unit_id TEXT,
            lesson_number INTEGER,
            title TEXT,
            procedure_html TEXT,
            narrative_html TEXT,
            content_hash TEXT
        );
        CREATE TABLE vocabulary_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            base_term_en TEXT,
            mw_definition_en TEXT
        );
        CREATE TABLE vocabulary_translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vocab_item_id INTEGER,
            language_code TEXT,
            translated_term TEXT,
            level_1_def TEXT,
            level_2_def TEXT,
            level_3_def TEXT,
            level_4_def TEXT,
            level_5_def TEXT,
            level_6_def TEXT
        );
        CREATE TABLE lesson_vocabulary (
            lesson_id TEXT,
            vocab_item_id INTEGER
        );
        CREATE TABLE standards (
            code TEXT PRIMARY KEY,
            description TEXT,
            subject TEXT
        );
        CREATE TABLE lesson_standards (
            lesson_id TEXT,
            standard_code TEXT
        );
        CREATE TABLE g2_science_book_lesson_extract (
            id TEXT PRIMARY KEY,
            lesson_id TEXT NOT NULL,
            page_number INTEGER NOT NULL,
            body_text TEXT NOT NULL,
            char_count INTEGER,
            content_sha256 TEXT,
            alignment_confidence TEXT NOT NULL DEFAULT 'high',
            alignment_ambiguous INTEGER NOT NULL DEFAULT 0,
            source_pdf_label TEXT NOT NULL,
            ingest_parser_version TEXT NOT NULL,
            ingested_at TEXT NOT NULL,
            FOREIGN KEY(lesson_id) REFERENCES lessons(id),
            UNIQUE(lesson_id, page_number)
        );
        INSERT INTO units VALUES ('u1', 2, 'ELA', 1, 'Unit 1');
        INSERT INTO lessons (id, unit_id, lesson_number, title, content_hash)
        VALUES ('les1', 'u1', 1, 'Hello', 'hashabc');
        INSERT INTO vocabulary_items (base_term_en, mw_definition_en)
        VALUES ('word', 'def');
        INSERT INTO vocabulary_translations (
            vocab_item_id, language_code, translated_term,
            level_1_def, level_2_def, level_3_def, level_4_def, level_5_def, level_6_def
        ) VALUES (1, 'pt', 'palavra', NULL, NULL, NULL, NULL, NULL, NULL);
        INSERT INTO lesson_vocabulary VALUES ('les1', 1);
        INSERT INTO standards VALUES ('NJSLS-ELA.1', 'Desc', 'ELA');
        INSERT INTO lesson_standards VALUES ('les1', 'NJSLS-ELA.1');
        """
    )
    conn.execute(
        """
        INSERT INTO g2_science_book_lesson_extract (
            id, lesson_id, page_number, body_text, char_count, content_sha256,
            alignment_confidence, alignment_ambiguous, source_pdf_label,
            ingest_parser_version, ingested_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "les1_bkp0001",
            "les1",
            1,
            body,
            len(body),
            "deadbeef",
            "high",
            0,
            "Inspire_G2_StudentWorkbook_9780021344871",
            "g2_book_extract@v1",
            "2026-01-01T00:00:00Z",
        ),
    )
    conn.commit()
    conn.close()
    return str(db_path)


def test_match_titles_in_head_prefers_longest_title() -> None:
    head = "Describe Matter and more header text"
    lessons = [
        ("other", "Matter"),
        ("winner", "Describe Matter"),
    ]
    lid, conf, amb = match_titles_in_head(head, lessons)
    assert lid == "winner"
    assert amb == 0
    assert conf in ("high", "low")


def test_override_lesson_for_page_range() -> None:
    ov = [
        {"lesson_id": "A", "page_start": 10, "page_end": 12},
        {"lesson_id": "B", "page": 5},
    ]
    assert override_lesson_for_page(11, ov) == "A"
    assert override_lesson_for_page(5, ov) == "B"
    assert override_lesson_for_page(99, ov) is None


def test_get_lesson_bundle_omits_extracts_by_default(tmp_path) -> None:
    p = _minimal_db_with_extract(tmp_path)
    cur = CurriculumDatabase(p)
    b = cur.get_lesson_bundle("les1")
    assert b is not None
    assert "book_page_extracts" not in b


def test_get_lesson_bundle_includes_extracts_when_requested(tmp_path) -> None:
    p = _minimal_db_with_extract(tmp_path)
    cur = CurriculumDatabase(p)
    b = cur.get_lesson_bundle("les1", include_book_extracts=True)
    assert b is not None
    ex = b.get("book_page_extracts")
    assert ex is not None
    assert len(ex) == 1
    assert ex[0]["page_number"] == 1
    assert "Page one" in ex[0]["body_text"]


@pytest.fixture()
def g2_extract_client(monkeypatch: pytest.MonkeyPatch, tmp_path):
    db_path = _minimal_db_with_extract(tmp_path)
    monkeypatch.setattr(
        "backend.database.curriculum_validation.get_curriculum_schema_issues",
        lambda: [],
    )
    from backend.database.curriculum import CurriculumDatabase as _Real

    monkeypatch.setattr(
        "backend.routers.curriculum.CurriculumDatabase",
        lambda *a, **k: _Real(db_path),
    )
    return TestClient(app), db_path


def test_bundle_include_book_extracts_query(g2_extract_client) -> None:
    client, _ = g2_extract_client
    r = client.get(
        "/api/curriculum/lessons/les1/bundle",
        params={"include_book_extracts": "true"},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["book_page_extracts"]) == 1
    row = body["book_page_extracts"][0]
    assert row["lesson_id"] == "les1"
    assert row["ingest_parser_version"] == "g2_book_extract@v1"


def test_book_extracts_route_truncates_body(g2_extract_client, tmp_path) -> None:
    client, db_path = g2_extract_client
    conn = sqlite3.connect(db_path)
    long_text = "y" * 13000
    conn.execute(
        "UPDATE g2_science_book_lesson_extract SET body_text = ?, char_count = ? WHERE id = ?",
        (long_text, len(long_text), "les1_bkp0001"),
    )
    conn.commit()
    conn.close()

    r = client.get("/api/curriculum/lessons/les1/book-extracts")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["body_text"].endswith("...[truncated]")
    assert len(rows[0]["body_text"]) < len(long_text)


def test_book_extracts_pagination_offset(g2_extract_client, tmp_path) -> None:
    client, db_path = g2_extract_client
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        INSERT INTO g2_science_book_lesson_extract (
            id, lesson_id, page_number, body_text, char_count, content_sha256,
            alignment_confidence, alignment_ambiguous, source_pdf_label,
            ingest_parser_version, ingested_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "les1_bkp0002",
            "les1",
            2,
            "second",
            6,
            "abc",
            "high",
            0,
            "Inspire_G2_StudentWorkbook_9780021344871",
            "g2_book_extract@v1",
            "2026-01-01T00:00:00Z",
        ),
    )
    conn.commit()
    conn.close()

    r = client.get(
        "/api/curriculum/lessons/les1/book-extracts",
        params={"offset": 1, "limit": 1},
    )
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["page_number"] == 2
