"""
Middleware to track rate limit metrics for successful requests.

This middleware tracks when requests pass rate limiting checks,
complementing the exception handler that tracks blocked requests.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from backend.telemetry import logger
from backend.metrics import record_rate_limit_allowed


class RateLimitMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track rate limit allowed metrics.
    
    Tracks successful requests that pass rate limiting checks.
    Note: Blocked requests are tracked in the exception handler.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and track metrics.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
        
        Returns:
            Response
        """
        # Determine limit name from path
        limit_name = self._get_limit_name(request.url.path)
        
        # Process request
        response = await call_next(request)
        
        # Track allowed requests (only if not rate limited)
        # Rate limited requests return 429 and are tracked in exception handler
        if response.status_code != 429:
            try:
                record_rate_limit_allowed(limit_name)
            except Exception as e:
                logger.warning("metrics_recording_failed", extra={"error": str(e)})
        
        return response
    
    def _get_limit_name(self, path: str) -> str:
        """
        Determine rate limit name from request path.
        
        Args:
            path: Request path
        
        Returns:
            Limit name (auth, general, heavy, batch, unknown)
        """
        if "process-week" in path or "batch" in path:
            return "batch"
        elif "/analytics" in path:
            return "heavy"
        elif any(x in path for x in ["/users/", "/slots/"]):
            return "auth"
        elif any(x in path for x in ["/users", "/slots", "/recent-weeks"]):
            return "general"
        else:
            return "unknown"

