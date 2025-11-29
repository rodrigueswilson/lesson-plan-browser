# Fix: Prometheus Can't Scrape Metrics Endpoint

## Problem

Prometheus shows: `Error scraping target: Get "http://host.docker.internal:8000/metrics": EOF`

Your FastAPI app is running (port 8000 is listening), but the `/metrics` endpoint isn't responding.

---

## Quick Fixes

### Fix 1: Restart Your FastAPI App

The app might be in a bad state. **Restart it:**

```bash
# Stop your current FastAPI process
# Then restart:
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

**Important:** Use `--host 0.0.0.0` so Docker can reach it.

### Fix 2: Check for Import Errors

The metrics endpoint imports `get_metrics_response` from `backend.metrics`. Check if there are import errors:

**Look at your FastAPI startup logs** for errors like:
- `ModuleNotFoundError: No module named 'backend.metrics'`
- `ImportError: cannot import name 'get_metrics_response'`

**If you see errors**, verify:
1. `backend/metrics.py` exists
2. `get_metrics_response()` function exists in that file
3. All dependencies are installed (`prometheus-client`)

### Fix 3: Test Metrics Endpoint Manually

**Try accessing it directly in your browser:**
```
http://localhost:8000/metrics
```

**Or with PowerShell:**
```powershell
# Try with different methods
Invoke-RestMethod -Uri http://localhost:8000/metrics
# Or
curl.exe http://localhost:8000/metrics
```

**Expected:** Should return Prometheus metrics text format.

**If it fails:** Check FastAPI logs for the error.

### Fix 4: Verify Metrics Module

**Check if metrics.py exists and has the function:**
```powershell
# Verify file exists
Test-Path backend/metrics.py

# Check if function exists
Select-String -Path backend/metrics.py -Pattern "def get_metrics_response"
```

**If missing:** The metrics module might not be set up correctly.

---

## Step-by-Step Diagnostic

### Step 1: Check FastAPI Logs

**Look at your FastAPI console output** for errors when you try to access `/metrics`.

Common errors:
- Import errors
- Runtime errors in `get_metrics_response()`
- Missing dependencies

### Step 2: Test Basic Endpoints

**Try these endpoints to see what works:**
```powershell
# Health endpoint
Invoke-WebRequest -Uri http://localhost:8000/api/health -UseBasicParsing

# Root endpoint
Invoke-WebRequest -Uri http://localhost:8000/ -UseBasicParsing

# Metrics endpoint
Invoke-WebRequest -Uri http://localhost:8000/metrics -UseBasicParsing
```

**If health works but metrics doesn't:** The issue is specific to the metrics endpoint.

### Step 3: Check Dependencies

**Verify prometheus-client is installed:**
```bash
pip list | findstr prometheus
# Should show: prometheus-client
```

**If missing:**
```bash
pip install prometheus-client
```

### Step 4: Test from Docker

**Test if Docker can reach your app:**
```powershell
docker exec prometheus wget -qO- http://host.docker.internal:8000/api/health
```

**If this works but metrics doesn't:** The issue is with the `/metrics` endpoint specifically.

---

## Common Solutions

### Solution A: App Needs Restart

**Most common:** App started but hit an error. Restart it.

```bash
# Kill existing process
# Then restart with:
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

### Solution B: Missing Dependencies

**Install missing packages:**
```bash
pip install prometheus-client
pip install -r requirements.txt  # If you have one
```

### Solution C: Import Error

**Check `backend/metrics.py` exists and is correct:**
- File should exist: `backend/metrics.py`
- Should have function: `get_metrics_response()`
- Should import: `from prometheus_client import ...`

### Solution D: App Crashes on Request

**Check FastAPI logs** when accessing `/metrics`. Look for:
- Python exceptions
- Import errors
- Runtime errors

---

## After Fixing

**Once `/metrics` works:**

1. **Test locally:**
   ```powershell
   Invoke-WebRequest -Uri http://localhost:8000/metrics -UseBasicParsing | Select-Object -ExpandProperty Content
   ```
   Should return Prometheus metrics.

2. **Check Prometheus:**
   - Go to http://localhost:9090/targets
   - `lesson-planner-api` should show **UP** (green)
   - Last scrape should be recent

3. **Query metrics:**
   - Go to http://localhost:9090/graph
   - Try: `rate(limiter_blocked_total[5m])`

---

## Still Not Working?

**Check these:**

1. **FastAPI startup logs** - Look for errors
2. **Python version** - Ensure compatible Python version
3. **Virtual environment** - Make sure you're in the right venv
4. **Port conflicts** - Ensure nothing else is using port 8000
5. **Firewall** - Check Windows Firewall isn't blocking

**Get more details:**
```powershell
# Check what's listening on port 8000
netstat -ano | Select-String ":8000"

# Check FastAPI process
Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*uvicorn*"}
```

---

## Quick Test Script

**Create `test_metrics.ps1`:**
```powershell
Write-Host "Testing FastAPI endpoints..." -ForegroundColor Cyan

# Test health
Write-Host "`n1. Testing /api/health..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri http://localhost:8000/api/health -UseBasicParsing
    Write-Host "✓ Health endpoint works" -ForegroundColor Green
} catch {
    Write-Host "✗ Health endpoint failed: $_" -ForegroundColor Red
}

# Test metrics
Write-Host "`n2. Testing /metrics..." -ForegroundColor Yellow
try {
    $metrics = Invoke-WebRequest -Uri http://localhost:8000/metrics -UseBasicParsing
    Write-Host "✓ Metrics endpoint works" -ForegroundColor Green
    Write-Host "Response length: $($metrics.Content.Length) bytes" -ForegroundColor Cyan
    Write-Host "First 200 chars: $($metrics.Content.Substring(0, [Math]::Min(200, $metrics.Content.Length)))" -ForegroundColor Gray
} catch {
    Write-Host "✗ Metrics endpoint failed: $_" -ForegroundColor Red
}

# Test from Docker
Write-Host "`n3. Testing from Docker container..." -ForegroundColor Yellow
try {
    $dockerTest = docker exec prometheus wget -qO- http://host.docker.internal:8000/metrics 2>&1
    if ($dockerTest -match "limiter") {
        Write-Host "✓ Docker can reach metrics" -ForegroundColor Green
    } else {
        Write-Host "✗ Docker test failed: $dockerTest" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Docker test failed: $_" -ForegroundColor Red
}
```

**Run it:**
```powershell
.\test_metrics.ps1
```

This will help identify exactly where the problem is.

