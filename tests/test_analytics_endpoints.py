"""
Unit tests for analytics API endpoints.
Tests the backend analytics functionality with mock data.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from datetime import datetime, timedelta
from backend.database import Database
from backend.performance_tracker import PerformanceTracker


@pytest.fixture
def db():
    """Create a test database."""
    db = Database(":memory:")
    # Initialize schema
    db.init_db()
    yield db


@pytest.fixture
def tracker(db):
    """Create a performance tracker with test database."""
    tracker = PerformanceTracker(enabled=True)
    tracker.db = db
    return tracker


@pytest.fixture
def sample_data(db):
    """Create sample data for testing."""
    # Create a test user
    user_id = db.create_user("Test User", "test@example.com")
    
    # Create test weekly plans
    plan_ids = []
    for i in range(3):
        plan_id = db.create_weekly_plan(
            user_id=user_id,
            week_of=f"2025-10-{15+i:02d}",
            output_file=f"test_plan_{i}.docx",
            week_folder_path="/test/path",
        )
        plan_ids.append(plan_id)
    
    # Add performance metrics
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        for idx, plan_id in enumerate(plan_ids):
            # Add parse operations
            cursor.execute(
                """
                INSERT INTO performance_metrics 
                (plan_id, operation_type, duration_ms, tokens_input, tokens_output, 
                 tokens_total, llm_model, llm_provider, cost_usd, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_id,
                    "parse_slot",
                    1500 + idx * 100,
                    0,
                    0,
                    0,
                    None,
                    None,
                    0.0,
                    (datetime.now() - timedelta(days=idx)).isoformat(),
                    (datetime.now() - timedelta(days=idx)).isoformat(),
                ),
            )
            
            # Add process operations
            cursor.execute(
                """
                INSERT INTO performance_metrics 
                (plan_id, operation_type, duration_ms, tokens_input, tokens_output, 
                 tokens_total, llm_model, llm_provider, cost_usd, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_id,
                    "process_slot",
                    3000 + idx * 200,
                    1000 + idx * 100,
                    500 + idx * 50,
                    1500 + idx * 150,
                    "gpt-4o-mini",
                    "openai",
                    0.002 + idx * 0.001,
                    (datetime.now() - timedelta(days=idx)).isoformat(),
                    (datetime.now() - timedelta(days=idx)).isoformat(),
                ),
            )
            
            # Add render operations
            cursor.execute(
                """
                INSERT INTO performance_metrics 
                (plan_id, operation_type, duration_ms, tokens_input, tokens_output, 
                 tokens_total, llm_model, llm_provider, cost_usd, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_id,
                    "render_document",
                    2000 + idx * 150,
                    0,
                    0,
                    0,
                    None,
                    None,
                    0.0,
                    (datetime.now() - timedelta(days=idx)).isoformat(),
                    (datetime.now() - timedelta(days=idx)).isoformat(),
                ),
            )
    
    return {"user_id": user_id, "plan_ids": plan_ids}


class TestAggregateStats:
    """Test aggregate statistics functionality."""
    
    def test_get_aggregate_stats_empty(self, tracker):
        """Test aggregate stats with no data."""
        stats = tracker.get_aggregate_stats(days=30)
        
        assert stats["total_plans"] == 0
        assert stats["total_operations"] == 0
        assert stats["total_cost_usd"] is None or stats["total_cost_usd"] == 0
        assert len(stats["model_distribution"]) == 0
        assert len(stats["operation_breakdown"]) == 0
    
    def test_get_aggregate_stats_with_data(self, tracker, sample_data):
        """Test aggregate stats with sample data."""
        stats = tracker.get_aggregate_stats(days=30)
        
        # Should have 3 plans
        assert stats["total_plans"] == 3
        
        # Should have 9 operations (3 plans * 3 operations each)
        assert stats["total_operations"] == 9
        
        # Should have positive duration
        assert stats["total_duration_ms"] > 0
        assert stats["avg_duration_ms"] > 0
        
        # Should have tokens from process operations
        assert stats["total_tokens"] > 0
        assert stats["total_tokens_input"] > 0
        assert stats["total_tokens_output"] > 0
        
        # Should have cost from process operations
        assert stats["total_cost_usd"] > 0
        assert stats["avg_cost_usd"] > 0
        
        # Should have model distribution
        assert len(stats["model_distribution"]) > 0
        assert stats["model_distribution"][0]["llm_model"] == "gpt-4o-mini"
        
        # Should have operation breakdown
        assert len(stats["operation_breakdown"]) == 3
        operation_types = {op["operation_type"] for op in stats["operation_breakdown"]}
        assert "parse_slot" in operation_types
        assert "process_slot" in operation_types
        assert "render_document" in operation_types
    
    def test_get_aggregate_stats_with_user_filter(self, tracker, sample_data):
        """Test aggregate stats filtered by user."""
        user_id = sample_data["user_id"]
        stats = tracker.get_aggregate_stats(days=30, user_id=user_id)
        
        assert stats["total_plans"] == 3
        assert stats["total_operations"] == 9
    
    def test_get_aggregate_stats_with_time_filter(self, tracker, sample_data):
        """Test aggregate stats with different time ranges."""
        # Last 1 day should have 1 plan
        stats_1d = tracker.get_aggregate_stats(days=1)
        assert stats_1d["total_plans"] >= 1
        
        # Last 30 days should have all 3 plans
        stats_30d = tracker.get_aggregate_stats(days=30)
        assert stats_30d["total_plans"] == 3


class TestDailyBreakdown:
    """Test daily breakdown functionality."""
    
    def test_get_daily_breakdown_empty(self, tracker):
        """Test daily breakdown with no data."""
        daily = tracker.get_daily_breakdown(days=30)
        assert len(daily) == 0
    
    def test_get_daily_breakdown_with_data(self, tracker, sample_data):
        """Test daily breakdown with sample data."""
        daily = tracker.get_daily_breakdown(days=30)
        
        # Should have data for 3 days (one plan per day)
        assert len(daily) == 3
        
        # Each day should have required fields
        for day_data in daily:
            assert "date" in day_data
            assert "plans" in day_data
            assert "operations" in day_data
            assert "duration_ms" in day_data
            assert "tokens" in day_data
            assert "cost_usd" in day_data
            
            # Each day should have 1 plan and 3 operations
            assert day_data["plans"] == 1
            assert day_data["operations"] == 3
    
    def test_get_daily_breakdown_sorted(self, tracker, sample_data):
        """Test that daily breakdown is sorted by date descending."""
        daily = tracker.get_daily_breakdown(days=30)
        
        dates = [day["date"] for day in daily]
        assert dates == sorted(dates, reverse=True)
    
    def test_get_daily_breakdown_with_user_filter(self, tracker, sample_data):
        """Test daily breakdown filtered by user."""
        user_id = sample_data["user_id"]
        daily = tracker.get_daily_breakdown(days=30, user_id=user_id)
        
        assert len(daily) == 3


class TestCSVExport:
    """Test CSV export functionality."""
    
    def test_export_analytics_csv_empty(self, tracker):
        """Test CSV export with no data."""
        csv_data = tracker.export_analytics_csv(days=30)
        assert csv_data == ""
    
    def test_export_analytics_csv_with_data(self, tracker, sample_data):
        """Test CSV export with sample data."""
        csv_data = tracker.export_analytics_csv(days=30)
        
        # Should have content
        assert len(csv_data) > 0
        
        # Should have header row
        lines = csv_data.strip().split('\n')
        assert len(lines) > 1  # Header + data rows
        
        # Header should have expected columns
        header = lines[0]
        assert "date" in header
        assert "plans" in header
        assert "operations" in header
        assert "duration_ms" in header
        assert "tokens" in header
        assert "cost_usd" in header
        
        # Should have 3 data rows (one per day)
        assert len(lines) == 4  # Header + 3 data rows
    
    def test_export_analytics_csv_format(self, tracker, sample_data):
        """Test CSV export format is valid."""
        csv_data = tracker.export_analytics_csv(days=30)
        
        lines = csv_data.strip().split('\n')
        header_cols = lines[0].split(',')
        
        # Each data row should have same number of columns as header
        for line in lines[1:]:
            data_cols = line.split(',')
            assert len(data_cols) == len(header_cols)


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_aggregate_stats_with_zero_days(self, tracker, sample_data):
        """Test with zero days (should still work)."""
        stats = tracker.get_aggregate_stats(days=0)
        # Should return empty or minimal data
        assert isinstance(stats, dict)
    
    def test_aggregate_stats_with_large_days(self, tracker, sample_data):
        """Test with very large day range."""
        stats = tracker.get_aggregate_stats(days=365)
        assert stats["total_plans"] == 3  # Still only 3 plans
    
    def test_aggregate_stats_with_invalid_user(self, tracker, sample_data):
        """Test with non-existent user ID."""
        stats = tracker.get_aggregate_stats(days=30, user_id="invalid-user-id")
        assert stats["total_plans"] == 0
    
    def test_daily_breakdown_with_negative_days(self, tracker, sample_data):
        """Test daily breakdown with negative days."""
        # Should handle gracefully (likely return empty)
        daily = tracker.get_daily_breakdown(days=-1)
        assert isinstance(daily, list)


class TestModelDistribution:
    """Test model distribution calculations."""
    
    def test_model_distribution_counts(self, tracker, sample_data):
        """Test that model distribution counts are correct."""
        stats = tracker.get_aggregate_stats(days=30)
        
        model_dist = stats["model_distribution"]
        assert len(model_dist) == 1  # Only one model used
        
        model = model_dist[0]
        assert model["llm_model"] == "gpt-4o-mini"
        assert model["count"] == 3  # 3 process operations
        assert model["tokens"] > 0
        assert model["cost"] > 0
    
    def test_model_distribution_excludes_none(self, tracker, sample_data):
        """Test that None models are excluded from distribution."""
        stats = tracker.get_aggregate_stats(days=30)
        
        model_dist = stats["model_distribution"]
        for model in model_dist:
            assert model["llm_model"] is not None


class TestOperationBreakdown:
    """Test operation breakdown calculations."""
    
    def test_operation_breakdown_types(self, tracker, sample_data):
        """Test that all operation types are included."""
        stats = tracker.get_aggregate_stats(days=30)
        
        op_breakdown = stats["operation_breakdown"]
        operation_types = {op["operation_type"] for op in op_breakdown}
        
        assert "parse_slot" in operation_types
        assert "process_slot" in operation_types
        assert "render_document" in operation_types
    
    def test_operation_breakdown_counts(self, tracker, sample_data):
        """Test that operation counts are correct."""
        stats = tracker.get_aggregate_stats(days=30)
        
        op_breakdown = stats["operation_breakdown"]
        
        # Each operation type should have count of 3 (one per plan)
        for op in op_breakdown:
            assert op["count"] == 3
            assert op["avg_duration_ms"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
