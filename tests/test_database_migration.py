"""
Test database migration for Session 2 performance tracking.
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from backend.database import Database


def test_performance_metrics_table_created():
    """Test that performance_metrics table is created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))
        
        # Check table exists
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='performance_metrics'
            """)
            result = cursor.fetchone()
            assert result is not None
            assert result[0] == "performance_metrics"


def test_performance_metrics_columns():
    """Test that performance_metrics has all required columns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(performance_metrics)")
            columns = {row[1] for row in cursor.fetchall()}
            
            required_columns = {
                "id",
                "plan_id",
                "slot_number",
                "day_number",
                "operation_type",
                "started_at",
                "completed_at",
                "duration_ms",
                "tokens_input",
                "tokens_output",
                "tokens_total",
                "llm_provider",
                "llm_model",
                "cost_usd",
                "error_message",
            }
            
            assert required_columns.issubset(columns)


def test_weekly_plans_performance_columns():
    """Test that weekly_plans has new performance tracking columns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(weekly_plans)")
            columns = {row[1] for row in cursor.fetchall()}
            
            required_columns = {
                "processing_time_ms",
                "total_tokens",
                "total_cost_usd",
                "llm_model",
            }
            
            assert required_columns.issubset(columns)


def test_performance_metrics_indexes():
    """Test that indexes are created for performance_metrics."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND tbl_name='performance_metrics'
            """)
            indexes = {row[0] for row in cursor.fetchall()}
            
            assert "idx_performance_metrics_plan_id" in indexes
            assert "idx_performance_metrics_started_at" in indexes


def test_migration_idempotent():
    """Test that running migration multiple times is safe."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        
        # Create database twice
        db1 = Database(str(db_path))
        db2 = Database(str(db_path))
        
        # Should not raise errors
        with db2.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(performance_metrics)")
            columns = cursor.fetchall()
            assert len(columns) > 0


def test_existing_data_preserved():
    """Test that existing data is preserved after migration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))
        
        # Create test user
        user_id = db.create_user("Test User", "test@example.com")
        
        # Create test weekly plan
        plan_id = db.create_weekly_plan(
            user_id=user_id,
            week_of="10/6-10/10",
            output_file="test.docx",
            week_folder_path="/test",
        )
        
        # Verify data exists
        plan = db.get_user_plans(user_id)[0]
        assert plan["id"] == plan_id
        assert plan["week_of"] == "10/6-10/10"
        
        # New columns should be NULL or have defaults
        assert plan.get("processing_time_ms") is None
        assert plan.get("total_tokens") is None
        assert plan.get("total_cost_usd") is None
        assert plan.get("llm_model") is None


def test_foreign_key_constraint():
    """Test that performance_metrics has foreign key to weekly_plans."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_key_list(performance_metrics)")
            foreign_keys = cursor.fetchall()
            
            # Should have foreign key to weekly_plans
            assert len(foreign_keys) > 0
            assert any(fk[2] == "weekly_plans" for fk in foreign_keys)
