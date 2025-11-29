# Alert Runbook - Quick Reference Card

**Date:** January 2025  
**Purpose:** One-page quick reference for on-call responders

---

## Critical Alerts (Immediate Action Required)

### RedisCircuitBreakerOpen
**Action:** Check Redis connectivity → Restart Redis if down → Verify circuit closes

### CriticalRateLimitViolations (>50 req/s)
**Action:** Check if attack → Block IPs if attack → Increase limits if legitimate

### RedisFallbackSustained (>10 fallbacks)
**Action:** Fix Redis connectivity → Restart Redis → Verify reconnection

### CriticalRateLimitLatency (>0.5s)
**Action:** Check Redis performance → Scale Redis → Optimize queries

### CriticalRateLimitBlockRatio (>30%)
**Action:** Emergency increase limits → Investigate root cause → Deploy fix

---

## Warning Alerts (Investigate Within 15 Minutes)

### HighRateLimitViolations (>10 req/s)
**Action:** Identify limit type → Check if legitimate → Adjust limits or block IPs

### AuthEndpointRateLimitViolations (>5 req/s)
**Action:** Check for brute force → Block attack IPs → Increase auth limits if needed

### HighRedisFailures (>5 failures/s)
**Action:** Check Redis health → Monitor for circuit breaker → Scale if needed

### RedisFallbackOccurred
**Action:** Check Redis status → Monitor recovery → Verify reconnection

### HighRateLimitLatency (>0.1s)
**Action:** Check Redis performance → Review Lua scripts → Optimize

### HighRateLimitBlockRatio (>10%)
**Action:** Review limits → Check usage patterns → Adjust if needed

---

## Quick Commands

### Check Alert Status
```bash
curl http://prometheus:9090/api/v1/alerts | jq '.data.alerts[] | {alertname, state, severity}'
```

### Check Redis Health
```bash
curl http://localhost:8000/api/health/redis | jq .
```

### Check Rate Limit Metrics
```bash
curl 'http://prometheus:9090/api/v1/query?query=sum(rate(limiter_blocked_total[5m]))'
```

### Find Attack IPs
```bash
grep "429" access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -10
```

### Block IP
```bash
iptables -A INPUT -s <IP> -j DROP
```

### Increase Limits (Emergency)
```python
# In backend/rate_limiter.py
AUTH_LIMIT = "100/minute"  # Increase from 30
GENERAL_LIMIT = "200/minute"  # Increase from 100
```

### Restart Redis
```bash
sudo systemctl restart redis-server
# or
docker restart redis-container
```

---

## Decision Tree

```
Alert Received?
├─ Critical Severity?
│  ├─ Circuit Breaker Open? → Check Redis → Restart if needed
│  ├─ >50 req/s blocked? → Check attack → Block IPs or increase limits
│  ├─ >30% blocked? → Emergency increase limits → Investigate
│  └─ >0.5s latency? → Check Redis performance → Scale
│
└─ Warning Severity?
   ├─ >10 req/s blocked? → Check if legitimate → Adjust limits
   ├─ Redis failures? → Monitor → Check Redis health
   └─ High latency? → Check Redis performance → Optimize
```

---

## Emergency Contacts

### On-Call Rotation
- **Primary:** [Name] - [Phone] - [Email] - [Slack: @username]
- **Secondary:** [Name] - [Phone] - [Email] - [Slack: @username]
- **Escalation:** [Name] - [Phone] - [Email] - [Slack: @username]

### Teams
- **Security Team:** [Slack: #security] - [Email: security@example.com] - [PagerDuty: security-oncall]
- **Infrastructure/Redis:** [Slack: #infrastructure] - [Email: infra@example.com] - [PagerDuty: infra-oncall]
- **Database Team:** [Slack: #database] - [Email: db@example.com]

### Communication Channels
- **Slack:** #oncall-alerts (critical), #rate-limiter-alerts (warnings)
- **PagerDuty:** [Service Key] (critical alerts only)
- **Email:** oncall@example.com (all alerts)
- **SMS:** [Phone number] (critical alerts only)

### Alert Routing
- **Critical Alerts:** PagerDuty → SMS → Slack → Email
- **Warning Alerts:** Slack → Email
- **Info Alerts:** Email only

---

## Full Runbook

See `docs/security/ALERT_RUNBOOK.md` for complete remediation procedures.

---

**Last Updated:** January 2025

