# Announcement Delivery Guide

Complete guide for delivering the On-Call Alertmanager Validation Checklist announcement to your team.

## Quick Options

### Option 1: Email (Recommended - Primary Method)

**Quick start:**
1. Open `docs/security/EMAIL_ANNOUNCEMENT_READY.md`
2. Copy the email template
3. Replace placeholders (`ALERTMANAGER_URL`, `<YOUR_DOCS_HOST>`, `[Your Name]`)
4. Send to your on-call rotation or engineering team

**See:** [Email Announcement Ready](EMAIL_ANNOUNCEMENT_READY.md) for copy-paste template

### Option 2: Slack Webhook (Optional - Future Use)

**Use the script:**
```bash
# Set your values
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
export ALERTMANAGER_URL="http://localhost:9093"
export DOCS_HOST="https://your-docs-site.com"

# Post announcement
./scripts/slack_webhook_announcement.sh
```

**Or use curl directly:**
```bash
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H 'Content-Type: application/json' \
  -d @docs/security/SLACK_WEBHOOK_PAYLOAD.json
```

**Note:** Remember to replace placeholders in the JSON payload first!

### Option 3: Manual Copy-Paste

1. Open `docs/security/TEAM_ANNOUNCEMENT_SHORT.md`
2. Replace placeholders:
   - `ALERTMANAGER_URL` → Your Alertmanager URL
   - `<YOUR_DOCS_HOST>` → Your docs host
3. Copy the appropriate format (Slack/Email/Teams)
4. Paste and send

### Option 4: Printable Checklist

1. Open `docs/security/ON_CALL_CHECKLIST_PRINTABLE.md`
2. Replace placeholders
3. Print and distribute to on-call team
4. Or convert to PDF and share

## Step-by-Step: Email (Primary Method)

### 1. Open Email Template

Open `docs/security/EMAIL_ANNOUNCEMENT_READY.md` and copy the email template.

### 2. Replace Placeholders

- `ALERTMANAGER_URL` → Your Alertmanager URL (e.g., `http://localhost:9093`)
- `<YOUR_DOCS_HOST>` → Your documentation host
- `[Your Name / SRE]` → Your name and role

### 3. Update Recipients

- **To:** On-call rotation or engineering team
- **CC:** Optional: Team leads, SRE team

### 4. Send Email

Send the email and optionally follow up with a calendar reminder.

---

## Step-by-Step: Slack Webhook (Optional - Future Use)

### 1. Get Slack Webhook URL

1. Go to https://api.slack.com/apps
2. Create a new app or select existing app
3. Go to "Incoming Webhooks"
4. Activate Incoming Webhooks
5. Click "Add New Webhook to Workspace"
6. Select channel (e.g., `#oncall` or `#engineering`)
7. Copy webhook URL

### 2. Update Script with Your Values

Edit `scripts/slack_webhook_announcement.sh` or set environment variables:

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
export ALERTMANAGER_URL="http://staging-alertmanager:9093"
export DOCS_HOST="https://github.com/yourorg/docs"
```

### 3. Run the Script

```bash
chmod +x scripts/slack_webhook_announcement.sh
./scripts/slack_webhook_announcement.sh
```

### 4. Verify Post

Check your Slack channel - the announcement should appear with formatted blocks.

## Step-by-Step: Manual Slack Post

### 1. Prepare Message

Copy from `docs/security/TEAM_ANNOUNCEMENT_SHORT.md` (Slack section)

### 2. Replace Placeholders

- `ALERTMANAGER_URL` → `http://localhost:9093` (or your URL)
- `<YOUR_DOCS_HOST>` → `https://github.com/yourorg/docs` (or your docs)

### 3. Post to Slack

Paste in your channel (e.g., `#oncall` or `#engineering`)

### 4. Pin Message (Optional)

Right-click message → Pin to channel (keeps it visible)

## Step-by-Step: Email

### 1. Prepare Email

Copy from `docs/security/TEAM_ANNOUNCEMENT_SHORT.md` (Email section)

### 2. Replace Placeholders

- `ALERTMANAGER_URL` → Your Alertmanager URL
- `<YOUR_DOCS_HOST>` → Your docs host
- `[Your Name / SRE]` → Your name/role

### 3. Send Email

- **To:** On-call rotation or engineering team
- **Subject:** New — On-Call Alertmanager Validation Checklist
- **Body:** Paste prepared message

### 4. Follow Up

Consider a calendar reminder or Slack message to reinforce

## Step-by-Step: Printable Checklist

### 1. Open Printable Version

Open `docs/security/ON_CALL_CHECKLIST_PRINTABLE.md`

### 2. Replace Placeholders

- `ALERTMANAGER_URL` → Your Alertmanager URL
- `<YOUR_DOCS_HOST>` → Your docs host
- Add emergency contacts

### 3. Print or Convert to PDF

**Print:**
- Open in markdown viewer or convert to HTML
- Print to PDF or paper
- Distribute to on-call team

**Convert to PDF:**
```bash
# Using pandoc (if installed)
pandoc docs/security/ON_CALL_CHECKLIST_PRINTABLE.md -o oncall-checklist.pdf

# Or use online converter
# Upload markdown to https://www.markdowntopdf.com/
```

### 4. Distribute

- Email PDF to on-call rotation
- Post PDF in shared drive/wiki
- Include in on-call runbook binder

## Customization Checklist

Before sending, update:

- [ ] `ALERTMANAGER_URL` - Your Alertmanager URL (staging/prod)
- [ ] `<YOUR_DOCS_HOST>` - Your documentation host
- [ ] Channel names - Your Slack/Teams channels
- [ ] Team mentions - `@oncall-lead`, `#sre-oncall`, etc.
- [ ] Emergency contacts - Add escalation contacts
- [ ] Alertmanager URL in scripts - Update if different

## Testing

**Test Slack webhook:**
```bash
# Test with a simple message first
curl -X POST YOUR_SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test message"}'
```

**Test announcement script:**
```bash
# Use a test channel first
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/TEST/WEBHOOK"
./scripts/slack_webhook_announcement.sh
```

## Scheduling (Optional)

**Using cron (Linux/Mac):**
```bash
# Post announcement every Monday at 9 AM
0 9 * * 1 /path/to/scripts/slack_webhook_announcement.sh
```

**Using GitHub Actions:**
Create `.github/workflows/oncall-announcement.yml`:
```yaml
name: On-Call Announcement
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
  workflow_dispatch:

jobs:
  announce:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Post announcement
        run: |
          export SLACK_WEBHOOK_URL="${{ secrets.SLACK_WEBHOOK_URL }}"
          export ALERTMANAGER_URL="${{ secrets.ALERTMANAGER_URL }}"
          export DOCS_HOST="${{ secrets.DOCS_HOST }}"
          ./scripts/slack_webhook_announcement.sh
```

## Files Reference

- `docs/security/TEAM_ANNOUNCEMENT_SHORT.md` - Copy-paste templates
- `docs/security/ON_CALL_CHECKLIST_PRINTABLE.md` - Printable checklist
- `scripts/slack_webhook_announcement.sh` - Automated Slack posting
- `docs/security/SLACK_WEBHOOK_PAYLOAD.json` - Raw Slack payload

## See Also

- [On-Call Validation Checklist](ON_CALL_VALIDATION_CHECKLIST.md) - Full guide
- [On-Call Checklist Summary](ON_CALL_CHECKLIST_SUMMARY.md) - Quick reference
- [Alertmanager Test Payloads](ALERTMANAGER_TEST_PAYLOADS.md) - Test commands

