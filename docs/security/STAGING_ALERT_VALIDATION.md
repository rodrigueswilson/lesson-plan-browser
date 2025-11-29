# Staging Alert Validation Guide

**Date:** January 2025  
**Purpose:** Guide for validating alerts and runbook procedures in staging

---

## Overview

This guide provides scripts and procedures to safely test alerts in staging, ensuring:
- Alerts fire correctly
- Runbook procedures work
- Metrics are accurate
- Circuit breaker functions properly

---

## Prerequisites

### Staging Environment Setup

- [ ] Staging API deployed
- [ ] Prometheus scraping staging metrics
- [ ] Alert rules loaded in Prometheus
- [ ] Redis configured (optional, for circuit breaker tests)
- [ ] Test user ID available

### Required Tools

- `curl` - HTTP requests
- `jq` - JSON parsing
- `bc` - Floating point math (for comparisons)
- `redis-cli` - Redis commands (if testing Redis)

---

## Automated Tests

### Script: `scripts/staging_alert_validation.sh`

**Purpose:** Automated validation of alert infrastructure

**Usage:**
```bash
# Set environment variables
export API_URL="http://staging-api.example.com"
export PROMETHEUS_URL="http://staging-prometheus.example.com"
export TEST_USER_ID="staging-test-user"

# Run tests
./scripts/staging_alert_validation.sh
```

**Tests Performed:**
1. High Rate Limit Violations - Generates traffic, checks alert
2. Rate Limit Metrics - Verifies metrics are recorded
3. Redis Health Check - Tests health endpoint
4. Metrics Endpoint - Verifies `/metrics` works
5. Alert Rules - Checks rules are loaded

**Expected Output:**
```
==========================================
Staging Alert Validation Test
==========================================
API URL: http://staging-api.example.com
Prometheus URL: http://staging-prometheus.example.com

=== Test 1: High Rate Limit Violations ===
Generating traffic...
✓ HighRateLimitViolations alert triggered

=== Test 2: Rate Limit Metrics ===
Blocked rate: 12.5 req/s
✓ Rate limit metrics working

=== Test 3: Redis Health Check ===
Redis Status: healthy
✓ Redis health endpoint working

=== Test 4: Redis Circuit Breaker ===
(Skipped if Redis not configured)

=== Test 5: Metrics Endpoint ===
✓ Metrics endpoint working

=== Test 6: Alert Rules Verification ===
✓ Found 13 rate limiter/Redis alert rules

Test Summary
==========================================
Passed: 5
Failed: 0
```

---

## Manual Tests

### Script: `scripts/staging_alert_validation_manual.sh`

**Purpose:** Interactive guide for manual alert testing

**Usage:**
```bash
./scripts/staging_alert_validation_manual.sh
```

**Tests Covered:**
1. High Rate Limit Violations - Step-by-step traffic generation
2. Redis Circuit Breaker - Manual Redis stop/start
3. Rate Limit Block Ratio - Sustained traffic test
4. Runbook Validation - Review runbook procedures

**Benefits:**
- Validates runbook steps work
- Identifies gaps in procedures
- Tests real-world scenarios
- Confirms alert notifications

---

## Test Scenarios

### Scenario 1: Rate Limit Violations

**Objective:** Verify rate limit alerts fire correctly

**Steps:**
1. Generate traffic exceeding limits:
   ```bash
   for i in {1..100}; do
     curl -H "X-Current-User-Id: test-user" \
          http://staging-api/api/users/test-user/slots
     sleep 0.1
   done
   ```

2. Wait 5 minutes for alert to fire

3. Verify alert in Prometheus:
   ```bash
   curl http://prometheus:9090/api/v1/alerts | \
     jq '.data.alerts[] | select(.labels.alertname=="HighRateLimitViolations")'
   ```

4. Follow runbook procedures:
   - Check alert details
   - Identify affected limit
   - Determine if legitimate or attack
   - Apply remediation

5. Verify resolution:
   ```bash
   curl 'http://prometheus:9090/api/v1/query?query=sum(rate(limiter_blocked_total[5m]))'
   ```

**Expected Results:**
- Alert fires within 5 minutes
- Alert shows correct limit_name
- Runbook steps are actionable
- Alert resolves after remediation

---

### Scenario 2: Redis Circuit Breaker

**Objective:** Verify circuit breaker alerts and recovery

**Steps:**
1. Check initial Redis status:
   ```bash
   curl http://staging-api/api/health/redis | jq .
   ```

2. Stop Redis:
   ```bash
   redis-cli SHUTDOWN
   # or
   docker stop redis-container
   ```

3. Wait for circuit breaker to open (up to 60 seconds):
   ```bash
   watch -n 5 'curl -s http://staging-api/api/health/redis | jq .circuit_breaker.circuit_open'
   ```

4. Verify alert fires:
   ```bash
   curl http://prometheus:9090/api/v1/alerts | \
     jq '.data.alerts[] | select(.labels.alertname=="RedisCircuitBreakerOpen")'
   ```

5. Follow runbook procedures:
   - Check Redis status
   - Restart Redis
   - Verify reconnection

6. Restart Redis:
   ```bash
   redis-server
   # or
   docker start redis-container
   ```

7. Wait for circuit breaker to close:
   ```bash
   watch -n 5 'curl -s http://staging-api/api/health/redis | jq .circuit_breaker.circuit_open'
   ```

**Expected Results:**
- Circuit breaker opens within 60 seconds
- Alert fires when circuit opens
- Redis restarts successfully
- Circuit breaker closes automatically
- Alert resolves

---

### Scenario 3: Rate Limit Block Ratio

**Objective:** Verify block ratio alerts

**Steps:**
1. Generate sustained traffic:
   ```bash
   for i in {1..200}; do
     curl -H "X-Current-User-Id: test-user" \
          http://staging-api/api/users/test-user/slots
     sleep 0.1
   done
   ```

2. Check block ratio:
   ```bash
   curl 'http://prometheus:9090/api/v1/query?query=sum(rate(limiter_blocked_total[5m]))%20/%20sum(rate(limiter_allowed_total[5m])%20+%20rate(limiter_blocked_total[5m]))'
   ```

3. Verify alert fires if ratio > 10%:
   ```bash
   curl http://prometheus:9090/api/v1/alerts | \
     jq '.data.alerts[] | select(.labels.alertname=="HighRateLimitBlockRatio")'
   ```

4. Follow runbook procedures:
   - Check if legitimate traffic
   - Increase limits if needed
   - Block IPs if attack

**Expected Results:**
- Block ratio calculated correctly
- Alert fires when threshold exceeded
- Runbook provides clear remediation

---

## Runbook Validation Checklist

For each alert tested, verify:

- [ ] Alert appears in runbook (`docs/security/ALERT_RUNBOOK.md`)
- [ ] Symptoms section matches observed behavior
- [ ] Immediate actions are clear and actionable
- [ ] Investigation steps help identify root cause
- [ ] Remediation steps work as described
- [ ] Verification commands produce expected results
- [ ] Escalation criteria are appropriate

---

## Gap Analysis

### Common Gaps to Look For

1. **Missing Steps:**
   - Runbook doesn't cover edge cases
   - Verification steps incomplete
   - Escalation unclear

2. **Incorrect Commands:**
   - Commands don't work in staging
   - Output format differs
   - Missing dependencies

3. **Timing Issues:**
   - Wait times too short/long
   - Alert firing delays not accounted for
   - Recovery time estimates wrong

4. **Missing Context:**
   - Assumptions not stated
   - Prerequisites not listed
   - Environment differences not noted

---

## Test Results Template

```markdown
## Alert Validation Results

**Date:** [Date]
**Tester:** [Name]
**Environment:** Staging

### HighRateLimitViolations
- [ ] Alert fired correctly
- [ ] Runbook steps followed successfully
- [ ] Remediation worked
- [ ] Verification confirmed resolution
- **Gaps Found:** [List any gaps]

### RedisCircuitBreakerOpen
- [ ] Alert fired correctly
- [ ] Runbook steps followed successfully
- [ ] Remediation worked
- [ ] Verification confirmed resolution
- **Gaps Found:** [List any gaps]

### Overall Assessment
- **Runbook Quality:** [Good/Fair/Poor]
- **Action Items:** [List improvements needed]
```

---

## Post-Test Actions

### 1. Document Gaps

- Update runbook with missing steps
- Fix incorrect commands
- Add missing context
- Clarify unclear procedures

### 2. Update Runbook

- Incorporate learnings from tests
- Add staging-specific notes
- Update timing estimates
- Improve verification steps

### 3. Schedule Regular Tests

- Monthly runbook reviews
- Quarterly full validation
- After major changes
- Before production incidents

---

## Safety Considerations

### Staging-Only Tests

- **Never run in production**
- Use test user IDs only
- Limit traffic generation
- Monitor staging resources

### Cleanup

After tests:
```bash
# Reset rate limits (if changed)
git checkout backend/rate_limiter.py

# Restart services
systemctl restart your-backend-service

# Clear test data (if needed)
redis-cli FLUSHDB  # Only in staging!
```

---

## Related Documents

- `docs/security/ALERT_RUNBOOK.md` - Complete runbook
- `docs/security/ALERT_RUNBOOK_QUICK_REFERENCE.md` - Quick reference
- `scripts/staging_alert_validation.sh` - Automated test script
- `scripts/staging_alert_validation_manual.sh` - Manual test guide

---

**Last Updated:** January 2025  
**Status:** Ready for Use ✅

