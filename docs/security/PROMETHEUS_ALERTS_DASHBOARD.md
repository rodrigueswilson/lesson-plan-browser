# Prometheus Alerts & Grafana Dashboard

**Date:** January 2025  
**Purpose:** Production-ready alert rules and dashboard for rate limiter monitoring

---

## Files Provided

1. **`prometheus/alerts.yml`** - Prometheus alert rules
2. **`grafana/dashboard-rate-limiter.json`** - Grafana dashboard JSON

---

## Prometheus Alert Rules

### Alert Groups

#### 1. Rate Limiter Alerts

**HighRateLimitViolations**
- **Trigger:** > 10 blocked requests/sec for 5 minutes
- **Severity:** Warning
- **Action:** Investigate if limits are too strict or attack in progress

**CriticalRateLimitViolations**
- **Trigger:** > 50 blocked requests/sec for 2 minutes
- **Severity:** Critical
- **Action:** Immediate investigation - may indicate attack

**AuthEndpointRateLimitViolations**
- **Trigger:** > 5 auth endpoint blocks/sec for 5 minutes
- **Severity:** Warning
- **Action:** Check for brute force attempts

#### 2. Circuit Breaker Alerts

**RedisCircuitBreakerOpen**
- **Trigger:** Circuit breaker open for 1 minute
- **Severity:** Critical
- **Action:** Check Redis connectivity, rate limiting degraded

**RedisCircuitBreakerOpenExtended**
- **Trigger:** Circuit breaker open for 10+ minutes
- **Severity:** Critical
- **Action:** Immediate investigation required

#### 3. Redis Health Alerts

**HighRedisFailures**
- **Trigger:** > 5 failures/sec for 5 minutes
- **Severity:** Warning
- **Action:** Monitor Redis connectivity

**CriticalRedisFailures**
- **Trigger:** > 20 failures/sec for 2 minutes
- **Severity:** Critical
- **Action:** Circuit breaker may open soon

**RedisFallbackOccurred**
- **Trigger:** Any fallback to memory in 5 minutes
- **Severity:** Warning
- **Action:** Redis unavailable, using in-memory storage

**RedisFallbackSustained**
- **Trigger:** > 10 fallbacks in 10 minutes
- **Severity:** Critical
- **Action:** Redis connectivity issues persist

#### 4. Performance Alerts

**HighRateLimitLatency**
- **Trigger:** p95 latency > 0.1s for 5 minutes
- **Severity:** Warning
- **Action:** Check Redis performance

**CriticalRateLimitLatency**
- **Trigger:** p95 latency > 0.5s for 2 minutes
- **Severity:** Critical
- **Action:** Rate limiting impacting user experience

#### 5. Ratio Alerts

**HighRateLimitBlockRatio**
- **Trigger:** > 10% of requests blocked for 5 minutes
- **Severity:** Warning
- **Action:** Limits may be too strict

**CriticalRateLimitBlockRatio**
- **Trigger:** > 30% of requests blocked for 2 minutes
- **Severity:** Critical
- **Action:** Immediate investigation required

---

## Installation

### Prometheus Alert Rules

1. **Copy alert rules:**
   ```bash
   cp prometheus/alerts.yml /etc/prometheus/alerts/rate-limiter.yml
   ```

2. **Update Prometheus config:**
   ```yaml
   # prometheus.yml
   rule_files:
     - "/etc/prometheus/alerts/rate-limiter.yml"
   ```

3. **Reload Prometheus:**
   ```bash
   # Send SIGHUP or use API
   curl -X POST http://prometheus:9090/-/reload
   ```

4. **Verify:**
   ```bash
   # Check rules are loaded
   curl http://prometheus:9090/api/v1/rules
   ```

### Grafana Dashboard

1. **Import dashboard:**
   - Open Grafana → Dashboards → Import
   - Upload `grafana/dashboard-rate-limiter.json`
   - Select Prometheus data source
   - Click "Import"

2. **Verify panels:**
   - All panels should show data
   - Check time range is correct
   - Verify data source connection

---

## Dashboard Panels

### 1. Rate Limit Requests (Allowed vs Blocked)
- **Type:** Time series graph
- **Metrics:** `limiter_allowed_total`, `limiter_blocked_total`
- **Purpose:** Visualize request flow

### 2. Circuit Breaker Status
- **Type:** Stat panel
- **Metric:** `redis_circuit_open`
- **Purpose:** Quick status check (OPEN/CLOSED)

### 3. Redis Connection Failures
- **Type:** Stat panel
- **Metric:** `redis_connection_failures`
- **Purpose:** Current failure count

### 4. Rate Limit Block Ratio
- **Type:** Bar gauge
- **Metric:** Blocked / (Allowed + Blocked)
- **Purpose:** Percentage of blocked requests by limit type

### 5. Redis Failures by Error Type
- **Type:** Pie chart
- **Metric:** `redis_failure_total` by `error_type`
- **Purpose:** Breakdown of failure types

### 6. Rate Limit Check Latency
- **Type:** Time series graph
- **Metric:** `rate_limit_check_duration_seconds` (p95, p50)
- **Purpose:** Performance monitoring

### 7. Redis Fallback Events
- **Type:** Time series graph
- **Metric:** `redis_fallback_total`
- **Purpose:** Track fallback frequency

### 8. Total Requests by Limit Type
- **Type:** Table
- **Metrics:** Allowed and blocked by limit_name
- **Purpose:** Summary view

---

## Customization

### Adjust Alert Thresholds

Edit `prometheus/alerts.yml`:

```yaml
# Example: Lower threshold for high violations
- alert: HighRateLimitViolations
  expr: sum(rate(limiter_blocked_total[5m])) > 5  # Changed from 10
```

### Add Custom Panels

1. Edit `grafana/dashboard-rate-limiter.json`
2. Add panel definition to `panels` array
3. Re-import dashboard

### Environment-Specific Alerts

Add environment filter:

```yaml
- alert: HighRateLimitViolations
  expr: |
    sum(rate(limiter_blocked_total{env="prod"}[5m])) > 10
```

---

## Testing Alerts

### Trigger Test Alert

```bash
# Make many requests to trigger rate limit
for i in {1..100}; do
  curl http://localhost:8000/api/users/test/slots
done

# Check alerts in Prometheus
curl http://prometheus:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.alertname=="HighRateLimitViolations")'
```

### Test Circuit Breaker Alert

```bash
# Stop Redis
redis-cli SHUTDOWN

# Wait for circuit breaker to open
sleep 70

# Check alert
curl http://prometheus:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.alertname=="RedisCircuitBreakerOpen")'
```

---

## Alert Routing

### Example Alertmanager Config

```yaml
# alertmanager.yml
route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'oncall'
    - match:
        component: redis
      receiver: 'redis-team'

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://slack-webhook/rate-limiter'
  
  - name: 'oncall'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
  
  - name: 'redis-team'
    email_configs:
      - to: 'redis-team@example.com'
```

---

## Troubleshooting

### Alerts Not Firing

1. **Check rules are loaded:**
   ```bash
   curl http://prometheus:9090/api/v1/rules
   ```

2. **Verify metrics exist:**
   ```bash
   curl http://localhost:8000/metrics | grep limiter_blocked_total
   ```

3. **Check alert evaluation:**
   ```bash
   curl 'http://prometheus:9090/api/v1/query?query=sum(rate(limiter_blocked_total[5m]))'
   ```

### Dashboard Not Showing Data

1. **Check data source:**
   - Verify Prometheus URL is correct
   - Test connection in Grafana

2. **Verify time range:**
   - Check dashboard time picker
   - Ensure metrics exist for selected range

3. **Check metric names:**
   - Verify labels match (env, service, limit_name)
   - Check for typos in queries

---

## Related Documents

- `docs/security/PROMETHEUS_METRICS.md` - Metrics documentation
- `docs/security/REDIS_RATE_LIMITER_MIGRATION.md` - Redis migration
- `prometheus/alerts.yml` - Alert rules file
- `grafana/dashboard-rate-limiter.json` - Dashboard JSON

---

**Last Updated:** January 2025  
**Status:** Production Ready ✅

