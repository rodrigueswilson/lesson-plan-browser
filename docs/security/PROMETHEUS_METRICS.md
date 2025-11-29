# Prometheus Metrics for Rate Limiting

**Date:** January 2025  
**Purpose:** Prometheus metrics for monitoring Redis rate limiter and circuit breaker

---

## Overview

The application exposes Prometheus metrics for:
- Rate limit allowed/blocked requests
- Redis connection failures and fallbacks
- Circuit breaker status
- Rate limit check performance

---

## Metrics Endpoint

**Endpoint:** `/metrics`

**Format:** Prometheus text format

**Example:**
```bash
curl http://localhost:8000/metrics
```

---

## Available Metrics

### Rate Limiting Metrics

#### `limiter_allowed_total`

**Type:** Counter  
**Description:** Total number of requests allowed by rate limiter  
**Labels:**
- `limit_name` - Rate limit tier (auth, general, heavy, batch, unknown)
- `service` - Service name (lesson_planner)
- `env` - Environment (prod, staging, dev, memory)

**Example:**
```
limiter_allowed_total{env="prod",limit_name="auth",service="lesson_planner"} 1234
limiter_allowed_total{env="prod",limit_name="general",service="lesson_planner"} 5678
```

#### `limiter_blocked_total`

**Type:** Counter  
**Description:** Total number of requests blocked by rate limiter  
**Labels:**
- `limit_name` - Rate limit tier (auth, general, heavy, batch, unknown)
- `service` - Service name (lesson_planner)
- `env` - Environment (prod, staging, dev, memory)
- `reason` - Block reason (limit_exceeded, circuit_open, etc.)

**Example:**
```
limiter_blocked_total{env="prod",limit_name="auth",reason="limit_exceeded",service="lesson_planner"} 56
```

### Redis Metrics

#### `redis_fallback_total`

**Type:** Counter  
**Description:** Total number of times rate limiter fell back to memory storage  
**Labels:**
- `service` - Service name (lesson_planner)
- `env` - Environment (prod, staging, dev)

**Example:**
```
redis_fallback_total{env="prod",service="lesson_planner"} 3
```

#### `redis_failure_total`

**Type:** Counter  
**Description:** Total number of Redis connection failures  
**Labels:**
- `service` - Service name (lesson_planner)
- `env` - Environment (prod, staging, dev)
- `error_type` - Error type (connection_error, circuit_opened, timeout)

**Example:**
```
redis_failure_total{env="prod",error_type="connection_error",service="lesson_planner"} 12
```

#### `redis_circuit_open`

**Type:** Gauge  
**Description:** Whether Redis circuit breaker is open (1 = open, 0 = closed)  
**Labels:**
- `service` - Service name (lesson_planner)
- `env` - Environment (prod, staging, dev)

**Example:**
```
redis_circuit_open{env="prod",service="lesson_planner"} 0
```

#### `redis_connection_failures`

**Type:** Gauge  
**Description:** Current count of Redis connection failures  
**Labels:**
- `service` - Service name (lesson_planner)
- `env` - Environment (prod, staging, dev)

**Example:**
```
redis_connection_failures{env="prod",service="lesson_planner"} 2
```

### Performance Metrics

#### `rate_limit_check_duration_seconds`

**Type:** Histogram  
**Description:** Time taken to check rate limit  
**Labels:**
- `limit_name` - Rate limit tier (auth, general, heavy, batch)
- `service` - Service name (lesson_planner)
- `env` - Environment (prod, staging, dev)

**Buckets:** 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0

**Example:**
```
rate_limit_check_duration_seconds_bucket{env="prod",limit_name="auth",service="lesson_planner",le="0.001"} 1000
rate_limit_check_duration_seconds_bucket{env="prod",limit_name="auth",service="lesson_planner",le="0.005"} 1500
rate_limit_check_duration_seconds_sum{env="prod",limit_name="auth",service="lesson_planner"} 2.5
rate_limit_check_duration_seconds_count{env="prod",limit_name="auth",service="lesson_planner"} 2000
```

---

## Prometheus Configuration

### Scrape Configuration

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'lesson-planner-api'
    scrape_interval: 15s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:8000']
        labels:
          service: 'lesson-planner'
          environment: 'prod'
```

### Service Discovery (Kubernetes)

```yaml
scrape_configs:
  - job_name: 'lesson-planner-api'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: lesson-planner
      - source_labels: [__meta_kubernetes_pod_ip]
        target_label: __address__
        replacement: '${1}:8000'
```

---

## Alerting Rules

### Example Prometheus Alert Rules

Create `alerts.yml`:

```yaml
groups:
  - name: rate_limiter
    interval: 30s
    rules:
      # High rate limit violations
      - alert: HighRateLimitViolations
        expr: rate(limiter_blocked_total[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High rate of rate limit violations"
          description: "{{ $value }} requests blocked per second in last 5 minutes"

      # Circuit breaker opened
      - alert: RedisCircuitBreakerOpen
        expr: redis_circuit_open == 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis circuit breaker is open"
          description: "Rate limiting may be degraded. Circuit opened at {{ $labels.env }}"

      # Redis connection failures
      - alert: HighRedisFailures
        expr: rate(redis_failure_total[5m]) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High rate of Redis connection failures"
          description: "{{ $value }} failures per second in last 5 minutes"

      # Fallback to memory
      - alert: RedisFallbackOccurred
        expr: increase(redis_fallback_total[5m]) > 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Rate limiter fell back to memory storage"
          description: "Redis unavailable, using in-memory storage at {{ $labels.env }}"

      # Rate limit check latency
      - alert: HighRateLimitLatency
        expr: histogram_quantile(0.95, rate(rate_limit_check_duration_seconds_bucket[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High rate limit check latency"
          description: "95th percentile latency is {{ $value }}s"
```

---

## Grafana Dashboard

### Example Queries

**Rate Limit Violations:**
```promql
sum(rate(limiter_blocked_total[5m])) by (limit_name, env)
```

**Allowed vs Blocked:**
```promql
sum(rate(limiter_allowed_total[5m])) by (limit_name)
/
sum(rate(limiter_blocked_total[5m])) by (limit_name)
```

**Circuit Breaker Status:**
```promql
redis_circuit_open
```

**Redis Failures:**
```promql
sum(rate(redis_failure_total[5m])) by (error_type)
```

**Rate Limit Check Latency (p95):**
```promql
histogram_quantile(0.95, rate(rate_limit_check_duration_seconds_bucket[5m]))
```

---

## Testing Metrics

### Verify Metrics Endpoint

```bash
# Check metrics endpoint
curl http://localhost:8000/metrics | grep limiter

# Check specific metric
curl http://localhost:8000/metrics | grep limiter_allowed_total

# Check Redis metrics
curl http://localhost:8000/metrics | grep redis_
```

### Generate Test Traffic

```bash
# Make requests to trigger metrics
for i in {1..50}; do
  curl -H "X-Current-User-Id: test-user" \
       http://localhost:8000/api/users/test-user/slots
done

# Check metrics
curl http://localhost:8000/metrics | grep limiter_allowed_total
```

---

## Integration with Existing Monitoring

### Datadog

If using Datadog, configure Prometheus endpoint:

```yaml
# datadog.yaml
prometheus_scrape:
  - url: http://localhost:8000/metrics
    namespace: lesson_planner
    metrics:
      - limiter_*
      - redis_*
```

### New Relic

Use Prometheus remote write:

```yaml
# prometheus.yml
remote_write:
  - url: https://metric-api.newrelic.com/prometheus/v1/write?prometheus_server=lesson-planner
    bearer_token: YOUR_NEW_RELIC_LICENSE_KEY
```

---

## Troubleshooting

### Metrics Not Appearing

1. **Check endpoint:**
   ```bash
   curl http://localhost:8000/metrics
   ```

2. **Verify Prometheus scraping:**
   ```bash
   # Check Prometheus targets
   curl http://prometheus:9090/api/v1/targets
   ```

3. **Check labels:**
   ```bash
   # Verify label values
   curl http://localhost:8000/metrics | grep limiter_allowed_total
   ```

### High Cardinality

If metrics have too many unique label combinations:

1. **Reduce label cardinality:**
   - Use fewer label values
   - Aggregate at Prometheus level

2. **Use recording rules:**
   ```yaml
   groups:
     - name: rate_limiter_aggregated
       interval: 1m
       rules:
         - record: limiter:blocked:rate5m
           expr: rate(limiter_blocked_total[5m])
   ```

---

## Related Documents

- `backend/metrics.py` - Metrics definitions
- `backend/rate_limiter.py` - Rate limiter with metrics integration
- `docs/security/REDIS_RATE_LIMITER_MIGRATION.md` - Redis migration guide
- `docs/security/REDIS_HARDENING_SUMMARY.md` - Hardening features

---

**Last Updated:** January 2025  
**Status:** Production Ready ✅

