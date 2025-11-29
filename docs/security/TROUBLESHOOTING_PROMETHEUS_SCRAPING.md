# Troubleshooting Prometheus Scraping Issues

## Problem: FastAPI Target Shows DOWN

**Error:** `Error scraping target: Get "http://host.docker.internal:8000/metrics": EOF`

This means Prometheus can't reach your FastAPI app. Here's how to fix it:

---

## Solution 1: Start Your FastAPI App

**Most common cause:** FastAPI app isn't running.

**Check if app is running:**
```powershell
# Try to access the metrics endpoint
Invoke-WebRequest -Uri http://localhost:8000/metrics -UseBasicParsing

# Or check if port 8000 is in use
netstat -an | Select-String ":8000"
```

**Start your FastAPI app:**
```bash
# Your usual command, e.g.:
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
```

**Important:** Make sure FastAPI is listening on `0.0.0.0` (all interfaces), not just `localhost`, so Docker can reach it.

---

## Solution 2: Verify Metrics Endpoint Works

**Test the metrics endpoint directly:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/metrics -UseBasicParsing | Select-Object -ExpandProperty Content
```

**Expected output:** Should show Prometheus metrics like:
```
# HELP limiter_allowed_total Total number of requests allowed by rate limiter
# TYPE limiter_allowed_total counter
limiter_allowed_total{env="dev",limit_name="general",service="lesson-planner"} 0
...
```

**If this fails:** Your FastAPI app might not have the `/metrics` endpoint configured correctly.

---

## Solution 3: Check Docker Network Connectivity

**On Windows Docker Desktop**, `host.docker.internal` should work, but let's verify:

**Test from inside Prometheus container:**
```powershell
docker exec prometheus wget -qO- http://host.docker.internal:8000/metrics | Select-Object -First 5
```

**If this fails**, try these alternatives:

### Option A: Use Host IP Address

1. Find your host IP:
   ```powershell
   ipconfig | Select-String "IPv4"
   ```
   Look for something like `192.168.x.x`

2. Update `prometheus/prometheus.yml`:
   ```yaml
   - targets:
       - '192.168.x.x:8000'  # Replace with your actual IP
   ```

3. Reload Prometheus:
   ```powershell
   Invoke-WebRequest -Uri http://localhost:9090/-/reload -Method POST
   ```

### Option B: Use Docker Network Mode

If your FastAPI app is also in Docker, use Docker networking instead:

1. Update `docker-compose.monitoring.yml` to include your FastAPI service
2. Use service name instead of `host.docker.internal`

---

## Solution 4: Check FastAPI Configuration

**Ensure FastAPI is accessible:**

1. **Check FastAPI is listening on all interfaces:**
   ```python
   # In your uvicorn command or startup script
   uvicorn backend.api:app --host 0.0.0.0 --port 8000
   ```
   Not `--host localhost` or `--host 127.0.0.1`

2. **Verify `/metrics` endpoint exists:**
   Check `backend/api.py` has:
   ```python
   @app.get("/metrics")
   async def metrics_endpoint():
       ...
   ```

3. **Check CORS/security middleware:**
   Make sure security middleware isn't blocking Prometheus requests.

---

## Solution 5: Check Firewall/Antivirus

**Windows Firewall or antivirus might be blocking:**

1. Check Windows Firewall settings
2. Temporarily disable to test (then re-enable)
3. Add exception for port 8000 if needed

---

## Quick Diagnostic Steps

**1. Is FastAPI running?**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/api/health -UseBasicParsing
```

**2. Is metrics endpoint accessible?**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/metrics -UseBasicParsing
```

**3. Can Docker reach host?**
```powershell
docker exec prometheus ping -c 1 host.docker.internal
```

**4. Check Prometheus logs:**
```powershell
docker logs prometheus --tail 50
```

**5. Check target status in Prometheus UI:**
- Go to http://localhost:9090/targets
- Click on the target to see detailed error

---

## Expected Behavior After Fix

Once your FastAPI app is running:

1. **Prometheus UI → Status → Targets:**
   - `lesson-planner-api` should show **UP** (green)
   - Last scrape should be recent (< 15 seconds ago)
   - No errors

2. **Prometheus UI → Graph:**
   - You can query metrics like `rate(limiter_blocked_total[5m])`
   - Metrics should have values

3. **Metrics endpoint:**
   - `http://localhost:8000/metrics` should return Prometheus format

---

## Common Issues Summary

| Issue | Symptom | Solution |
|-------|---------|----------|
| App not running | EOF error | Start FastAPI app |
| Wrong host binding | Connection refused | Use `--host 0.0.0.0` |
| Metrics endpoint missing | 404 error | Add `/metrics` endpoint |
| Network issue | Timeout | Check `host.docker.internal` or use IP |
| Firewall blocking | Connection refused | Check Windows Firewall |

---

## Still Having Issues?

1. **Check Prometheus logs:**
   ```powershell
   docker logs prometheus --tail 100
   ```

2. **Check FastAPI logs:**
   Look for errors when Prometheus tries to connect

3. **Test connectivity:**
   ```powershell
   # From host
   Invoke-WebRequest -Uri http://localhost:8000/metrics -UseBasicParsing
   
   # From Docker container
   docker exec prometheus wget -qO- http://host.docker.internal:8000/metrics
   ```

4. **Verify configuration:**
   - `prometheus/prometheus.yml` has correct target
   - FastAPI is listening on port 8000
   - FastAPI `/metrics` endpoint exists

---

## Next Steps

Once the target shows UP:
1. ✅ Verify metrics appear in Prometheus
2. ✅ Test alert rules
3. ✅ Configure email notifications
4. ✅ Send test alerts

See [PROMETHEUS_QUICK_START.md](PROMETHEUS_QUICK_START.md) for next steps.

