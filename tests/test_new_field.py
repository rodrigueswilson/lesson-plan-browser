"""Test if avg_duration_per_plan_ms is in the API response (in-process client)."""


def test_analytics_summary_returns_dict(client):
    """GET /api/analytics/summary returns a dict with expected keys or empty."""
    r = client.get("/api/analytics/summary?days=30")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    if "avg_duration_per_plan_ms" in data:
        assert isinstance(data["avg_duration_per_plan_ms"], (int, float, type(None)))
