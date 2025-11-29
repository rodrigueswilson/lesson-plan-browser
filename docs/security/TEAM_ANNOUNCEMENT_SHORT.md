# Quick Team Announcement (Copy-Paste Ready)

**Replace placeholders before sending:**
- `ALERTMANAGER_URL` → Your Alertmanager URL (e.g., `http://localhost:9093` or `http://staging-alertmanager:9093`)
- `<YOUR_DOCS_HOST>` → Your documentation host (e.g., `https://github.com/yourorg/docs` or `https://docs.yourcompany.com`)

---

## Slack (Short)

```
🚨 *New: On-Call Alertmanager Validation Checklist*

Quick 2‑min pre-shift checks:

```bash
curl ALERTMANAGER_URL/-/healthy
curl ALERTMANAGER_URL/api/v1/alerts | jq '.data.alerts | length'
```

📋 Full checklist: <YOUR_DOCS_HOST>/docs/security/ON_CALL_VALIDATION_CHECKLIST.md
⚡ Quick ref: <YOUR_DOCS_HOST>/docs/security/ON_CALL_CHECKLIST_SUMMARY.md
🧪 Tests: <YOUR_DOCS_HOST>/docs/security/ALERTMANAGER_TEST_PAYLOADS.md

Please run these before your on-call shift. Thank you!
```

---

## Slack (Detailed)

```
:rotating_light: *New: On-Call — Alertmanager Validation Checklist*

Team — we've published a short on-call checklist to validate Alertmanager before your shift. Please perform these quick checks (≈2 mins) before you start:

*Health*
```bash
curl ALERTMANAGER_URL/-/healthy
# expected: "ok"
```

*Active alerts count*
```bash
curl ALERTMANAGER_URL/api/v1/alerts | jq '.data.alerts | length'
```

If alerts are present, run a test notification (staging only):
```bash
export ALERTMANAGER_URL="ALERTMANAGER_URL"
./scripts/test_alertmanager_curl.sh
```

Confirm runbook links in notifications and escalate if routing or templates fail.

*Resources:*
• Full checklist: <YOUR_DOCS_HOST>/docs/security/ON_CALL_VALIDATION_CHECKLIST.md
• Quick ref: <YOUR_DOCS_HOST>/docs/security/ON_CALL_CHECKLIST_SUMMARY.md
• Test payloads & scripts: <YOUR_DOCS_HOST>/docs/security/ALERTMANAGER_TEST_PAYLOADS.md

If you see failures during pre-shift checks, tag @oncall-lead and open an incident with the outputs. Thanks!
```

---

## Email (Detailed)

**Subject:** New — On-Call Alertmanager Validation Checklist

**Body:**

Hi team,

We've published an on-call validation checklist to make pre-shift Alertmanager checks fast and consistent. Please follow the quick steps below before starting your on-call shift (estimated time: 2 minutes).

**Pre-shift checks:**

*Health*
```bash
curl ALERTMANAGER_URL/-/healthy
# -> Expect: "ok"
```

*Active alerts count*
```bash
curl ALERTMANAGER_URL/api/v1/alerts | jq '.data.alerts | length'
```

If you see alerts, run a staging test:
```bash
export ALERTMANAGER_URL="ALERTMANAGER_URL"
./scripts/test_alertmanager_curl.sh
```

Verify notifications contain the runbook_url and are routed to the correct channels.

**Useful links:**
• Full checklist: <YOUR_DOCS_HOST>/docs/security/ON_CALL_VALIDATION_CHECKLIST.md
• One-page quick ref: <YOUR_DOCS_HOST>/docs/security/ON_CALL_CHECKLIST_SUMMARY.md
• Test payloads & scripts: <YOUR_DOCS_HOST>/docs/security/ALERTMANAGER_TEST_PAYLOADS.md

**Action items for leads:**
• Ensure the Alertmanager URL is correct in the docs and scripts.
• Confirm the on-call rotation has the updated checklist.
• Add escalation contacts in the checklist if not already present.

Thanks — please run these checks before your next on-call shift. Reply to this email or DM me in Slack if you need help.

Best,
[Your Name / SRE]

---

## Confluence/Notion Blurb (Short)

```
New: On-Call Alertmanager Validation Checklist — run the 2‑minute pre-shift checks:

```bash
curl ALERTMANAGER_URL/-/healthy
curl ALERTMANAGER_URL/api/v1/alerts | jq '.data.alerts | length'
```

Full guide and scripts: <YOUR_DOCS_HOST>/docs/security/ON_CALL_VALIDATION_CHECKLIST.md
```

