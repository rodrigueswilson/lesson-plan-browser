# Starting Prometheus & Alertmanager

## Current Status

✅ **Backend (FastAPI):** Running on http://localhost:8000  
✅ **Frontend:** Running on http://localhost:1420  
✅ **Metrics Endpoint:** Working at http://localhost:8000/metrics  
❌ **Prometheus:** Not running (Docker Desktop needs to be started)

---

## Start Docker Desktop

**Prometheus and Alertmanager run in Docker containers.** You need Docker Desktop running first.

### Step 1: Start Docker Desktop

1. **Open Docker Desktop** from your Start menu or desktop shortcut
2. **Wait for it to fully start** (you'll see "Docker Desktop is running" in the system tray)
3. **Verify it's running:**
   ```powershell
   docker ps
   ```
   Should show running containers (or empty list if no containers running)

### Step 2: Start Prometheus & Alertmanager

Once Docker Desktop is running:

```powershell
cd D:\LP
docker-compose -f docker-compose.monitoring.yml up -d
```

**Expected output:**
```
Creating network lp_monitoring ...
Creating volume lp_prometheus-data ...
Creating volume lp_alertmanager-data ...
Creating container prometheus ...
Creating container alertmanager ...
Starting prometheus ...
Starting alertmanager ...
```

### Step 3: Verify Services

**Wait 5-10 seconds, then check:**

**Prometheus:**
```powershell
Invoke-WebRequest -Uri http://localhost:9090/-/healthy -UseBasicParsing
```
Should return: `Prometheus Server is Healthy.`

**Alertmanager:**
```powershell
Invoke-WebRequest -Uri http://localhost:9093/-/healthy -UseBasicParsing
```
Should return: `ok`

**Or open in browser:**
- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093

---

## Check Prometheus Targets

Once Prometheus is running:

1. **Open:** http://localhost:9090/targets
2. **Look for:** `lesson-planner-api`
3. **Status should be:** **UP** (green) within 15-30 seconds

**If it shows DOWN:**
- Wait a bit longer (scrape interval is 15 seconds)
- Check Prometheus logs: `docker logs prometheus`
- Verify FastAPI metrics endpoint: http://localhost:8000/metrics

---

## Quick Commands

**Start monitoring stack:**
```powershell
cd D:\LP
docker-compose -f docker-compose.monitoring.yml up -d
```

**Stop monitoring stack:**
```powershell
docker-compose -f docker-compose.monitoring.yml down
```

**View logs:**
```powershell
docker logs prometheus
docker logs alertmanager
```

**Check status:**
```powershell
docker ps --filter "name=prometheus" --filter "name=alertmanager"
```

---

## Troubleshooting

### Docker Desktop Not Starting

**If Docker Desktop won't start:**
1. Check if it's already running in system tray
2. Restart Docker Desktop
3. Check Windows Services: `services.msc` → Look for "Docker Desktop Service"

### Port Already in Use

**If ports 9090 or 9093 are in use:**
```powershell
# Find processes using ports
netstat -ano | findstr ":9090"
netstat -ano | findstr ":9093"

# Stop the processes (replace PID)
taskkill /PID <PID> /F
```

### Containers Won't Start

**Check logs:**
```powershell
docker-compose -f docker-compose.monitoring.yml logs
```

**Common issues:**
- Config file errors → Check `prometheus/prometheus.yml` syntax
- Volume permissions → Ensure Docker has access to `D:\LP\prometheus`
- Port conflicts → Check if ports are already in use

---

## Summary

**To get Prometheus running:**

1. ✅ Start Docker Desktop
2. ✅ Run: `docker-compose -f docker-compose.monitoring.yml up -d`
3. ✅ Wait 5-10 seconds
4. ✅ Check: http://localhost:9090
5. ✅ Verify targets: http://localhost:9090/targets

**Your backend and frontend are already running perfectly!** Just need to start the monitoring stack.

