#!/bin/bash
# Manual Staging Alert Validation
# Step-by-step guide for manually testing alerts

set -e

API_URL="${API_URL:-http://localhost:8000}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
TEST_USER_ID="${TEST_USER_ID:-staging-test-user}"

echo "=========================================="
echo "Manual Alert Validation Guide"
echo "=========================================="
echo ""
echo "This script guides you through manual alert testing."
echo "Follow each step and verify the expected behavior."
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test 1: High Rate Limit Violations
echo -e "${BLUE}=== Test 1: High Rate Limit Violations ===${NC}"
echo ""
echo "Step 1: Generate traffic to trigger rate limit"
echo "Command:"
echo "  for i in {1..100}; do"
echo "    curl -H \"X-Current-User-Id: $TEST_USER_ID\" \\"
echo "         $API_URL/api/users/$TEST_USER_ID/slots"
echo "  done"
echo ""
read -p "Press Enter after running the command above..."
echo ""

echo "Step 2: Wait 5 minutes for alert to fire"
echo "Check Prometheus: $PROMETHEUS_URL/api/v1/alerts"
echo ""
read -p "Press Enter after waiting and checking alerts..."
echo ""

echo "Step 3: Verify alert fired"
echo "Expected: HighRateLimitViolations alert in 'firing' state"
ALERT_STATE=$(curl -s "$PROMETHEUS_URL/api/v1/alerts" | \
    jq -r '.data.alerts[] | select(.labels.alertname=="HighRateLimitViolations") | .state' | head -1)

if [ "$ALERT_STATE" = "firing" ]; then
    echo -e "${GREEN}✓ Alert fired successfully${NC}"
else
    echo -e "${YELLOW}⚠ Alert state: $ALERT_STATE (expected: firing)${NC}"
fi
echo ""

# Test 2: Redis Circuit Breaker
echo -e "${BLUE}=== Test 2: Redis Circuit Breaker ===${NC}"
echo ""
echo "Step 1: Check current Redis status"
echo "Command: curl $API_URL/api/health/redis | jq ."
echo ""
read -p "Press Enter to check Redis status..."
REDIS_STATUS=$(curl -s "$API_URL/api/health/redis" | jq -r '.status')
echo "Redis Status: $REDIS_STATUS"
echo ""

if [ "$REDIS_STATUS" = "not_configured" ]; then
    echo -e "${YELLOW}Redis not configured - skipping circuit breaker test${NC}"
else
    echo "Step 2: Stop Redis to trigger circuit breaker"
    echo "Command: redis-cli SHUTDOWN"
    echo "  or: docker stop redis-container"
    echo ""
    read -p "Press Enter after stopping Redis..."
    echo ""
    
    echo "Step 3: Wait for circuit breaker to open (up to 60 seconds)"
    echo "Monitor: curl $API_URL/api/health/redis | jq .circuit_breaker"
    echo ""
    read -p "Press Enter after circuit breaker opens..."
    echo ""
    
    echo "Step 4: Verify alert fired"
    echo "Expected: RedisCircuitBreakerOpen alert in 'firing' state"
    ALERT_STATE=$(curl -s "$PROMETHEUS_URL/api/v1/alerts" | \
        jq -r '.data.alerts[] | select(.labels.alertname=="RedisCircuitBreakerOpen") | .state' | head -1)
    
    if [ "$ALERT_STATE" = "firing" ]; then
        echo -e "${GREEN}✓ Circuit breaker alert fired${NC}"
    else
        echo -e "${YELLOW}⚠ Alert state: $ALERT_STATE${NC}"
    fi
    echo ""
    
    echo "Step 5: Restart Redis"
    echo "Command: redis-server"
    echo "  or: docker start redis-container"
    echo ""
    read -p "Press Enter after restarting Redis..."
    echo ""
    
    echo "Step 6: Wait for circuit breaker to close (up to 60 seconds)"
    echo "Monitor: curl $API_URL/api/health/redis | jq .circuit_breaker.circuit_open"
    echo ""
    read -p "Press Enter after circuit breaker closes..."
    echo ""
    
    CIRCUIT_OPEN=$(curl -s "$API_URL/api/health/redis" | jq -r '.circuit_breaker.circuit_open')
    if [ "$CIRCUIT_OPEN" = "false" ]; then
        echo -e "${GREEN}✓ Circuit breaker closed successfully${NC}"
    else
        echo -e "${YELLOW}⚠ Circuit breaker still open${NC}"
    fi
fi
echo ""

# Test 3: Rate Limit Block Ratio
echo -e "${BLUE}=== Test 3: Rate Limit Block Ratio ===${NC}"
echo ""
echo "Step 1: Generate sustained traffic"
echo "Command:"
echo "  for i in {1..200}; do"
echo "    curl -H \"X-Current-User-Id: $TEST_USER_ID\" \\"
echo "         $API_URL/api/users/$TEST_USER_ID/slots"
echo "    sleep 0.1"
echo "  done"
echo ""
read -p "Press Enter after generating traffic..."
echo ""

echo "Step 2: Check block ratio"
echo "Query Prometheus:"
echo "  sum(rate(limiter_blocked_total[5m])) /"
echo "  sum(rate(limiter_allowed_total[5m]) + rate(limiter_blocked_total[5m]))"
echo ""
read -p "Press Enter to check block ratio..."
BLOCK_RATIO=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=sum(rate(limiter_blocked_total[5m]))%20/%20sum(rate(limiter_allowed_total[5m])%20+%20rate(limiter_blocked_total[5m]))" | \
    jq -r '.data.result[0].value[1]' | sed 's/"//g')
echo "Block Ratio: $BLOCK_RATIO"
echo ""

# Test 4: Verify Runbook Steps
echo -e "${BLUE}=== Test 4: Runbook Validation ===${NC}"
echo ""
echo "For each alert that fired, verify:"
echo "1. Alert appears in runbook: docs/security/ALERT_RUNBOOK.md"
echo "2. Symptoms match observed behavior"
echo "3. Immediate actions are clear"
echo "4. Remediation steps are actionable"
echo "5. Verification steps work"
echo ""
read -p "Press Enter after reviewing runbook..."
echo ""

# Summary
echo "=========================================="
echo "Manual Test Summary"
echo "=========================================="
echo ""
echo "Tests completed:"
echo "1. High Rate Limit Violations"
echo "2. Redis Circuit Breaker"
echo "3. Rate Limit Block Ratio"
echo "4. Runbook Validation"
echo ""
echo "Next steps:"
echo "1. Document any gaps found"
echo "2. Update runbook if needed"
echo "3. Test alert notifications"
echo "4. Schedule regular runbook reviews"
echo ""

