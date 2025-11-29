# On-Call Alertmanager Validation Checklist
## Printable One-Page Reference

---

## Pre-Shift Check (2 minutes)

**Health Check:**
```bash
curl ALERTMANAGER_URL/-/healthy
# Expected: "ok"
```

**Active Alerts:**
```bash
curl ALERTMANAGER_URL/api/v1/alerts | jq '.data.alerts | length'
```

**Quick Visual:**
- [ ] Alertmanager UI accessible
- [ ] No configuration errors
- [ ] Receivers configured

---

## During Incident

**When alert fires:**
- [ ] Alert received in Alertmanager
- [ ] Notification received (Slack/PagerDuty/Email)
- [ ] Runbook URL works and opens correct section
- [ ] Alert routes to correct receiver

**Verify routing:**
- Critical alerts → `oncall-critical` receiver
- Rate limiter alerts → `rate-limiter-team` receiver
- Redis alerts → `redis-team` receiver

---

## Post-Incident

**After resolving:**
- [ ] Alert resolved in Alertmanager
- [ ] Resolution notification received
- [ ] Test alerts silenced (if any)

---

## Emergency Test

**If Alertmanager not working:**
```bash
curl -X POST ALERTMANAGER_URL/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[{"labels":{"alertname":"TestAlert","severity":"warning"},"annotations":{"summary":"Test"},"startsAt":"'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}]'
```

Verify notification received within 30 seconds.

---

## Quick Commands

**Health:** `curl ALERTMANAGER_URL/-/healthy`

**Active Alerts:** `curl ALERTMANAGER_URL/api/v1/alerts | jq '.'`

**View Config:** `curl ALERTMANAGER_URL/api/v1/status/config | jq '.data'`

**Reload Config:** `curl -X POST ALERTMANAGER_URL/-/reload`

**Create Silence:**
```bash
curl -X POST ALERTMANAGER_URL/api/v2/silences \
  -H 'Content-Type: application/json' \
  -d '{"matchers":[{"name":"alertname","value":"ALERT_NAME","isRegex":false}],"startsAt":"'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'","endsAt":"'$(date -u -d "+1 hour" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+1H +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")'","comment":"Silence reason"}'
```

---

## Common Issues

**Alertmanager not responding:**
- Check process running
- Check port 9093 accessible
- Review logs: `docker logs alertmanager` or `journalctl -u alertmanager`

**Alerts not routing:**
- Verify route matching in `alertmanager.yml`
- Check alert labels match route conditions

**Notifications not received:**
- Verify receiver webhook URLs/keys configured
- Check network connectivity

**Runbook URLs broken:**
- Verify docs URL correct (not placeholder)
- Check URL accessible
- Verify anchor links work

---

## Emergency Contacts

**On-Call Lead:** @oncall-lead

**Escalation:** [Add your escalation contact]

**Slack Channel:** #oncall-alerts

**Runbook:** <YOUR_DOCS_HOST>/docs/security/ALERT_RUNBOOK.md

---

**Print Date:** _______________

**Alertmanager URL:** _______________

**Docs Host:** _______________

---

*For full details, see: <YOUR_DOCS_HOST>/docs/security/ON_CALL_VALIDATION_CHECKLIST.md*

