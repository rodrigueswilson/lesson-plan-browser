# Alertmanager Test Payloads - Copy-Paste Ready

Ready-to-use curl commands for testing Alertmanager alert routing and notifications.

## Quick Start

**Set your Alertmanager URL:**
```bash
export ALERTMANAGER_URL="http://localhost:9093"
# or for staging
export ALERTMANAGER_URL="http://staging-alertmanager:9093"
```

**Run interactive test script:**
```bash
scripts/test_alertmanager_curl.sh
```

## Individual Test Payloads

### 1. High Rate Limit Violations (Warning)

```bash
curl -X POST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[
  {
    "labels": {
      "alertname": "HighRateLimitViolations",
      "severity": "warning",
      "component": "rate_limiter",
      "limit_name": "general",
      "env": "staging",
      "service": "lesson-planner-api"
    },
    "annotations": {
      "summary": "Test: High rate of rate limit violations",
      "description": "Test: 15 requests blocked per second in last 5 minutes. Limit: general. Environment: staging.",
      "runbook_url": "https://your-docs-site.com/docs/security/ALERT_RUNBOOK.md#high-rate-limit-violations"
    },
    "startsAt": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "endsAt": "'$(date -u -d "+5 minutes" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+5M +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }
]'
```

**Expected:** Routes to `rate-limiter-team` receiver, sends to Slack channel `#rate-limiter-alerts`.

### 2. Critical Rate Limit Violations (Critical)

```bash
curl -X POST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[
  {
    "labels": {
      "alertname": "CriticalRateLimitViolations",
      "severity": "critical",
      "component": "rate_limiter",
      "limit_name": "general",
      "env": "staging",
      "service": "lesson-planner-api"
    },
    "annotations": {
      "summary": "Test: Critical rate of rate limit violations",
      "description": "Test: 60 requests blocked per second. This may indicate an attack. Limit: general. Environment: staging.",
      "runbook_url": "https://your-docs-site.com/docs/security/ALERT_RUNBOOK.md#critical-rate-limit-violations"
    },
    "startsAt": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "endsAt": "'$(date -u -d "+5 minutes" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+5M +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }
]'
```

**Expected:** Routes to `oncall-critical` receiver (critical severity), sends to Slack `#oncall-alerts` and email.

### 3. Redis Circuit Breaker Open (Critical)

```bash
curl -X POST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[
  {
    "labels": {
      "alertname": "RedisCircuitBreakerOpen",
      "severity": "critical",
      "component": "redis",
      "env": "staging",
      "service": "lesson-planner-api"
    },
    "annotations": {
      "summary": "Test: Redis circuit breaker is open",
      "description": "Test: Rate limiting may be degraded. Circuit breaker opened due to Redis connection failures. Environment: staging.",
      "runbook_url": "https://your-docs-site.com/docs/security/ALERT_RUNBOOK.md#redis-circuit-breaker-open"
    },
    "startsAt": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "endsAt": "'$(date -u -d "+5 minutes" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+5M +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }
]'
```

**Expected:** Routes to `redis-team` receiver, sends to Slack channel `#redis-alerts`.

### 4. High Redis Failures (Warning)

```bash
curl -X POST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[
  {
    "labels": {
      "alertname": "HighRedisFailures",
      "severity": "warning",
      "component": "redis",
      "error_type": "connection_timeout",
      "env": "staging",
      "service": "lesson-planner-api"
    },
    "annotations": {
      "summary": "Test: High rate of Redis connection failures",
      "description": "Test: 8 Redis failures per second in last 5 minutes. Error type: connection_timeout. Environment: staging.",
      "runbook_url": "https://your-docs-site.com/docs/security/ALERT_RUNBOOK.md#high-redis-failures"
    },
    "startsAt": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "endsAt": "'$(date -u -d "+5 minutes" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+5M +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }
]'
```

**Expected:** Routes to `redis-team` receiver, sends to Slack channel `#redis-alerts`.

### 5. Auth Endpoint Rate Limit Violations

```bash
curl -X POST http://localhost:9093/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '[
  {
    "labels": {
      "alertname": "AuthEndpointRateLimitViolations",
      "severity": "warning",
      "component": "rate_limiter",
      "limit_name": "auth",
      "env": "staging",
      "service": "lesson-planner-api"
    },
    "annotations": {
      "summary": "Test: High rate limit violations on auth endpoints",
      "description": "Test: 6 auth requests blocked per second. This may indicate brute force attempts. Environment: staging.",
      "runbook_url": "https://your-docs-site.com/docs/security/ALERT_RUNBOOK.md#auth-endpoint-rate-limit-violations"
    },
    "startsAt": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "endsAt": "'$(date -u -d "+5 minutes" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+5M +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }
]'
```

## Verification Commands

**Check Alertmanager health:**
```bash
curl http://localhost:9093/-/healthy
```

**List active alerts:**
```bash
curl http://localhost:9093/api/v1/alerts | jq '.'
```

**View Alertmanager status:**
```bash
curl http://localhost:9093/api/v1/status | jq '.'
```

**View configuration:**
```bash
curl http://localhost:9093/api/v1/status/config | jq '.data'
```

**Reload configuration (if file-based):**
```bash
curl -X POST http://localhost:9093/-/reload
```

## Create Silence

**Silence a specific alert:**
```bash
curl -X POST http://localhost:9093/api/v2/silences \
  -H 'Content-Type: application/json' \
  -d '{
    "matchers": [
      {
        "name": "alertname",
        "value": "HighRateLimitViolations",
        "isRegex": false
      }
    ],
    "startsAt": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "endsAt": "'$(date -u -d "+1 hour" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -v+1H +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "comment": "Test silence"
  }'
```

**List active silences:**
```bash
curl http://localhost:9093/api/v2/silences | jq '.'
```

## Testing Checklist

After sending each test alert:

- [ ] Alert appears in Alertmanager UI (`http://localhost:9093`)
- [ ] Notification received in expected channel (Slack/PagerDuty/Email)
- [ ] Runbook URL is present and clickable
- [ ] Runbook URL opens correct section
- [ ] Alert routes to correct receiver (check Alertmanager logs)
- [ ] Inhibition rules work (critical suppresses warning)
- [ ] Alert resolves correctly when `endsAt` time passes

## Troubleshooting

**Alert not received:**
1. Check Alertmanager logs: `docker logs alertmanager` or `journalctl -u alertmanager`
2. Verify receiver configuration in `alertmanager.yml`
3. Check webhook URLs/keys are valid (not placeholders)
4. Verify network connectivity to notification endpoints

**Runbook URL missing:**
1. Ensure `alerts.yml` has `runbook_url` annotation
2. Check templates are loaded (if using templates)
3. Verify Alertmanager can access template files

**Wrong receiver:**
1. Check route matching in `alertmanager.yml`
2. Verify alert labels match route `match` conditions
3. Check `group_by` settings

## See Also

- [Alert Runbook](ALERT_RUNBOOK.md) - Detailed remediation steps
- [Alert Runbook Quick Reference](ALERT_RUNBOOK_QUICK_REFERENCE.md) - One-page reference
- [Alertmanager Validation Guide](ALERTMANAGER_VALIDATION_TESTING.md) - Full validation guide
- [Receiver Configuration Guide](ALERTMANAGER_RECEIVERS_GUIDE.md) - Setup notification channels

