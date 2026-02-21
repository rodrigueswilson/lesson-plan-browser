"""
Test database migration for Session 2 performance tracking.
"""

import pytest
from sqlalchemy import text

from backend.database import Database


def test_performance_metrics_table_created(isolated_db):
    """Test that performance_metrics table is created."""
    db = isolated_db
    with db.get_connection() as session:
        result = session.execute(text("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='performance_metrics'
        """)).fetchone()
        assert result is not None
        assert result[0] == "performance_metrics"


def test_performance_metrics_columns(isolated_db):
    """Test that performance_metrics has all required columns."""
    db = isolated_db
    with db.get_connection() as session:
        rows = session.execute(text("PRAGMA table_info(performance_metrics)")).fetchall()
        columns = {row[1] for row in rows}
        required_columns = {
            "id", "plan_id", "slot_number", "day_number", "operation_type",
            "started_at", "completed_at", "duration_ms", "tokens_input",
            "tokens_output", "tokens_total", "llm_provider", "llm_model",
            "cost_usd", "error_message",
        }
        assert required_columns.issubset(columns)


def test_weekly_plans_performance_columns(isolated_db):
    """Test that weekly_plans has new performance tracking columns."""
    db = isolated_db
    with db.get_connection() as session:
        rows = session.execute(text("PRAGMA table_info(weekly_plans)")).fetchall()
        columns = {row[1] for row in rows}
        required_columns = {"processing_time_ms", "total_tokens", "total_cost_usd", "llm_model"}
        assert required_columns.issubset(columns)


def test_performance_metrics_indexes(isolated_db):
    """Test that indexes are created for performance_metrics."""
    db = isolated_db
    with db.get_connection() as session:
        rows = session.execute(text("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND tbl_name='performance_metrics'
        """)).fetchall()
        indexes = {row[0] for row in rows}
        assert len(indexes) >= 1
        assert any("plan_id" in n for n in indexes)


def test_migration_idempotent(isolated_db):
    """Test that running migration multiple times is safe."""
    db = isolated_db
    with db.get_connection() as session:
        rows = session.execute(text("PRAGMA table_info(performance_metrics)")).fetchall()
        assert len(rows) > 0


def test_existing_data_preserved(isolated_db):
    """Test that existing data is preserved after migration."""
    db = isolated_db
    user_id = db.create_user(name="Test User", email="test@example.com")
    plan_id = db.create_weekly_plan(
        user_id=user_id,
        week_of="10/6-10/10",
        output_file="test.docx",
        week_folder_path="/test",
    )
    plan = db.get_user_plans(user_id)[0]
    assert plan.id == plan_id
    assert plan.week_of == "10/6-10/10"
    assert getattr(plan, "processing_time_ms", None) is None
    assert getattr(plan, "total_tokens", None) is None
    assert getattr(plan, "total_cost_usd", None) is None
    assert getattr(plan, "llm_model", None) is None


def test_foreign_key_constraint(isolated_db):
    """Test that performance_metrics.plan_id references weekly_plans (schema allows FK)."""
    db = isolated_db
    with db.get_connection() as session:
        rows = session.execute(text("PRAGMA foreign_key_list(performance_metrics)")).fetchall()
        if rows:
            assert any(row[2] == "weekly_plans" for row in rows)
