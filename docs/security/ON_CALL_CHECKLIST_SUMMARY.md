# On-Call Validation Checklist - Quick Reference

## Pre-Shift Check (2 minutes)

```bash
# Health check
curl http://localhost:9093/-/healthy

# Active alerts count
curl http://localhost:9093/api/v1/alerts | jq '.data.alerts | length'
```

- [ ] Alertmanager UI accessible
- [ ] No config errors
- [ ] Receivers configured

## During Incident

- [ ] Alert received in Alertmanager
- [ ] Notification received (Slack/PagerDuty/Email)
- [ ] Runbook URL works
- [ ] Alert routes to correct receiver

## Post-Incident

- [ ] Alert resolved
- [ ] Resolution notification received
- [ ] Test alerts silenced (if any)

## Emergency Test

```bash
# Send test alert
curl -X POST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[{"labels":{"alertname":"TestAlert","severity":"warning"},"annotations":{"summary":"Test"},"startsAt":"'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}]'
```

See [ON_CALL_VALIDATION_CHECKLIST.md](ON_CALL_VALIDATION_CHECKLIST.md) for full details.

