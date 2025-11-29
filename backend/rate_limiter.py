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
AUTH_LIMIT = "60/minute"  # 60 requests per minute (increased for schedule endpoints)

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


def _rate_limit_exceeded_handler_with_metrics(request: Request, exc: RateLimitExceeded):
    """
    Custom rate limit exceeded handler with metrics tracking.
    
    Args:
        request: FastAPI request object
        exc: RateLimitExceeded exception
    """
    # Determine limit name from request path
    limit_name = "unknown"
    path = request.url.path
    
    if "/slots" in path or "/users" in path:
        if "process-week" in path or "batch" in path:
            limit_name = "batch"
        elif any(x in path for x in ["/users/", "/slots/"]):
            limit_name = "auth"
        else:
            limit_name = "general"
    elif "/analytics" in path:
        limit_name = "heavy"
    
    # Record blocked metric
    try:
        from backend.metrics import record_rate_limit_blocked
        record_rate_limit_blocked(limit_name, reason="limit_exceeded")
    except Exception as e:
        logger.warning("metrics_recording_failed", extra={"error": str(e)})
    
    # Call original handler
    return _rate_limit_exceeded_handler(request, exc)


def setup_rate_limiting(app):
    """
    Set up rate limiting for FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # Add limiter state to app
    app.state.limiter = limiter
    
    # Register rate limit exceeded exception handler with metrics
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler_with_metrics)
    
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


# Circuit breaker state for Redis
_redis_circuit_breaker = {
    "failures": 0,
    "last_failure": None,
    "circuit_open": False,
    "circuit_open_until": None,
    "fallback_count": 0,  # Count of times we fell back to memory
}


def test_redis_connection() -> bool:
    """
    Test Redis connection (for health checks).
    
    Returns:
        True if Redis is accessible, False otherwise
    """
    if not settings.REDIS_URL:
        return True  # Not using Redis
    
    # Check circuit breaker
    if _redis_circuit_breaker["circuit_open"]:
        if _redis_circuit_breaker["circuit_open_until"]:
            import time
            if time.time() < _redis_circuit_breaker["circuit_open_until"]:
                return False  # Circuit still open
            else:
                # Try to close circuit (half-open state)
                _redis_circuit_breaker["circuit_open"] = False
    
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
        
        # Reset circuit breaker on success
        _redis_circuit_breaker["failures"] = 0
        _redis_circuit_breaker["circuit_open"] = False
        _redis_circuit_breaker["circuit_open_until"] = None
        
        # Update metrics
        try:
            from backend.metrics import update_circuit_breaker_status, update_connection_failures
            update_circuit_breaker_status(False)
            update_connection_failures(0)
        except Exception as metrics_error:
            logger.warning("metrics_update_failed", extra={"error": str(metrics_error)})
        
        return True
    except Exception as e:
        logger.error("redis_connection_failed", extra={"error": str(e)})
        
        # Update circuit breaker
        import time
        _redis_circuit_breaker["failures"] += 1
        _redis_circuit_breaker["last_failure"] = time.time()
        
        if _redis_circuit_breaker["failures"] >= settings.REDIS_CIRCUIT_BREAKER_THRESHOLD:
            _redis_circuit_breaker["circuit_open"] = True
            _redis_circuit_breaker["circuit_open_until"] = time.time() + settings.REDIS_CIRCUIT_BREAKER_TIMEOUT
            logger.warning("redis_circuit_opened", extra={
                "failures": _redis_circuit_breaker["failures"],
                "open_until": _redis_circuit_breaker["circuit_open_until"],
            })
            
            # Update metrics
            try:
                from backend.metrics import (
                    update_circuit_breaker_status,
                    update_connection_failures,
                    record_redis_failure
                )
                update_circuit_breaker_status(True)
                update_connection_failures(_redis_circuit_breaker["failures"])
                record_redis_failure("circuit_opened")
            except Exception as metrics_error:
                logger.warning("metrics_update_failed", extra={"error": str(metrics_error)})
        
        # Record failure metric
        try:
            from backend.metrics import record_redis_failure, update_connection_failures
            record_redis_failure("connection_error")
            update_connection_failures(_redis_circuit_breaker["failures"])
        except Exception as metrics_error:
            logger.warning("metrics_recording_failed", extra={"error": str(metrics_error)})
        
        return False


def get_redis_circuit_breaker_status() -> dict:
    """
    Get circuit breaker status for monitoring.
    
    Returns:
        Dictionary with circuit breaker metrics
    """
    status = {
        "circuit_open": _redis_circuit_breaker["circuit_open"],
        "connection_failures": _redis_circuit_breaker["failures"],
        "last_failure_time": _redis_circuit_breaker["last_failure"],
        "circuit_open_until": _redis_circuit_breaker["circuit_open_until"],
        "fallback_count": _redis_circuit_breaker["fallback_count"],
    }
    
    # Update metrics gauges
    try:
        from backend.metrics import update_circuit_breaker_status, update_connection_failures
        update_circuit_breaker_status(_redis_circuit_breaker["circuit_open"])
        update_connection_failures(_redis_circuit_breaker["failures"])
    except Exception as metrics_error:
        logger.warning("metrics_update_failed", extra={"error": str(metrics_error)})
    
    return status

