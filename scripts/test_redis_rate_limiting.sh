#!/bin/bash
# Test Redis rate limiting

set -e

API_URL="${API_URL:-http://localhost:8000}"
TEST_USER_ID="${TEST_USER_ID:-test-redis-user}"

echo "=== Testing Redis Rate Limiting ==="
echo "API URL: $API_URL"
echo "Test User ID: $TEST_USER_ID"
echo ""

# Test 1: Health check
echo "Test 1: Redis health check..."
REDIS_HEALTH=$(curl -s "$API_URL/api/health/redis")
echo "$REDIS_HEALTH" | python -m json.tool || echo "$REDIS_HEALTH"

# Test 2: Make requests until rate limited
echo ""
echo "Test 2: Rate limiting behavior..."
SUCCESS_COUNT=0
RATE_LIMITED=0

for i in {1..35}; do
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -H "X-Current-User-Id: $TEST_USER_ID" \
        "$API_URL/api/users/$TEST_USER_ID/slots")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
        ((SUCCESS_COUNT++))
    elif [ "$HTTP_CODE" = "429" ]; then
        ((RATE_LIMITED++))
        echo "Request $i: Rate limited (HTTP 429)"
        break
    fi
done

echo "Successful requests: $SUCCESS_COUNT"
echo "Rate limited: $RATE_LIMITED"

if [ $RATE_LIMITED -gt 0 ]; then
    echo "✓ Rate limiting working correctly"
else
    echo "✗ Rate limiting not working (no 429 responses)"
    exit 1
fi

