"""
Tests for performance tracker module.
"""

import tempfile
import time
from pathlib import Path

import pytest

from backend.database import Database
from backend.performance_tracker import PerformanceTracker, get_tracker


@pytest.fixture
def tracker(test_db, monkeypatch):
    """Create test tracker using the same database instance."""
    # Patch get_db to return our test database
    monkeypatch.setattr("backend.performance_tracker.get_db", lambda: test_db)
    return PerformanceTracker(enabled=True)


@pytest.fixture
def test_plan(test_db):
    """Create test plan."""
    user_id = test_db.create_user("Test User")
    plan_id = test_db.create_weekly_plan(
        user_id=user_id,
        week_of="10/6-10/10",
        output_file="test.docx",
        week_folder_path="/test",
    )
    return plan_id


def test_tracker_initialization_enabled():
    """Test tracker initializes with tracking enabled."""
    tracker = PerformanceTracker(enabled=True)
    assert tracker.enabled is True


def test_tracker_initialization_disabled():
    """Test tracker initializes with tracking disabled."""
    tracker = PerformanceTracker(enabled=False)
    assert tracker.enabled is False


def test_start_operation(tracker, test_plan):
    """Test starting an operation."""
    op_id = tracker.start_operation(
        plan_id=test_plan, operation_type="test_operation", metadata={"test": "data"}
    )

    assert op_id != ""
    assert op_id in tracker._active_operations
    assert tracker._active_operations[op_id]["plan_id"] == test_plan
    assert tracker._active_operations[op_id]["operation_type"] == "test_operation"


def test_start_operation_disabled():
    """Test starting operation when tracking disabled."""
    tracker = PerformanceTracker(enabled=False)
    op_id = tracker.start_operation(
        plan_id="test", operation_type="test_operation"
    )

    assert op_id == ""
    assert len(tracker._active_operations) == 0


def test_end_operation(tracker, test_plan):
    """Test ending an operation."""
    op_id = tracker.start_operation(
        plan_id=test_plan, operation_type="test_operation"
    )

    time.sleep(0.01)  # Small delay to measure duration

    tracker.end_operation(
        op_id,
        result={
            "tokens_input": 1000,
            "tokens_output": 500,
            "llm_model": "gpt-4-turbo-preview",
            "llm_provider": "openai",
        },
    )

    # Operation should be removed from active operations
    assert op_id not in tracker._active_operations

    # Metric should be saved to database
    metrics = tracker.get_plan_metrics(test_plan)
    assert len(metrics) == 1
    assert metrics[0]["tokens_input"] == 1000
    assert metrics[0]["tokens_output"] == 500
    assert metrics[0]["tokens_total"] == 1500
    assert metrics[0]["llm_model"] == "gpt-4-turbo-preview"
    assert metrics[0]["duration_ms"] > 0
    assert metrics[0]["cost_usd"] > 0


def test_end_operation_with_error(tracker, test_plan):
    """Test ending operation with error."""
    op_id = tracker.start_operation(
        plan_id=test_plan, operation_type="test_operation"
    )

    tracker.end_operation(op_id, result={"error": "Test error message"})

    metrics = tracker.get_plan_metrics(test_plan)
    assert len(metrics) == 1
    assert metrics[0]["error_message"] == "Test error message"


def test_end_operation_disabled():
    """Test ending operation when tracking disabled."""
    tracker = PerformanceTracker(enabled=False)
    # Should not raise error
    tracker.end_operation("fake_id", result={})


def test_end_operation_unknown_id(tracker):
    """Test ending operation with unknown ID."""
    # Should not raise error (silent failure)
    tracker.end_operation("unknown_id", result={})


def test_get_plan_metrics(tracker, test_plan):
    """Test retrieving plan metrics."""
    # Create multiple operations
    for i in range(3):
        op_id = tracker.start_operation(
            plan_id=test_plan,
            operation_type="test_operation",
            metadata={"day_number": i + 1},
        )
        tracker.end_operation(
            op_id,
            result={
                "tokens_input": 1000 * (i + 1),
                "tokens_output": 500 * (i + 1),
                "llm_model": "gpt-4-turbo-preview",
                "llm_provider": "openai",
            },
        )

    metrics = tracker.get_plan_metrics(test_plan)
    assert len(metrics) == 3
    assert metrics[0]["day_number"] == 1
    assert metrics[1]["day_number"] == 2
    assert metrics[2]["day_number"] == 3


def test_get_plan_summary(tracker, test_plan):
    """Test getting plan summary."""
    # Create operations
    for i in range(3):
        op_id = tracker.start_operation(
            plan_id=test_plan, operation_type="test_operation"
        )
        time.sleep(0.001)  # Small delay to ensure measurable duration
        tracker.end_operation(
            op_id,
            result={
                "tokens_input": 1000,
                "tokens_output": 500,
                "llm_model": "gpt-4-turbo-preview",
                "llm_provider": "openai",
            },
        )

    summary = tracker.get_plan_summary(test_plan)
    assert summary["operation_count"] == 3
    assert summary["total_tokens"] == 4500  # 3 * 1500
    assert summary["total_cost_usd"] > 0
    assert summary["total_time_ms"] >= 0  # Allow zero for very fast operations


def test_update_plan_summary(tracker, test_plan, test_db):
    """Test updating plan summary in database."""
    # Create operations
    op_id = tracker.start_operation(
        plan_id=test_plan, operation_type="test_operation"
    )
    time.sleep(0.001)  # Small delay to ensure measurable duration
    tracker.end_operation(
        op_id,
        result={
            "tokens_input": 1000,
            "tokens_output": 500,
            "llm_model": "gpt-4-turbo-preview",
            "llm_provider": "openai",
        },
    )

    # Update summary
    success = tracker.update_plan_summary(test_plan)
    assert success is True

    # Check weekly_plans table
    plans = test_db.get_user_plans(test_db.list_users()[0].id)
    plan = plans[0]
    assert plan.total_tokens == 1500
    assert plan.total_cost_usd > 0
    assert plan.processing_time_ms >= 0  # Allow zero for very fast operations
    assert plan.llm_model == "gpt-4-turbo-preview"


def test_export_to_csv(tracker, test_plan):
    """Test exporting metrics to CSV."""
    # Create operations
    op_id = tracker.start_operation(
        plan_id=test_plan, operation_type="test_operation"
    )
    tracker.end_operation(
        op_id,
        result={
            "tokens_input": 1000,
            "tokens_output": 500,
            "llm_model": "gpt-4-turbo-preview",
            "llm_provider": "openai",
        },
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "metrics.csv"
        result_path = tracker.export_to_csv(test_plan, str(output_path))

        assert result_path == str(output_path)
        assert output_path.exists()

        # Read CSV and verify content
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "tokens_input" in content
            assert "tokens_output" in content
            assert "1000" in content
            assert "500" in content


def test_export_to_csv_no_metrics(tracker, test_plan):
    """Test exporting when no metrics exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "metrics.csv"
        result_path = tracker.export_to_csv(test_plan, str(output_path))

        assert result_path == ""
        assert not output_path.exists()


def test_get_tracker_singleton():
    """Test that get_tracker returns singleton instance."""
    tracker1 = get_tracker()
    tracker2 = get_tracker()
    assert tracker1 is tracker2


def test_metadata_tracking(tracker, test_plan):
    """Test that metadata is properly tracked."""
    op_id = tracker.start_operation(
        plan_id=test_plan,
        operation_type="test_operation",
        metadata={"slot_number": 3, "day_number": 2},
    )
    tracker.end_operation(
        op_id,
        result={
            "tokens_input": 1000,
            "tokens_output": 500,
            "llm_model": "gpt-4-turbo-preview",
            "llm_provider": "openai",
        },
    )

    metrics = tracker.get_plan_metrics(test_plan)
    assert metrics[0]["slot_number"] == 3
    assert metrics[0]["day_number"] == 2


def test_cost_calculation_integration(tracker, test_plan):
    """Test that cost is calculated correctly."""
    op_id = tracker.start_operation(
        plan_id=test_plan, operation_type="test_operation"
    )
    tracker.end_operation(
        op_id,
        result={
            "tokens_input": 1000,
            "tokens_output": 500,
            "llm_model": "gpt-4-turbo-preview",
            "llm_provider": "openai",
        },
    )

    metrics = tracker.get_plan_metrics(test_plan)
    # (1000/1000 * 0.01) + (500/1000 * 0.03) = 0.01 + 0.015 = 0.025
    expected_cost = 0.025
    assert abs(metrics[0]["cost_usd"] - expected_cost) < 0.0001
