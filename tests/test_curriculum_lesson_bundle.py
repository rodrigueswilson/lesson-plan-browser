"""Lesson bundle endpoint matches separate lesson + vocabulary + standards queries."""

from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

from backend.api import app
from backend.database.curriculum import CurriculumDatabase


def _minimal_curriculum_db(path) -> None:
    conn = sqlite3.connect(path)
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
    conn.commit()
    conn.close()


def test_get_lesson_bundle_matches_individual_queries(tmp_path) -> None:
    db_path = tmp_path / "bundle.db"
    _minimal_curriculum_db(str(db_path))
    cur = CurriculumDatabase(str(db_path))
    b = cur.get_lesson_bundle("les1")
    assert b is not None
    assert b["lesson"] == cur.get_lesson_details("les1")
    assert b["vocabulary"] == cur.get_lesson_vocabulary("les1")
    assert b["standards"] == cur.get_lesson_standards("les1")


def test_bundle_route_and_etag(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    db_path = tmp_path / "bundle_route.db"
    _minimal_curriculum_db(str(db_path))
    p = str(db_path)
    monkeypatch.setattr(
        "backend.database.curriculum_validation.get_curriculum_schema_issues",
        lambda: [],
    )
    from backend.database.curriculum import CurriculumDatabase as _RealCurriculumDatabase

    monkeypatch.setattr(
        "backend.routers.curriculum.CurriculumDatabase",
        lambda *a, **k: _RealCurriculumDatabase(p),
    )

    client = TestClient(app)
    r = client.get("/api/curriculum/lessons/les1/bundle")
    assert r.status_code == 200
    body = r.json()
    assert body["lesson"]["id"] == "les1"
    assert body["lesson"]["title"] == "Hello"
    assert len(body["vocabulary"]) == 1
    assert body["vocabulary"][0]["term"] == "word"
    assert len(body["standards"]) == 1
    assert body["standards"][0]["code"] == "NJSLS-ELA.1"
    assert body.get("science_day_segments") == []
    assert body.get("book_lesson_supplement") is None
    assert body.get("book_page_extracts") == []
    etag = r.headers.get("etag")
    assert etag == '"hashabc"'

    r304 = client.get(
        "/api/curriculum/lessons/les1/bundle",
        headers={"If-None-Match": etag},
    )
    assert r304.status_code == 304
