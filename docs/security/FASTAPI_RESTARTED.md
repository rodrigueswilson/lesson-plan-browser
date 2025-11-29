# FastAPI Restarted

## ✅ FastAPI Application Restarted

I've started your FastAPI application in a new PowerShell window.

---

## What Happened

1. **Stopped** any existing process on port 8000
2. **Started** FastAPI with: `uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000`
3. **Opened** in a new PowerShell window so you can see the logs

---

## Verify It's Working

### 1. Check the New PowerShell Window

Look for the new PowerShell window that opened. You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 2. Test the Endpoints

**Health endpoint:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/api/health -UseBasicParsing
```

**Metrics endpoint:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/metrics -UseBasicParsing
```

**Or open in browser:**
- Health: http://localhost:8000/api/health
- Metrics: http://localhost:8000/metrics
- API Docs: http://localhost:8000/docs

### 3. Check Prometheus

**Wait 15-30 seconds**, then check Prometheus:

1. Open http://localhost:9090/targets
2. Look for `lesson-planner-api`
3. Status should change to **UP** (green) within 15-30 seconds
4. Last scrape should be recent

---

## If It's Not Working

### Check the PowerShell Window

Look at the FastAPI startup logs for errors:
- Import errors
- Missing dependencies
- Configuration errors

### Common Issues

**Import Error:**
```
ModuleNotFoundError: No module named 'backend.metrics'
```
**Fix:** Ensure `backend/metrics.py` exists and is importable

**Port Already in Use:**
```
Error: [Errno 48] Address already in use
```
**Fix:** Stop the existing process or use a different port

**Missing Dependencies:**
```
ModuleNotFoundError: No module named 'prometheus_client'
```
**Fix:** `pip install prometheus-client`

---

## Manual Restart (If Needed)

If you need to restart manually:

**Stop:**
```powershell
# Find and stop process on port 8000
.\scripts\stop_fastapi.ps1
```

**Start:**
```powershell
# Start FastAPI
.\scripts\start_fastapi.ps1

# Or manually:
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

---

## Next Steps

Once FastAPI is running and Prometheus shows the target as UP:

1. ✅ **View metrics in Prometheus:**
   - Go to http://localhost:9090/graph
   - Try query: `rate(limiter_blocked_total[5m])`

2. ✅ **Test alerts:**
   ```powershell
   scripts\test_alertmanager_payload.sh HighRateLimitViolations
   ```

3. ✅ **Configure email** (if not done):
   - Edit `prometheus/alertmanager.yml`
   - Add SMTP settings
   - Reload: `Invoke-WebRequest -Uri http://localhost:9093/-/reload -Method POST`

---

## Scripts Created

I've created helper scripts for you:

- `scripts/start_fastapi.ps1` - Start FastAPI easily
- `scripts/stop_fastapi.ps1` - Stop FastAPI easily

Use these for future restarts!

