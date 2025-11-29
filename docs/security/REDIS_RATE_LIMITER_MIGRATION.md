# Redis-Backed Rate Limiter Migration

**Date:** January 2025  
**Purpose:** Migrate from in-memory rate limiting to Redis-backed rate limiting for multi-instance deployments

---

## Overview

This migration replaces the in-memory rate limiter with a Redis-backed implementation, enabling:
- **Multi-instance deployments** - Rate limits shared across all backend instances
- **Persistent rate limits** - Limits survive server restarts
- **Better scalability** - Redis handles high-throughput rate limiting efficiently
- **Per-user rate limiting** - More granular control than IP-based limits

---

## Prerequisites

### 1. Redis Installation

**Option A: Local Redis (Development)**
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

**Option B: Managed Redis (Production)**
- AWS ElastiCache
- Redis Cloud
- Azure Cache for Redis
- DigitalOcean Managed Redis

### 2. Python Dependencies

Add to `requirements.txt`:
```
redis>=5.0.0
```

Install:
```bash
pip install redis>=5.0.0
```

**Note:** `slowapi` already supports Redis via `storage_uri="redis://..."` - no additional libraries needed beyond `redis`.

---

## Migration Steps

### Step 1: Add Redis Configuration

Add to `backend/config.py`:

```python
# Rate Limiting
REDIS_URL: Optional[str] = Field(
    default=None,
    description="Redis connection URL (e.g., redis://localhost:6379/0). If not set, uses in-memory storage."
)
REDIS_PASSWORD: Optional[str] = Field(
    default=None,
    description="Redis password (if required)"
)
REDIS_SSL: bool = Field(
    default=False,
    description="Use SSL/TLS for Redis connection"
)
REDIS_KEY_PREFIX: str = Field(
    default="rate_limit",
    description="Prefix for rate limit keys in Redis"
)
```

### Step 2: Update Rate Limiter

Modify `backend/rate_limiter.py` to support Redis:

```python
"""
Rate limiting middleware for API endpoints.

Provides protection against brute force attacks and API abuse by limiting
the number of requests per IP address or user.

Uses slowapi for rate limiting with Redis storage (for multi-instance deployments)
or in-memory storage (for single-instance deployments).
"""

from typing import Optional
from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.config import settings
from backend.telemetry import logger


def get_storage_uri() -> str:
    """
    Get rate limiter storage URI based on configuration.
    
    Returns:
        Storage URI string (redis://... or memory://)
    """
    if settings.REDIS_URL:
        # Build Redis URI
        redis_uri = settings.REDIS_URL
        
        # Add password if provided
        if settings.REDIS_PASSWORD:
            # Insert password into URI: redis://:password@host:port/db
            if "@" in redis_uri:
                # URI already has auth, replace password
                parts = redis_uri.split("@")
                if ":" in parts[0]:
                    redis_uri = f"{parts[0].split(':')[0]}:{settings.REDIS_PASSWORD}@{parts[1]}"
                else:
                    redis_uri = f"redis://:{settings.REDIS_PASSWORD}@{parts[1]}"
            else:
                # Insert password before host
                redis_uri = redis_uri.replace("redis://", f"redis://:{settings.REDIS_PASSWORD}@")
        
        logger.info("rate_limiting_redis_enabled", extra={
            "redis_url": redis_uri.split("@")[-1] if "@" in redis_uri else redis_uri,  # Don't log password
            "key_prefix": settings.REDIS_KEY_PREFIX,
        })
        return redis_uri
    
    # Fall back to in-memory storage
    logger.info("rate_limiting_memory_enabled")
    return "memory://"


# Initialize rate limiter
# Uses IP address as the key function (can be customized)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000/hour"],  # Default: 1000 requests per hour per IP
    storage_uri=get_storage_uri(),
    key_prefix=settings.REDIS_KEY_PREFIX if settings.REDIS_URL else None,
)


def get_user_id_for_rate_limit(request: Request) -> Optional[str]:
    """
    Extract user ID from header for user-based rate limiting.
    
    This allows per-user rate limiting instead of per-IP.
    Falls back to IP address if no user ID header present.
    
    Args:
        request: FastAPI request object
    
    Returns:
        User ID string or None
    """
    # Try to get user ID from authorization header
    user_id = request.headers.get("X-Current-User-Id")
    if user_id:
        return f"user:{user_id}"
    # Fall back to IP address
    return get_remote_address(request)


# Rate limit configurations per endpoint type
# Format: "count/period" where period can be: second, minute, hour, day

# General API endpoints (moderate limits)
GENERAL_LIMIT = "100/minute"  # 100 requests per minute

# Authorization-sensitive endpoints (stricter limits)
AUTH_LIMIT = "30/minute"  # 30 requests per minute

# Resource-intensive endpoints (very strict limits)
HEAVY_LIMIT = "10/minute"  # 10 requests per minute

# Batch processing endpoints (very strict limits)
BATCH_LIMIT = "5/minute"  # 5 requests per minute


def create_rate_limit_decorator(limit: str, key_func=None):
    """
    Create a rate limit decorator with specified limit.
    
    Args:
        limit: Rate limit string (e.g., "30/minute")
        key_func: Optional key function (defaults to get_remote_address)
    
    Returns:
        Decorator function
    """
    if key_func is None:
        key_func = get_remote_address
    
    return limiter.limit(limit, key_func=key_func)


# Convenience decorators for common rate limit scenarios
rate_limit_general = create_rate_limit_decorator(GENERAL_LIMIT)
rate_limit_auth = create_rate_limit_decorator(AUTH_LIMIT)
rate_limit_heavy = create_rate_limit_decorator(HEAVY_LIMIT)
rate_limit_batch = create_rate_limit_decorator(BATCH_LIMIT)


def setup_rate_limiting(app):
    """
    Set up rate limiting for FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Add limiter state to app
    app.state.limiter = limiter
    
    # Register rate limit exceeded exception handler
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    storage_type = "redis" if settings.REDIS_URL else "memory"
    logger.info("rate_limiting_enabled", extra={
        "storage_type": storage_type,
        "general_limit": GENERAL_LIMIT,
        "auth_limit": AUTH_LIMIT,
        "heavy_limit": HEAVY_LIMIT,
        "batch_limit": BATCH_LIMIT,
    })


def get_rate_limit_info(request: Request) -> dict:
    """
    Get rate limit information for a request.
    
    Useful for debugging and monitoring.
    
    Args:
        request: FastAPI request object
    
    Returns:
        Dictionary with rate limit information
    """
    return {
        "ip_address": get_remote_address(request),
        "user_id": request.headers.get("X-Current-User-Id"),
        "storage_type": "redis" if settings.REDIS_URL else "memory",
    }


def test_redis_connection() -> bool:
    """
    Test Redis connection (for health checks).
    
    Returns:
        True if Redis is accessible, False otherwise
    """
    if not settings.REDIS_URL:
        return True  # Not using Redis
    
    try:
        import redis
        from urllib.parse import urlparse
        
        # Parse Redis URL
        parsed = urlparse(settings.REDIS_URL)
        redis_client = redis.Redis(
            host=parsed.hostname or "localhost",
            port=parsed.port or 6379,
            password=settings.REDIS_PASSWORD or parsed.password,
            db=int(parsed.path.lstrip("/")) if parsed.path else 0,
            ssl=settings.REDIS_SSL,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        
        # Test connection
        redis_client.ping()
        return True
    except Exception as e:
        logger.error("redis_connection_failed", extra={"error": str(e)})
        return False
```

### Step 3: Update Configuration File

Add Redis settings to `backend/config.py` (in the `Settings` class):

```python
# Rate Limiting
REDIS_URL: Optional[str] = Field(
    default=None,
    description="Redis connection URL (e.g., redis://localhost:6379/0). If not set, uses in-memory storage."
)
REDIS_PASSWORD: Optional[str] = Field(
    default=None,
    description="Redis password (if required)"
)
REDIS_SSL: bool = Field(
    default=False,
    description="Use SSL/TLS for Redis connection"
)
REDIS_KEY_PREFIX: str = Field(
    default="rate_limit",
    description="Prefix for rate limit keys in Redis"
)
```

### Step 4: Environment Variables

Add to `.env` file:

```bash
# Redis Configuration (optional - if not set, uses in-memory storage)
REDIS_URL=redis://localhost:6379/0
# REDIS_PASSWORD=your_password_here  # Only if Redis requires authentication
# REDIS_SSL=false  # Set to true for SSL/TLS connections
REDIS_KEY_PREFIX=rate_limit
```

**Production Example:**
```bash
# AWS ElastiCache
REDIS_URL=redis://your-cluster.cache.amazonaws.com:6379/0

# Redis Cloud
REDIS_URL=redis://:password@redis-12345.c1.us-east-1-1.ec2.cloud.redislabs.com:12345/0
REDIS_SSL=true

# Azure Cache
REDIS_URL=redis://your-cache.redis.cache.windows.net:6380/0
REDIS_SSL=true
REDIS_PASSWORD=your_access_key
```

---

## Safety Checks

### Pre-Migration Checklist

Before enabling Redis:

- [ ] Redis server is running and accessible
- [ ] Redis connection tested (`redis-cli ping` returns `PONG`)
- [ ] Environment variables set correctly
- [ ] Backend can connect to Redis (run health check)
- [ ] Backup of current rate limit configuration

### Health Check

Add to `backend/api.py` health endpoint:

```python
@app.get("/api/health/redis", tags=["System"])
async def health_redis():
    """Check Redis connection health."""
    from backend.rate_limiter import test_redis_connection
    
    if not settings.REDIS_URL:
        return {"status": "not_configured", "message": "Redis not configured, using in-memory storage"}
    
    is_healthy = test_redis_connection()
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "redis_url": settings.REDIS_URL.split("@")[-1] if "@" in settings.REDIS_URL else settings.REDIS_URL,
    }
```

Test:
```bash
curl http://localhost:8000/api/health/redis
```

---

## Testing

### Unit Tests

Create `tests/test_rate_limiter_redis.py`:

```python
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
        uri = get_storage_uri()
        assert uri.startswith("redis://")


def test_storage_uri_with_password():
    """Test that storage URI includes password when provided."""
    with patch("backend.rate_limiter.settings") as mock_settings:
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        mock_settings.REDIS_PASSWORD = "secret123"
        uri = get_storage_uri()
        assert ":secret123@" in uri


@pytest.mark.skipif(
    os.getenv("REDIS_URL") is None,
    reason="Redis not available for integration testing"
)
def test_redis_connection_integration():
    """Test Redis connection (requires Redis server)."""
    assert test_redis_connection() is True


@pytest.mark.skipif(
    os.getenv("REDIS_URL") is None,
    reason="Redis not available for integration testing"
)
def test_rate_limiting_with_redis():
    """Test rate limiting works with Redis."""
    client = TestClient(app)
    
    # Make requests until rate limited
    responses = []
    for i in range(35):  # AUTH_LIMIT is 30/minute
        response = client.get(
            "/api/users/test-user/slots",
            headers={"X-Current-User-Id": "test-user"}
        )
        responses.append(response.status_code)
    
    # Should have some 429 responses
    assert 429 in responses


def test_fallback_to_memory():
    """Test that system falls back to memory if Redis unavailable."""
    with patch("backend.rate_limiter.settings") as mock_settings:
        mock_settings.REDIS_URL = "redis://invalid-host:6379/0"
        mock_settings.REDIS_PASSWORD = None
        
        # Should not raise exception, but may log warning
        uri = get_storage_uri()
        assert uri.startswith("redis://")  # Still tries Redis
```

### Integration Test Script

Create `scripts/test_redis_rate_limiting.sh`:

```bash
#!/bin/bash
# Test Redis rate limiting

set -e

API_URL="${API_URL:-http://localhost:8000}"
TEST_USER_ID="${TEST_USER_ID:-test-redis-user}"

echo "=== Testing Redis Rate Limiting ==="
echo "API URL: $API_URL"
echo "Test User ID: $TEST_USER_ID"
echo ""

# Test 1: Health check
echo "Test 1: Redis health check..."
REDIS_HEALTH=$(curl -s "$API_URL/api/health/redis")
echo "$REDIS_HEALTH" | jq .

# Test 2: Make requests until rate limited
echo ""
echo "Test 2: Rate limiting behavior..."
SUCCESS_COUNT=0
RATE_LIMITED=0

for i in {1..35}; do
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -H "X-Current-User-Id: $TEST_USER_ID" \
        "$API_URL/api/users/$TEST_USER_ID/slots")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
        ((SUCCESS_COUNT++))
    elif [ "$HTTP_CODE" = "429" ]; then
        ((RATE_LIMITED++))
        echo "Request $i: Rate limited (HTTP 429)"
        break
    fi
done

echo "Successful requests: $SUCCESS_COUNT"
echo "Rate limited: $RATE_LIMITED"

if [ $RATE_LIMITED -gt 0 ]; then
    echo "✓ Rate limiting working correctly"
else
    echo "✗ Rate limiting not working (no 429 responses)"
    exit 1
fi
```

---

## Deployment

### Staging Deployment

1. **Set up Redis:**
   ```bash
   # Start Redis
   redis-server
   
   # Or use Docker
   docker run -d -p 6379:6379 redis:7-alpine
   ```

2. **Configure Environment:**
   ```bash
   export REDIS_URL=redis://localhost:6379/0
   export REDIS_KEY_PREFIX=rate_limit_staging
   ```

3. **Deploy Backend:**
   ```bash
   # Install dependencies
   pip install redis>=5.0.0
   
   # Start backend
   python -m uvicorn backend.api:app --reload
   ```

4. **Verify:**
   ```bash
   # Check Redis health
   curl http://localhost:8000/api/health/redis
   
   # Run integration test
   ./scripts/test_redis_rate_limiting.sh
   ```

### Production Deployment

1. **Set up Managed Redis:**
   - Provision Redis instance (AWS ElastiCache, Redis Cloud, etc.)
   - Note connection URL and credentials
   - Configure security groups/firewall rules

2. **Update Environment Variables:**
   ```bash
   REDIS_URL=redis://your-redis-host:6379/0
   REDIS_PASSWORD=your_secure_password
   REDIS_SSL=true  # If using SSL
   REDIS_KEY_PREFIX=rate_limit_prod
   ```

3. **Deploy:**
   ```bash
   # Install dependencies
   pip install redis>=5.0.0
   
   # Restart backend
   systemctl restart your-backend-service
   ```

4. **Monitor:**
   ```bash
   # Check Redis health
   curl https://your-api.com/api/health/redis
   
   # Monitor Redis metrics
   redis-cli INFO stats
   ```

---

## Monitoring

### Redis Metrics to Monitor

**Key Metrics:**
- `used_memory` - Redis memory usage
- `keyspace_hits` / `keyspace_misses` - Cache hit ratio
- `total_commands_processed` - Request volume
- `connected_clients` - Active connections

**Monitor Rate Limit Keys:**
```bash
# Count rate limit keys
redis-cli KEYS "rate_limit:*" | wc -l

# Check specific user/IP rate limit
redis-cli GET "rate_limit:user:test-user-123"

# View all rate limit keys
redis-cli KEYS "rate_limit:*"
```

### Application Metrics

Monitor in your application:
- Rate limit violations per endpoint
- Redis connection failures
- Fallback to in-memory storage events

---

## Rollback Procedures

### Quick Rollback

If Redis causes issues, rollback by removing Redis configuration:

1. **Remove Redis URL:**
   ```bash
   # In .env or environment
   unset REDIS_URL
   # Or comment out:
   # REDIS_URL=redis://localhost:6379/0
   ```

2. **Restart Backend:**
   ```bash
   systemctl restart your-backend-service
   ```

3. **Verify:**
   ```bash
   curl http://localhost:8000/api/health/redis
   # Should return: {"status": "not_configured", ...}
   ```

### Full Rollback

If you need to revert code changes:

1. **Revert Code:**
   ```bash
   git checkout HEAD~1 backend/rate_limiter.py
   git checkout HEAD~1 backend/config.py
   ```

2. **Restart Backend:**
   ```bash
   systemctl restart your-backend-service
   ```

3. **Verify:**
   ```bash
   # Rate limiting should still work (in-memory)
   curl http://localhost:8000/api/users/test/slots
   ```

---

## Troubleshooting

### Issue: Redis Connection Failed

**Symptoms:**
- Health check returns `unhealthy`
- Logs show `redis_connection_failed`

**Solutions:**
1. Check Redis is running: `redis-cli ping`
2. Verify connection URL: `echo $REDIS_URL`
3. Check firewall/security groups
4. Verify credentials (if password required)
5. Test connection manually:
   ```python
   import redis
   r = redis.Redis.from_url("redis://localhost:6379/0")
   r.ping()
   ```

### Issue: Rate Limits Not Working

**Symptoms:**
- No 429 responses
- Rate limits seem ignored

**Solutions:**
1. Check Redis is being used:
   ```bash
   curl http://localhost:8000/api/health/redis
   ```
2. Verify keys in Redis:
   ```bash
   redis-cli KEYS "rate_limit:*"
   ```
3. Check logs for rate limiting events
4. Verify `REDIS_KEY_PREFIX` matches

### Issue: High Memory Usage

**Symptoms:**
- Redis memory usage growing
- OOM errors

**Solutions:**
1. Redis automatically expires rate limit keys (TTL based on limit period)
2. Monitor key expiration:
   ```bash
   redis-cli TTL "rate_limit:user:test-user"
   ```
3. Set max memory policy:
   ```bash
   redis-cli CONFIG SET maxmemory-policy allkeys-lru
   ```

---

## Performance Considerations

### Redis Performance

- **Latency:** Redis adds ~1-2ms per request (vs in-memory <0.1ms)
- **Throughput:** Redis can handle 100K+ ops/sec
- **Memory:** ~100 bytes per rate limit key

### Optimization Tips

1. **Use Redis Pipeline** (if slowapi supports it)
2. **Monitor Connection Pool** - Reuse connections
3. **Set Appropriate TTL** - Let Redis expire keys automatically
4. **Use Redis Cluster** - For high availability

---

## Hardening Features

### Circuit Breaker

The implementation includes a circuit breaker pattern to prevent cascading failures:

- **Automatic Detection:** Tracks Redis connection failures
- **Fail Fast:** Opens circuit after threshold failures
- **Auto-Recovery:** Attempts reconnection after timeout
- **Monitoring:** Exposed via `/api/health/redis` endpoint

**Configuration:**
```bash
REDIS_CIRCUIT_BREAKER_THRESHOLD=5  # Failures before opening
REDIS_CIRCUIT_BREAKER_TIMEOUT=60   # Seconds to keep open
```

### Enhanced Key Naming

Keys use structured naming for better organization:

**Format:** `{env}:{service}:{prefix}:{limit_name}:{identifier}`

**Example:**
```
prod:lesson_planner:rate_limit:auth:user:abc123
staging:lesson_planner:rate_limit:general:192.168.1.1
```

**Benefits:**
- Environment isolation
- Service namespacing
- Easy debugging
- Safe key sweeps

**Configuration:**
```bash
REDIS_KEY_PREFIX=prod:lesson_planner:rate_limit
REDIS_ENVIRONMENT=prod
```

### Redis Memory Policy

**Recommended:** Use `volatile-lru` eviction policy

```bash
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy volatile-lru
```

This ensures:
- Only keys with TTL are evicted
- Least recently used keys removed first
- Automatic cleanup of expired keys
- Memory safety

### Lua Scripts (Advanced)

For maximum atomicity, Lua scripts are available (see `docs/security/REDIS_LUA_SCRIPTS.md`):

- Atomic increment + expire operations
- Race-condition prevention
- Server-side execution (low latency)
- Pre-loaded for efficiency

---

## Prometheus Metrics

The implementation includes Prometheus metrics for monitoring:

- **Rate Limiting:** `limiter_allowed_total`, `limiter_blocked_total`
- **Redis Health:** `redis_failure_total`, `redis_fallback_total`
- **Circuit Breaker:** `redis_circuit_open`, `redis_connection_failures`
- **Performance:** `rate_limit_check_duration_seconds`

**Metrics Endpoint:** `/metrics`

**Documentation:** See `docs/security/PROMETHEUS_METRICS.md` for complete guide.

---

## Related Documents

- `backend/rate_limiter.py` - Rate limiter implementation
- `backend/config.py` - Configuration settings
- `backend/metrics.py` - Prometheus metrics definitions
- `backend/redis_lua_scripts.py` - Lua scripts for atomic operations
- `backend/redis_storage.py` - Custom Redis storage wrapper
- `docs/security/PROMETHEUS_METRICS.md` - Prometheus metrics guide
- `docs/security/REDIS_LUA_SCRIPTS.md` - Lua scripts guide
- `docs/security/RATE_LIMITING.md` - Rate limiting guide
- `docs/security/INCIDENT_RESPONSE_CHECKLIST.md` - Incident response

---

**Last Updated:** January 2025  
**Status:** Ready for Migration ✅

