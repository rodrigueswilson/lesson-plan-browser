"""Test API connection and endpoints via in-process client."""


def test_health(client):
    """Health endpoint returns 200."""
    r = client.get("/api/health", timeout=5)
    assert r.status_code == 200
    assert r.json().get("status") == "healthy"


def test_list_users(client):
    """List users returns a list."""
    r = client.get("/api/users", timeout=5)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_create_user_accepts_json(client):
    """Create user endpoint accepts first_name/last_name (API shape)."""
    r = client.post(
        "/api/users",
        json={"first_name": "API", "last_name": "Test", "email": "apitest@example.com"},
        timeout=5,
    )
    assert r.status_code == 200
    data = r.json()
    assert "id" in data
    assert data.get("name") == "API Test"
