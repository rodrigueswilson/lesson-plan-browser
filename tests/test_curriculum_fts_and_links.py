"""Phase 6: FTS5 lesson search and semantic link table behavior."""

from __future__ import annotations

import sqlite3

import pytest

from backend.database.curriculum import CurriculumDatabase, _fts5_prefix_query


def test_fts5_prefix_query_builds_and_escapes() -> None:
    assert _fts5_prefix_query("area model") == '"area"* AND "model"*'
    assert _fts5_prefix_query('foo "bar') == '"foo"* AND "bar"*'
    assert _fts5_prefix_query("a") is None


def test_search_uses_fts_and_snippet(tmp_path) -> None:
    db_path = tmp_path / "c.db"
    conn = sqlite3.connect(db_path)
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
            narrative_html TEXT
        );
        INSERT INTO units (id, grade, subject, unit_number, title)
        VALUES ('u1', 3, 'Math', 1, 'Unit One');
        INSERT INTO lessons (id, unit_id, lesson_number, title, procedure_html, narrative_html)
        VALUES (
            'l1',
            'u1',
            1,
            'Intro',
            '<p>Explore the area model for multiplication</p>',
            ''
        );
        """
    )
    conn.close()

    cur = CurriculumDatabase(str(db_path))
    hits = cur.search_lessons_text("area multiplication", limit=10)
    assert len(hits) == 1
    assert hits[0]["id"] == "l1"
    assert hits[0].get("snippet_html")
    assert "<mark>" in hits[0]["snippet_html"]


def test_semantic_links_merge_manual_and_suggested(tmp_path) -> None:
    db_path = tmp_path / "c2.db"
    conn = sqlite3.connect(db_path)
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
            narrative_html TEXT
        );
        INSERT INTO units VALUES ('g3u', 3, 'Math', 1, 'G3 Unit');
        INSERT INTO units VALUES ('g4u', 4, 'Math', 1, 'G4 Unit');
        INSERT INTO units VALUES ('g2u', 2, 'Math', 1, 'G2 Unit');
        """
    )
    conn.close()

    cur = CurriculumDatabase(str(db_path))
    cur.ensure_unit_semantic_links_table()
    with cur._get_conn() as cx:
        cx.execute(
            """
            INSERT INTO unit_semantic_links
            (id, from_unit_id, to_unit_id, link_kind, rationale, source)
            VALUES ('lk1', 'g3u', 'g4u', 'vertical', 'Official successor unit', 'manual')
            """
        )
        cx.commit()

    links = cur.get_unit_semantic_links("g3u")
    kinds = {(x["to_unit_id"], x["source"], x["link_kind"]) for x in links}
    assert ("g4u", "manual", "vertical") in kinds
    assert ("g2u", "suggested", "vertical_band") in kinds
