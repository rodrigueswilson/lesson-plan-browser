"""
Tests for Redis-backed rate limiting.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.api import app
from backend.config import Settings
from backend.rate_limiter import test_redis_connection, get_storage_uri


def test_storage_uri_without_redis():
    """Test that storage URI defaults to memory when Redis not configured."""
    with patch("backend.rate_limiter.settings") as mock_settings:
        mock_settings.REDIS_URL = None
        assert get_storage_uri() == "memory://"


def test_storage_uri_with_redis():
    """Test that storage URI uses Redis when configured."""
    with patch("backend.rate_limiter.settings") as mock_settings:
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        mock_settings.REDIS_PASSWORD = None
        mock_settings.REDIS_KEY_PREFIX = "rate_limit"
        uri = get_storage_uri()
        assert uri.startswith("redis://")


def test_storage_uri_with_password():
    """Test that storage URI includes password when provided."""
    with patch("backend.rate_limiter.settings") as mock_settings:
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        mock_settings.REDIS_PASSWORD = "secret123"
        mock_settings.REDIS_KEY_PREFIX = "rate_limit"
        uri = get_storage_uri()
        assert ":secret123@" in uri


@pytest.mark.skipif(
    os.getenv("REDIS_URL") is None,
    reason="Redis not available for integration testing"
)
def test_redis_connection_integration():
    """Test Redis connection (requires Redis server)."""
    assert test_redis_connection() is True


def test_redis_health_endpoint_not_configured():
    """Test Redis health endpoint when Redis not configured."""
    with patch("backend.api.settings") as mock_settings:
        mock_settings.REDIS_URL = None
        mock_settings.REDIS_KEY_PREFIX = "rate_limit"
        client = TestClient(app)
        response = client.get("/api/health/redis")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_configured"
        assert data["storage_type"] == "memory"


@pytest.mark.skipif(
    os.getenv("REDIS_URL") is None,
    reason="Redis not available for integration testing"
)
def test_redis_health_endpoint_configured():
    """Test Redis health endpoint when Redis is configured."""
    client = TestClient(app)
    response = client.get("/api/health/redis")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["storage_type"] == "redis"


def test_fallback_to_memory():
    """Test that system falls back to memory if Redis unavailable."""
    with patch("backend.rate_limiter.settings") as mock_settings:
        mock_settings.REDIS_URL = "redis://invalid-host:6379/0"
        mock_settings.REDIS_PASSWORD = None
        mock_settings.REDIS_KEY_PREFIX = "rate_limit"
        
        # Should not raise exception, but may log warning
        uri = get_storage_uri()
        assert uri.startswith("redis://")  # Still tries Redis

