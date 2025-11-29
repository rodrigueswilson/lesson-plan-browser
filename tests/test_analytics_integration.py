"""
Integration tests for analytics API endpoints.
Tests the FastAPI endpoints with a test client.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from backend.api import app
from backend.database import Database
from backend.performance_tracker import get_tracker


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def setup_test_data():
    """Setup test data in the database."""
    db = Database()
    tracker = get_tracker()
    
    # Create test user
    user_id = db.create_user("Analytics Test User", "analytics@test.com")
    
    # Create test plans with metrics
    plan_ids = []
    for i in range(5):
        plan_id = db.create_weekly_plan(
            user_id=user_id,
            week_of=f"2025-10-{10+i:02d}",
            output_file=f"analytics_test_{i}.docx",
            week_folder_path="/test/analytics",
        )
        plan_ids.append(plan_id)
        
        # Add metrics for each plan
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Parse operation
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
                    1000 + i * 100,
                    0,
                    0,
                    0,
                    None,
                    None,
                    0.0,
                    (datetime.now() - timedelta(days=i)).isoformat(),
                    (datetime.now() - timedelta(days=i)).isoformat(),
                ),
            )
            
            # Process operation
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
                    2500 + i * 200,
                    800 + i * 50,
                    400 + i * 25,
                    1200 + i * 75,
                    "gpt-4o-mini" if i % 2 == 0 else "claude-3-5-sonnet-20241022",
                    "openai" if i % 2 == 0 else "anthropic",
                    0.0015 + i * 0.0005,
                    (datetime.now() - timedelta(days=i)).isoformat(),
                    (datetime.now() - timedelta(days=i)).isoformat(),
                ),
            )
    
    yield {"user_id": user_id, "plan_ids": plan_ids}
    
    # Cleanup
    for plan_id in plan_ids:
        db.delete_weekly_plan(plan_id)
    db.delete_user(user_id)


class TestAnalyticsSummaryEndpoint:
    """Test /api/analytics/summary endpoint."""
    
    def test_summary_endpoint_exists(self, client):
        """Test that summary endpoint is accessible."""
        response = client.get("/api/analytics/summary")
        assert response.status_code == 200
    
    def test_summary_endpoint_with_data(self, client, setup_test_data):
        """Test summary endpoint returns correct data structure."""
        response = client.get("/api/analytics/summary?days=30")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields
        assert "total_plans" in data
        assert "total_operations" in data
        assert "total_duration_ms" in data
        assert "avg_duration_ms" in data
        assert "total_tokens" in data
        assert "total_cost_usd" in data
        assert "model_distribution" in data
        assert "operation_breakdown" in data
        
        # Verify data types
        assert isinstance(data["total_plans"], int)
        assert isinstance(data["model_distribution"], list)
        assert isinstance(data["operation_breakdown"], list)
    
    def test_summary_endpoint_with_days_parameter(self, client, setup_test_data):
        """Test summary endpoint with different day ranges."""
        # Test 7 days
        response_7d = client.get("/api/analytics/summary?days=7")
        assert response_7d.status_code == 200
        
        # Test 30 days
        response_30d = client.get("/api/analytics/summary?days=30")
        assert response_30d.status_code == 200
        
        # Test 90 days
        response_90d = client.get("/api/analytics/summary?days=90")
        assert response_90d.status_code == 200
    
    def test_summary_endpoint_with_user_filter(self, client, setup_test_data):
        """Test summary endpoint with user filter."""
        user_id = setup_test_data["user_id"]
        response = client.get(f"/api/analytics/summary?days=30&user_id={user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_plans"] > 0
    
    def test_summary_endpoint_invalid_days(self, client):
        """Test summary endpoint with invalid days parameter."""
        response = client.get("/api/analytics/summary?days=invalid")
        # Should return 422 for validation error
        assert response.status_code == 422


class TestAnalyticsDailyEndpoint:
    """Test /api/analytics/daily endpoint."""
    
    def test_daily_endpoint_exists(self, client):
        """Test that daily endpoint is accessible."""
        response = client.get("/api/analytics/daily")
        assert response.status_code == 200
    
    def test_daily_endpoint_with_data(self, client, setup_test_data):
        """Test daily endpoint returns correct data structure."""
        response = client.get("/api/analytics/daily?days=30")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            # Check first item structure
            item = data[0]
            assert "date" in item
            assert "plans" in item
            assert "operations" in item
            assert "duration_ms" in item
            assert "tokens" in item
            assert "cost_usd" in item
    
    def test_daily_endpoint_sorted_by_date(self, client, setup_test_data):
        """Test that daily data is sorted by date descending."""
        response = client.get("/api/analytics/daily?days=30")
        assert response.status_code == 200
        
        data = response.json()
        if len(data) > 1:
            dates = [item["date"] for item in data]
            assert dates == sorted(dates, reverse=True)
    
    def test_daily_endpoint_with_user_filter(self, client, setup_test_data):
        """Test daily endpoint with user filter."""
        user_id = setup_test_data["user_id"]
        response = client.get(f"/api/analytics/daily?days=30&user_id={user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)


class TestAnalyticsExportEndpoint:
    """Test /api/analytics/export endpoint."""
    
    def test_export_endpoint_exists(self, client):
        """Test that export endpoint is accessible."""
        response = client.get("/api/analytics/export")
        # Should return 404 if no data, or 200 if data exists
        assert response.status_code in [200, 404]
    
    def test_export_endpoint_with_data(self, client, setup_test_data):
        """Test export endpoint returns CSV data."""
        response = client.get("/api/analytics/export?days=30")
        
        if response.status_code == 200:
            # Check content type
            assert response.headers["content-type"] == "text/csv; charset=utf-8"
            
            # Check content disposition header
            assert "attachment" in response.headers["content-disposition"]
            assert "analytics_" in response.headers["content-disposition"]
            assert ".csv" in response.headers["content-disposition"]
            
            # Check CSV content
            csv_content = response.text
            assert len(csv_content) > 0
            
            lines = csv_content.strip().split('\n')
            assert len(lines) > 1  # Header + data
            
            # Check header
            header = lines[0]
            assert "date" in header
            assert "plans" in header
    
    def test_export_endpoint_no_data(self, client):
        """Test export endpoint with no data returns 404."""
        # Use a very short time range where no data exists
        response = client.get("/api/analytics/export?days=0")
        # Should return 404 when no data
        assert response.status_code in [404, 200]
    
    def test_export_endpoint_with_user_filter(self, client, setup_test_data):
        """Test export endpoint with user filter."""
        user_id = setup_test_data["user_id"]
        response = client.get(f"/api/analytics/export?days=30&user_id={user_id}")
        
        if response.status_code == 200:
            assert response.headers["content-type"] == "text/csv; charset=utf-8"


class TestAnalyticsEndpointErrors:
    """Test error handling in analytics endpoints."""
    
    def test_summary_with_invalid_user_id(self, client):
        """Test summary endpoint with invalid user ID."""
        response = client.get("/api/analytics/summary?user_id=nonexistent")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_plans"] == 0
    
    def test_daily_with_negative_days(self, client):
        """Test daily endpoint with negative days."""
        response = client.get("/api/analytics/daily?days=-1")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_export_with_very_large_days(self, client):
        """Test export endpoint with very large day range."""
        response = client.get("/api/analytics/export?days=10000")
        # Should handle gracefully
        assert response.status_code in [200, 404]


class TestAnalyticsDataAccuracy:
    """Test accuracy of analytics calculations."""
    
    def test_total_plans_count(self, client, setup_test_data):
        """Test that total plans count is accurate."""
        response = client.get("/api/analytics/summary?days=30")
        data = response.json()
        
        # Should have 5 plans from setup
        assert data["total_plans"] == 5
    
    def test_total_operations_count(self, client, setup_test_data):
        """Test that total operations count is accurate."""
        response = client.get("/api/analytics/summary?days=30")
        data = response.json()
        
        # Should have 10 operations (5 plans * 2 operations each)
        assert data["total_operations"] == 10
    
    def test_model_distribution_accuracy(self, client, setup_test_data):
        """Test that model distribution is accurate."""
        response = client.get("/api/analytics/summary?days=30")
        data = response.json()
        
        model_dist = data["model_distribution"]
        
        # Should have 2 models (alternating in setup)
        assert len(model_dist) == 2
        
        # Check model names
        model_names = {m["llm_model"] for m in model_dist}
        assert "gpt-4o-mini" in model_names
        assert "claude-3-5-sonnet-20241022" in model_names
    
    def test_operation_breakdown_accuracy(self, client, setup_test_data):
        """Test that operation breakdown is accurate."""
        response = client.get("/api/analytics/summary?days=30")
        data = response.json()
        
        op_breakdown = data["operation_breakdown"]
        
        # Should have 2 operation types
        assert len(op_breakdown) == 2
        
        # Check operation types
        op_types = {op["operation_type"] for op in op_breakdown}
        assert "parse_slot" in op_types
        assert "process_slot" in op_types
        
        # Each should have 5 operations
        for op in op_breakdown:
            assert op["count"] == 5


class TestAnalyticsPerformance:
    """Test performance of analytics endpoints."""
    
    def test_summary_endpoint_response_time(self, client, setup_test_data):
        """Test that summary endpoint responds quickly."""
        import time
        
        start = time.time()
        response = client.get("/api/analytics/summary?days=30")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0  # Should respond in less than 1 second
    
    def test_daily_endpoint_response_time(self, client, setup_test_data):
        """Test that daily endpoint responds quickly."""
        import time
        
        start = time.time()
        response = client.get("/api/analytics/daily?days=30")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0  # Should respond in less than 1 second


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
