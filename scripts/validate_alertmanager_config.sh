#!/bin/bash
# Validate Alertmanager Configuration
# Checks that alertmanager.yml references templates and receivers correctly

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ALERTMANAGER_CONFIG="$PROJECT_ROOT/prometheus/alertmanager.yml"
ALERT_TEMPLATES="$PROJECT_ROOT/prometheus/alert_templates.tmpl"
ALERTS_FILE="$PROJECT_ROOT/prometheus/alerts.yml"

echo "=== Validating Alertmanager Configuration ==="
echo ""

# Check files exist
echo "1. Checking files exist..."
if [ ! -f "$ALERTMANAGER_CONFIG" ]; then
    echo "   ERROR: alertmanager.yml not found at $ALERTMANAGER_CONFIG"
    exit 1
fi
echo "   ✓ alertmanager.yml found"

if [ ! -f "$ALERT_TEMPLATES" ]; then
    echo "   ERROR: alert_templates.tmpl not found at $ALERT_TEMPLATES"
    exit 1
fi
echo "   ✓ alert_templates.tmpl found"

if [ ! -f "$ALERTS_FILE" ]; then
    echo "   ERROR: alerts.yml not found at $ALERTS_FILE"
    exit 1
fi
echo "   ✓ alerts.yml found"
echo ""

# Check templates section exists
echo "2. Checking templates configuration..."
if grep -q "^templates:" "$ALERTMANAGER_CONFIG"; then
    TEMPLATE_PATH=$(grep -A 1 "^templates:" "$ALERTMANAGER_CONFIG" | tail -1 | sed 's/^[[:space:]]*-[[:space:]]*//' | tr -d "'\"")
    echo "   ✓ Templates section found"
    echo "   Template path: $TEMPLATE_PATH"
    echo "   NOTE: Ensure this path matches your Alertmanager deployment"
else
    echo "   WARNING: No templates section found in alertmanager.yml"
    echo "   Templates are optional but recommended for runbook URLs"
fi
echo ""

# Check receivers are defined
echo "3. Checking receivers..."
RECEIVERS=$(grep -E "^- name:" "$ALERTMANAGER_CONFIG" | sed "s/^- name: //" | tr -d "'\"")
RECEIVER_COUNT=$(echo "$RECEIVERS" | wc -l)
echo "   Found $RECEIVER_COUNT receiver(s):"
echo "$RECEIVERS" | sed 's/^/     - /'
echo ""

# Check routes reference receivers
echo "4. Checking route references..."
MISSING_RECEIVERS=""
for receiver in $RECEIVERS; do
    if grep -q "receiver: '$receiver'" "$ALERTMANAGER_CONFIG" || grep -q "receiver: \"$receiver\"" "$ALERTMANAGER_CONFIG"; then
        echo "   ✓ Receiver '$receiver' is referenced in routes"
    else
        echo "   WARNING: Receiver '$receiver' is defined but not referenced in routes"
        MISSING_RECEIVERS="$MISSING_RECEIVERS $receiver"
    fi
done
echo ""

# Check for placeholder values
echo "5. Checking for placeholder values..."
PLACEHOLDERS_FOUND=0
if grep -q "YOUR_SLACK_WEBHOOK_URL\|YOUR_PAGERDUTY_SERVICE_KEY\|oncall@example.com\|your-docs-site.com" "$ALERTMANAGER_CONFIG"; then
    echo "   WARNING: Placeholder values found in alertmanager.yml:"
    grep -n "YOUR_SLACK_WEBHOOK_URL\|YOUR_PAGERDUTY_SERVICE_KEY\|oncall@example.com\|your-docs-site.com" "$ALERTMANAGER_CONFIG" | sed 's/^/     Line /'
    PLACEHOLDERS_FOUND=1
else
    echo "   ✓ No placeholder values found"
fi
echo ""

# Check alerts.yml for runbook_url annotations
echo "6. Checking alerts.yml for runbook_url annotations..."
ALERT_COUNT=$(grep -c "^- alert:" "$ALERTS_FILE" || echo "0")
RUNBOOK_COUNT=$(grep -c "runbook_url:" "$ALERTS_FILE" || echo "0")
echo "   Found $ALERT_COUNT alert(s)"
echo "   Found $RUNBOOK_COUNT runbook_url annotation(s)"
if [ "$ALERT_COUNT" -eq "$RUNBOOK_COUNT" ]; then
    echo "   ✓ All alerts have runbook_url annotations"
else
    echo "   WARNING: Alert count ($ALERT_COUNT) != runbook_url count ($RUNBOOK_COUNT)"
fi

if grep -q "your-docs-site.com" "$ALERTS_FILE"; then
    echo "   WARNING: Placeholder docs URL found in alerts.yml"
    echo "   Replace 'your-docs-site.com' with your actual documentation URL"
fi
echo ""

# Check template file for placeholder URLs
echo "7. Checking alert_templates.tmpl..."
if grep -q "your-docs-site.com" "$ALERT_TEMPLATES"; then
    echo "   WARNING: Placeholder docs URL found in alert_templates.tmpl"
    echo "   Replace 'your-docs-site.com' with your actual documentation URL"
else
    echo "   ✓ No placeholder URLs found in templates"
fi
echo ""

# Summary
echo "=== Validation Summary ==="
if [ "$PLACEHOLDERS_FOUND" -eq 1 ]; then
    echo "⚠️  Configuration has placeholder values that need to be replaced"
    echo "   See warnings above for details"
    exit 1
elif [ -n "$MISSING_RECEIVERS" ]; then
    echo "⚠️  Some receivers are not referenced in routes"
    echo "   Receivers: $MISSING_RECEIVERS"
    exit 1
else
    echo "✓ Configuration looks good!"
    echo ""
    echo "Next steps:"
    echo "1. Replace placeholder URLs/credentials if any warnings were shown"
    echo "2. Ensure template path matches your Alertmanager deployment"
    echo "3. Test configuration with: scripts/test_alertmanager_payload.sh"
    exit 0
fi

