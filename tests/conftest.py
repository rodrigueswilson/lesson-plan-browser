"""
Shared pytest fixtures. Test client uses Starlette TestClient when compatible with httpx;
if your environment has httpx>=0.28 and an older Starlette, upgrade Starlette or use httpx<0.28.
"""
import pytest
import tempfile
from pathlib import Path

from backend.database import Database


@pytest.fixture
def isolated_db():
    """Create an isolated SQLite DB with schema; dispose and delete on teardown (Windows-safe)."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name
    db = Database(db_path)
    db.init_db()
    try:
        yield db
    finally:
        db.engine.dispose()
        Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def temp_db(isolated_db):
    """Alias for isolated_db for tests that use temp_db."""
    return isolated_db


@pytest.fixture
def test_db(isolated_db):
    """Alias for isolated_db for tests that use test_db."""
    return isolated_db


@pytest.fixture
def db(isolated_db):
    """Alias for isolated_db for tests that use db."""
    return isolated_db


@pytest.fixture
def client():
    """FastAPI/Starlette test client (in-process, no live server)."""
    try:
        from starlette.testclient import TestClient
        from backend.api import app
        return TestClient(app)
    except TypeError as e:
        if "unexpected keyword argument 'app'" in str(e):
            pytest.skip(
                "TestClient incompatible with this httpx version. "
                "Use starlette>=0.36 or httpx<0.28."
            )
        raise


@pytest.fixture
def client_isolated_db(isolated_db, monkeypatch):
    """Test client that uses an isolated DB so user-creation tests do not share state."""
    def get_test_db(user_id=None, **kwargs):
        return isolated_db

    monkeypatch.setattr("backend.database.get_db", get_test_db)
    monkeypatch.setattr("backend.api.get_db", get_test_db)
    monkeypatch.setattr("backend.routers.users.get_db", get_test_db)
    try:
        from starlette.testclient import TestClient
        from backend.api import app
        yield TestClient(app)
    except TypeError as e:
        if "unexpected keyword argument 'app'" in str(e):
            pytest.skip(
                "TestClient incompatible with this httpx version. "
                "Use starlette>=0.36 or httpx<0.28."
            )
        raise
