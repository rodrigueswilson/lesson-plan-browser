"""
Simple focused tests for analytics functionality.
Tests the core analytics methods with real database.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from datetime import datetime, timedelta
from backend.database import get_db
from backend.performance_tracker import get_tracker


class TestAnalyticsWithRealDatabase:
    """Test analytics with the actual application database."""
    
    def test_get_aggregate_stats_returns_dict(self):
        """Test that get_aggregate_stats returns a dictionary."""
        tracker = get_tracker()
        stats = tracker.get_aggregate_stats(days=30)
        
        assert isinstance(stats, dict)
        assert "total_plans" in stats
        assert "total_operations" in stats
        assert "model_distribution" in stats
        assert "operation_breakdown" in stats
    
    def test_get_aggregate_stats_with_different_days(self):
        """Test aggregate stats with different day ranges."""
        tracker = get_tracker()
        
        stats_7 = tracker.get_aggregate_stats(days=7)
        stats_30 = tracker.get_aggregate_stats(days=30)
        stats_90 = tracker.get_aggregate_stats(days=90)
        
        assert isinstance(stats_7, dict)
        assert isinstance(stats_30, dict)
        assert isinstance(stats_90, dict)
    
    def test_get_daily_breakdown_returns_list(self):
        """Test that get_daily_breakdown returns a list."""
        tracker = get_tracker()
        daily = tracker.get_daily_breakdown(days=30)
        
        assert isinstance(daily, list)
    
    def test_get_daily_breakdown_structure(self):
        """Test daily breakdown data structure."""
        tracker = get_tracker()
        daily = tracker.get_daily_breakdown(days=30)
        
        # If there's data, check structure
        if len(daily) > 0:
            item = daily[0]
            assert "date" in item
            assert "plans" in item
            assert "operations" in item
            assert "duration_ms" in item
            assert "tokens" in item
            assert "cost_usd" in item
    
    def test_export_analytics_csv_returns_string(self):
        """Test that export_analytics_csv returns a string."""
        tracker = get_tracker()
        csv_data = tracker.export_analytics_csv(days=30)
        
        assert isinstance(csv_data, str)
    
    def test_export_analytics_csv_format(self):
        """Test CSV export format when data exists."""
        tracker = get_tracker()
        csv_data = tracker.export_analytics_csv(days=30)
        
        # If there's data, check format
        if csv_data:
            lines = csv_data.strip().split('\n')
            assert len(lines) >= 1  # At least header
            
            # Check header
            header = lines[0]
            assert "date" in header.lower()
    
    def test_aggregate_stats_model_distribution_is_list(self):
        """Test that model distribution is a list."""
        tracker = get_tracker()
        stats = tracker.get_aggregate_stats(days=30)
        
        assert isinstance(stats["model_distribution"], list)
    
    def test_aggregate_stats_operation_breakdown_is_list(self):
        """Test that operation breakdown is a list."""
        tracker = get_tracker()
        stats = tracker.get_aggregate_stats(days=30)
        
        assert isinstance(stats["operation_breakdown"], list)
    
    def test_aggregate_stats_with_user_filter(self):
        """Test aggregate stats with user filter."""
        tracker = get_tracker()
        
        # Test with a fake user ID (should return empty data)
        stats = tracker.get_aggregate_stats(days=30, user_id="nonexistent-user")
        
        assert isinstance(stats, dict)
        assert stats["total_plans"] == 0 or stats["total_plans"] is None
    
    def test_daily_breakdown_with_user_filter(self):
        """Test daily breakdown with user filter."""
        tracker = get_tracker()
        
        # Test with a fake user ID (should return empty list)
        daily = tracker.get_daily_breakdown(days=30, user_id="nonexistent-user")
        
        assert isinstance(daily, list)
    
    def test_aggregate_stats_handles_zero_days(self):
        """Test that zero days is handled gracefully."""
        tracker = get_tracker()
        stats = tracker.get_aggregate_stats(days=0)
        
        assert isinstance(stats, dict)
    
    def test_aggregate_stats_handles_large_days(self):
        """Test that large day ranges are handled."""
        tracker = get_tracker()
        stats = tracker.get_aggregate_stats(days=365)
        
        assert isinstance(stats, dict)
    
    def test_daily_breakdown_sorted_descending(self):
        """Test that daily breakdown is sorted by date descending."""
        tracker = get_tracker()
        daily = tracker.get_daily_breakdown(days=30)
        
        if len(daily) > 1:
            dates = [item["date"] for item in daily]
            # Check if sorted descending
            assert dates == sorted(dates, reverse=True)
    
    def test_model_distribution_structure(self):
        """Test model distribution data structure."""
        tracker = get_tracker()
        stats = tracker.get_aggregate_stats(days=30)
        
        model_dist = stats["model_distribution"]
        
        # If there's data, check structure
        for model in model_dist:
            assert "llm_model" in model
            assert "count" in model
            assert "tokens" in model
            assert "cost" in model
    
    def test_operation_breakdown_structure(self):
        """Test operation breakdown data structure."""
        tracker = get_tracker()
        stats = tracker.get_aggregate_stats(days=30)
        
        op_breakdown = stats["operation_breakdown"]
        
        # If there's data, check structure
        for op in op_breakdown:
            assert "operation_type" in op
            assert "count" in op
            assert "avg_duration_ms" in op
            assert "tokens" in op
    
    def test_tracker_is_enabled(self):
        """Test that tracker is properly initialized."""
        tracker = get_tracker()
        
        assert tracker is not None
        assert hasattr(tracker, 'get_aggregate_stats')
        assert hasattr(tracker, 'get_daily_breakdown')
        assert hasattr(tracker, 'export_analytics_csv')
    
    def test_aggregate_stats_numeric_fields(self):
        """Test that numeric fields are present and correct type."""
        tracker = get_tracker()
        stats = tracker.get_aggregate_stats(days=30)
        
        # These should be numeric or None
        numeric_fields = [
            "total_plans", "total_operations", "total_duration_ms",
            "avg_duration_ms", "total_tokens", "total_cost_usd"
        ]
        
        for field in numeric_fields:
            assert field in stats
            value = stats[field]
            assert value is None or isinstance(value, (int, float))
    
    def test_csv_export_with_no_data_returns_empty(self):
        """Test that CSV export with no data returns empty string."""
        tracker = get_tracker()
        
        # Use a very restrictive filter that won't match anything
        csv_data = tracker.export_analytics_csv(days=0, user_id="impossible-user-id-12345")
        
        # Should return empty string when no data
        assert csv_data == ""


class TestAnalyticsPerformance:
    """Test performance characteristics of analytics queries."""
    
    def test_aggregate_stats_performance(self):
        """Test that aggregate stats query is fast."""
        import time
        
        tracker = get_tracker()
        
        start = time.time()
        stats = tracker.get_aggregate_stats(days=30)
        elapsed = time.time() - start
        
        # Should complete in less than 1 second
        assert elapsed < 1.0
        assert isinstance(stats, dict)
    
    def test_daily_breakdown_performance(self):
        """Test that daily breakdown query is fast."""
        import time
        
        tracker = get_tracker()
        
        start = time.time()
        daily = tracker.get_daily_breakdown(days=30)
        elapsed = time.time() - start
        
        # Should complete in less than 1 second
        assert elapsed < 1.0
        assert isinstance(daily, list)
    
    def test_csv_export_performance(self):
        """Test that CSV export is fast."""
        import time
        
        tracker = get_tracker()
        
        start = time.time()
        csv_data = tracker.export_analytics_csv(days=30)
        elapsed = time.time() - start
        
        # Should complete in less than 1 second
        assert elapsed < 1.0
        assert isinstance(csv_data, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
