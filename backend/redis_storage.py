"""
Custom Redis storage backend for rate limiting with atomic Lua operations.

Provides atomic increment+expire operations to prevent race conditions
in high-concurrency scenarios.
"""

import time
from typing import Optional, Tuple
from urllib.parse import urlparse
import redis
from redis.exceptions import ConnectionError, TimeoutError, RedisError

from backend.config import settings
from backend.telemetry import logger
from backend.redis_lua_scripts import (
    RATE_LIMIT_CHECK_SCRIPT,
    RATE_LIMIT_INCREMENT_SCRIPT,
    RATE_LIMIT_STATUS_SCRIPT,
)


class RedisStorageWithLua:
    """
    Redis storage backend with atomic Lua script operations.
    
    Provides thread-safe rate limiting operations using Redis Lua scripts
    to ensure atomic increment+expire operations.
    """
    
    def __init__(self, redis_url: str, key_prefix: str = "rate_limit"):
        """
        Initialize Redis storage.
        
        Args:
            redis_url: Redis connection URL
            key_prefix: Prefix for all rate limit keys
        """
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self._client: Optional[redis.Redis] = None
        self._connection_failures = 0
        self._last_failure_time: Optional[float] = None
        self._circuit_open = False
        self._circuit_open_until: Optional[float] = None
        
        # Load Lua scripts
        self._check_script = None
        self._increment_script = None
        self._status_script = None
        
        self._connect()
    
    def _connect(self):
        """Establish Redis connection and load Lua scripts."""
        try:
            parsed = urlparse(self.redis_url)
            self._client = redis.Redis(
                host=parsed.hostname or "localhost",
                port=parsed.port or 6379,
                password=settings.REDIS_PASSWORD or parsed.password,
                db=int(parsed.path.lstrip("/")) if parsed.path else 0,
                ssl=settings.REDIS_SSL,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
                max_connections=50,  # Connection pool size
            )
            
            # Test connection
            self._client.ping()
            
            # Load Lua scripts (register them server-side for efficiency)
            self._check_script = self._client.register_script(RATE_LIMIT_CHECK_SCRIPT)
            self._increment_script = self._client.register_script(RATE_LIMIT_INCREMENT_SCRIPT)
            self._status_script = self._client.register_script(RATE_LIMIT_STATUS_SCRIPT)
            
            # Reset circuit breaker on successful connection
            self._connection_failures = 0
            self._circuit_open = False
            self._circuit_open_until = None
            
            logger.info("redis_storage_connected", extra={
                "key_prefix": self.key_prefix,
                "host": parsed.hostname or "localhost",
            })
            
        except Exception as e:
            logger.error("redis_storage_connection_failed", extra={"error": str(e)})
            self._handle_connection_failure()
            raise
    
    def _handle_connection_failure(self):
        """Handle connection failure and implement circuit breaker pattern."""
        self._connection_failures += 1
        self._last_failure_time = time.time()
        
        # Open circuit if too many failures
        if self._connection_failures >= 5:
            self._circuit_open = True
            self._circuit_open_until = time.time() + 60  # Keep circuit open for 60 seconds
            logger.warning("redis_circuit_opened", extra={
                "failures": self._connection_failures,
                "open_until": self._circuit_open_until,
            })
    
    def _check_circuit(self) -> bool:
        """Check if circuit breaker should allow operation."""
        if not self._circuit_open:
            return True
        
        # Check if circuit should be closed (half-open state)
        if self._circuit_open_until and time.time() > self._circuit_open_until:
            self._circuit_open = False
            logger.info("redis_circuit_half_open")
            return True
        
        return False
    
    def _get_key(self, identifier: str, limit_name: str = "") -> str:
        """
        Build Redis key with proper prefixing.
        
        Format: {env}:{service}:{prefix}:{limit_name}:{identifier}
        
        Args:
            identifier: User ID or IP address
            limit_name: Optional limit name (e.g., "auth", "general")
        
        Returns:
            Formatted Redis key
        """
        env = settings.REDIS_KEY_PREFIX.split(":")[0] if ":" in settings.REDIS_KEY_PREFIX else "prod"
        service = "lesson_planner"
        parts = [env, service, self.key_prefix]
        
        if limit_name:
            parts.append(limit_name)
        
        parts.append(identifier)
        return ":".join(parts)
    
    def hit(self, key: str, limit: int, window: int) -> Tuple[int, int, bool]:
        """
        Atomically check and increment rate limit counter.
        
        Uses Lua script to ensure atomic operation (increment + expire).
        
        Args:
            key: Rate limit key (identifier)
            limit: Maximum allowed requests
            window: Time window in seconds
        
        Returns:
            Tuple of (current_count, ttl, limit_exceeded)
            - current_count: Current request count
            - ttl: Time until reset in seconds
            - limit_exceeded: True if limit exceeded
        """
        if not self._check_circuit():
            # Circuit is open, fail fast
            raise RedisError("Circuit breaker is open")
        
        if not self._client:
            self._connect()
        
        try:
            redis_key = self._get_key(key)
            result = self._check_script(
                keys=[redis_key],
                args=[limit, window]
            )
            
            current_count, ttl, limit_exceeded = result
            return (current_count, ttl, bool(limit_exceeded))
            
        except (ConnectionError, TimeoutError) as e:
            logger.error("redis_operation_failed", extra={"error": str(e)})
            self._handle_connection_failure()
            raise
        except Exception as e:
            logger.error("redis_unexpected_error", extra={"error": str(e)})
            raise
    
    def get(self, key: str) -> Tuple[int, int]:
        """
        Get current rate limit status without incrementing.
        
        Args:
            key: Rate limit key (identifier)
        
        Returns:
            Tuple of (current_count, ttl)
        """
        if not self._check_circuit():
            raise RedisError("Circuit breaker is open")
        
        if not self._client:
            self._connect()
        
        try:
            redis_key = self._get_key(key)
            result = self._status_script(keys=[redis_key])
            current_count, ttl = result
            return (current_count, ttl)
        except Exception as e:
            logger.error("redis_get_failed", extra={"error": str(e)})
            raise
    
    def get_circuit_breaker_status(self) -> dict:
        """
        Get circuit breaker status for monitoring.
        
        Returns:
            Dictionary with circuit breaker metrics
        """
        return {
            "circuit_open": self._circuit_open,
            "connection_failures": self._connection_failures,
            "last_failure_time": self._last_failure_time,
            "circuit_open_until": self._circuit_open_until,
        }

