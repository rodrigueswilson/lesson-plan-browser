"""Test API endpoints with structured names end-to-end (in-process client)."""


def test_post_users_structured_names(client):
    """POST /api/users with first_name/last_name."""
    response = client.post(
        "/api/users",
        json={"first_name": "API", "last_name": "Test", "email": "api.test@example.com"},
    )
    assert response.status_code == 200
    user = response.json()
    assert user["first_name"] == "API"
    assert user["last_name"] == "Test"
    assert user["name"] == "API Test"


def test_api_endpoints_structured_names_flow(client):
    """Full flow: create user, get, update, create slot, update slot, list users, cleanup."""
    # Create user
    r = client.post(
        "/api/users",
        json={"first_name": "API", "last_name": "Test", "email": "api.test@example.com"},
    )
    assert r.status_code == 200
    user = r.json()
    user_id = user["id"]

    # Get user
    r = client.get(f"/api/users/{user_id}")
    assert r.status_code == 200
    assert r.json()["first_name"] == "API"

    # Update user
    r = client.put(
        f"/api/users/{user_id}",
        json={"first_name": "Updated", "last_name": "Name"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Name"

    # Create slot
    r = client.post(
        f"/api/users/{user_id}/slots",
        json={
            "slot_number": 1,
            "subject": "Math",
            "grade": "3",
            "homeroom": "301",
            "primary_teacher_first_name": "Sarah",
            "primary_teacher_last_name": "Lang",
        },
    )
    assert r.status_code == 200
    slot = r.json()
    slot_id = slot["id"]
    assert slot["primary_teacher_name"] == "Sarah Lang"

    # Update slot
    r = client.put(
        f"/api/slots/{slot_id}",
        json={"primary_teacher_first_name": "Maria", "primary_teacher_last_name": "Savoca"},
    )
    assert r.status_code == 200
    assert r.json()["primary_teacher_name"] == "Maria Savoca"

    # List users
    r = client.get("/api/users")
    assert r.status_code == 200
    users = r.json()
    test_user = next(u for u in users if u["id"] == user_id)
    assert "first_name" in test_user and "last_name" in test_user

    # Cleanup
    client.delete(f"/api/slots/{slot_id}")
    client.delete(f"/api/users/{user_id}")
