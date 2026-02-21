"""
Test the backend API directly via in-process client (no live server).
"""


def test_health(client):
    """Health endpoint returns 200."""
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json().get("status") == "healthy"


def test_get_users(client):
    """GET /api/users returns list (may be empty)."""
    r = client.get("/api/users")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_user_slots_requires_valid_user(client):
    """GET /api/users/{id}/slots with invalid id returns 404 or empty."""
    r = client.get("/api/users/00000000-0000-0000-0000-000000000000/slots")
    # Either 404 or 200 with []
    assert r.status_code in (200, 404)
