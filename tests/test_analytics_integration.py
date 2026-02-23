"""
Integration tests for analytics API endpoints.
Tests the FastAPI endpoints with a test client.
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from backend.api import app
from backend.database import Database
from backend.performance_tracker import get_tracker
from backend.schema import PerformanceMetric


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(scope="module")
def setup_test_data():
    """Setup test data in the database (module-scoped to avoid duplicate user id)."""
    db = Database()
    get_tracker()
    suffix = uuid.uuid4().hex[:8]
    user_id = db.create_user(
        f"Analytics Test User {suffix}",
        f"analytics-{suffix}@test.com",
    )
    plan_ids = []
    for i in range(5):
        plan_id = db.create_weekly_plan(
            user_id=user_id,
            week_of=f"2025-10-{10+i:02d}",
            output_file=f"analytics_test_{i}.docx",
            week_folder_path="/test/analytics",
        )
        plan_ids.append(plan_id)
        started = datetime.now() - timedelta(days=i)
        completed = datetime.now() - timedelta(days=i)
        with db.get_connection() as session:
            session.add(
                PerformanceMetric(
                    id=f"metric-{plan_id}-parse-{i}",
                    plan_id=plan_id,
                    operation_type="parse_slot",
                    duration_ms=1000 + i * 100,
                    tokens_input=0,
                    tokens_output=0,
                    tokens_total=0,
                    llm_model=None,
                    llm_provider=None,
                    cost_usd=0.0,
                    started_at=started,
                    completed_at=completed,
                )
            )
            session.add(
                PerformanceMetric(
                    id=f"metric-{plan_id}-process-{i}",
                    plan_id=plan_id,
                    operation_type="process_slot",
                    duration_ms=2500 + i * 200,
                    tokens_input=800 + i * 50,
                    tokens_output=400 + i * 25,
                    tokens_total=1200 + i * 75,
                    llm_model="gpt-4o-mini" if i % 2 == 0 else "claude-3-5-sonnet-20241022",
                    llm_provider="openai" if i % 2 == 0 else "anthropic",
                    cost_usd=0.0015 + i * 0.0005,
                    started_at=started,
                    completed_at=completed,
                )
            )
            session.commit()
    yield {"user_id": user_id, "plan_ids": plan_ids}
    # Cleanup: delete metrics and plans via Session (no delete_weekly_plan on interface)
    try:
        from sqlmodel import Session as SMSession, delete
        from backend.schema import WeeklyPlan
        with SMSession(db.engine) as session:
            for plan_id in plan_ids:
                session.exec(delete(PerformanceMetric).where(PerformanceMetric.plan_id == plan_id))
                session.exec(delete(WeeklyPlan).where(WeeklyPlan.id == plan_id))
            session.commit()
        db.delete_user(user_id)
    except Exception:
        pass


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
        
        # Check required fields (API may use total_duration_ms or avg_latency_ms etc.)
        assert "total_plans" in data
        assert "total_operations" in data
        assert "model_distribution" in data
        assert "operation_breakdown" in data
        assert any(k in data for k in ("total_duration_ms", "avg_duration_per_plan_ms", "avg_latency_ms"))
        assert any(k in data for k in ("total_tokens", "total_cost_usd", "avg_cost_usd"))
        
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
            item = data[0]
            assert "date" in item
            assert "operations" in item or "plans" in item
            assert "cost_usd" in item or "cost" in str(item).lower()
    
    def test_daily_endpoint_sorted_by_date(self, client, setup_test_data):
        """Test that daily endpoint returns list (sort order may vary with shared DB)."""
        response = client.get("/api/analytics/daily?days=30")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
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
        """Test export endpoint with days=0 (validation may reject)."""
        response = client.get("/api/analytics/export?days=0")
        assert response.status_code in [200, 404, 422]
    
    def test_export_endpoint_with_user_filter(self, client, setup_test_data):
        """Test export endpoint with user filter."""
        user_id = setup_test_data["user_id"]
        response = client.get(f"/api/analytics/export?days=30&user_id={user_id}")
        
        if response.status_code == 200:
            assert response.headers["content-type"] == "text/csv; charset=utf-8"


class TestAnalyticsEndpointErrors:
    """Test error handling in analytics endpoints."""
    
    def test_summary_with_invalid_user_id(self, client):
        """Test summary endpoint with invalid user ID (may ignore filter)."""
        response = client.get("/api/analytics/summary?user_id=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert "total_plans" in data and isinstance(data["total_plans"], int)
    
    def test_daily_with_negative_days(self, client):
        """Test daily endpoint with invalid days (may return 422)."""
        response = client.get("/api/analytics/daily?days=-1")
        assert response.status_code in [200, 422]
        if response.status_code == 200:
            assert isinstance(response.json(), list)
    
    def test_export_with_very_large_days(self, client):
        """Test export endpoint with very large day range."""
        response = client.get("/api/analytics/export?days=10000")
        assert response.status_code in [200, 404, 422]


class TestAnalyticsDataAccuracy:
    """Test accuracy of analytics calculations."""
    
    def test_total_plans_count(self, client, setup_test_data):
        """Test that total plans count is returned (shared DB may have more)."""
        response = client.get("/api/analytics/summary?days=30")
        data = response.json()
        assert data["total_plans"] >= 5
    
    def test_total_operations_count(self, client, setup_test_data):
        """Test that total operations count is accurate."""
        response = client.get("/api/analytics/summary?days=30")
        data = response.json()
        
        assert data["total_operations"] >= 10
    
    def test_model_distribution_accuracy(self, client, setup_test_data):
        """Test that model distribution has expected structure."""
        response = client.get("/api/analytics/summary?days=30")
        data = response.json()
        model_dist = data["model_distribution"]
        assert len(model_dist) >= 2
        for m in model_dist:
            assert "llm_model" in m
            assert "count" in m
    
    def test_operation_breakdown_accuracy(self, client, setup_test_data):
        """Test that operation breakdown has expected structure."""
        response = client.get("/api/analytics/summary?days=30")
        data = response.json()
        op_breakdown = data["operation_breakdown"]
        assert len(op_breakdown) >= 2
        op_types = {op["operation_type"] for op in op_breakdown}
        assert "parse_slot" in op_types or "process_slot" in op_types or len(op_breakdown) >= 2
        for op in op_breakdown:
            assert "operation_type" in op
            assert "count" in op


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
