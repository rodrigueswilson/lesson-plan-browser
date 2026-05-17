"""Tests for relational Science day segments (replace + lesson bundle)."""

from __future__ import annotations

import json
import sqlite3

import pytest

from backend.database.curriculum import CurriculumDatabase
from tests.test_curriculum_lesson_bundle import _minimal_curriculum_db


def test_replace_science_lesson_day_segments_and_bundle(tmp_path) -> None:
    db_path = tmp_path / "sci_seg.db"
    _minimal_curriculum_db(str(db_path))
    db = CurriculumDatabase(str(db_path))
    payload = {
        "schema_version": 2,
        "doc_lesson_number": 3,
        "segments": [
            {
                "label": "Day 1",
                "learning_intention_html": "<p>LI</p>",
                "success_criteria_html": "<p>SC</p>",
                "brief_overview": "<p>Bo</p>",
                "lesson_in_action_html": "<table>x</table>",
                "experimental_splits": {"opening_html": "<p>O</p>"},
            },
        ],
    }
    db.replace_science_lesson_day_segments("les1", payload)
    bundle = db.get_lesson_bundle("les1")
    assert bundle is not None
    assert bundle["lesson"]["id"] == "les1"
    segs = bundle["science_day_segments"]
    assert len(segs) == 1
    seg = segs[0]
    assert seg["id"] == "les1_sci_0"
    assert seg["lesson_id"] == "les1"
    assert seg["segment_index"] == 0
    assert seg["day_label"] == "Day 1"
    assert seg["science_doc_lesson_number"] == 3
    assert seg["learning_intention_html"] == "<p>LI</p>"
    assert seg["brief_overview_html"] == "<p>Bo</p>"
    exp = json.loads(seg["experimental_splits_json"])
    assert exp["opening_html"] == "<p>O</p>"

    db.replace_science_lesson_day_segments("les1", None)
    bundle2 = db.get_lesson_bundle("les1")
    assert bundle2 is not None
    assert bundle2["science_day_segments"] == []


def test_replace_accepts_json_string(tmp_path) -> None:
    db_path = tmp_path / "sci_seg2.db"
    _minimal_curriculum_db(str(db_path))
    db = CurriculumDatabase(str(db_path))
    raw = json.dumps(
        {"doc_lesson_number": 1, "segments": [{"label": "Days 2&3"}]},
        ensure_ascii=False,
    )
    db.replace_science_lesson_day_segments("les1", raw)
    bundle = db.get_lesson_bundle("les1")
    assert bundle is not None
    assert len(bundle["science_day_segments"]) == 1
    assert bundle["science_day_segments"][0]["day_label"] == "Days 2&3"


def test_bundle_route_includes_science_day_segments(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    db_path = tmp_path / "sci_bundle_route.db"
    _minimal_curriculum_db(str(db_path))
    p = str(db_path)
    db = CurriculumDatabase(p)
    db.replace_science_lesson_day_segments(
        "les1",
        {"segments": [{"label": "Day 1", "learning_intention_html": "<p>x</p>"}]},
    )
    monkeypatch.setattr(
        "backend.database.curriculum_validation.get_curriculum_schema_issues",
        lambda: [],
    )
    from backend.database.curriculum import CurriculumDatabase as _RealCurriculumDatabase

    monkeypatch.setattr(
        "backend.routers.curriculum.CurriculumDatabase",
        lambda *a, **k: _RealCurriculumDatabase(p),
    )
    from fastapi.testclient import TestClient

    from backend.api import app

    client = TestClient(app)
    r = client.get("/api/curriculum/lessons/les1/bundle")
    assert r.status_code == 200
    body = r.json()
    assert len(body["science_day_segments"]) == 1
    assert body["science_day_segments"][0]["day_label"] == "Day 1"
    assert "<p>x</p>" in (body["science_day_segments"][0]["learning_intention_html"] or "")


def test_get_unit_science_day_outline_orders_lessons_and_counts_bands(tmp_path) -> None:
    db_path = tmp_path / "sci_outline.db"
    _minimal_curriculum_db(str(db_path))
    db = CurriculumDatabase(str(db_path))
    db.ensure_science_lesson_day_segments_table()
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO lessons (id, unit_id, lesson_number, title, content_hash) "
        "VALUES ('les2', 'u1', 2, 'Second', 'h2')"
    )
    conn.commit()
    conn.close()
    db.replace_science_lesson_day_segments(
        "les1",
        {"segments": [{"label": "Day 1"}, {"label": "Days 2&3"}]},
    )
    db.replace_science_lesson_day_segments(
        "les2",
        {"segments": [{"label": "Day 1"}]},
    )
    outline = db.get_unit_science_day_outline("u1")
    assert outline["unit_id"] == "u1"
    assert outline["total_writer_bands"] == 3
    assert len(outline["lessons"]) == 2
    assert outline["lessons"][0]["lesson_id"] == "les1"
    assert [s["day_label"] for s in outline["lessons"][0]["segments"]] == ["Day 1", "Days 2&3"]
    assert [s["day_label"] for s in outline["lessons"][1]["segments"]] == ["Day 1"]


def test_science_day_outline_route(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    db_path = tmp_path / "sci_outline_route.db"
    _minimal_curriculum_db(str(db_path))
    p = str(db_path)
    db = CurriculumDatabase(p)
    db.ensure_science_lesson_day_segments_table()
    db.replace_science_lesson_day_segments(
        "les1",
        {"segments": [{"label": "Day 1"}]},
    )
    monkeypatch.setattr(
        "backend.database.curriculum_validation.get_curriculum_schema_issues",
        lambda: [],
    )
    from backend.database.curriculum import CurriculumDatabase as _RealCurriculumDatabase

    monkeypatch.setattr(
        "backend.routers.curriculum.CurriculumDatabase",
        lambda *a, **k: _RealCurriculumDatabase(p),
    )
    from fastapi.testclient import TestClient

    from backend.api import app

    client = TestClient(app)
    r = client.get("/api/curriculum/units/u1/science-day-outline")
    assert r.status_code == 200
    body = r.json()
    assert body["unit_id"] == "u1"
    assert body["total_writer_bands"] == 1
    assert len(body["lessons"]) == 1
    assert body["lessons"][0]["segments"][0]["day_label"] == "Day 1"
