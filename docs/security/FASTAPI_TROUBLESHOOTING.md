# FastAPI Troubleshooting Guide

## Issue: ERR_EMPTY_RESPONSE or Connection Refused

### Symptoms
- Browser shows "ERR_EMPTY_RESPONSE" or "This page isn't working"
- FastAPI endpoints don't respond
- Port 8000 shows as LISTENING but connections fail

### Common Causes

1. **FastAPI process crashed but port still bound**
2. **Multiple FastAPI instances conflicting**
3. **FastAPI hanging on startup**
4. **Import errors preventing startup**

### Solution Steps

#### Step 1: Kill All Python Processes
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force
```

#### Step 2: Clear Port 8000
```powershell
# Find process on port 8000
netstat -ano | findstr ":8000" | findstr "LISTENING"

# Kill the process (replace PID with actual process ID)
Stop-Process -Id <PID> -Force
```

#### Step 3: Start FastAPI Fresh
```powershell
cd D:\LP
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

#### Step 4: Verify It's Running
```powershell
# Check port
netstat -ano | findstr ":8000" | findstr "LISTENING"

# Test health endpoint
curl http://127.0.0.1:8000/api/health

# Or in browser:
# http://127.0.0.1:8000/docs
```

### Alternative: Start with Python Directly

If `uvicorn` command doesn't work, try:

```powershell
cd D:\LP
python -c "import sys; sys.path.insert(0, '.'); from backend.api import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8000)"
```

### Check for Import Errors

```powershell
cd D:\LP
python -c "from backend.api import app; print('Import successful')"
```

### Verify Dependencies

```powershell
pip list | findstr "uvicorn"
pip list | findstr "fastapi"
pip list | findstr "slowapi"
```

### If Still Not Working

1. **Check Python environment:**
   ```powershell
   python --version
   where python
   ```

2. **Reinstall dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Check for port conflicts:**
   ```powershell
   netstat -ano | findstr ":8000"
   ```

4. **Try a different port:**
   ```powershell
   python -m uvicorn backend.api:app --host 127.0.0.1 --port 8001
   ```

### Quick Restart Script

Create `restart_fastapi.ps1`:

```powershell
# Kill all Python processes
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force -ErrorAction SilentlyContinue

# Wait
Start-Sleep -Seconds 2

# Start FastAPI
cd D:\LP
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd D:\LP; python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000"
```

### Expected Behavior

When FastAPI starts successfully, you should see:
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Test Endpoints

Once running, test these URLs:
- http://127.0.0.1:8000/docs (API documentation)
- http://127.0.0.1:8000/api/health (Health check)
- http://127.0.0.1:8000/metrics (Prometheus metrics)
- http://127.0.0.1:8000/ (Root - redirects to /docs)

---

## Current Status

**Alertmanager:** ✅ Working perfectly
- http://localhost:9093 (UI)
- http://localhost:9093/-/healthy (Health check)

**Prometheus:** ✅ Working perfectly
- http://localhost:9090 (UI)
- Successfully scraping FastAPI metrics

**FastAPI:** ⚠️ Needs restart
- Currently not responding
- Follow steps above to restart

