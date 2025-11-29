# What is Prometheus? - Explained Simply

## What Prometheus Does

**Prometheus** is a monitoring and alerting system that:

1. **Collects metrics** from your applications (like your FastAPI app)
2. **Stores metrics** in a time-series database
3. **Evaluates alert rules** to detect problems
4. **Sends alerts** to Alertmanager when thresholds are exceeded

Think of it as a **health monitor** that watches your application 24/7 and alerts you when something goes wrong.

---

## How It Works in Your Setup

### Step 1: Your FastAPI App Exposes Metrics

Your FastAPI app has a `/metrics` endpoint that exposes data like:
```
limiter_blocked_total{env="prod",limit_name="auth"} 42
limiter_allowed_total{env="prod",limit_name="general"} 1234
redis_circuit_open{env="prod"} 0
```

**What this means:** Your app is saying "I've blocked 42 auth requests" and "I've allowed 1234 general requests."

### Step 2: Prometheus Scrapes (Collects) These Metrics

Prometheus periodically (every 15 seconds by default) makes HTTP requests to your `/metrics` endpoint and collects all those numbers.

**What this means:** Prometheus is like a robot that checks your app's health every 15 seconds and writes down the numbers.

### Step 3: Prometheus Stores the Metrics

Prometheus stores all these metrics with timestamps, so you can see:
- "At 2:00 PM, blocked requests = 10"
- "At 2:01 PM, blocked requests = 15"
- "At 2:02 PM, blocked requests = 25"

**What this means:** You can see trends over time - "Are blocked requests increasing?"

### Step 4: Prometheus Evaluates Alert Rules

Prometheus checks your alert rules (in `prometheus/alerts.yml`) like:
```yaml
- alert: HighRateLimitViolations
  expr: sum(rate(limiter_blocked_total[5m])) > 10
  for: 5m
```

**What this means:** "If blocked requests exceed 10 per second for 5 minutes, trigger an alert."

### Step 5: Prometheus Sends Alerts to Alertmanager

When an alert fires, Prometheus sends it to Alertmanager, which then:
- Routes the alert to the right team
- Sends email notifications
- Includes runbook links

**What this means:** You get notified when problems occur, with instructions on how to fix them.

---

## What the Prometheus Configuration Does

The `prometheus/prometheus.yml` file tells Prometheus:

### 1. Where to Find Your Application

```yaml
scrape_configs:
  - job_name: 'lesson-planner-api'
    static_configs:
      - targets:
          - 'localhost:8000'  # Your FastAPI app
```

**Translation:** "Go to `localhost:8000/metrics` every 15 seconds and collect metrics."

### 2. What Alert Rules to Use

```yaml
rule_files:
  - 'alerts.yml'
```

**Translation:** "Use the alert rules in `alerts.yml` to detect problems."

### 3. Where to Send Alerts

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - 'alertmanager:9093'
```

**Translation:** "When an alert fires, send it to Alertmanager at port 9093."

### 4. How Often to Check

```yaml
global:
  scrape_interval: 15s      # Check every 15 seconds
  evaluation_interval: 15s   # Evaluate alerts every 15 seconds
```

**Translation:** "Check metrics every 15 seconds, and check alert rules every 15 seconds."

---

## Real-World Example

### Scenario: Rate Limiting Attack

**1. Attacker sends 1000 requests/second to your API**

**2. Your FastAPI app:**
- Blocks most requests (rate limiting works!)
- Updates metrics: `limiter_blocked_total` increases rapidly

**3. Prometheus:**
- Scrapes metrics every 15 seconds
- Sees: "Blocked requests went from 10/sec to 500/sec in 1 minute"
- Evaluates alert rule: `rate(limiter_blocked_total[5m]) > 50`
- **Alert fires:** "CriticalRateLimitViolations"

**4. Alertmanager:**
- Receives alert from Prometheus
- Routes to `oncall-critical` receiver
- Sends email to on-call engineer
- Email includes: "500 requests blocked per second - possible attack"
- Email includes runbook link: "How to investigate rate limit violations"

**5. On-Call Engineer:**
- Receives email
- Clicks runbook link
- Follows steps to investigate
- Identifies attacker IP
- Blocks IP or adjusts rate limits

**Result:** You're notified within minutes of an attack, not hours or days later.

---

## What You Can Do With Prometheus

### 1. View Metrics in Real-Time

Open http://localhost:9090 and you can:
- See current metrics values
- Graph metrics over time
- Query metrics with PromQL (Prometheus Query Language)

**Example query:**
```
rate(limiter_blocked_total[5m])
```
Shows: "How many requests are being blocked per second, averaged over 5 minutes"

### 2. Set Up Dashboards

Use Grafana (or Prometheus's built-in UI) to create dashboards showing:
- Rate limit violations over time
- Redis circuit breaker status
- Request latency percentiles
- Error rates

### 3. Get Alerted Automatically

When problems occur:
- High rate of blocked requests → Alert
- Redis circuit breaker opens → Alert
- High latency → Alert
- Too many Redis failures → Alert

### 4. Investigate Issues

When an alert fires, you can:
- Query Prometheus to see what happened
- View graphs showing when the problem started
- Compare metrics before/after the incident

---

## Key Concepts

### Scraping vs Pushing

**Scraping (Prometheus style):**
- Prometheus pulls metrics from your app
- Your app just exposes `/metrics` endpoint
- Prometheus controls when to collect data

**Pushing (other systems):**
- Your app sends metrics to monitoring system
- Your app controls when to send data

**Why scraping is better:**
- If your app crashes, Prometheus knows immediately (can't scrape)
- Prometheus controls collection frequency
- Simpler for your app (just expose endpoint)

### Time-Series Database

Prometheus stores metrics as **time-series**:
- Each metric has a timestamp
- You can query: "What was the value at 2:00 PM?"
- You can graph: "Show me the value over the last hour"

**Example:**
```
limiter_blocked_total{limit_name="auth"} @ 2025-01-15T14:00:00Z = 10
limiter_blocked_total{limit_name="auth"} @ 2025-01-15T14:01:00Z = 15
limiter_blocked_total{limit_name="auth"} @ 2025-01-15T14:02:00Z = 25
```

### Alert Rules

Alert rules are like **if-then statements**:
```
IF blocked_requests_per_second > 50 FOR 5 minutes
THEN send alert "CriticalRateLimitViolations"
```

Prometheus evaluates these rules continuously and fires alerts when conditions are met.

---

## What Happens Without Prometheus?

**Without Prometheus:**
- ❌ You don't know about problems until users complain
- ❌ No historical data to investigate issues
- ❌ Manual monitoring (checking logs, dashboards)
- ❌ Reactive (fix problems after they happen)

**With Prometheus:**
- ✅ Automatic problem detection
- ✅ Historical data for investigation
- ✅ Proactive alerts before users notice
- ✅ Data-driven decisions

---

## Summary

**Prometheus** = Health monitor that:
1. Collects metrics from your app
2. Stores historical data
3. Detects problems automatically
4. Alerts you when issues occur

**Prometheus Configuration** = Instructions that tell Prometheus:
1. Where to find your app (`localhost:8000`)
2. What alerts to watch for (`alerts.yml`)
3. Where to send alerts (`alertmanager:9093`)
4. How often to check (every 15 seconds)

**Result:** You get notified automatically when problems occur, with data to investigate and fix them quickly.

---

## Next Steps

1. **Start Prometheus:** `docker-compose -f docker-compose.monitoring.yml up -d`
2. **View metrics:** http://localhost:9090
3. **Check targets:** http://localhost:9090/targets (should show your FastAPI app)
4. **Query metrics:** Try `rate(limiter_blocked_total[5m])` in Prometheus UI

See [NEXT_STEPS_ALERTS_DEPLOYMENT.md](NEXT_STEPS_ALERTS_DEPLOYMENT.md) for deployment guide.

