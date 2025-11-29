#!/bin/bash
# Staging Alert Validation Script
# Safely triggers alerts in staging to validate runbook procedures

set -e

API_URL="${API_URL:-http://localhost:8000}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
TEST_USER_ID="${TEST_USER_ID:-staging-test-user}"
ALERT_WAIT_TIME="${ALERT_WAIT_TIME:-90}"  # Wait 90 seconds for alerts to fire

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Staging Alert Validation Test"
echo "=========================================="
echo "API URL: $API_URL"
echo "Prometheus URL: $PROMETHEUS_URL"
echo "Test User ID: $TEST_USER_ID"
echo ""

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to check alert
check_alert() {
    local alert_name=$1
    local expected_state=${2:-"firing"}
    
    echo -n "Checking alert '$alert_name'... "
    
    local result=$(curl -s "$PROMETHEUS_URL/api/v1/alerts" | \
        jq -r ".data.alerts[] | select(.labels.alertname==\"$alert_name\") | .state" | head -1)
    
    if [ "$result" = "$expected_state" ]; then
        echo -e "${GREEN}PASS${NC} (state: $result)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}FAIL${NC} (expected: $expected_state, got: $result)"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to check metric value
check_metric() {
    local metric_query=$1
    local threshold=$2
    local comparison=${3:-">"}
    
    local value=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$metric_query" | \
        jq -r '.data.result[0].value[1]' | sed 's/"//g')
    
    if [ -z "$value" ] || [ "$value" = "null" ]; then
        echo "Metric not found or no data"
        return 1
    fi
    
    # Compare using bc for floating point
    if (( $(echo "$value $comparison $threshold" | bc -l) )); then
        return 0
    else
        return 1
    fi
}

# Function to wait for alert
wait_for_alert() {
    local alert_name=$1
    local max_wait=${2:-60}
    local wait_time=0
    
    echo "Waiting for alert '$alert_name' to fire (max ${max_wait}s)..."
    
    while [ $wait_time -lt $max_wait ]; do
        if check_alert "$alert_name" "firing" > /dev/null 2>&1; then
            echo -e "${GREEN}Alert fired after ${wait_time}s${NC}"
            return 0
        fi
        sleep 5
        wait_time=$((wait_time + 5))
        echo -n "."
    done
    
    echo -e "${RED}Alert did not fire within ${max_wait}s${NC}"
    return 1
}

# Function to generate traffic
generate_traffic() {
    local endpoint=$1
    local count=$2
    local user_id=${3:-$TEST_USER_ID}
    
    echo "Generating $count requests to $endpoint..."
    
    for i in $(seq 1 $count); do
        curl -s -w "\n%{http_code}" \
            -H "X-Current-User-Id: $user_id" \
            "$API_URL$endpoint" > /dev/null 2>&1 || true
        sleep 0.1  # Small delay to avoid overwhelming
    done
    
    echo "Traffic generation complete"
}

# Test 1: High Rate Limit Violations
echo ""
echo -e "${BLUE}=== Test 1: High Rate Limit Violations ===${NC}"
echo "Generating traffic to trigger rate limit violations..."

# Generate enough traffic to trigger alert (>10 req/s for 5 minutes)
# Note: This is a simplified test - in real scenario, need sustained traffic
generate_traffic "/api/users/$TEST_USER_ID/slots" 50 "$TEST_USER_ID"

echo "Waiting for alert to fire..."
sleep $ALERT_WAIT_TIME

if check_alert "HighRateLimitViolations" "firing"; then
    echo -e "${GREEN}✓ HighRateLimitViolations alert triggered${NC}"
else
    echo -e "${YELLOW}⚠ Alert may not have fired (check Prometheus)${NC}"
fi

# Test 2: Check Rate Limit Metrics
echo ""
echo -e "${BLUE}=== Test 2: Rate Limit Metrics ===${NC}"
echo "Checking rate limit metrics..."

BLOCKED_RATE=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=sum(rate(limiter_blocked_total[5m]))" | \
    jq -r '.data.result[0].value[1]' | sed 's/"//g')

ALLOWED_RATE=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=sum(rate(limiter_allowed_total[5m]))" | \
    jq -r '.data.result[0].value[1]' | sed 's/"//g')

echo "Blocked rate: $BLOCKED_RATE req/s"
echo "Allowed rate: $ALLOWED_RATE req/s"

if [ -n "$BLOCKED_RATE" ] && [ "$BLOCKED_RATE" != "null" ] && (( $(echo "$BLOCKED_RATE > 0" | bc -l) )); then
    echo -e "${GREEN}✓ Rate limit metrics working${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ No blocked requests detected (may be normal)${NC}"
fi

# Test 3: Redis Health Check
echo ""
echo -e "${BLUE}=== Test 3: Redis Health Check ===${NC}"
echo "Checking Redis health endpoint..."

REDIS_HEALTH=$(curl -s "$API_URL/api/health/redis")
REDIS_STATUS=$(echo "$REDIS_HEALTH" | jq -r '.status')
CIRCUIT_OPEN=$(echo "$REDIS_HEALTH" | jq -r '.circuit_breaker.circuit_open // false')

echo "Redis Status: $REDIS_STATUS"
echo "Circuit Open: $CIRCUIT_OPEN"

if [ "$REDIS_STATUS" = "healthy" ] || [ "$REDIS_STATUS" = "not_configured" ]; then
    echo -e "${GREEN}✓ Redis health endpoint working${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Redis health check failed${NC}"
    ((TESTS_FAILED++))
fi

# Test 4: Simulate Redis Failure (if Redis configured)
if [ -n "$REDIS_URL" ] && [ "$REDIS_STATUS" != "not_configured" ]; then
    echo ""
    echo -e "${BLUE}=== Test 4: Redis Circuit Breaker (Simulated) ===${NC}"
    echo -e "${YELLOW}Note: This test requires manual Redis stop/start${NC}"
    echo ""
    echo "To test circuit breaker:"
    echo "1. Stop Redis: redis-cli SHUTDOWN"
    echo "2. Wait for circuit breaker to open (check health endpoint)"
    echo "3. Verify alert fires: RedisCircuitBreakerOpen"
    echo "4. Restart Redis: redis-server"
    echo "5. Verify circuit breaker closes"
    echo ""
    echo "Skipping automated test (requires manual intervention)"
else
    echo ""
    echo -e "${YELLOW}=== Test 4: Redis Circuit Breaker ===${NC}"
    echo "Redis not configured - skipping circuit breaker test"
fi

# Test 5: Metrics Endpoint
echo ""
echo -e "${BLUE}=== Test 5: Metrics Endpoint ===${NC}"
echo "Checking /metrics endpoint..."

METRICS_RESPONSE=$(curl -s "$API_URL/metrics")
if echo "$METRICS_RESPONSE" | grep -q "limiter_allowed_total"; then
    echo -e "${GREEN}✓ Metrics endpoint working${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Metrics endpoint not working${NC}"
    ((TESTS_FAILED++))
fi

# Test 6: Verify Alert Rules Loaded
echo ""
echo -e "${BLUE}=== Test 6: Alert Rules Verification ===${NC}"
echo "Checking if alert rules are loaded in Prometheus..."

RULES=$(curl -s "$PROMETHEUS_URL/api/v1/rules" | jq -r '.data.groups[].rules[].name' | grep -i "rate\|redis" | wc -l)

if [ "$RULES" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $RULES rate limiter/Redis alert rules${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ No alert rules found (may not be configured)${NC}"
fi

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All automated tests passed${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Manually test Redis circuit breaker (if Redis configured)"
    echo "2. Review runbook procedures"
    echo "3. Validate alert notifications"
    exit 0
else
    echo -e "${YELLOW}⚠ Some tests failed - review output above${NC}"
    exit 1
fi

