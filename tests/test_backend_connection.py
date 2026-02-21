"""Test if backend is accessible (in-process client; no live server required)."""


def test_backend_health_via_test_client(client):
    """Backend health endpoint works when called via test client."""
    response = client.get("/api/health", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"
