# Team Announcement: On-Call Alertmanager Validation Checklist

Ready-to-send email/Slack message for distributing the on-call checklist to your team.

---

## Email Version

**Subject:** New On-Call Alertmanager Validation Checklist Available

**Body:**

Hi team,

We've added a new **On-Call Alertmanager Validation Checklist** to help verify Alertmanager is functioning correctly during incidents.

**What's included:**
- Pre-shift validation (2-minute health check)
- During-incident verification steps
- Post-incident checks
- Emergency test procedures
- Quick reference commands

**Quick start:**
1. **Pre-shift check** (run before your on-call shift):
   ```bash
   curl http://localhost:9093/-/healthy
   curl http://localhost:9093/api/v1/alerts | jq '.data.alerts | length'
   ```

2. **During incident:** Verify alerts are received and notifications work
3. **Post-incident:** Verify alerts resolve correctly

**Resources:**
- 📋 [On-Call Validation Checklist](docs/security/ON_CALL_VALIDATION_CHECKLIST.md) - Full guide
- ⚡ [Quick Reference](docs/security/ON_CALL_CHECKLIST_SUMMARY.md) - One-page summary
- 🧪 [Test Payloads](docs/security/ALERTMANAGER_TEST_PAYLOADS.md) - Copy-paste test commands
- 📚 [Complete Setup Guide](docs/security/ALERTMANAGER_COMPLETE_SETUP.md) - Full documentation

**Questions?** Check the [Alert Runbook](docs/security/ALERT_RUNBOOK.md) for detailed remediation steps, or reach out to the team.

Thanks!

---

## Slack Version (Short)

**Channel:** `#oncall` or `#alerts` or `#engineering`

**Message:**

🚨 **New: On-Call Alertmanager Validation Checklist**

Quick validation steps to verify Alertmanager is working during incidents:

**Pre-shift (2 min):**
```bash
curl http://localhost:9093/-/healthy
curl http://localhost:9093/api/v1/alerts | jq '.data.alerts | length'
```

**Resources:**
• 📋 [Full Checklist](docs/security/ON_CALL_VALIDATION_CHECKLIST.md)
• ⚡ [Quick Reference](docs/security/ON_CALL_CHECKLIST_SUMMARY.md)
• 🧪 [Test Commands](docs/security/ALERTMANAGER_TEST_PAYLOADS.md)

Run these checks before your on-call shift starts! Questions? Check the [Alert Runbook](docs/security/ALERT_RUNBOOK.md).

---

## Slack Version (Detailed)

**Channel:** `#engineering` or `#devops` or `#alerts`

**Message:**

📢 **Alertmanager On-Call Validation Checklist Now Available**

We've added a new validation checklist to help on-call engineers quickly verify Alertmanager is functioning correctly.

**What it covers:**
✅ Pre-shift health checks (2 minutes)
✅ During-incident verification
✅ Post-incident validation
✅ Emergency test procedures

**Quick start - Pre-shift check:**
```bash
# Health check
curl http://localhost:9093/-/healthy

# Active alerts count
curl http://localhost:9093/api/v1/alerts | jq '.data.alerts | length'
```

**Full resources:**
• 📋 [On-Call Validation Checklist](docs/security/ON_CALL_VALIDATION_CHECKLIST.md) - Complete guide with all steps
• ⚡ [Quick Reference Card](docs/security/ON_CALL_CHECKLIST_SUMMARY.md) - One-page summary for quick access
• 🧪 [Test Payloads](docs/security/ALERTMANAGER_TEST_PAYLOADS.md) - Copy-paste curl commands for testing
• 📚 [Complete Setup Guide](docs/security/ALERTMANAGER_COMPLETE_SETUP.md) - Full documentation index

**When to use:**
- Before starting your on-call shift
- When an alert fires (verify it's received)
- After resolving an incident (verify resolution)
- If you suspect Alertmanager isn't working (emergency test)

**Related:**
- [Alert Runbook](docs/security/ALERT_RUNBOOK.md) - Detailed remediation steps for each alert
- [Alert Runbook Quick Reference](docs/security/ALERT_RUNBOOK_QUICK_REFERENCE.md) - One-page runbook summary

Questions or feedback? Drop them in this thread or reach out to the team.

---

## Confluence/Notion Version

**Title:** On-Call Alertmanager Validation Checklist

**Content:**

# On-Call Alertmanager Validation Checklist

A quick validation checklist to verify Alertmanager is functioning correctly during incidents.

## Quick Links

- 📋 [Full Checklist](docs/security/ON_CALL_VALIDATION_CHECKLIST.md) - Complete validation guide
- ⚡ [Quick Reference](docs/security/ON_CALL_CHECKLIST_SUMMARY.md) - One-page summary
- 🧪 [Test Payloads](docs/security/ALERTMANAGER_TEST_PAYLOADS.md) - Copy-paste test commands
- 📚 [Complete Setup Guide](docs/security/ALERTMANAGER_COMPLETE_SETUP.md) - Full documentation

## Pre-Shift Check (2 minutes)

Run these commands before your on-call shift starts:

```bash
# Health check
curl http://localhost:9093/-/healthy

# Active alerts count
curl http://localhost:9093/api/v1/alerts | jq '.data.alerts | length'
```

**Expected results:**
- Health check returns HTTP 200
- Active alerts count is a number (may be 0)

## During Incident

When an alert fires:
1. Verify alert received in Alertmanager UI
2. Check notification received (Slack/PagerDuty/Email)
3. Verify runbook URL works
4. Follow remediation steps in [Alert Runbook](docs/security/ALERT_RUNBOOK.md)

## Post-Incident

After resolving an incident:
1. Verify alert resolved
2. Check resolution notification received
3. Silence test alerts if any

## Emergency Test

If you suspect Alertmanager isn't working:

```bash
curl -X POST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[{"labels":{"alertname":"TestAlert","severity":"warning"},"annotations":{"summary":"Test"},"startsAt":"'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}]'
```

Verify notification received within 30 seconds.

## Related Documentation

- [Alert Runbook](docs/security/ALERT_RUNBOOK.md) - Detailed remediation steps
- [Alert Runbook Quick Reference](docs/security/ALERT_RUNBOOK_QUICK_REFERENCE.md) - One-page reference
- [Alertmanager Validation Guide](docs/security/ALERTMANAGER_VALIDATION_TESTING.md) - Full validation procedures

---

## Teams/Microsoft Teams Version

**Title:** 🚨 New On-Call Alertmanager Validation Checklist

**Message:**

Hi team,

We've added a new **On-Call Alertmanager Validation Checklist** to help verify Alertmanager is working correctly during incidents.

**Quick pre-shift check (2 minutes):**
```bash
curl http://localhost:9093/-/healthy
curl http://localhost:9093/api/v1/alerts | jq '.data.alerts | length'
```

**Resources:**
• 📋 [Full Checklist](docs/security/ON_CALL_VALIDATION_CHECKLIST.md)
• ⚡ [Quick Reference](docs/security/ON_CALL_CHECKLIST_SUMMARY.md)
• 🧪 [Test Commands](docs/security/ALERTMANAGER_TEST_PAYLOADS.md)

Run these checks before your on-call shift! Questions? Check the [Alert Runbook](docs/security/ALERT_RUNBOOK.md).

---

## Usage Instructions

1. **Choose the format** that matches your team's communication style (Email, Slack, Teams, Confluence, etc.)
2. **Customize** the message with:
   - Your team's channel names
   - Your documentation base URL (if different)
   - Any team-specific instructions
3. **Send** to your on-call rotation or engineering team
4. **Follow up** with a quick demo in your next team meeting

## Customization Tips

- **Add your Alertmanager URL** if it's different from `http://localhost:9093`
- **Include your docs base URL** in the links if your docs are hosted elsewhere
- **Add team-specific channels** or contact information
- **Include a calendar reminder** for on-call engineers to run pre-shift checks
- **Link to your internal wiki** if you're copying the checklist there

