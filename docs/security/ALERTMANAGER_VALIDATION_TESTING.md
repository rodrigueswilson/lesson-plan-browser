# Alertmanager Configuration Validation and Testing Guide

This guide helps you validate your Alertmanager configuration and test alert routing before deploying to production.

## Quick Start

1. **Validate Configuration:**
   
   **Linux/Mac/Git Bash:**
   ```bash
   scripts/validate_alertmanager_config.sh
   ```
   
   **Windows PowerShell:**
   ```powershell
   scripts/validate_alertmanager_config.ps1
   ```

2. **Test Alert Payload:**
   
   **Linux/Mac/Git Bash:**
   ```bash
   # Test with default alert (HighRateLimitViolations)
   scripts/test_alertmanager_payload.sh

   # Test specific alert
   scripts/test_alertmanager_payload.sh CriticalRateLimitViolations

   # Test with custom Alertmanager URL
   ALERTMANAGER_URL=http://alertmanager:9093 scripts/test_alertmanager_payload.sh
   ```
   
   **Note:** The test payload script requires bash (use Git Bash on Windows or WSL).

## Validation Checklist

### 1. Configuration Files

- [ ] `prometheus/alertmanager.yml` exists and is valid YAML
- [ ] `prometheus/alert_templates.tmpl` exists (optional but recommended)
- [ ] `prometheus/alerts.yml` exists and all alerts have `runbook_url` annotations

### 2. Template Path

The template path in `alertmanager.yml` must match your deployment:

**Docker:**
```yaml
templates:
  - '/etc/alertmanager/templates/*.tmpl'
```
Mount templates: `-v ./prometheus:/etc/alertmanager/templates:ro`

**Kubernetes:**
```yaml
templates:
  - '/etc/alertmanager/templates/*.tmpl'
```
Mount ConfigMap at `/etc/alertmanager/templates/`

**Local/Binary:**
```yaml
templates:
  - './prometheus/alert_templates.tmpl'
```
Use relative or absolute path to template file

**Note:** Templates are optional if Prometheus is setting `runbook_url` annotations directly (which it does in `alerts.yml`).

### 3. Receivers Configuration

All receivers referenced in `routes:` must be defined in `receivers:`:

- [ ] `oncall-critical` - Critical alerts
- [ ] `rate-limiter-team` - Rate limiter alerts
- [ ] `redis-team` - Redis alerts
- [ ] `default` - Warning alerts

### 4. Placeholder Replacement

Replace these placeholders before production:

- [ ] `YOUR_SLACK_WEBHOOK_URL` → Actual Slack webhook URL
- [ ] `YOUR_PAGERDUTY_SERVICE_KEY` → Actual PagerDuty integration key
- [ ] `oncall@example.com` → Actual on-call email address
- [ ] `your-docs-site.com` → Actual documentation base URL

**In files:**
- `prometheus/alertmanager.yml` - Receiver webhooks/keys
- `prometheus/alerts.yml` - Runbook URLs
- `prometheus/alert_templates.tmpl` - Runbook URLs (if using templates)

### 5. Route Matching

Verify routes match alert labels correctly:

- Critical alerts (`severity: critical`) → `oncall-critical`
- Rate limiter alerts (`component: rate_limiter`) → `rate-limiter-team`
- Redis alerts (`component: redis`) → `redis-team`
- Warning alerts (`severity: warning`) → `default`

## Testing Procedures

### Manual Validation

1. **Check Alertmanager Health:**
   ```bash
   curl http://localhost:9093/-/healthy
   ```

2. **View Active Alerts:**
   ```bash
   curl http://localhost:9093/api/v1/alerts | jq '.'
   ```

3. **View Configuration:**
   ```bash
   curl http://localhost:9093/api/v1/status/config | jq '.data'
   ```

4. **Reload Configuration (if using file-based config):**
   ```bash
   curl -X POST http://localhost:9093/-/reload
   ```

### Automated Testing

**Test Script:**
```bash
# Run validation
scripts/validate_alertmanager_config.sh

# Send test alert
scripts/test_alertmanager_payload.sh HighRateLimitViolations

# Test different alert types
scripts/test_alertmanager_payload.sh RedisCircuitBreakerOpen
scripts/test_alertmanager_payload.sh CriticalRedisFailures
```

**Expected Results:**
- Validation script exits with code 0 if configuration is valid
- Test script sends alert and receives HTTP 200 response
- Alert appears in notification channels (Slack, PagerDuty, Email)
- Runbook URLs are present and clickable in notifications

### Staging Validation

Before production deployment:

1. **Deploy Alertmanager to staging** with test receivers
2. **Configure test notification channels:**
   - Test Slack channel (e.g., `#alerts-test`)
   - Test PagerDuty service (or use PagerDuty test mode)
   - Test email address
3. **Run test suite:**
   ```bash
   # Validate config
   scripts/validate_alertmanager_config.sh

   # Test each alert type
   for alert in HighRateLimitViolations CriticalRateLimitViolations RedisCircuitBreakerOpen HighRedisFailures; do
     echo "Testing $alert..."
     scripts/test_alertmanager_payload.sh $alert
     sleep 5
   done
   ```
4. **Verify notifications:**
   - Check Slack channel for alerts
   - Check PagerDuty for incidents
   - Check email inbox
   - Verify runbook URLs are correct
5. **Test alert resolution:**
   - Wait for alert to resolve (or manually resolve)
   - Verify "resolved" notifications are sent

## Common Issues and Solutions

### Issue: Template Path Not Found

**Symptoms:**
- Alertmanager logs show: `template: parse error: open /etc/alertmanager/templates/*.tmpl: no such file or directory`

**Solution:**
- Update template path in `alertmanager.yml` to match your deployment
- Or remove templates section if using annotations directly (recommended)

### Issue: Receivers Not Receiving Alerts

**Symptoms:**
- Alerts fire but no notifications received

**Check:**
1. Receiver is defined in `receivers:` section
2. Route matches alert labels correctly
3. Webhook URLs/keys are valid and not placeholders
4. Alertmanager can reach notification endpoints (network/firewall)

**Debug:**
```bash
# Check Alertmanager logs
docker logs alertmanager
# or
journalctl -u alertmanager

# Check active alerts
curl http://localhost:9093/api/v1/alerts | jq '.[] | {alertname, status, receiver}'
```

### Issue: Runbook URLs Missing or Incorrect

**Symptoms:**
- Notifications don't include runbook links
- Runbook URLs point to placeholder domain

**Solution:**
1. Ensure `alerts.yml` has `runbook_url` annotation for each alert
2. Replace `your-docs-site.com` with actual docs URL in:
   - `prometheus/alerts.yml`
   - `prometheus/alert_templates.tmpl` (if using)
3. Verify templates are loaded (check Alertmanager logs)

### Issue: Too Many Notifications

**Symptoms:**
- Receiving duplicate or excessive notifications

**Solution:**
- Adjust `group_wait`, `group_interval`, and `repeat_interval` in routes
- Check inhibition rules are working correctly
- Verify `group_by` is set appropriately

## Production Readiness Checklist

Before deploying to production:

- [ ] All placeholder values replaced with real credentials/URLs
- [ ] Configuration validated with `validate_alertmanager_config.sh`
- [ ] Test alerts sent and verified in all notification channels
- [ ] Runbook URLs tested and accessible
- [ ] Alert routing verified for all alert types
- [ ] Inhibition rules tested (critical suppresses warning)
- [ ] Alert resolution notifications tested
- [ ] On-call rotation configured in notification channels
- [ ] Secrets stored in secrets manager (not in git)
- [ ] Monitoring for Alertmanager itself (health checks, metrics)

## Additional Resources

- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Alert Runbook](../security/ALERT_RUNBOOK.md)
- [Alert Runbook Quick Reference](../security/ALERT_RUNBOOK_QUICK_REFERENCE.md)
- [Receiver Configuration Guide](../security/ALERTMANAGER_RECEIVERS_GUIDE.md)

