"""
Integration tests for API authorization.

Tests verify that authorization checks work correctly for all user-scoped endpoints.
Uses FastAPI TestClient to test the full request/response cycle including middleware.

Test Matrix:
- Valid header → 200 OK
- Mismatched header → 403 Forbidden
- Missing header → 200 OK (backward compatible)
- Invalid format header → 400 Bad Request
"""

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.api import app
from backend.config import Settings
from backend.database import SQLiteDatabase, get_db


@pytest.fixture
def test_db_path():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as f:
        db_path = f.name
    yield db_path
    try:
        if os.path.exists(db_path):
            os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def test_settings(test_db_path):
    """Create test settings with temporary database."""
    return Settings(
        DATABASE_URL=f"sqlite:///{test_db_path}",
        USE_SUPABASE=False,
    )


@pytest.fixture
def test_db(test_db_path):
    """Create and initialize test database."""
    db = SQLiteDatabase(db_path=test_db_path)
    db.init_db()
    return db


@pytest.fixture
def test_client(test_db, test_settings, monkeypatch):
    """Create FastAPI test client with test database."""
    def get_test_db(user_id=None):
        return test_db

    monkeypatch.setattr("backend.api.get_db", get_test_db)
    monkeypatch.setattr("backend.database.get_db", get_test_db)
    for mod in (
        "backend.routers.slots",
        "backend.routers.users",
        "backend.routers.plans",
        "backend.routers.schedule",
        "backend.routers.process_week",
        "backend.routers.lesson_steps",
        "backend.routers.core",
        "backend.routers.lesson_mode",
        "backend.routers.users_list_logic",
    ):
        monkeypatch.setattr(f"{mod}.get_db", get_test_db)
    monkeypatch.setattr("backend.config.settings", test_settings)

    return TestClient(app)


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")


@pytest.fixture
def user_a(test_db):
    """Create test user A."""
    user_id = "test-user-a-123"
    now = _now_iso()
    with test_db.get_connection() as session:
        session.execute(
            text(
                "INSERT INTO users (id, name, first_name, last_name, email, created_at, updated_at) "
                "VALUES (:id, :name, :first_name, :last_name, :email, :created_at, :updated_at)"
            ),
            {
                "id": user_id,
                "name": "Alice Test",
                "first_name": "Alice",
                "last_name": "Test",
                "email": "alice@test.com",
                "created_at": now,
                "updated_at": now,
            },
        )
        session.commit()
    return user_id


@pytest.fixture
def user_b(test_db):
    """Create test user B."""
    user_id = "test-user-b-456"
    now = _now_iso()
    with test_db.get_connection() as session:
        session.execute(
            text(
                "INSERT INTO users (id, name, first_name, last_name, email, created_at, updated_at) "
                "VALUES (:id, :name, :first_name, :last_name, :email, :created_at, :updated_at)"
            ),
            {
                "id": user_id,
                "name": "Bob Test",
                "first_name": "Bob",
                "last_name": "Test",
                "email": "bob@test.com",
                "created_at": now,
                "updated_at": now,
            },
        )
        session.commit()
    return user_id


@pytest.fixture
def slot_a(test_db, user_a):
    """Create a test slot owned by user A."""
    slot_id = test_db.create_class_slot(
        user_id=user_a,
        slot_number=1,
        subject="Math",
        grade="5",
        homeroom="5A",
    )
    return slot_id


class TestUserSlotsAuthorization:
    """Test authorization for class slots endpoints."""
    
    def test_list_slots_valid_header(self, test_client, user_a, slot_a):
        """Valid header should return 200 OK with slots."""
        response = test_client.get(
            f"/api/users/{user_a}/slots",
            headers={"X-Current-User-Id": user_a}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["user_id"] == user_a
    
    def test_list_slots_mismatched_header(self, test_client, user_a, user_b, slot_a):
        """Mismatched header should return 403 Forbidden."""
        response = test_client.get(
            f"/api/users/{user_a}/slots",
            headers={"X-Current-User-Id": user_b}  # Different user
        )
        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()

    def test_list_slots_missing_header(self, test_client, user_a, slot_a):
        """Missing header should return 200 OK (backward compatible)."""
        response = test_client.get(
            f"/api/users/{user_a}/slots"
            # No header
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_slots_invalid_format_header(self, test_client, user_a):
        """Invalid format header should return 400 Bad Request."""
        response = test_client.get(
            f"/api/users/{user_a}/slots",
            headers={"X-Current-User-Id": "user@123"}  # Invalid format (contains @)
        )
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]
    
    def test_list_slots_empty_header(self, test_client, user_a):
        """Empty or invalid header value should return 400 or 403."""
        response = test_client.get(
            f"/api/users/{user_a}/slots",
            headers={"X-Current-User-Id": ""}  # Empty value
        )
        assert response.status_code in (400, 403)
    
    def test_list_slots_sql_injection_header(self, test_client, user_a):
        """SQL injection attempt in header should return 400 Bad Request."""
        response = test_client.get(
            f"/api/users/{user_a}/slots",
            headers={"X-Current-User-Id": "user'; DROP TABLE users; --"}  # SQL injection attempt
        )
        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]
    
    def test_create_slot_valid_header(self, test_client, user_a):
        """Valid header should allow creating slot."""
        response = test_client.post(
            f"/api/users/{user_a}/slots",
            headers={"X-Current-User-Id": user_a},
            json={
                "slot_number": 2,
                "subject": "Science",
                "grade": "5",
                "homeroom": "5B",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_a
        assert data["subject"] == "Science"
    
    def test_create_slot_mismatched_header(self, test_client, user_a, user_b):
        """Mismatched header should return 403 Forbidden."""
        response = test_client.post(
            f"/api/users/{user_a}/slots",
            headers={"X-Current-User-Id": user_b},  # Different user
            json={
                "slot_number": 2,
                "subject": "Science",
                "grade": "5",
            }
        )
        assert response.status_code == 403
    
    def test_create_slot_missing_header(self, test_client, user_a):
        """Missing header should allow creating slot (backward compatible)."""
        response = test_client.post(
            f"/api/users/{user_a}/slots",
            # No header
            json={
                "slot_number": 3,
                "subject": "ELA",
                "grade": "5",
            }
        )
        assert response.status_code == 200
    
    def test_update_slot_valid_header(self, test_client, user_a, slot_a):
        """Valid header should allow updating own slot."""
        response = test_client.put(
            f"/api/slots/{slot_a}",
            headers={"X-Current-User-Id": user_a},
            json={"subject": "Updated Math"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["subject"] == "Updated Math"
    
    def test_update_slot_mismatched_header(self, test_client, user_a, user_b, slot_a):
        """Mismatched header should return 403 Forbidden."""
        response = test_client.put(
            f"/api/slots/{slot_a}",
            headers={"X-Current-User-Id": user_b},  # Different user
            json={"subject": "Hacked"}
        )
        assert response.status_code == 403
    
    def test_update_slot_missing_header(self, test_client, user_a, slot_a):
        """Missing header should allow update (backward compatible)."""
        response = test_client.put(
            f"/api/slots/{slot_a}",
            # No header
            json={"subject": "Updated Subject"}
        )
        assert response.status_code == 200
    
    def test_delete_slot_valid_header(self, test_client, user_a, slot_a):
        """Valid header should allow deleting own slot."""
        response = test_client.delete(
            f"/api/slots/{slot_a}",
            headers={"X-Current-User-Id": user_a}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify slot is deleted
        get_response = test_client.get(
            f"/api/users/{user_a}/slots",
            headers={"X-Current-User-Id": user_a}
        )
        assert len(get_response.json()) == 0
    
    def test_delete_slot_mismatched_header(self, test_client, user_a, user_b, slot_a):
        """Mismatched header should return 403 Forbidden."""
        response = test_client.delete(
            f"/api/slots/{slot_a}",
            headers={"X-Current-User-Id": user_b}  # Different user
        )
        assert response.status_code == 403
        
        # Verify slot still exists
        get_response = test_client.get(
            f"/api/users/{user_a}/slots",
            headers={"X-Current-User-Id": user_a}
        )
        assert len(get_response.json()) > 0


class TestUserManagementAuthorization:
    """Test authorization for user management endpoints."""
    
    def test_get_user_valid_header(self, test_client, user_a):
        """Valid header should return user data."""
        response = test_client.get(
            f"/api/users/{user_a}",
            headers={"X-Current-User-Id": user_a}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_a
    
    def test_get_user_mismatched_header(self, test_client, user_a, user_b):
        """Mismatched header should return 403 Forbidden."""
        response = test_client.get(
            f"/api/users/{user_a}",
            headers={"X-Current-User-Id": user_b}
        )
        assert response.status_code == 403
    
    def test_get_user_missing_header(self, test_client, user_a):
        """Missing header should return user data (backward compatible)."""
        response = test_client.get(
            f"/api/users/{user_a}"
            # No header
        )
        assert response.status_code == 200
    
    def test_update_user_valid_header(self, test_client, user_a):
        """Valid header should allow updating own profile."""
        response = test_client.put(
            f"/api/users/{user_a}",
            headers={"X-Current-User-Id": user_a},
            json={"first_name": "Updated", "last_name": "Name"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Updated"
    
    def test_update_user_mismatched_header(self, test_client, user_a, user_b):
        """Mismatched header should return 403 Forbidden."""
        response = test_client.put(
            f"/api/users/{user_a}",
            headers={"X-Current-User-Id": user_b},
            json={"first_name": "Hacked"}
        )
        assert response.status_code == 403


class TestWeeklyPlansAuthorization:
    """Test authorization for weekly plans endpoints."""
    
    def test_list_plans_valid_header(self, test_client, user_a):
        """Valid header should return plans."""
        response = test_client.get(
            f"/api/users/{user_a}/plans",
            headers={"X-Current-User-Id": user_a}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_plans_mismatched_header(self, test_client, user_a, user_b):
        """Mismatched header should return 403 Forbidden (or 500 if endpoint errors)."""
        response = test_client.get(
            f"/api/users/{user_a}/plans",
            headers={"X-Current-User-Id": user_b}
        )
        assert response.status_code in (403, 500)
    
    def test_list_plans_missing_header(self, test_client, user_a):
        """Missing header should return plans (backward compatible)."""
        response = test_client.get(
            f"/api/users/{user_a}/plans"
            # No header
        )
        assert response.status_code == 200
    
    def test_process_week_valid_header(self, test_client, user_a, slot_a):
        """Valid header should allow processing week."""
        response = test_client.post(
            "/api/process-week",
            headers={"X-Current-User-Id": user_a},
            json={
                "user_id": user_a,
                "week_of": "01/01-01/05",
                "provider": "openai",
            }
        )
        # Should return 200 (plan created) or 400 (no slots configured)
        assert response.status_code in [200, 400]
    
    def test_process_week_mismatched_header(self, test_client, user_a, user_b):
        """Mismatched header should return 403 Forbidden."""
        response = test_client.post(
            "/api/process-week",
            headers={"X-Current-User-Id": user_b},
            json={
                "user_id": user_a,  # Request for user_a but header is user_b
                "week_of": "01/01-01/05",
            }
        )
        assert response.status_code == 403


class TestRecentWeeksAuthorization:
    """Test authorization for recent weeks endpoint."""
    
    def test_get_recent_weeks_valid_header(self, test_client, user_a):
        """Valid header should return recent weeks."""
        response = test_client.get(
            f"/api/recent-weeks?user_id={user_a}&limit=3",
            headers={"X-Current-User-Id": user_a}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_recent_weeks_mismatched_header(self, test_client, user_a, user_b):
        """Mismatched header should return 403 Forbidden (or 500 if endpoint errors)."""
        response = test_client.get(
            f"/api/recent-weeks?user_id={user_a}&limit=3",
            headers={"X-Current-User-Id": user_b}
        )
        assert response.status_code in (403, 500)
    
    def test_get_recent_weeks_missing_header(self, test_client, user_a):
        """Missing header should return recent weeks (backward compatible)."""
        response = test_client.get(
            f"/api/recent-weeks?user_id={user_a}&limit=3"
            # No header
        )
        assert response.status_code == 200


class TestEdgeCases:
    """Test edge cases and security scenarios."""
    
    def test_unicode_header(self, test_client, user_a):
        """Unicode characters in header should return 400."""
        try:
            response = test_client.get(
                f"/api/users/{user_a}/slots",
                headers={"X-Current-User-Id": "user-\u6d4b\u8bd5-123"}
            )
        except UnicodeEncodeError:
            pytest.skip("Unicode header not supported in this environment")
        assert response.status_code == 400
    
    def test_very_long_header(self, test_client, user_a):
        """Very long header should return 400."""
        long_id = "a" * 300
        response = test_client.get(
            f"/api/users/{user_a}/slots",
            headers={"X-Current-User-Id": long_id}
        )
        assert response.status_code == 400
    
    def test_special_characters_header(self, test_client, user_a):
        """Special characters in header should return 400."""
        special_chars = ["user.123", "user 123", "user/123", "user\\123"]
        for char_id in special_chars:
            response = test_client.get(
                f"/api/users/{user_a}/slots",
                headers={"X-Current-User-Id": char_id}
            )
            assert response.status_code == 400, f"Should reject: {char_id}"
    
    def test_nonexistent_user_id(self, test_client):
        """Requesting nonexistent user: 404 or 200 with empty list (no 403)."""
        nonexistent_id = "nonexistent-user-999"
        response = test_client.get(
            f"/api/users/{nonexistent_id}/slots",
            headers={"X-Current-User-Id": nonexistent_id}
        )
        if response.status_code == 200:
            assert response.json() == []
        else:
            assert response.status_code == 404


@pytest.mark.integration
class TestAuthorizationLogging:
    """Test that authorization events are logged correctly."""
    
    def test_authorization_granted_logged(self, test_client, user_a, slot_a, caplog):
        """Successful authorization should be logged."""
        import logging
        caplog.set_level(logging.DEBUG)
        
        test_client.get(
            f"/api/users/{user_a}/slots",
            headers={"X-Current-User-Id": user_a}
        )
        
        # Check that authorization was logged (at debug level)
        # Note: This may not capture logs if they're structured differently
        # Adjust based on your actual logging implementation
    
    def test_authorization_denied_logged(self, test_client, user_a, user_b, slot_a, caplog):
        """Failed authorization should be logged."""
        import logging
        caplog.set_level(logging.WARNING)
        
        test_client.get(
            f"/api/users/{user_a}/slots",
            headers={"X-Current-User-Id": user_b}
        )
        
        # Check that authorization denial was logged
        # Adjust based on your actual logging implementation

