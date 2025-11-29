# Next Steps: Alerts & Monitoring Deployment

Complete guide for deploying Prometheus, Alertmanager, and integrating with your FastAPI application.

## Overview

You now have:
- ✅ Prometheus alert rules (`prometheus/alerts.yml`)
- ✅ Alertmanager configuration (`prometheus/alertmanager.yml`)
- ✅ Alert runbooks and documentation
- ✅ FastAPI `/metrics` endpoint
- ✅ Email notification setup

**Next:** Deploy and integrate everything.

---

## Phase 1: Local Testing (30 minutes)

### Step 1.1: Start Prometheus and Alertmanager

**Option A: Docker Compose (Recommended)**

Create `docker-compose.monitoring.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus:/etc/prometheus:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./prometheus/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - ./prometheus/alert_templates.tmpl:/etc/alertmanager/templates/alert_templates.tmpl:ro
      - alertmanager-data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--web.external-url=http://localhost:9093'
    restart: unless-stopped
    depends_on:
      - prometheus

volumes:
  prometheus-data:
  alertmanager-data:
```

**Start services:**
```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

**Option B: Local Binaries**

Download and run Prometheus/Alertmanager locally:
```bash
# Download Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# Start Prometheus
./prometheus --config.file=../prometheus/prometheus.yml

# In another terminal, download Alertmanager
wget https://github.com/prometheus/alertmanager/releases/download/v0.26.0/alertmanager-0.26.0.linux-amd64.tar.gz
tar xvfz alertmanager-*.tar.gz
cd alertmanager-*

# Start Alertmanager
./alertmanager --config.file=../prometheus/alertmanager.yml
```

### Step 1.2: Verify Services

**Check Prometheus:**
```bash
curl http://localhost:9090/-/healthy
# Expected: Prometheus is Healthy.

# Open in browser: http://localhost:9090
# Check Status → Targets - should show "lesson-planner-api" as UP
```

**Check Alertmanager:**
```bash
curl http://localhost:9093/-/healthy
# Expected: ok

# Open in browser: http://localhost:9093
```

**Check FastAPI metrics:**
```bash
curl http://localhost:8000/metrics
# Should show Prometheus metrics
```

### Step 1.3: Update Prometheus Config

Edit `prometheus/prometheus.yml`:
- Update `localhost:8000` to your FastAPI host:port
- Update `alertmanager:9093` if Alertmanager is hosted elsewhere
- Update `environment` labels (prod/staging/dev)

**Reload Prometheus config:**
```bash
curl -X POST http://localhost:9090/-/reload
```

### Step 1.4: Test Alert Firing

**Send test alert:**
```bash
scripts/test_alertmanager_payload.sh HighRateLimitViolations
```

**Verify:**
1. Alert appears in Alertmanager UI: http://localhost:9093
2. Email notification received (if email configured)
3. Alert shows in Prometheus: http://localhost:9090/alerts

---

## Phase 2: Integration Testing (1 hour)

### Step 2.1: Generate Real Metrics

**Trigger rate limiting:**
```bash
# Send requests to trigger rate limits
for i in {1..100}; do
  curl http://localhost:8000/api/health
  sleep 0.1
done
```

**Check metrics:**
```bash
curl http://localhost:8000/metrics | grep limiter_blocked_total
```

### Step 2.2: Verify Alerts Fire

**Wait 5-10 minutes** for alerts to evaluate, then check:

**Prometheus Alerts:**
```bash
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | {alertname, state}'
```

**Alertmanager:**
- Open http://localhost:9093
- Check "Alerts" tab
- Verify alerts are firing

### Step 2.3: Test Email Notifications

**Configure email in `prometheus/alertmanager.yml`:**
```yaml
receivers:
  - name: 'oncall-critical'
    email_configs:
      - to: 'your-email@example.com'  # ← Update this
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'your-email@gmail.com'
        auth_password: 'your-app-password'
```

**Reload Alertmanager:**
```bash
curl -X POST http://localhost:9093/-/reload
```

**Send test alert and verify email received**

### Step 2.4: Validate Runbook Links

1. Click runbook URL in email notification
2. Verify it opens correct documentation section
3. Update placeholder URLs if needed:
   - `prometheus/alerts.yml` - Replace `your-docs-site.com`
   - `prometheus/alert_templates.tmpl` - Replace `your-docs-site.com`

---

## Phase 3: Staging Deployment (2 hours)

### Step 3.1: Deploy to Staging

**Update configurations for staging:**
- `prometheus/prometheus.yml` - Set `environment: staging`
- `prometheus/alertmanager.yml` - Update email to staging on-call
- `prometheus/alerts.yml` - Update docs URLs if different

**Deploy Prometheus/Alertmanager:**
- Use Docker Compose, Kubernetes, or your deployment method
- Ensure volumes persist data
- Configure health checks

### Step 3.2: Configure Scraping

**Update Prometheus scrape config:**
```yaml
scrape_configs:
  - job_name: 'lesson-planner-api'
    static_configs:
      - targets:
          - 'staging-api.yourcompany.com:8000'  # ← Update
        labels:
          env: 'staging'
```

**Or use service discovery** (Kubernetes, Consul, etc.)

### Step 3.3: Run Validation Scripts

```bash
# Validate configuration
scripts/validate_alertmanager_config.sh

# Test alerts
scripts/test_alertmanager_payload.sh

# Run staging validation
scripts/staging_alert_validation.sh  # If you have this
```

### Step 3.4: Monitor for 24-48 Hours

- Watch for false positives
- Adjust alert thresholds if needed
- Verify all alert types fire correctly
- Test alert resolution

---

## Phase 4: Production Deployment (4 hours)

### Step 4.1: Pre-Deployment Checklist

- [ ] All placeholder URLs replaced
- [ ] Email SMTP configured and tested
- [ ] Alert thresholds validated in staging
- [ ] Runbooks accessible to on-call team
- [ ] On-call rotation configured
- [ ] Escalation contacts added
- [ ] Monitoring for Prometheus/Alertmanager itself configured

### Step 4.2: Deploy to Production

**Update configurations:**
- `prometheus/prometheus.yml` - Set `environment: production`
- `prometheus/alertmanager.yml` - Production email addresses
- Update scrape targets to production API

**Deploy:**
- Use your standard deployment process
- Ensure high availability (multiple Prometheus/Alertmanager instances if needed)
- Configure persistent storage
- Set up backups

### Step 4.3: Verify Production

**Health checks:**
```bash
curl https://prometheus.yourcompany.com/-/healthy
curl https://alertmanager.yourcompany.com/-/healthy
```

**Check targets:**
- Prometheus UI → Status → Targets
- Verify all targets are UP

**Test alerts:**
- Send test alert (use staging-like payload)
- Verify email notifications
- Verify runbook links work

### Step 4.4: Send Team Announcement

**Send email announcement:**
- Use `docs/security/EMAIL_ANNOUNCEMENT_READY.md`
- Include on-call checklist
- Share runbook links

---

## Phase 5: Ongoing Maintenance

### Step 5.1: Regular Checks

**Weekly:**
- Review alert firing frequency
- Check for false positives
- Verify email notifications working

**Monthly:**
- Review alert thresholds
- Update runbooks based on incidents
- Review and tune alert rules

### Step 5.2: Monitoring Prometheus/Alertmanager

**Set up monitoring for:**
- Prometheus uptime
- Alertmanager uptime
- Scrape failures
- Storage usage
- Alert evaluation time

**Example alerts:**
```yaml
- alert: PrometheusDown
  expr: up{job="prometheus"} == 0
  for: 5m

- alert: AlertmanagerDown
  expr: up{job="alertmanager"} == 0
  for: 5m

- alert: PrometheusScrapeFailures
  expr: rate(prometheus_target_scrapes_exceeded_sample_limit_total[5m]) > 0
  for: 10m
```

### Step 5.3: Documentation Updates

- Update runbooks based on incidents
- Add new alerts as needed
- Keep on-call checklist current

---

## Quick Reference

### Configuration Files

- `prometheus/prometheus.yml` - Prometheus scrape config
- `prometheus/alertmanager.yml` - Alert routing and receivers
- `prometheus/alerts.yml` - Alert rules
- `prometheus/alert_templates.tmpl` - Notification templates

### Key Endpoints

- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093
- FastAPI Metrics: http://localhost:8000/metrics

### Useful Commands

**Validate config:**
```bash
scripts/validate_alertmanager_config.sh
```

**Test alerts:**
```bash
scripts/test_alertmanager_payload.sh HighRateLimitViolations
```

**Reload config:**
```bash
curl -X POST http://localhost:9090/-/reload  # Prometheus
curl -X POST http://localhost:9093/-/reload  # Alertmanager
```

**View active alerts:**
```bash
curl http://localhost:9093/api/v1/alerts | jq '.'
```

### Troubleshooting

**Prometheus not scraping:**
- Check targets: http://localhost:9090/targets
- Verify FastAPI `/metrics` endpoint accessible
- Check network connectivity

**Alerts not firing:**
- Check Prometheus alerts: http://localhost:9090/alerts
- Verify alert rules loaded: http://localhost:9090/rules
- Check alert evaluation interval

**Email not received:**
- Verify SMTP settings in `alertmanager.yml`
- Check Alertmanager logs
- Test SMTP connectivity separately

---

## See Also

- [Prometheus Metrics Guide](PROMETHEUS_METRICS.md) - Metrics documentation
- [Alert Runbook](ALERT_RUNBOOK.md) - Detailed remediation steps
- [On-Call Validation Checklist](ON_CALL_VALIDATION_CHECKLIST.md) - Pre-shift checks
- [Email-Focused Quick Start](EMAIL_FOCUSED_QUICK_START.md) - Email setup

---

## Timeline Estimate

- **Phase 1 (Local Testing):** 30 minutes
- **Phase 2 (Integration Testing):** 1 hour
- **Phase 3 (Staging):** 2 hours
- **Phase 4 (Production):** 4 hours
- **Phase 5 (Ongoing):** Continuous

**Total initial setup:** ~8 hours

