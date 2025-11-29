#!/bin/bash
# Copy-paste ready curl commands for testing Alertmanager
# Safe, non-destructive test payloads

set -e

# Configuration - Update these for your environment
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"
ALERT_NAME="${1:-HighRateLimitViolations}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo "=== Alertmanager Test Payloads ==="
echo ""
echo "Alertmanager URL: $ALERTMANAGER_URL"
echo "Alert Name: $ALERT_NAME"
echo ""

# Function to generate payload
generate_payload() {
    local alert_name=$1
    local severity=$2
    local component=$3
    local extra_labels=$4
    local description=$5
    
    cat <<EOF
[
  {
    "labels": {
      "alertname": "$alert_name",
      "severity": "$severity",
      "component": "$component",
      "env": "staging",
      "service": "lesson-planner-api"$extra_labels
    },
    "annotations": {
      "summary": "Test: $alert_name",
      "description": "$description",
      "runbook_url": "https://your-docs-site.com/docs/security/ALERT_RUNBOOK.md#$(echo "$alert_name" | tr '[:upper:]' '[:lower:]' | sed 's/\([A-Z]\)/-\1/g' | sed 's/^-//')"
    },
    "startsAt": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "endsAt": "$(date -u -d "+5 minutes" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+5M +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")"
  }
]
EOF
}

# Test 1: High Rate Limit Violations
echo -e "${CYAN}=== Test 1: High Rate Limit Violations ===${NC}"
echo ""
PAYLOAD1=$(generate_payload \
    "HighRateLimitViolations" \
    "warning" \
    "rate_limiter" \
    ',
      "limit_name": "general"' \
    "Test: 15 requests blocked per second in last 5 minutes. Limit: general. Environment: staging."
)
echo "Payload:"
echo "$PAYLOAD1" | jq '.' 2>/dev/null || echo "$PAYLOAD1"
echo ""
echo "curl command:"
echo -e "${GREEN}curl -X POST $ALERTMANAGER_URL/api/v1/alerts \\${NC}"
echo -e "${GREEN}  -H 'Content-Type: application/json' \\${NC}"
echo -e "${GREEN}  -d '$PAYLOAD1'${NC}"
echo ""
read -p "Press Enter to send this alert, or Ctrl+C to skip..."
curl -X POST "$ALERTMANAGER_URL/api/v1/alerts" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD1"
echo ""
echo ""

# Test 2: Critical Rate Limit Violations
echo -e "${CYAN}=== Test 2: Critical Rate Limit Violations ===${NC}"
echo ""
PAYLOAD2=$(generate_payload \
    "CriticalRateLimitViolations" \
    "critical" \
    "rate_limiter" \
    ',
      "limit_name": "general"' \
    "Test: 60 requests blocked per second. This may indicate an attack. Limit: general. Environment: staging."
)
echo "curl command:"
echo -e "${GREEN}curl -X POST $ALERTMANAGER_URL/api/v1/alerts \\${NC}"
echo -e "${GREEN}  -H 'Content-Type: application/json' \\${NC}"
echo -e "${GREEN}  -d '$PAYLOAD2'${NC}"
echo ""
read -p "Press Enter to send this alert, or Ctrl+C to skip..."
curl -X POST "$ALERTMANAGER_URL/api/v1/alerts" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD2"
echo ""
echo ""

# Test 3: Redis Circuit Breaker Open
echo -e "${CYAN}=== Test 3: Redis Circuit Breaker Open ===${NC}"
echo ""
PAYLOAD3=$(generate_payload \
    "RedisCircuitBreakerOpen" \
    "critical" \
    "redis" \
    "" \
    "Test: Rate limiting may be degraded. Circuit breaker opened due to Redis connection failures. Environment: staging."
)
echo "curl command:"
echo -e "${GREEN}curl -X POST $ALERTMANAGER_URL/api/v1/alerts \\${NC}"
echo -e "${GREEN}  -H 'Content-Type: application/json' \\${NC}"
echo -e "${GREEN}  -d '$PAYLOAD3'${NC}"
echo ""
read -p "Press Enter to send this alert, or Ctrl+C to skip..."
curl -X POST "$ALERTMANAGER_URL/api/v1/alerts" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD3"
echo ""
echo ""

# Test 4: High Redis Failures
echo -e "${CYAN}=== Test 4: High Redis Failures ===${NC}"
echo ""
PAYLOAD4=$(generate_payload \
    "HighRedisFailures" \
    "warning" \
    "redis" \
    ',
      "error_type": "connection_timeout"' \
    "Test: 8 Redis failures per second in last 5 minutes. Error type: connection_timeout. Environment: staging."
)
echo "curl command:"
echo -e "${GREEN}curl -X POST $ALERTMANAGER_URL/api/v1/alerts \\${NC}"
echo -e "${GREEN}  -H 'Content-Type: application/json' \\${NC}"
echo -e "${GREEN}  -d '$PAYLOAD4'${NC}"
echo ""
read -p "Press Enter to send this alert, or Ctrl+C to skip..."
curl -X POST "$ALERTMANAGER_URL/api/v1/alerts" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD4"
echo ""
echo ""

# Summary
echo -e "${CYAN}=== Test Summary ===${NC}"
echo ""
echo "View active alerts:"
echo -e "${GREEN}curl $ALERTMANAGER_URL/api/v1/alerts | jq '.'${NC}"
echo ""
echo "View Alertmanager status:"
echo -e "${GREEN}curl $ALERTMANAGER_URL/api/v1/status | jq '.'${NC}"
echo ""
echo "Create silence (replace ALERT_NAME):"
echo -e "${GREEN}curl -X POST $ALERTMANAGER_URL/api/v2/silences \\${NC}"
echo -e "${GREEN}  -H 'Content-Type: application/json' \\${NC}"
echo -e "${GREEN}  -d '{\"matchers\":[{\"name\":\"alertname\",\"value\":\"ALERT_NAME\",\"isRegex\":false}],\"startsAt\":\"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"endsAt\":\"$(date -u -d "+1 hour" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+1H +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")\",\"comment\":\"Test silence\"}'${NC}"
echo ""

