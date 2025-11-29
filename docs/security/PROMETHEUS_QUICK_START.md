# Prometheus Quick Start Guide

## ✅ Prometheus & Alertmanager Are Running!

Your monitoring stack is now active. Here's how to use it:

---

## Access the UIs

### Prometheus UI
**URL:** http://localhost:9090

**What you can do:**
- View metrics in real-time
- Query metrics with PromQL
- Check alert rules
- See scrape targets
- View graphs

**Quick checks:**
1. **Status → Targets** - Should show your FastAPI app (may show DOWN if app isn't running yet)
2. **Alerts** - View active alerts
3. **Graph** - Query metrics like `rate(limiter_blocked_total[5m])`

### Alertmanager UI
**URL:** http://localhost:9093

**What you can do:**
- View active alerts
- Create silences
- View alert history
- Test alert routing

---

## Current Status

### Prometheus Configuration
- **Scrape target:** `host.docker.internal:8000` (your FastAPI app)
- **Scrape interval:** Every 15 seconds
- **Alert rules:** Loaded from `prometheus/alerts.yml`

### Alertmanager Configuration
- **Port:** 9093
- **Receivers:** Configured for email notifications
- **Templates:** Loaded from `prometheus/alert_templates.tmpl`

---

## Next Steps

### 1. Start Your FastAPI App

If your FastAPI app isn't running yet, start it:

```bash
# Your usual command to start FastAPI
# e.g., uvicorn backend.api:app --reload
```

### 2. Verify Prometheus is Scraping

Once FastAPI is running:

1. Open http://localhost:9090
2. Go to **Status → Targets**
3. Look for `lesson-planner-api`
4. Status should be **UP** (green)

**If it shows DOWN:**
- Check FastAPI is running: `curl http://localhost:8000/metrics`
- Verify `/metrics` endpoint works
- Check Prometheus logs: `docker logs prometheus`

### 3. View Metrics

**In Prometheus UI:**
1. Go to **Graph** tab
2. Try these queries:
   ```
   rate(limiter_blocked_total[5m])
   rate(limiter_allowed_total[5m])
   redis_circuit_open
   ```

**Or via curl:**
```bash
curl http://localhost:8000/metrics
```

### 4. Test Alerts

**Send a test alert:**
```bash
scripts/test_alertmanager_payload.sh HighRateLimitViolations
```

**Verify:**
- Alert appears in Alertmanager UI: http://localhost:9093
- Check email (if configured)

### 5. Configure Email (If Not Done)

Edit `prometheus/alertmanager.yml`:
```yaml
receivers:
  - name: 'oncall-critical'
    email_configs:
      - to: 'your-email@example.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'your-email@gmail.com'
        auth_password: 'your-app-password'
```

**Reload Alertmanager:**
```bash
curl -X POST http://localhost:9093/-/reload
```

---

## Useful Commands

### Check Container Status
```bash
docker ps --filter "name=prometheus" --filter "name=alertmanager"
```

### View Logs
```bash
docker logs prometheus
docker logs alertmanager
```

### Stop Services
```bash
docker-compose -f docker-compose.monitoring.yml down
```

### Restart Services
```bash
docker-compose -f docker-compose.monitoring.yml restart
```

### Reload Configuration
```bash
# Prometheus
curl -X POST http://localhost:9090/-/reload

# Alertmanager
curl -X POST http://localhost:9093/-/reload
```

### Check Targets
```bash
curl http://localhost:9090/api/v1/targets | ConvertFrom-Json | Select-Object -ExpandProperty data | Select-Object -ExpandProperty activeTargets | Format-Table
```

---

## Troubleshooting

### Prometheus Can't Scrape FastAPI

**Problem:** Target shows DOWN in Prometheus

**Solutions:**
1. Verify FastAPI is running: `curl http://localhost:8000/metrics`
2. Check if `/metrics` endpoint exists and works
3. On Windows, ensure `host.docker.internal` resolves correctly
4. Check Prometheus logs: `docker logs prometheus`

**If using Linux/Mac:** Update `prometheus/prometheus.yml` to use `localhost:8000` instead of `host.docker.internal:8000`

### No Metrics Showing

**Problem:** Metrics don't appear in Prometheus

**Solutions:**
1. Wait 15-30 seconds (scrape interval)
2. Check target is UP: http://localhost:9090/targets
3. Verify metrics endpoint: `curl http://localhost:8000/metrics`
4. Check Prometheus logs for errors

### Alerts Not Firing

**Problem:** Alerts don't appear in Alertmanager

**Solutions:**
1. Check alert rules loaded: http://localhost:9090/rules
2. Verify metrics exist (alerts need metrics to evaluate)
3. Check Prometheus logs for rule evaluation errors
4. Ensure Alertmanager is connected: http://localhost:9090/status

---

## What's Happening Now

1. **Prometheus** is running and ready to scrape your FastAPI app
2. **Alertmanager** is running and ready to receive alerts
3. **Alert rules** are loaded and evaluating every 15 seconds
4. **When FastAPI starts**, Prometheus will automatically start collecting metrics
5. **When thresholds are exceeded**, alerts will fire and go to Alertmanager

---

## Next: Start Your FastAPI App

Once your FastAPI app is running:
1. Prometheus will automatically start scraping metrics
2. You'll see metrics in Prometheus UI
3. Alerts will fire when thresholds are exceeded
4. You'll get email notifications (if configured)

---

## See Also

- [Prometheus Explained](PROMETHEUS_EXPLAINED.md) - What Prometheus does
- [Next Steps Deployment](NEXT_STEPS_ALERTS_DEPLOYMENT.md) - Full deployment guide
- [Alert Runbook](ALERT_RUNBOOK.md) - How to respond to alerts

