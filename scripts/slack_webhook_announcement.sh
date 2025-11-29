#!/bin/bash
# Post Alertmanager On-Call Checklist announcement to Slack
# Usage: ./slack_webhook_announcement.sh <SLACK_WEBHOOK_URL> [ALERTMANAGER_URL] [DOCS_HOST]

set -e

SLACK_WEBHOOK_URL="${1:-${SLACK_WEBHOOK_URL}}"
ALERTMANAGER_URL="${2:-${ALERTMANAGER_URL:-http://localhost:9093}}"
DOCS_HOST="${3:-${DOCS_HOST:-https://your-docs-site.com}}"

if [ -z "$SLACK_WEBHOOK_URL" ]; then
    echo "Usage: $0 <SLACK_WEBHOOK_URL> [ALERTMANAGER_URL] [DOCS_HOST]"
    echo "Or set environment variables: SLACK_WEBHOOK_URL, ALERTMANAGER_URL, DOCS_HOST"
    exit 1
fi

# Generate the Slack message payload
PAYLOAD=$(cat <<EOF
{
  "text": "🚨 *New: On-Call Alertmanager Validation Checklist*",
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "🚨 New: On-Call Alertmanager Validation Checklist"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "Quick 2‑min pre-shift checks to verify Alertmanager is working:"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Health Check:*\n\`\`\`bash\ncurl ${ALERTMANAGER_URL}/-/healthy\n# expected: \"ok\"\n\`\`\`\n\n*Active Alerts Count:*\n\`\`\`bash\ncurl ${ALERTMANAGER_URL}/api/v1/alerts | jq '.data.alerts | length'\n\`\`\`"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Resources:*\n• 📋 <${DOCS_HOST}/docs/security/ON_CALL_VALIDATION_CHECKLIST.md|Full Checklist>\n• ⚡ <${DOCS_HOST}/docs/security/ON_CALL_CHECKLIST_SUMMARY.md|Quick Reference>\n• 🧪 <${DOCS_HOST}/docs/security/ALERTMANAGER_TEST_PAYLOADS.md|Test Payloads & Scripts>"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "Please run these checks before your on-call shift starts. If you see failures, tag @oncall-lead and open an incident."
      }
    },
    {
      "type": "divider"
    },
    {
      "type": "context",
      "elements": [
        {
          "type": "mrkdwn",
          "text": "Alertmanager URL: \`${ALERTMANAGER_URL}\` | Docs: ${DOCS_HOST}"
        }
      ]
    }
  ]
}
EOF
)

# Post to Slack
echo "Posting announcement to Slack..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    "$SLACK_WEBHOOK_URL")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✓ Announcement posted successfully!"
    echo "Response: $BODY"
else
    echo "✗ Failed to post announcement (HTTP $HTTP_CODE)"
    echo "Response: $BODY"
    exit 1
fi

