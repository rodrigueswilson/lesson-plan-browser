# FastAPI Endpoints Summary

## API Documentation

**Swagger UI (Interactive):**
- **URL:** http://127.0.0.1:8000/api/docs
- **Status:** ✅ Working
- **Description:** Interactive API documentation with "Try it out" feature

**ReDoc (Alternative Docs):**
- **URL:** http://127.0.0.1:8000/api/redoc
- **Status:** ✅ Working
- **Description:** Alternative documentation format

**Root Endpoint:**
- **URL:** http://127.0.0.1:8000/
- **Status:** ✅ Working (redirects to `/api/docs`)
- **Description:** Redirects to Swagger UI

## Important Notes

❌ **`/docs` does NOT exist** - This is expected!
- FastAPI is configured with `docs_url="/api/docs"` (not `/docs`)
- If you try to access `/docs`, you'll get `{"detail":"Not Found"}`
- Always use `/api/docs` instead

## Health & Monitoring

**Health Check:**
- **URL:** http://127.0.0.1:8000/api/health
- **Status:** ✅ Working
- **Response:** `{"status":"healthy","version":"1.0.0","timestamp":"..."}`

**Database Health:**
- **URL:** http://127.0.0.1:8000/api/health/database
- **Status:** ✅ Available

**Redis Health:**
- **URL:** http://127.0.0.1:8000/api/health/redis
- **Status:** ✅ Available

**Prometheus Metrics:**
- **URL:** http://127.0.0.1:8000/metrics
- **Status:** ✅ Working
- **Format:** Prometheus text format

## API Endpoints

**Users:**
- `GET /api/users` - List users
- `GET /api/users/{user_id}` - Get user by ID

**Weeks:**
- `GET /api/recent-weeks` - Get recent weeks

**Rendering:**
- `GET /api/render/{filename}` - Render document

**Progress:**
- `GET /api/progress` - List progress tasks
- `GET /api/progress/{task_id}` - Get task status
- `GET /api/progress/{task_id}/poll` - Poll task status

**Analytics:**
- `GET /api/analytics/summary` - Analytics summary
- `GET /api/analytics/daily` - Daily analytics
- `GET /api/analytics/export` - Export analytics

**See `/api/docs` for complete list with descriptions and request/response schemas.**

## Quick Reference

| Endpoint | Status | Description |
|----------|--------|-------------|
| `/` | ✅ | Redirects to `/api/docs` |
| `/api/docs` | ✅ | Swagger UI (use this!) |
| `/api/redoc` | ✅ | ReDoc documentation |
| `/docs` | ❌ | **Does NOT exist** |
| `/api/health` | ✅ | Health check |
| `/metrics` | ✅ | Prometheus metrics |

## Configuration

The FastAPI app is configured with:
```python
app = FastAPI(
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc",  # ReDoc
)
```

This means:
- ✅ `/api/docs` exists
- ✅ `/api/redoc` exists
- ❌ `/docs` does NOT exist (this is correct!)

## Troubleshooting

**If `/docs` returns "Not Found":**
- This is expected! Use `/api/docs` instead.

**If root (`/`) doesn't redirect:**
- Clear browser cache (Ctrl+F5)
- Wait for FastAPI auto-reload
- Use `/api/docs` directly

**To see all endpoints:**
- Visit http://127.0.0.1:8000/api/docs
- Or check `/openapi.json` for the OpenAPI schema

