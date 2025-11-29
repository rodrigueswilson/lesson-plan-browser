# Alertmanager Setup Guide

**Date:** January 2025  
**Purpose:** Configure Alertmanager with runbook links and notification routing

---

## Overview

Alertmanager routes Prometheus alerts to notification channels (Slack, PagerDuty, Email) and attaches runbook URLs for quick access to remediation procedures.

---

## Files Provided

1. **`prometheus/alertmanager.yml`** - Alertmanager configuration
2. **`prometheus/alert_templates.tmpl`** - Alert templates with runbook URLs
3. **`prometheus/alerts.yml`** - Updated with runbook_url annotations

---

## Configuration

### 1. Update Runbook URLs

Edit `prometheus/alerts.yml` and replace:
```
https://your-docs-site.com/docs/security/ALERT_RUNBOOK.md
```

With your actual documentation URL:
```
https://docs.yourcompany.com/security/ALERT_RUNBOOK.md
# or
https://github.com/your-org/your-repo/blob/main/docs/security/ALERT_RUNBOOK.md
```

### 2. Configure Notification Channels

Edit `prometheus/alertmanager.yml`:

**Slack:**
```yaml
slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
    channel: '#oncall-alerts'
```

**PagerDuty:**
```yaml
pagerduty_configs:
  - service_key: 'YOUR_PAGERDUTY_SERVICE_KEY'
```

**Email:**
```yaml
email_configs:
  - to: 'oncall@example.com'
    smarthost: 'smtp.example.com:587'
    auth_username: 'alertmanager@example.com'
    auth_password: 'your-password'
```

### 3. Update Contact Information

Edit `prometheus/alertmanager.yml` receivers section:
- Replace `oncall@example.com` with your on-call email
- Replace Slack webhook URLs
- Replace PagerDuty service keys

### 4. Update Quick Reference

Edit `docs/security/ALERT_RUNBOOK_QUICK_REFERENCE.md`:
- Add on-call contact details
- Add Slack channels
- Add PagerDuty service information
- Add phone numbers for escalation

---

## Installation

### Option 1: Standalone Alertmanager

1. **Install Alertmanager:**
   ```bash
   # Download from https://prometheus.io/download/
   wget https://github.com/prometheus/alertmanager/releases/download/v0.26.0/alertmanager-0.26.0.linux-amd64.tar.gz
   tar xvfz alertmanager-0.26.0.linux-amd64.tar.gz
   ```

2. **Copy Configuration:**
   ```bash
   cp prometheus/alertmanager.yml /etc/alertmanager/alertmanager.yml
   cp prometheus/alert_templates.tmpl /etc/alertmanager/templates/
   ```

3. **Start Alertmanager:**
   ```bash
   ./alertmanager --config.file=/etc/alertmanager/alertmanager.yml
   ```

### Option 2: Docker

```bash
docker run -d \
  --name alertmanager \
  -p 9093:9093 \
  -v $(pwd)/prometheus/alertmanager.yml:/etc/alertmanager/alertmanager.yml \
  -v $(pwd)/prometheus/alert_templates.tmpl:/etc/alertmanager/templates/alert_templates.tmpl \
  prom/alertmanager:latest
```

### Option 3: Kubernetes

See `kubernetes/alertmanager.yaml` (if created separately)

---

## Prometheus Integration

### Configure Prometheus to Use Alertmanager

Edit `prometheus.yml`:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - 'alertmanager:9093'
```

### Reload Prometheus

```bash
curl -X POST http://prometheus:9090/-/reload
```

---

## Alert Routing Logic

### Route Tree

```
All Alerts
├─ Critical Severity → oncall-critical (PagerDuty + Slack + Email)
├─ Rate Limiter Component → rate-limiter-team (Slack)
├─ Redis Component → redis-team (Slack)
└─ Warning Severity → default (Slack + Email)
```

### Inhibition Rules

- Suppress warnings when critical fires (same alert)
- Suppress HighRateLimitViolations when CriticalRateLimitViolations fires
- Suppress HighRedisFailures when CriticalRedisFailures fires
- Suppress RedisFallbackOccurred when RedisFallbackSustained fires

---

## Testing

### Test Alert Routing

1. **Trigger Test Alert:**
   ```bash
   # Generate traffic to trigger rate limit alert
   for i in {1..100}; do
     curl http://localhost:8000/api/users/test/slots
   done
   ```

2. **Check Alertmanager UI:**
   ```bash
   # Open browser
   http://localhost:9093
   ```

3. **Verify Notification:**
   - Check Slack channel
   - Check email inbox
   - Check PagerDuty (if critical)

4. **Verify Runbook Link:**
   - Click runbook_url in alert
   - Should open runbook page
   - Verify correct section loads

---

## Notification Examples

### Slack Notification

```
🚨 *Critical Alert: CriticalRateLimitViolations*

*Severity:* critical
*Environment:* prod

*Description:* 52 requests blocked per second in last 5 minutes.
This may indicate an attack or misconfiguration.
Limit: auth
Environment: prod

*Runbook:* https://docs.example.com/security/ALERT_RUNBOOK.md#critical-rate-limit-violations
```

### Email Notification

**Subject:** CRITICAL: CriticalRateLimitViolations

**Body:**
```
Critical Alert: CriticalRateLimitViolations

Severity: critical
Environment: prod

Description: 52 requests blocked per second in last 5 minutes.
This may indicate an attack or misconfiguration.

View Runbook: https://docs.example.com/security/ALERT_RUNBOOK.md#critical-rate-limit-violations
```

---

## Customization

### Add Custom Receivers

```yaml
receivers:
  - name: 'custom-team'
    slack_configs:
      - api_url: 'YOUR_WEBHOOK'
        channel: '#custom-team'
```

### Modify Routing Rules

```yaml
routes:
  - match:
      team: 'backend'
    receiver: 'backend-team'
```

### Add More Templates

Create additional `.tmpl` files in templates directory:
```bash
/etc/alertmanager/templates/
  ├── alert_templates.tmpl
  └── custom_templates.tmpl
```

---

## Troubleshooting

### Alerts Not Routing

1. **Check Alertmanager Status:**
   ```bash
   curl http://localhost:9093/api/v2/status
   ```

2. **Check Prometheus Configuration:**
   ```bash
   curl http://prometheus:9090/api/v1/alertmanagers
   ```

3. **Check Alertmanager Logs:**
   ```bash
   journalctl -u alertmanager -f
   ```

### Notifications Not Sending

1. **Test Slack Webhook:**
   ```bash
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"Test"}' \
     YOUR_SLACK_WEBHOOK_URL
   ```

2. **Test Email:**
   ```bash
   # Check SMTP settings
   telnet smtp.example.com 587
   ```

3. **Check Alertmanager UI:**
   - Open http://localhost:9093
   - Check "Silences" tab
   - Check "Status" tab for errors

---

## Related Documents

- `prometheus/alertmanager.yml` - Alertmanager configuration
- `prometheus/alert_templates.tmpl` - Alert templates
- `prometheus/alerts.yml` - Alert definitions with runbook URLs
- `docs/security/ALERT_RUNBOOK.md` - Complete runbook
- `docs/security/ALERT_RUNBOOK_QUICK_REFERENCE.md` - Quick reference

---

**Last Updated:** January 2025  
**Status:** Ready for Configuration ✅

