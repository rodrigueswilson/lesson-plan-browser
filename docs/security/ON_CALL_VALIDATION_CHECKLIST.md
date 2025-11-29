# On-Call Alertmanager Validation Checklist

Quick validation steps for on-call engineers to verify Alertmanager is functioning correctly during incidents.

## Pre-Incident Validation (5 minutes)

**Run before your on-call shift starts:**

```bash
# 1. Check Alertmanager health
curl http://localhost:9093/-/healthy
# Expected: HTTP 200

# 2. Verify configuration loaded
curl http://localhost:9093/api/v1/status/config | jq '.data' | grep -q "receivers"
# Expected: Shows receiver configuration

# 3. Check active alerts
curl http://localhost:9093/api/v1/alerts | jq '.data.alerts | length'
# Expected: Number of active alerts (may be 0)
```

**Quick visual check:**
- [ ] Alertmanager UI accessible: `http://localhost:9093`
- [ ] No configuration errors in UI
- [ ] Receivers listed in status page

## During Incident - Alert Verification

**When an alert fires, verify:**

1. **Alert received:**
   ```bash
   curl http://localhost:9093/api/v1/alerts | jq '.data.alerts[] | select(.labels.alertname=="ALERT_NAME")'
   ```
   Replace `ALERT_NAME` with actual alert name.

2. **Notification received:**
   - [ ] Slack message in expected channel
   - [ ] PagerDuty incident created (if configured)
   - [ ] Email received (if configured)

3. **Runbook link works:**
   - [ ] Click runbook URL in notification
   - [ ] URL opens correct documentation section
   - [ ] Runbook contains remediation steps

4. **Alert routing correct:**
   - [ ] Critical alerts → `oncall-critical` receiver
   - [ ] Rate limiter alerts → `rate-limiter-team` receiver
   - [ ] Redis alerts → `redis-team` receiver

## Post-Incident Validation

**After resolving an incident:**

1. **Alert resolved:**
   ```bash
   curl http://localhost:9093/api/v1/alerts | jq '.data.alerts[] | select(.status.state=="active")'
   ```
   Verify resolved alerts are no longer active.

2. **Resolution notification:**
   - [ ] "Resolved" notification received
   - [ ] Notification includes incident duration

3. **Silence test alerts:**
   ```bash
   # If test alerts are still active, silence them
   curl -X POST http://localhost:9093/api/v2/silences \
     -H 'Content-Type: application/json' \
     -d '{
       "matchers": [{"name": "env", "value": "staging", "isRegex": false}],
       "startsAt": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
       "endsAt": "'$(date -u -d "+1 hour" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+1H +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")'",
       "comment": "Silence test alerts"
     }'
   ```

## Emergency Test (If Alert Not Received)

**If you suspect Alertmanager isn't working:**

1. **Send test alert:**
   ```bash
   curl -X POST http://localhost:9093/api/v1/alerts \
     -H 'Content-Type: application/json' \
     -d '[
       {
         "labels": {
           "alertname": "TestAlert",
           "severity": "warning",
           "component": "test"
         },
         "annotations": {
           "summary": "On-call test alert",
           "description": "Testing Alertmanager during on-call shift"
         },
         "startsAt": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
       }
     ]'
   ```

2. **Verify notification received within 30 seconds**

3. **If not received, check:**
   - Alertmanager logs: `docker logs alertmanager` or `journalctl -u alertmanager`
   - Receiver configuration: `curl http://localhost:9093/api/v1/status/config | jq '.data.receivers'`
   - Network connectivity to notification endpoints

## Quick Reference Commands

**Health check:**
```bash
curl http://localhost:9093/-/healthy
```

**List active alerts:**
```bash
curl http://localhost:9093/api/v1/alerts | jq '.data.alerts[] | {alertname, status, labels}'
```

**View configuration:**
```bash
curl http://localhost:9093/api/v1/status/config | jq '.data'
```

**Reload configuration:**
```bash
curl -X POST http://localhost:9093/-/reload
```

**Create silence:**
```bash
curl -X POST http://localhost:9093/api/v2/silences \
  -H 'Content-Type: application/json' \
  -d '{
    "matchers": [{"name": "alertname", "value": "ALERT_NAME", "isRegex": false}],
    "startsAt": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "endsAt": "'$(date -u -d "+1 hour" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+1H +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "comment": "Silence reason"
  }'
```

## Common Issues

**Alertmanager not responding:**
- Check if Alertmanager process is running
- Check port 9093 is accessible
- Review Alertmanager logs for errors

**Alerts not routing:**
- Verify route matching in `alertmanager.yml`
- Check alert labels match route conditions
- Review Alertmanager logs for routing errors

**Notifications not received:**
- Verify receiver webhook URLs/keys are configured
- Check network connectivity to notification endpoints
- Review receiver logs in Alertmanager

**Runbook URLs broken:**
- Verify docs URL is correct (not placeholder)
- Check URL is accessible from your network
- Verify anchor links work (e.g., `#high-rate-limit-violations`)

## Integration with Runbook

This checklist complements the [Alert Runbook](ALERT_RUNBOOK.md):

1. **When alert fires:**
   - Use this checklist to verify Alertmanager is working
   - Use [Alert Runbook](ALERT_RUNBOOK.md) for remediation steps

2. **During incident:**
   - Verify notifications are received (this checklist)
   - Follow remediation steps (runbook)

3. **After incident:**
   - Verify alerts resolved (this checklist)
   - Update runbook if gaps found (runbook)

## See Also

- [Alert Runbook](ALERT_RUNBOOK.md) - Detailed remediation steps for each alert
- [Alert Runbook Quick Reference](ALERT_RUNBOOK_QUICK_REFERENCE.md) - One-page quick reference
- [Alertmanager Test Payloads](ALERTMANAGER_TEST_PAYLOADS.md) - Copy-paste test commands
- [Alertmanager Validation Guide](ALERTMANAGER_VALIDATION_TESTING.md) - Full validation procedures

