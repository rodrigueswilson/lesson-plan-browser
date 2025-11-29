#!/bin/bash
# Test Alertmanager Alert Payload
# Simulates an alert to validate routing and templates

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"
ALERT_NAME="${1:-HighRateLimitViolations}"
TIMESTAMP=$(date +%s)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== Testing Alertmanager Alert Payload ==="
echo ""
echo "Alertmanager URL: $ALERTMANAGER_URL"
echo "Alert Name: $ALERT_NAME"
echo ""

# Generate test payload based on alert name
case "$ALERT_NAME" in
    HighRateLimitViolations|CriticalRateLimitViolations)
        PAYLOAD=$(cat <<EOF
[
  {
    "labels": {
      "alertname": "$ALERT_NAME",
      "severity": "$(if [[ "$ALERT_NAME" == *Critical* ]]; then echo "critical"; else echo "warning"; fi)",
      "component": "rate_limiter",
      "limit_name": "general",
      "env": "staging",
      "service": "lesson-planner-api"
    },
    "annotations": {
      "summary": "Test: High rate of rate limit violations",
      "description": "Test alert: 15 requests blocked per second in last 5 minutes. Limit: general. Environment: staging. Service: lesson-planner-api",
      "runbook_url": "https://your-docs-site.com/docs/security/ALERT_RUNBOOK.md#$(echo "$ALERT_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/\([A-Z]\)/-\1/g' | sed 's/^-//')"
    },
    "startsAt": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "endsAt": "$(date -u -d "+5 minutes" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+5M +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")"
  }
]
EOF
)
        ;;
    RedisCircuitBreakerOpen|RedisCircuitBreakerOpenExtended)
        PAYLOAD=$(cat <<EOF
[
  {
    "labels": {
      "alertname": "$ALERT_NAME",
      "severity": "critical",
      "component": "redis",
      "env": "staging",
      "service": "lesson-planner-api"
    },
    "annotations": {
      "summary": "Test: Redis circuit breaker is open",
      "description": "Test alert: Rate limiting may be degraded. Circuit breaker opened due to Redis connection failures. Environment: staging. Service: lesson-planner-api",
      "runbook_url": "https://your-docs-site.com/docs/security/ALERT_RUNBOOK.md#$(echo "$ALERT_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/\([A-Z]\)/-\1/g' | sed 's/^-//')"
    },
    "startsAt": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "endsAt": "$(date -u -d "+5 minutes" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+5M +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")"
  }
]
EOF
)
        ;;
    HighRedisFailures|CriticalRedisFailures)
        PAYLOAD=$(cat <<EOF
[
  {
    "labels": {
      "alertname": "$ALERT_NAME",
      "severity": "$(if [[ "$ALERT_NAME" == *Critical* ]]; then echo "critical"; else echo "warning"; fi)",
      "component": "redis",
      "error_type": "connection_timeout",
      "env": "staging",
      "service": "lesson-planner-api"
    },
    "annotations": {
      "summary": "Test: High rate of Redis connection failures",
      "description": "Test alert: 8 Redis failures per second in last 5 minutes. Error type: connection_timeout. Environment: staging. Service: lesson-planner-api",
      "runbook_url": "https://your-docs-site.com/docs/security/ALERT_RUNBOOK.md#$(echo "$ALERT_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/\([A-Z]\)/-\1/g' | sed 's/^-//')"
    },
    "startsAt": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "endsAt": "$(date -u -d "+5 minutes" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+5M +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")"
  }
]
EOF
)
        ;;
    *)
        echo -e "${YELLOW}Unknown alert name: $ALERT_NAME${NC}"
        echo "Using generic payload..."
        PAYLOAD=$(cat <<EOF
[
  {
    "labels": {
      "alertname": "$ALERT_NAME",
      "severity": "warning",
      "component": "rate_limiter",
      "env": "staging",
      "service": "lesson-planner-api"
    },
    "annotations": {
      "summary": "Test alert: $ALERT_NAME",
      "description": "This is a test alert payload",
      "runbook_url": "https://your-docs-site.com/docs/security/ALERT_RUNBOOK.md"
    },
    "startsAt": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "endsAt": "$(date -u -d "+5 minutes" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+5M +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")"
  }
]
EOF
)
        ;;
esac

echo "Generated payload:"
echo "$PAYLOAD" | jq '.' 2>/dev/null || echo "$PAYLOAD"
echo ""

# Check if Alertmanager is reachable
echo "Checking Alertmanager connectivity..."
if curl -s -f "$ALERTMANAGER_URL/-/healthy" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Alertmanager is reachable${NC}"
else
    echo -e "${RED}✗ Alertmanager is not reachable at $ALERTMANAGER_URL${NC}"
    echo "  Set ALERTMANAGER_URL environment variable if using a different URL"
    echo "  Example: ALERTMANAGER_URL=http://alertmanager:9093 $0"
    exit 1
fi
echo ""

# Send alert
echo "Sending test alert..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    "$ALERTMANAGER_URL/api/v1/alerts" 2>&1)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Alert sent successfully (HTTP $HTTP_CODE)${NC}"
    echo ""
    echo "Response:"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
    echo ""
    echo "Next steps:"
    echo "1. Check your notification channels (Slack, PagerDuty, Email) for the alert"
    echo "2. Verify runbook URLs are present and correct"
    echo "3. Verify routing matches expected receiver"
    echo ""
    echo "To view active alerts:"
    echo "  curl $ALERTMANAGER_URL/api/v1/alerts"
    echo ""
    echo "To silence this test alert:"
    echo "  curl -X POST $ALERTMANAGER_URL/api/v2/silences -H 'Content-Type: application/json' -d '{\"matchers\":[{\"name\":\"alertname\",\"value\":\"$ALERT_NAME\",\"isRegex\":false}],\"startsAt\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"endsAt\":\"$(date -u -d "+1 minute" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+1M +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"comment\":\"Test alert silence\"}'"
else
    echo -e "${RED}✗ Failed to send alert (HTTP $HTTP_CODE)${NC}"
    echo ""
    echo "Response:"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
    exit 1
fi

