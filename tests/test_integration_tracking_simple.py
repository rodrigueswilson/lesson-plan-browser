"""
Simplified integration test for performance tracking.
Tests tracking without full document rendering.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from backend.database import Database
from backend.llm_service import LLMService
from backend.performance_tracker import PerformanceTracker


@pytest.fixture
def test_db():
    """Create test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(str(db_path))
        yield db


@pytest.fixture
def test_plan(test_db):
    """Create test plan."""
    user_id = test_db.create_user("Test Teacher")
    plan_id = test_db.create_weekly_plan(
        user_id=user_id,
        week_of="10/6-10/10",
        output_file="test.docx",
        week_folder_path="/test",
    )
    return plan_id


def test_mock_llm_with_tracking(test_db, test_plan, monkeypatch):
    """Test that LLM service integration captures token usage."""
    
    # Patch get_db
    monkeypatch.setattr("backend.performance_tracker.get_db", lambda: test_db)
    
    # Create tracker
    tracker = PerformanceTracker(enabled=True)
    
    # Simulate what happens in batch processor
    # 1. Start tracking
    op_id = tracker.start_operation(
        plan_id=test_plan,
        operation_type="process_slot",
        metadata={"slot_number": 1, "subject": "Math"}
    )
    
    # 2. Simulate LLM call (this is what the real LLM service returns)
    mock_usage = {
        "tokens_input": 1500,
        "tokens_output": 800,
        "tokens_total": 2300
    }
    
    # 3. End tracking with usage
    import time
    time.sleep(0.001)  # Small delay to ensure measurable duration
    
    tracker.end_operation(op_id, result={
        "tokens_input": mock_usage["tokens_input"],
        "tokens_output": mock_usage["tokens_output"],
        "llm_model": "gpt-4-turbo-preview",
        "llm_provider": "openai"
    })
    
    # Verify metrics were recorded
    metrics = tracker.get_plan_metrics(test_plan)
    assert len(metrics) == 1
    
    metric = metrics[0]
    assert metric["plan_id"] == test_plan
    assert metric["operation_type"] == "process_slot"
    assert metric["slot_number"] == 1
    assert metric["tokens_input"] == 1500
    assert metric["tokens_output"] == 800
    assert metric["tokens_total"] == 2300
    assert metric["llm_model"] == "gpt-4-turbo-preview"
    assert metric["llm_provider"] == "openai"
    assert metric["duration_ms"] >= 0  # Allow zero for very fast operations
    
    # Verify cost calculation
    # (1500/1000 * 0.01) + (800/1000 * 0.03) = 0.015 + 0.024 = 0.039
    expected_cost = 0.039
    assert abs(metric["cost_usd"] - expected_cost) < 0.0001


def test_multiple_operations_tracking(test_db, test_plan, monkeypatch):
    """Test tracking multiple operations."""
    
    monkeypatch.setattr("backend.performance_tracker.get_db", lambda: test_db)
    tracker = PerformanceTracker(enabled=True)
    
    # Simulate processing 3 slots
    for slot_num in range(1, 4):
        op_id = tracker.start_operation(
            plan_id=test_plan,
            operation_type="process_slot",
            metadata={"slot_number": slot_num, "subject": f"Subject{slot_num}"}
        )
        
        tracker.end_operation(op_id, result={
            "tokens_input": 1000 * slot_num,
            "tokens_output": 500 * slot_num,
            "llm_model": "gpt-4-turbo-preview",
            "llm_provider": "openai"
        })
    
    # Verify all metrics recorded
    metrics = tracker.get_plan_metrics(test_plan)
    assert len(metrics) == 3
    
    # Verify summary
    summary = tracker.get_plan_summary(test_plan)
    assert summary["operation_count"] == 3
    assert summary["total_tokens_input"] == 6000  # 1000 + 2000 + 3000
    assert summary["total_tokens_output"] == 3000  # 500 + 1000 + 1500
    assert summary["total_tokens"] == 9000
    assert summary["total_cost_usd"] > 0
    
    # Update plan summary
    success = tracker.update_plan_summary(test_plan)
    assert success is True
    
    # Verify weekly_plans table updated
    with test_db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM weekly_plans WHERE id = ?", (test_plan,))
        plan = dict(cursor.fetchone())
        
        assert plan["total_tokens"] == 9000
        assert plan["total_cost_usd"] > 0
        assert plan["llm_model"] == "gpt-4-turbo-preview"


def test_tracking_with_errors(test_db, test_plan, monkeypatch):
    """Test that errors are tracked properly."""
    
    monkeypatch.setattr("backend.performance_tracker.get_db", lambda: test_db)
    tracker = PerformanceTracker(enabled=True)
    
    # Start operation
    op_id = tracker.start_operation(
        plan_id=test_plan,
        operation_type="process_slot",
        metadata={"slot_number": 1}
    )
    
    # End with error
    tracker.end_operation(op_id, result={
        "error": "Mock LLM API error"
    })
    
    # Verify error was recorded
    metrics = tracker.get_plan_metrics(test_plan)
    assert len(metrics) == 1
    assert metrics[0]["error_message"] == "Mock LLM API error"
    assert metrics[0]["tokens_input"] == 0
    assert metrics[0]["cost_usd"] == 0.0


def test_csv_export_with_mock_data(test_db, test_plan, monkeypatch):
    """Test CSV export with mock tracking data."""
    
    monkeypatch.setattr("backend.performance_tracker.get_db", lambda: test_db)
    tracker = PerformanceTracker(enabled=True)
    
    # Create some mock operations
    for i in range(3):
        op_id = tracker.start_operation(
            plan_id=test_plan,
            operation_type="process_slot",
            metadata={"slot_number": i + 1}
        )
        
        tracker.end_operation(op_id, result={
            "tokens_input": 1000,
            "tokens_output": 500,
            "llm_model": "gpt-4-turbo-preview",
            "llm_provider": "openai"
        })
    
    # Export to CSV
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test_metrics.csv"
        result_path = tracker.export_to_csv(test_plan, str(csv_path))
        
        assert result_path == str(csv_path)
        assert csv_path.exists()
        
        # Verify CSV content
        with open(csv_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")
            
            # Should have header + 3 data rows
            assert len([l for l in lines if l.strip()]) >= 4
            
            # Verify headers
            assert "tokens_input" in lines[0]
            assert "tokens_output" in lines[0]
            assert "cost_usd" in lines[0]
            assert "llm_model" in lines[0]
            
            # Verify data
            assert "1000" in content
            assert "500" in content
            assert "gpt-4-turbo-preview" in content


def test_tracking_disabled_no_data(test_db, test_plan, monkeypatch):
    """Test that no data is recorded when tracking is disabled."""
    
    monkeypatch.setattr("backend.performance_tracker.get_db", lambda: test_db)
    tracker = PerformanceTracker(enabled=False)
    
    # Try to track (should be no-op)
    op_id = tracker.start_operation(
        plan_id=test_plan,
        operation_type="process_slot"
    )
    
    assert op_id == ""  # Returns empty string when disabled
    
    tracker.end_operation(op_id, result={
        "tokens_input": 1000,
        "tokens_output": 500
    })
    
    # Verify no metrics recorded
    metrics = tracker.get_plan_metrics(test_plan)
    assert len(metrics) == 0


def test_cost_accuracy_for_different_models():
    """Test cost calculations for various models."""
    from backend.model_pricing import calculate_cost
    
    test_cases = [
        # (model, input_tokens, output_tokens, expected_cost)
        ("gpt-4-turbo-preview", 1000, 500, 0.025),
        ("gpt-4", 1000, 500, 0.060),
        ("gpt-3.5-turbo", 1000, 500, 0.00125),
        ("claude-3-opus-20240229", 1000, 500, 0.0525),
        ("claude-3-sonnet-20240229", 1000, 500, 0.0105),
    ]
    
    for model, input_tok, output_tok, expected in test_cases:
        cost = calculate_cost(model, input_tok, output_tok)
        assert abs(cost - expected) < 0.0001, f"Cost mismatch for {model}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
