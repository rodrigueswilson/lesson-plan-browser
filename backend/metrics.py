"""
Prometheus metrics for rate limiting and Redis monitoring.

Provides metrics for:
- Rate limit allowed/blocked requests
- Redis connection failures and fallbacks
- Circuit breaker status
"""

from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from typing import Optional

from backend.config import settings


# Rate limiting metrics
limiter_allowed_total = Counter(
    'limiter_allowed_total',
    'Total number of requests allowed by rate limiter',
    ['limit_name', 'service', 'env']
)

limiter_blocked_total = Counter(
    'limiter_blocked_total',
    'Total number of requests blocked by rate limiter',
    ['limit_name', 'service', 'env', 'reason']
)

# Redis metrics
redis_fallback_total = Counter(
    'redis_fallback_total',
    'Total number of times rate limiter fell back to memory storage',
    ['service', 'env']
)

redis_failure_total = Counter(
    'redis_failure_total',
    'Total number of Redis connection failures',
    ['service', 'env', 'error_type']
)

redis_circuit_open_gauge = Gauge(
    'redis_circuit_open',
    'Whether Redis circuit breaker is open (1 = open, 0 = closed)',
    ['service', 'env']
)

redis_connection_failures_gauge = Gauge(
    'redis_connection_failures',
    'Current count of Redis connection failures',
    ['service', 'env']
)

# Rate limit performance metrics
rate_limit_check_duration = Histogram(
    'rate_limit_check_duration_seconds',
    'Time taken to check rate limit',
    ['limit_name', 'service', 'env'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)


def get_service_name() -> str:
    """Get service name for metrics labels."""
    return "lesson_planner"


def get_env_name() -> str:
    """Get environment name for metrics labels."""
    return settings.REDIS_ENVIRONMENT if settings.REDIS_URL else "memory"


def record_rate_limit_allowed(limit_name: str):
    """Record a rate limit allowed event."""
    limiter_allowed_total.labels(
        limit_name=limit_name,
        service=get_service_name(),
        env=get_env_name()
    ).inc()


def record_rate_limit_blocked(limit_name: str, reason: str = "limit_exceeded"):
    """Record a rate limit blocked event."""
    limiter_blocked_total.labels(
        limit_name=limit_name,
        service=get_service_name(),
        env=get_env_name(),
        reason=reason
    ).inc()


def record_redis_fallback():
    """Record a Redis fallback event."""
    redis_fallback_total.labels(
        service=get_service_name(),
        env=get_env_name()
    ).inc()


def record_redis_failure(error_type: str = "connection_error"):
    """Record a Redis failure event."""
    redis_failure_total.labels(
        service=get_service_name(),
        env=get_env_name(),
        error_type=error_type
    ).inc()


def update_circuit_breaker_status(is_open: bool):
    """Update circuit breaker status gauge."""
    redis_circuit_open_gauge.labels(
        service=get_service_name(),
        env=get_env_name()
    ).set(1 if is_open else 0)


def update_connection_failures(count: int):
    """Update connection failures gauge."""
    redis_connection_failures_gauge.labels(
        service=get_service_name(),
        env=get_env_name()
    ).set(count)


def get_metrics_response():
    """Get Prometheus metrics response."""
    return generate_latest(), CONTENT_TYPE_LATEST

