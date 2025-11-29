# /docs Endpoint Troubleshooting

## Current Status

The `/docs` endpoint is defined in `backend/api.py` at line 155:

```python
@app.get("/docs", tags=["System"], status_code=307)
async def docs_redirect():
    """
    Convenience endpoint - redirects /docs to /api/docs.
    
    Returns:
        Redirect response to /api/docs
    """
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/docs", status_code=307)
```

## If /docs Still Returns 404

### 1. Check FastAPI Terminal
Look for:
- **Reload messages**: Should see "Reloading..." when file changes
- **Error messages**: Any Python syntax errors or import errors
- **Startup messages**: "Application startup complete"

### 2. Manual Restart
If auto-reload isn't working:
```powershell
# Stop FastAPI (Ctrl+C in terminal)
# Then restart:
cd D:\LP
& d:/LP/.venv/Scripts/Activate.ps1
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

### 3. Clear Browser Cache
- Press `Ctrl+F5` (hard refresh)
- Or use incognito/private mode
- Or clear browser cache completely

### 4. Verify Endpoint Order
FastAPI processes routes in order. Make sure `/docs` route comes before any catch-all routes.

### 5. Test Direct Access
Always use `/api/docs` directly - it always works:
- http://127.0.0.1:8000/api/docs ✅

## Expected Behavior

**After FastAPI reloads:**
- `GET /docs` → `307 Temporary Redirect` → `/api/docs`
- `GET /api/docs` → `200 OK` (Swagger UI)

**If still not working:**
- Check FastAPI terminal for errors
- Verify the code was saved
- Restart FastAPI manually

## Quick Test

**In browser:**
1. Open http://127.0.0.1:8000/docs
2. Should redirect to http://127.0.0.1:8000/api/docs
3. If 404, check FastAPI terminal

**Alternative:**
- Just use http://127.0.0.1:8000/api/docs directly (always works)

