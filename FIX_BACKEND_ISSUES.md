# Fix Backend Connection Issues

## Problem
Frontend shows error: "Cannot load users! Error: Failed to execute 'json' on 'Response': Unexpected end of JSON input"

This means the backend isn't responding correctly to API requests.

## Quick Fix Steps

### 1. Check if Backend is Running

Open PowerShell and run:
```powershell
curl http://localhost:8000/api/health
```

**Expected**: Should return JSON with `{"status":"healthy",...}`
**If Error**: Backend is not running

### 2. Start Backend Manually

**Open a NEW PowerShell/Command Prompt window:**

```powershell
cd D:\LP
python -m uvicorn backend.api:app --reload --port 8000
```

**Watch for errors in the terminal:**
- `ModuleNotFoundError` → Missing dependencies
- `Port 8000 already in use` → Another process is using the port
- Database connection errors → Check database configuration
- Import errors → Check Python path and dependencies

### 3. Check for Missing Dependencies

If you see `ModuleNotFoundError`, install dependencies:

```powershell
cd D:\LP
pip install -r requirements.txt
```

Or install minimal dependencies:
```powershell
pip install uvicorn fastapi sse-starlette sqlmodel python-dotenv
```

### 4. Check Port 8000 Availability

If port 8000 is already in use, kill the process:

**PowerShell:**
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
```

**Or use a different port:**
```powershell
python -m uvicorn backend.api:app --reload --port 8001
```

Then update frontend config to use port 8001 (or add proxy config).

### 5. Check Database Migration

If backend starts but database errors occur:

**SQLite:**
```powershell
python backend/migrations/create_lesson_mode_sessions_table.py
```

**Supabase:**
- Open Supabase SQL Editor
- Run SQL from: `sql/create_lesson_mode_sessions_table_supabase.sql`

### 6. Verify Backend is Working

Once backend starts, test these URLs in your browser:

- **Health**: http://localhost:8000/api/health
  - Should return: `{"status":"healthy","version":"1.0.0",...}`

- **API Docs**: http://localhost:8000/api/docs
  - Should show FastAPI interactive documentation

- **Users Endpoint**: http://localhost:8000/api/users
  - Should return: `[]` (empty array) or list of users

### 7. Check Frontend Connection

Once backend is running:

1. **Refresh frontend** (http://localhost:1420)
2. **Open Chrome DevTools** (F12)
3. **Go to Console tab**
4. **Check for errors:**
   - If still "Cannot load users" → Check Network tab for API request details
   - If "Failed to fetch" → Backend connection issue
   - If "CORS error" → Check CORS configuration in backend

## Common Error Solutions

### Error: `ModuleNotFoundError: No module named 'backend'`

**Solution:**
- Make sure you're in the project root (D:\LP)
- Check if Python path includes the project root
- Try: `set PYTHONPATH=%CD%` (Windows) before running

### Error: `Port 8000 already in use`

**Solution:**
- Kill existing process on port 8000
- Or use different port (8001, 8002, etc.)
- Update frontend proxy config if needed

### Error: Database connection failed

**Solution:**
- Check `backend/config.py` for database settings
- Ensure database file exists (SQLite) or Supabase credentials are correct
- Run database migrations

### Error: `Failed to fetch` in frontend

**Solution:**
- Verify backend is running on port 8000
- Check browser console Network tab for request details
- Check CORS settings in `backend/api.py`

## Verification Checklist

- [ ] Backend terminal shows: "Uvicorn running on http://127.0.0.1:8000"
- [ ] http://localhost:8000/api/health returns JSON
- [ ] http://localhost:8000/api/docs loads successfully
- [ ] Frontend can connect to backend (no "Failed to fetch" errors)
- [ ] Users API endpoint responds (http://localhost:8000/api/users)
- [ ] Chrome console shows no connection errors

## Still Having Issues?

1. Check backend terminal for error messages
2. Check browser console (F12) for detailed errors
3. Check browser Network tab for failed API requests
4. Verify all dependencies are installed
5. Check database configuration and migrations

