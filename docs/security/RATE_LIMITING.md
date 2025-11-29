# Rate Limiting Implementation

**Date:** January 2025  
**Status:** ✅ Implemented

---

## Overview

Rate limiting middleware has been added to protect API endpoints from brute force attacks and API abuse. The implementation uses `slowapi`, a lightweight rate limiting library for FastAPI.

## Implementation

### Rate Limit Tiers

Different endpoints have different rate limits based on their sensitivity and resource intensity:

| Tier | Limit | Endpoints |
|------|-------|-----------|
| **General** | 100/minute | List operations, read-only endpoints |
| **Auth** | 30/minute | User management, slot operations (create/update/delete) |
| **Heavy** | 10/minute | Resource-intensive operations |
| **Batch** | 5/minute | Batch processing, week processing |

### Endpoint Classifications

**General (100/minute):**
- `GET /api/users/{user_id}/slots` - List slots
- `GET /api/users/{user_id}/plans` - List plans
- `GET /api/recent-weeks` - Get recent weeks

**Auth (30/minute):**
- `GET /api/users/{user_id}` - Get user
- `PUT /api/users/{user_id}` - Update user
- `PUT /api/users/{user_id}/base-path` - Update base path
- `DELETE /api/users/{user_id}` - Delete user
- `POST /api/users/{user_id}/slots` - Create slot
- `PUT /api/slots/{slot_id}` - Update slot
- `DELETE /api/slots/{slot_id}` - Delete slot

**Batch (5/minute):**
- `POST /api/process-week` - Process week (resource-intensive)

## Configuration

### Current Settings

```python
# Rate limit configurations
GENERAL_LIMIT = "100/minute"   # General endpoints
AUTH_LIMIT = "30/minute"       # Authorization-sensitive endpoints
HEAVY_LIMIT = "10/minute"      # Resource-intensive endpoints
BATCH_LIMIT = "5/minute"       # Batch processing endpoints
```

### Storage

Currently using **in-memory storage** (`memory://`), which is suitable for:
- ✅ Single-instance deployments
- ✅ Development/testing environments
- ✅ Small-scale production

For **multi-instance deployments**, consider Redis-backed storage:
```python
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",  # Redis storage
)
```

## Rate Limit Key Function

Rate limiting is based on **IP address** by default:
- Each IP address has its own rate limit counter
- Limits reset after the time period expires
- Prevents single IP from overwhelming the API

### Custom Key Functions

You can customize rate limiting to use user ID instead:

```python
from backend.rate_limiter import get_user_id_for_rate_limit

@rate_limit_auth(key_func=get_user_id_for_rate_limit)
async def endpoint(...):
    ...
```

## Rate Limit Response

When rate limit is exceeded, the API returns:

```json
{
  "detail": "Rate limit exceeded: 30 per 1 minute"
}
```

**HTTP Status:** `429 Too Many Requests`

**Headers:**
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets

## Monitoring

### Logging

Rate limit events are logged:
- Rate limit exceeded events
- IP address (sanitized)
- Endpoint accessed
- Time of event

### Metrics to Monitor

- Rate limit violation frequency
- Which endpoints hit limits most
- IP addresses causing violations
- Patterns indicating attacks

## Adjusting Limits

### Gradual Ramp-Up

Start with generous limits and tighten gradually:

1. **Initial:** Set limits higher than expected usage
2. **Monitor:** Track actual usage patterns
3. **Adjust:** Gradually reduce limits based on data
4. **Alert:** Set up alerts for frequent violations

### Example Adjustments

```python
# Start generous
AUTH_LIMIT = "100/minute"

# After monitoring, tighten
AUTH_LIMIT = "50/minute"

# Final production setting
AUTH_LIMIT = "30/minute"
```

## Testing

### Test Rate Limiting

```bash
# Make rapid requests to trigger rate limit
for i in {1..35}; do
  curl -H "X-Current-User-Id: user-123" \
       http://localhost:8000/api/users/user-123/slots
done

# Should get 429 after 30 requests
```

### Integration Tests

Add rate limit tests to `tests/test_integration_authorization.py`:

```python
def test_rate_limit_exceeded(test_client, user_a):
    """Rate limit should return 429 when exceeded."""
    # Make requests exceeding the limit
    for _ in range(35):
        response = test_client.get(
            f"/api/users/{user_a}/slots",
            headers={"X-Current-User-Id": user_a}
        )
    
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["detail"]
```

## Production Considerations

### Multi-Instance Deployments

For multiple backend instances, use Redis:

```python
# Install redis
pip install redis

# Update rate_limiter.py
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://redis-host:6379",
)
```

### Load Balancer Considerations

If behind a load balancer, ensure `X-Forwarded-For` header is trusted:

```python
def get_remote_address(request: Request) -> str:
    """Get client IP, handling load balancer."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host
```

### Bypassing Rate Limits

For admin/health endpoints, you can bypass rate limiting:

```python
from backend.rate_limiter import limiter

@app.get("/api/health")
@limiter.exempt  # No rate limit
async def health_check():
    ...
```

## Troubleshooting

### Issue: Rate limits too strict

**Solution:** Increase limits gradually:
```python
AUTH_LIMIT = "50/minute"  # Increase from 30
```

### Issue: Rate limits not working

**Check:**
1. Rate limiter is initialized: `setup_rate_limiting(app)`
2. Decorators are applied to endpoints
3. Storage backend is accessible (if using Redis)

### Issue: Rate limits resetting incorrectly

**Solution:** Check storage backend:
- In-memory: Resets on server restart
- Redis: Persistent across restarts

## Future Enhancements

### Planned Improvements

- [ ] Per-user rate limiting (using user ID from header)
- [ ] Dynamic rate limits based on user tier
- [ ] Rate limit metrics dashboard
- [ ] Automatic rate limit adjustment based on load
- [ ] Whitelist for trusted IPs/users

### Redis Integration

When scaling to multiple instances:

1. Install Redis
2. Update `storage_uri` to Redis
3. Configure Redis connection pooling
4. Monitor Redis performance

---

## Files Modified

- ✅ `backend/rate_limiter.py` - Rate limiting module (NEW)
- ✅ `backend/api.py` - Applied rate limit decorators to endpoints
- ✅ `requirements.txt` - Added `slowapi` dependency
- ✅ `docs/security/RATE_LIMITING.md` - This documentation

---

## Summary

**Status:** ✅ Rate limiting implemented and active

**Protection:**
- ✅ Brute force attack prevention
- ✅ API abuse protection
- ✅ Resource exhaustion prevention
- ✅ Configurable limits per endpoint type

**Next Steps:**
1. Monitor rate limit violations
2. Adjust limits based on usage patterns
3. Consider Redis for multi-instance deployments
4. Add rate limit metrics to monitoring dashboard

---

**Last Updated:** January 2025

