# Email-Focused Quick Start

Since you're using **email** as your primary notification channel, here's the quickest way to get started.

## Send the Announcement Email

1. **Open:** `docs/security/EMAIL_ANNOUNCEMENT_READY.md`
2. **Copy** the email template
3. **Replace placeholders:**
   - `ALERTMANAGER_URL` → Your Alertmanager URL
   - `<YOUR_DOCS_HOST>` → Your docs URL
   - `[Your Name / SRE]` → Your name
4. **Send** to your on-call rotation

**That's it!** The email includes all the information your team needs.

## Configure Email in Alertmanager

Your `prometheus/alertmanager.yml` already has email receivers configured. Just update the email settings:

```yaml
receivers:
  - name: 'oncall-critical'
    email_configs:
      - to: 'oncall@yourcompany.com'  # ← Update this
        smarthost: 'smtp.gmail.com:587'  # ← Or your SMTP server
        auth_username: 'your-email@gmail.com'  # ← Update this
        auth_password: 'your-app-password'  # ← Update this
```

**For Gmail:**
- Use an [App Password](https://support.google.com/accounts/answer/185833) (not your regular password)
- SMTP: `smtp.gmail.com:587`
- Enable "Less secure app access" or use OAuth2

**For Office 365:**
- SMTP: `smtp.office365.com:587`
- Use your Office 365 credentials

**For other SMTP:**
- Update `smarthost` to your SMTP server
- Configure authentication as needed

See [Alertmanager Receivers Guide](ALERTMANAGER_RECEIVERS_GUIDE.md) for detailed email setup.

## Test Email Notifications

1. **Send a test alert:**
   ```bash
   curl -X POST http://localhost:9093/api/v1/alerts \
     -H 'Content-Type: application/json' \
     -d '[{"labels":{"alertname":"TestAlert","severity":"critical"},"annotations":{"summary":"Test email"},"startsAt":"'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"}]'
   ```

2. **Check your email inbox** - You should receive the alert within 30 seconds

3. **Verify:**
   - Email received
   - Runbook URL is present and clickable
   - Email formatting looks correct

## What About Slack?

The Slack features (webhook script, templates) are included for **future use** if you add Slack later. They're completely optional and won't affect email functionality. You can ignore:
- `scripts/slack_webhook_announcement.sh` (optional)
- `docs/security/SLACK_WEBHOOK_PAYLOAD.json` (optional)
- Slack sections in documentation (optional)

**Email is your primary notification channel** - everything else is optional.

## Quick Reference

**Send announcement:** `docs/security/EMAIL_ANNOUNCEMENT_READY.md`

**Configure email:** Update `prometheus/alertmanager.yml` email receivers

**Test alerts:** Use `scripts/test_alertmanager_payload.sh` or curl commands

**Full guide:** `docs/security/ALERTMANAGER_RECEIVERS_GUIDE.md`

## Next Steps

1. ✅ Send announcement email to your team
2. ✅ Configure email SMTP settings in `alertmanager.yml`
3. ✅ Test email notifications with a test alert
4. ✅ Verify team receives emails correctly
5. ✅ Optional: Print checklist for on-call binders (`docs/security/ON_CALL_CHECKLIST_PRINTABLE.md`)

That's all you need for email-based alerting!

