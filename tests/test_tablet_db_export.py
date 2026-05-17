"""
Tests for tablet DB export and exported DB compatibility with app queries.

Validates the connection between (1) backend export that produces the user-only
tablet DB and (2) the queries the tablet app runs against that DB. When adding
a new column to a standalone query in shared/lesson-api, add it to
REQUIRED_COLUMNS_BY_TABLE below so the export compatibility test stays green.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.database import Database
from backend.tablet_db_export import (
    TABLET_MIGRATIONS_RELATIVE,
    export_user_tablet_db,
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


# Columns the app's standalone queries use (shared/lesson-api). Update when changing lesson-api SELECTs.
REQUIRED_COLUMNS_BY_TABLE = {
    "users": [
        "id",
        "email",
        "first_name",
        "last_name",
        "name",
        "base_path_override",
        "template_path",
        "signature_image_path",
        "created_at",
        "updated_at",
    ],
    "weekly_plans": [
        "id",
        "user_id",
        "week_of",
        "status",
        "output_file",
        "generated_at",
        "error_message",
        "lesson_json",
    ],
    "class_slots": [
        "id",
        "user_id",
        "slot_number",
        "subject",
        "grade",
        "homeroom",
        "plan_group_label",
        "proficiency_levels",
        "primary_teacher_name",
        "primary_teacher_first_name",
        "primary_teacher_last_name",
        "primary_teacher_file_pattern",
        "display_order",
        "created_at",
        "updated_at",
    ],
    "schedules": [
        "id",
        "user_id",
        "day_of_week",
        "slot_number",
        "start_time",
        "end_time",
        "subject",
        "grade",
        "homeroom",
        "plan_slot_group_id",
        "is_active",
        "created_at",
        "updated_at",
    ],
    "lesson_steps": [
        "id",
        "lesson_plan_id",
        "day_of_week",
        "slot_number",
        "step_number",
        "step_name",
        "duration_minutes",
        "start_time_offset",
        "content_type",
        "display_content",
        "hidden_content",
        "sentence_frames",
        "materials_needed",
        "vocabulary_cognates",
        "created_at",
        "updated_at",
    ],
    "lesson_mode_sessions": [
        "id",
        "user_id",
        "lesson_plan_id",
        "schedule_entry_id",
        "day_of_week",
        "slot_number",
        "current_step_index",
        "remaining_time",
        "is_running",
        "is_paused",
        "is_synced",
        "timer_start_time",
        "paused_at",
        "adjusted_durations",
        "session_start_time",
        "last_updated",
        "ended_at",
    ],
}

# Critical SELECTs the app runs in standalone mode (run against exported DB to verify no missing column/table).
APP_CRITICAL_QUERIES = [
    (
        "SELECT id, email, first_name, last_name, name, base_path_override, template_path, signature_image_path, created_at, updated_at FROM users ORDER BY created_at DESC",
        [],
    ),
    (
        "SELECT week_of, MAX(generated_at) as latest_created_at FROM weekly_plans WHERE user_id = ? AND week_of IS NOT NULL GROUP BY week_of ORDER BY MAX(generated_at) DESC LIMIT ?",
        ["test-user-id", 25],
    ),
    (
        "SELECT id, user_id, week_of, status, output_file, generated_at, error_message FROM weekly_plans WHERE user_id = ? ORDER BY generated_at DESC LIMIT ?",
        ["test-user-id", 100],
    ),
]


@pytest.fixture
def source_db_for_export(tmp_path):
    """Create an isolated DB with schema and yield (db, path) for export tests."""
    path = tmp_path / "source.sqlite"
    db = Database(path)
    db.init_db()
    try:
        yield db, path
    finally:
        db.engine.dispose()
        path.unlink(missing_ok=True)


def test_tablet_migrations_exist():
    """Tablet migration files must exist so export can read schema."""
    root = _project_root()
    for rel in TABLET_MIGRATIONS_RELATIVE:
        path = root / rel
        assert path.exists(), f"Tablet migration not found: {path}"


def test_export_user_tablet_db_single_user(source_db_for_export, tmp_path):
    """Export produces a valid single-user DB with expected counts."""
    db, source_path = source_db_for_export
    user_id = db.create_user(name="Test User", email="test@example.com")
    db.create_weekly_plan(
        user_id=user_id,
        week_of="12/9/2025-12/13/2025",
        output_file="out1.docx",
        week_folder_path="w1",
    )
    db.create_weekly_plan(
        user_id=user_id,
        week_of="12/16/2025-12/20/2025",
        output_file="out2.docx",
        week_folder_path="w2",
    )
    output_path = tmp_path / "lesson_planner.db"

    result = export_user_tablet_db(
        source_db_path=source_path,
        user_id=user_id,
        output_db_path=output_path,
        vacuum=True,
        keep_previous_backup=False,
    )

    assert result.counts.users == 1
    assert result.counts.weekly_plans == 2
    assert output_path.exists()
    assert output_path.stat().st_size > 0

    conn = sqlite3.connect(output_path)
    try:
        n_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        n_plans = conn.execute("SELECT COUNT(*) FROM weekly_plans").fetchone()[0]
        assert n_users == 1
        assert n_plans == 2
    finally:
        conn.close()


def test_export_succeeds_with_zero_weekly_plans(source_db_for_export, tmp_path):
    """Export succeeds when user has no weekly_plans."""
    db, source_path = source_db_for_export
    user_id = db.create_user(name="Empty User", email="empty@example.com")
    output_path = tmp_path / "lesson_planner.db"

    result = export_user_tablet_db(
        source_db_path=source_path,
        user_id=user_id,
        output_db_path=output_path,
        vacuum=True,
        keep_previous_backup=False,
    )

    assert result.counts.users == 1
    assert result.counts.weekly_plans == 0
    assert output_path.exists()


def test_exported_db_has_required_columns_for_app(source_db_for_export, tmp_path):
    """Exported DB has all tables and columns the app's standalone queries need."""
    db, source_path = source_db_for_export
    user_id = db.create_user(name="Test User", email="test@example.com")
    db.create_weekly_plan(
        user_id=user_id,
        week_of="12/9/2025-12/13/2025",
        output_file="out.docx",
        week_folder_path="w",
    )
    output_path = tmp_path / "lesson_planner.db"

    export_user_tablet_db(
        source_db_path=source_path,
        user_id=user_id,
        output_db_path=output_path,
        vacuum=True,
        keep_previous_backup=False,
    )

    conn = sqlite3.connect(output_path)
    try:
        for table, required_cols in REQUIRED_COLUMNS_BY_TABLE.items():
            cursor = conn.execute(f"PRAGMA table_info({table})")
            existing = {row[1] for row in cursor.fetchall()}
            for col in required_cols:
                assert col in existing, f"Table {table} missing column {col} (required by app)"
    finally:
        conn.close()


def test_app_queries_run_against_exported_db(source_db_for_export, tmp_path):
    """App-critical SELECTs run without OperationalError on the exported DB."""
    db, source_path = source_db_for_export
    user_id = db.create_user(name="Test User", email="test@example.com")
    db.create_weekly_plan(
        user_id=user_id,
        week_of="12/9/2025-12/13/2025",
        output_file="out.docx",
        week_folder_path="w",
    )
    output_path = tmp_path / "lesson_planner.db"

    export_user_tablet_db(
        source_db_path=source_path,
        user_id=user_id,
        output_db_path=output_path,
        vacuum=True,
        keep_previous_backup=False,
    )

    conn = sqlite3.connect(output_path)
    try:
        for sql, params in APP_CRITICAL_QUERIES:
            qparams = [user_id if p == "test-user-id" else p for p in params]
            cursor = conn.execute(sql, qparams)
            cursor.fetchall()
    except sqlite3.OperationalError as e:
        pytest.fail(f"App query failed on exported DB: {e}\nSQL: {sql}\nParams: {params}")
    finally:
        conn.close()


def test_export_tablet_db_endpoint_returns_counts(source_db_for_export, tmp_path, monkeypatch):
    """POST /api/tablet/export-db returns response with counts when using isolated DB."""
    db, source_path = source_db_for_export
    user_id = db.create_user(name="Endpoint User", email="endpoint@example.com")
    monkeypatch.setattr("backend.config.settings.SQLITE_DB_PATH", source_path)

    try:
        from starlette.testclient import TestClient
        from backend.api import app
        client = TestClient(app)
    except TypeError as e:
        if "unexpected keyword argument 'app'" in str(e):
            pytest.skip(
                "TestClient incompatible with this httpx version. "
                "Use starlette>=0.36 or httpx<0.28."
            )
        raise

    response = client.post(
        "/api/tablet/export-db",
        json={"user_id": user_id},
    )

    assert response.status_code == 200
    data = response.json()
    assert "counts" in data
    assert data["counts"]["users"] >= 1
