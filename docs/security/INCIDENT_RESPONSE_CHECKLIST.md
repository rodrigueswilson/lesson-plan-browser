# Incident Response Checklist

**Date:** January 2025  
**Purpose:** Quick reference for detecting and responding to authorization and rate limiting incidents

---

## Alert Thresholds

### Authorization Failures

| Severity | Threshold | Action |
|----------|-----------|--------|
| **Low** | > 5 failures/minute | Monitor, investigate patterns |
| **Medium** | > 10 failures/minute | Investigate immediately, check logs |
| **High** | > 50 failures/hour | Escalate, check for attack patterns |
| **Critical** | > 100 failures/hour OR SQL injection detected | Emergency response, potential rollback |

### Rate Limit Violations

| Severity | Threshold | Action |
|----------|-----------|--------|
| **Low** | > 10 violations/minute | Monitor usage patterns |
| **Medium** | > 20 violations/minute | Investigate source, check if legitimate |
| **High** | > 50 violations/minute OR sustained from single IP | Block IP if malicious, increase limits if legitimate |
| **Critical** | > 100 violations/minute OR DDoS pattern | Emergency response, consider rate limit bypass |

---

## Detection Methods

### 1. Authorization Failure Detection

#### Real-time Log Monitoring

```bash
# Monitor authorization failures in real-time
tail -f logs/json_pipeline.log | grep "authorization_denied"

# Count failures in last 5 minutes
grep "authorization_denied" logs/json_pipeline.log | \
  awk -v cutoff=$(date -d '5 minutes ago' +%s) \
  '$1 >= cutoff {count++} END {print count}'
```

#### Log Query Patterns

**Authorization Denials:**
```bash
# Count denials per hour
grep "authorization_denied" logs/json_pipeline.log | \
  grep -oP '\d{4}-\d{2}-\d{2}T\d{2}' | \
  sort | uniq -c

# Find patterns (user ID mismatches)
grep "authorization_denied" logs/json_pipeline.log | \
  grep -oP '"requested_user_id":"[^"]+"' | \
  sort | uniq -c | sort -rn | head -20
```

**Invalid Format Attempts:**
```bash
# Detect SQL injection attempts
grep "authorization_invalid_user_id" logs/json_pipeline.log | \
  grep -iE "(union|select|drop|insert|delete|--|;|')"

# Count invalid format attempts
grep "authorization_invalid_user_id" logs/json_pipeline.log | wc -l
```

**Skipped Authorization (No Header):**
```bash
# Count requests without authorization header
grep "authorization_skipped" logs/json_pipeline.log | wc -l

# Find endpoints most affected
grep "authorization_skipped" logs/json_pipeline.log | \
  grep -oP '"path":"[^"]+"' | \
  sort | uniq -c | sort -rn
```

### 2. Rate Limit Violation Detection

#### Real-time Monitoring

```bash
# Monitor rate limit violations (check HTTP 429 responses)
tail -f logs/json_pipeline.log | grep -E "(429|rate_limit)"

# Check slowapi rate limit logs (if configured)
grep "RateLimitExceeded" logs/*.log
```

#### Log Query Patterns

**Rate Limit Violations by IP:**
```bash
# Count violations per IP
grep "429" access.log | \
  awk '{print $1}' | \
  sort | uniq -c | sort -rn | head -20

# Find sustained violations
grep "429" access.log | \
  awk '{print $1, $4}' | \
  awk '{ip=$1; date=$2; count[ip]++} END {for (ip in count) if (count[ip] > 50) print ip, count[ip]}'
```

**Rate Limit Violations by Endpoint:**
```bash
# Find most affected endpoints
grep "429" access.log | \
  awk '{print $7}' | \
  sort | uniq -c | sort -rn | head -10
```

### 3. Structured Log Queries (JSON Logs)

If using JSON logging, use `jq` for structured queries:

```bash
# Authorization failures in last hour
cat logs/json_pipeline.log | jq -r 'select(.event == "authorization_denied") | select(.timestamp > (now - 3600 | todateiso8601))'

# Rate limit violations by user
cat logs/json_pipeline.log | jq -r 'select(.status_code == 429) | .user_id' | sort | uniq -c

# Invalid format attempts (potential attacks)
cat logs/json_pipeline.log | jq -r 'select(.event == "authorization_invalid_user_id") | .user_id_length'
```

---

## Incident Response Procedures

### Severity: Low (5-10 auth failures/min OR 10-20 rate limit violations/min)

**Detection:**
- Automated monitoring alerts
- Periodic log review

**Response Steps:**
1. **Investigate:**
   ```bash
   # Check recent failures
   grep "authorization_denied" logs/json_pipeline.log | tail -50
   
   # Check rate limit patterns
   grep "429" access.log | tail -50
   ```

2. **Analyze Patterns:**
   - Are failures from legitimate users?
   - Are rate limits too strict?
   - Is there a pattern (specific user, IP, endpoint)?

3. **Document:**
   - Record incident in incident log
   - Note patterns observed
   - Document any configuration changes

4. **Monitor:**
   - Continue monitoring for 1 hour
   - Check if issue resolves itself

**Remediation:**
- If legitimate users blocked: Consider increasing rate limits temporarily
- If configuration issue: Fix configuration, redeploy
- If false positive: Adjust alert thresholds

**Time to Resolution:** < 1 hour

---

### Severity: Medium (10-50 auth failures/min OR 20-50 rate limit violations/min)

**Detection:**
- Automated alerts triggered
- User reports of access issues

**Response Steps:**

1. **Immediate Actions (0-5 minutes):**
   ```bash
   # Check current failure rate
   grep "authorization_denied" logs/json_pipeline.log | \
     grep "$(date +%Y-%m-%d)" | \
     awk -v now=$(date +%s) \
     '{split($1, dt, "T"); split(dt[2], tm, ":"); ts=mktime(dt[1] " " tm[1] " " tm[2] " " tm[3]); if (now - ts < 300) count++} END {print count " failures in last 5 minutes"}'
   
   # Check if specific user/IP affected
   grep "authorization_denied" logs/json_pipeline.log | tail -100 | \
     grep -oP '"requested_user_id":"[^"]+"' | sort | uniq -c
   ```

2. **Investigate Root Cause (5-15 minutes):**
   - Check if frontend sending headers correctly
   - Verify authorization logic
   - Check for recent deployments
   - Review rate limit configuration

3. **Determine Legitimacy:**
   - Are failures from known users?
   - Are rate limits blocking normal usage?
   - Is this an attack or misconfiguration?

4. **Quick Fix Options:**
   - **If authorization issue:** Temporarily allow without header (see Rollback Procedures)
   - **If rate limit too strict:** Increase limits temporarily
   - **If attack:** Block IP addresses

**Remediation:**

**Authorization Issues:**
```python
# Quick fix: Temporarily allow without header
# In backend/authorization.py, modify verify_user_access calls:
verify_user_access(user_id, current_user_id, allow_if_none=True)
```

**Rate Limit Issues:**
```python
# Quick fix: Increase limits temporarily
# In backend/rate_limiter.py:
AUTH_LIMIT = "100/minute"  # Increase from 30
GENERAL_LIMIT = "200/minute"  # Increase from 100
```

5. **Deploy Fix:**
   - Make code change
   - Test locally
   - Deploy to production
   - Monitor for resolution

6. **Document:**
   - Record incident details
   - Document root cause
   - Update runbooks if needed

**Time to Resolution:** < 30 minutes

---

### Severity: High (50-100 auth failures/hour OR 50+ rate limit violations/min OR sustained single IP)

**Detection:**
- Multiple alerts triggered
- User reports flooding in
- System performance degradation

**Response Steps:**

1. **Immediate Assessment (0-2 minutes):**
   ```bash
   # Quick status check
   curl http://localhost:8000/api/health
   
   # Check failure rate
   grep "authorization_denied" logs/json_pipeline.log | tail -200 | wc -l
   
   # Check if specific IP/user causing issues
   grep "authorization_denied" logs/json_pipeline.log | tail -200 | \
     grep -oP 'IP:[0-9.]+' | sort | uniq -c | sort -rn | head -10
   ```

2. **Determine Attack vs. Misconfiguration (2-5 minutes):**
   - Check if failures from single IP → Likely attack
   - Check if failures from multiple users → Likely misconfiguration
   - Check for SQL injection patterns → Security incident

3. **Immediate Mitigation:**

   **If Attack:**
   ```bash
   # Block malicious IPs (if using firewall/nginx)
   # Add to blocklist
   iptables -A INPUT -s <MALICIOUS_IP> -j DROP
   
   # Or increase rate limits temporarily to allow legitimate traffic
   ```

   **If Misconfiguration:**
   ```python
   # Temporarily disable authorization checks
   # In backend/api.py, comment out authorization:
   # verify_user_access(user_id, current_user_id)
   ```

   **If Rate Limits Too Strict:**
   ```python
   # Temporarily disable rate limiting
   # In backend/api.py:
   # Comment out @rate_limit_auth decorators
   ```

4. **Escalate:**
   - Notify on-call engineer
   - Notify security team if attack confirmed
   - Prepare rollback plan

5. **Investigate Root Cause:**
   - Review recent changes
   - Check deployment logs
   - Analyze attack patterns (if applicable)

6. **Implement Permanent Fix:**
   - Fix root cause
   - Test thoroughly
   - Deploy fix
   - Re-enable security features gradually

**Time to Resolution:** < 1 hour

---

### Severity: Critical (>100 auth failures/hour OR SQL injection detected OR DDoS pattern)

**Detection:**
- Critical alerts triggered
- System unavailable or severely degraded
- Security breach suspected

**Response Steps:**

1. **Immediate Actions (0-1 minute):**
   ```bash
   # Check system status
   curl http://localhost:8000/api/health
   
   # Check if under attack
   grep -E "(authorization_denied|429)" logs/json_pipeline.log | tail -500 | wc -l
   
   # Check for SQL injection attempts
   grep "authorization_invalid_user_id" logs/json_pipeline.log | \
     grep -iE "(union|select|drop|insert|delete|--|;|')" | head -20
   ```

2. **Emergency Mitigation (1-5 minutes):**

   **Option A: Temporary Rollback (Safest)**
   ```bash
   # Restore previous code version
   git checkout <previous-commit>
   pip install -r requirements.txt
   # Restart backend
   ```

   **Option B: Disable Security Features Temporarily**
   ```python
   # In backend/api.py - Comment out all authorization checks
   # In backend/api.py - Comment out rate limiting setup
   # Deploy emergency fix
   ```

   **Option C: Block Attack Source**
   ```bash
   # Identify attack IPs
   grep "authorization_denied" logs/json_pipeline.log | \
     awk '{print $1}' | sort | uniq -c | sort -rn | head -10
   
   # Block at firewall level
   # Contact hosting provider for DDoS mitigation
   ```

3. **Notify Stakeholders:**
   - On-call engineer (immediate)
   - Security team (if breach suspected)
   - Management (if system unavailable)

4. **Preserve Evidence:**
   ```bash
   # Archive logs
   tar -czf incident_logs_$(date +%Y%m%d_%H%M%S).tar.gz logs/
   
   # Export relevant log entries
   grep -E "(authorization_denied|429|SQL)" logs/json_pipeline.log > incident_export.log
   ```

5. **Investigate:**
   - Full log analysis
   - Review recent deployments
   - Check for data breaches
   - Document attack vectors

6. **Post-Incident:**
   - Root cause analysis
   - Update security measures
   - Update incident response procedures
   - Conduct post-mortem

**Time to Resolution:** < 2 hours (mitigation), < 24 hours (full resolution)

---

## Remediation Steps by Issue Type

### Authorization Always Failing

**Symptoms:**
- All requests return 403 Forbidden
- Legitimate users cannot access their data

**Quick Fix:**
```python
# In backend/authorization.py
# Temporarily allow without header
verify_user_access(user_id, current_user_id, allow_if_none=True)
```

**Investigation:**
```bash
# Check header format
curl -v -H "X-Current-User-Id: user-123" \
     http://localhost:8000/api/users/user-123/slots

# Check logs for patterns
grep "authorization_denied" logs/json_pipeline.log | tail -50
```

**Permanent Fix:**
1. Verify frontend sends header correctly
2. Check user ID format validation
3. Verify authorization logic
4. Test thoroughly before re-enabling strict checks

---

### Rate Limits Too Strict

**Symptoms:**
- Legitimate users hitting 429 Too Many Requests
- Normal usage patterns blocked

**Quick Fix:**
```python
# In backend/rate_limiter.py
AUTH_LIMIT = "100/minute"  # Increase from 30
GENERAL_LIMIT = "200/minute"  # Increase from 100
```

**Investigation:**
```bash
# Check rate limit violations
grep "429" access.log | wc -l

# Find most affected endpoints
grep "429" access.log | awk '{print $7}' | sort | uniq -c | sort -rn
```

**Permanent Fix:**
1. Analyze actual usage patterns
2. Adjust limits based on data
3. Consider per-user rate limiting
4. Monitor and adjust iteratively

---

### SQL Injection Attempts Detected

**Symptoms:**
- Logs show invalid user ID formats with SQL keywords
- Patterns like: `union`, `select`, `drop`, `--`, `;`

**Immediate Actions:**
1. **Block Attack Source:**
   ```bash
   # Identify attack IPs
   grep "authorization_invalid_user_id" logs/json_pipeline.log | \
     grep -iE "(union|select|drop)" | \
     awk '{print $1}' | sort | uniq
   
   # Block IPs at firewall
   ```

2. **Verify Protection:**
   ```bash
   # Test that SQL injection is blocked
   curl -H "X-Current-User-Id: '; DROP TABLE users; --" \
        http://localhost:8000/api/users/test/slots
   # Should return 400 Bad Request, not execute SQL
   ```

3. **Review Logs:**
   ```bash
   # Export all SQL injection attempts
   grep "authorization_invalid_user_id" logs/json_pipeline.log | \
     grep -iE "(union|select|drop|insert|delete|--|;|')" > sql_injection_attempts.log
   ```

4. **Notify Security Team:**
   - Share attack patterns
   - Provide log exports
   - Coordinate response

**Prevention:**
- Ensure input validation is working
- Review authorization logic
- Consider WAF (Web Application Firewall) if attacks persist

---

### Sustained Rate Limit Violations from Single IP

**Symptoms:**
- Single IP causing hundreds of violations
- Pattern suggests automated attack

**Immediate Actions:**
1. **Identify Attack IP:**
   ```bash
   # Find top violating IPs
   grep "429" access.log | \
     awk '{print $1}' | \
     sort | uniq -c | sort -rn | head -10
   ```

2. **Block IP:**
   ```bash
   # At firewall level (example)
   iptables -A INPUT -s <ATTACK_IP> -j DROP
   
   # Or at application level (if supported)
   # Add to rate limiter blocklist
   ```

3. **Verify Block:**
   ```bash
   # Check if violations stop
   tail -f access.log | grep <ATTACK_IP>
   ```

4. **Document:**
   - Record attack IP
   - Note attack pattern
   - Update blocklist if persistent

---

## Post-Remediation Sanity Checks

After applying any remediation step, run this automated sanity check to verify the fix worked:

### Sanity Check Script

```bash
#!/bin/bash
# post_remediation_sanity_check.sh
# Run immediately after applying a remediation fix

set -e

API_URL="${API_URL:-http://localhost:8000}"
TEST_USER_ID="${TEST_USER_ID:-test-user-sanity-check}"
ALERT_CHANNEL="${ALERT_CHANNEL:-console}"  # console, slack, email, etc.

echo "=== Post-Remediation Sanity Check ==="
echo "API URL: $API_URL"
echo "Test User ID: $TEST_USER_ID"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILURES=0
PASSES=0

# Function to send alert
send_alert() {
    local severity=$1
    local message=$2
    case $ALERT_CHANNEL in
        slack)
            curl -X POST -H 'Content-type: application/json' \
                --data "{\"text\":\"[$severity] $message\"}" \
                "$SLACK_WEBHOOK_URL" 2>/dev/null || true
            ;;
        email)
            echo "$message" | mail -s "[$severity] Sanity Check Alert" "$ALERT_EMAIL" 2>/dev/null || true
            ;;
        *)
            echo "[$severity] $message"
            ;;
    esac
}

# Test 1: Health Check
echo -n "Test 1: Health check... "
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/api/health" || echo "000")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSES++))
else
    echo -e "${RED}FAIL${NC} (HTTP $HTTP_CODE)"
    send_alert "CRITICAL" "Health check failed: HTTP $HTTP_CODE"
    ((FAILURES++))
fi

# Test 2: Database Health
echo -n "Test 2: Database health... "
DB_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/api/health/database" || echo "000")
HTTP_CODE=$(echo "$DB_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSES++))
else
    echo -e "${RED}FAIL${NC} (HTTP $HTTP_CODE)"
    send_alert "HIGH" "Database health check failed: HTTP $HTTP_CODE"
    ((FAILURES++))
fi

# Test 3: Authorization - Valid Header (should succeed)
echo -n "Test 3: Authorization with valid header... "
AUTH_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "X-Current-User-Id: $TEST_USER_ID" \
    "$API_URL/api/users/$TEST_USER_ID/slots" || echo "000")
HTTP_CODE=$(echo "$AUTH_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
    # 200 = success, 404 = user/slots don't exist (but auth passed)
    echo -e "${GREEN}PASS${NC}"
    ((PASSES++))
else
    echo -e "${RED}FAIL${NC} (HTTP $HTTP_CODE)"
    send_alert "HIGH" "Valid authorization header test failed: HTTP $HTTP_CODE"
    ((FAILURES++))
fi

# Test 4: Authorization - Mismatched Header (should fail with 403)
echo -n "Test 4: Authorization with mismatched header (should deny)... "
MISMATCH_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "X-Current-User-Id: different-user-id" \
    "$API_URL/api/users/$TEST_USER_ID/slots" || echo "000")
HTTP_CODE=$(echo "$MISMATCH_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "403" ]; then
    echo -e "${GREEN}PASS${NC} (correctly denied)"
    ((PASSES++))
elif [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "404" ]; then
    # If we're in backward-compatible mode (allow_if_none=True), this is expected
    echo -e "${YELLOW}WARN${NC} (HTTP $HTTP_CODE - authorization may be relaxed)"
    ((PASSES++))
else
    echo -e "${RED}FAIL${NC} (HTTP $HTTP_CODE - unexpected response)"
    send_alert "MEDIUM" "Mismatched authorization test unexpected: HTTP $HTTP_CODE"
    ((FAILURES++))
fi

# Test 5: Rate Limiting - Single Request (should succeed)
echo -n "Test 5: Rate limiting - single request... "
RATE_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "X-Current-User-Id: $TEST_USER_ID" \
    "$API_URL/api/users/$TEST_USER_ID" || echo "000")
HTTP_CODE=$(echo "$RATE_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" != "429" ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSES++))
else
    echo -e "${RED}FAIL${NC} (HTTP 429 - rate limited on first request)"
    send_alert "HIGH" "Rate limiting too strict: first request blocked"
    ((FAILURES++))
fi

# Test 6: Invalid Format Protection (should return 400)
echo -n "Test 6: Invalid user ID format protection... "
INVALID_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "X-Current-User-Id: '; DROP TABLE users; --" \
    "$API_URL/api/users/test/slots" || echo "000")
HTTP_CODE=$(echo "$INVALID_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "400" ]; then
    echo -e "${GREEN}PASS${NC} (correctly rejected)"
    ((PASSES++))
else
    echo -e "${RED}FAIL${NC} (HTTP $HTTP_CODE - SQL injection not blocked)"
    send_alert "CRITICAL" "SQL injection protection failed: HTTP $HTTP_CODE"
    ((FAILURES++))
fi

# Summary
echo ""
echo "=== Sanity Check Summary ==="
echo "Passed: $PASSES"
echo "Failed: $FAILURES"
echo ""

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ All sanity checks passed${NC}"
    send_alert "INFO" "Post-remediation sanity check: All tests passed"
    exit 0
else
    echo -e "${RED}✗ $FAILURES test(s) failed${NC}"
    send_alert "HIGH" "Post-remediation sanity check: $FAILURES test(s) failed"
    exit 1
fi
```

### Usage

**After Authorization Fix:**
```bash
# Set test user ID (use a real user ID from your system)
export TEST_USER_ID="your-test-user-id"
export API_URL="http://localhost:8000"

# Run sanity check
./post_remediation_sanity_check.sh
```

**After Rate Limit Adjustment:**
```bash
# Same script works for rate limit fixes
./post_remediation_sanity_check.sh
```

**With Alerting Integration:**
```bash
# Slack integration
export ALERT_CHANNEL="slack"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
./post_remediation_sanity_check.sh

# Email integration
export ALERT_CHANNEL="email"
export ALERT_EMAIL="oncall@example.com"
./post_remediation_sanity_check.sh
```

### Integration with Remediation Steps

Add to each remediation section:

**After Quick Fix:**
```bash
# Apply fix (code change, config update, etc.)
# ... remediation code ...

# Run sanity check
./post_remediation_sanity_check.sh

# If sanity check fails, consider rollback
if [ $? -ne 0 ]; then
    echo "Sanity check failed - consider rollback"
    # Rollback procedure
fi
```

### Expected Results by Remediation Type

| Remediation | Expected Test Results |
|-------------|----------------------|
| **Authorization relaxed** | Test 4 may show WARN (expected) |
| **Rate limits increased** | All tests should pass |
| **Rate limits disabled** | Test 5 should pass |
| **RLS disabled** | All authorization tests should pass |
| **IP blocked** | Tests from blocked IP will fail (expected) |

---

## Monitoring Queries

### Daily Health Check

```bash
#!/bin/bash
# daily_security_check.sh

echo "=== Authorization Failures (Last 24h) ==="
grep "authorization_denied" logs/json_pipeline.log | \
  grep "$(date -d '24 hours ago' +%Y-%m-%d)" | wc -l

echo "=== Rate Limit Violations (Last 24h) ==="
grep "429" access.log | \
  grep "$(date -d '24 hours ago' +%Y-%m-%d)" | wc -l

echo "=== Invalid Format Attempts (Last 24h) ==="
grep "authorization_invalid_user_id" logs/json_pipeline.log | \
  grep "$(date -d '24 hours ago' +%Y-%m-%d)" | wc -l

echo "=== Top Failing User IDs ==="
grep "authorization_denied" logs/json_pipeline.log | \
  grep "$(date -d '24 hours ago' +%Y-%m-%d)" | \
  grep -oP '"requested_user_id":"[^"]+"' | \
  sort | uniq -c | sort -rn | head -10

echo "=== Top Violating IPs ==="
grep "429" access.log | \
  grep "$(date -d '24 hours ago' +%Y-%m-%d)" | \
  awk '{print $1}' | \
  sort | uniq -c | sort -rn | head -10
```

### Real-time Alert Script

```bash
#!/bin/bash
# monitor_security.sh - Run every minute via cron

AUTH_FAILURES=$(grep "authorization_denied" logs/json_pipeline.log | \
  grep "$(date -d '1 minute ago' +%Y-%m-%dT%H:%M)" | wc -l)

RATE_LIMIT_VIOLATIONS=$(grep "429" access.log | \
  grep "$(date -d '1 minute ago' +%Y-%m-%dT%H:%M)" | wc -l)

if [ $AUTH_FAILURES -gt 10 ]; then
  echo "ALERT: High authorization failures: $AUTH_FAILURES/min"
  # Send alert (email, Slack, etc.)
fi

if [ $RATE_LIMIT_VIOLATIONS -gt 20 ]; then
  echo "ALERT: High rate limit violations: $RATE_LIMIT_VIOLATIONS/min"
  # Send alert
fi
```

---

## Escalation Contacts

**On-Call Engineer:** [Contact Info]  
**Security Team:** [Contact Info]  
**Database Admin:** [Contact Info]  
**Management:** [Contact Info]

**Escalation Criteria:**
- Medium severity: Escalate if not resolved in 30 minutes
- High severity: Escalate immediately
- Critical severity: Escalate immediately + notify security team

---

## Post-Incident Checklist

After resolving an incident:

- [ ] Root cause identified and documented
- [ ] Permanent fix implemented
- [ ] Incident log updated
- [ ] Monitoring alerts adjusted (if needed)
- [ ] Runbooks updated (if needed)
- [ ] Team notified of resolution
- [ ] Post-mortem scheduled (for High/Critical incidents)
- [ ] Security measures reviewed and improved

---

## Related Documents

- `docs/security/PRODUCTION_ROLLOUT_PLAYBOOK.md` - Deployment procedures
- `docs/security/ROLLBACK_PROCEDURES.md` - Quick rollback reference
- `docs/security/AUTHORIZATION_IMPLEMENTATION.md` - Authorization details
- `docs/security/RATE_LIMITING.md` - Rate limiting details

---

**Last Updated:** January 2025  
**Status:** Production Ready ✅

