# Email Announcement - Ready to Send

Copy-paste ready email for distributing the On-Call Alertmanager Validation Checklist.

**Replace placeholders before sending:**
- `ALERTMANAGER_URL` → Your Alertmanager URL (e.g., `http://localhost:9093` or `http://staging-alertmanager:9093`)
- `<YOUR_DOCS_HOST>` → Your documentation host (e.g., `https://github.com/yourorg/docs` or `https://docs.yourcompany.com`)
- `[Your Name / SRE]` → Your name and role

---

## Email Template

**To:** On-call rotation / Engineering team  
**Subject:** New — On-Call Alertmanager Validation Checklist  
**CC:** [Optional: Team leads, SRE team]

---

Hi team,

We've published an on-call validation checklist to make pre-shift Alertmanager checks fast and consistent. Please follow the quick steps below before starting your on-call shift (estimated time: 2 minutes).

**Pre-shift checks:**

*Health Check*
```bash
curl ALERTMANAGER_URL/-/healthy
# Expected: "ok"
```

*Active Alerts Count*
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

Thanks — please run these checks before your next on-call shift. Reply to this email if you need help or have questions.

Best,  
[Your Name / SRE]

---

## Quick Steps to Send

1. **Copy the email template above**
2. **Replace placeholders:**
   - `ALERTMANAGER_URL` → Your actual Alertmanager URL
   - `<YOUR_DOCS_HOST>` → Your documentation URL
   - `[Your Name / SRE]` → Your name/role
3. **Update recipient list** (To/CC fields)
4. **Send email**

## Email Configuration for Alertmanager

Since you're using email for alerts, ensure your `prometheus/alertmanager.yml` has email receivers configured:

```yaml
receivers:
  - name: 'oncall-critical'
    email_configs:
      - to: 'oncall@yourcompany.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'your-email@gmail.com'
        auth_password: 'your-app-password'
        headers:
          Subject: 'CRITICAL: {{ .GroupLabels.alertname }}'
        html: |
          <h2>Critical Alert: {{ .GroupLabels.alertname }}</h2>
          <p><strong>Severity:</strong> {{ .GroupLabels.severity }}</p>
          <p><strong>Environment:</strong> {{ .GroupLabels.env }}</p>
          <p><strong>Description:</strong> {{ .Annotations.description }}</p>
          <p><a href="{{ .Annotations.runbook_url }}">View Runbook</a></p>
```

See [Alertmanager Receivers Guide](ALERTMANAGER_RECEIVERS_GUIDE.md) for detailed email setup instructions.

## Note on Slack Features

The Slack webhook and templates are included for future use if you add Slack later. For now, email is the primary notification channel. You can ignore the Slack-related files:
- `scripts/slack_webhook_announcement.sh` (optional, future use)
- `docs/security/SLACK_WEBHOOK_PAYLOAD.json` (optional, future use)

All Slack references in documentation are optional and won't affect email functionality.

