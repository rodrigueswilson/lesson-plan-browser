# Alert Runbook - Rate Limiter & Redis

**Date:** January 2025  
**Purpose:** On-call remediation guide for rate limiter and Redis alerts

---

## Quick Reference

| Alert | Severity | Page | Quick Fix |
|-------|----------|------|-----------|
| HighRateLimitViolations | Warning | [Page](#high-rate-limit-violations) | Check if legitimate traffic |
| CriticalRateLimitViolations | Critical | [Page](#critical-rate-limit-violations) | Investigate attack vs misconfig |
| AuthEndpointRateLimitViolations | Warning | [Page](#auth-endpoint-rate-limit-violations) | Check for brute force |
| RedisCircuitBreakerOpen | Critical | [Page](#redis-circuit-breaker-open) | Check Redis connectivity |
| RedisCircuitBreakerOpenExtended | Critical | [Page](#redis-circuit-breaker-open-extended) | Immediate Redis investigation |
| HighRedisFailures | Warning | [Page](#high-redis-failures) | Monitor Redis health |
| CriticalRedisFailures | Critical | [Page](#critical-redis-failures) | Check Redis immediately |
| RedisFallbackOccurred | Warning | [Page](#redis-fallback-occurred) | Verify Redis status |
| RedisFallbackSustained | Critical | [Page](#redis-fallback-sustained) | Fix Redis connectivity |
| HighRateLimitLatency | Warning | [Page](#high-rate-limit-latency) | Check Redis performance |
| CriticalRateLimitLatency | Critical | [Page](#critical-rate-limit-latency) | Investigate Redis/network |
| HighRateLimitBlockRatio | Warning | [Page](#high-rate-limit-block-ratio) | Review limits |
| CriticalRateLimitBlockRatio | Critical | [Page](#critical-rate-limit-block-ratio) | Immediate investigation |

---

## Rate Limiter Alerts

### High Rate Limit Violations

**Alert:** `HighRateLimitViolations`  
**Severity:** Warning  
**Trigger:** > 10 blocked requests/sec for 5 minutes

#### Symptoms

- High number of 429 responses
- Users reporting access issues
- Metrics show `limiter_blocked_total` increasing

#### Immediate Actions (0-5 minutes)

1. **Check Alert Details:**
   ```bash
   # View alert in Prometheus
   curl http://prometheus:9090/api/v1/alerts | \
     jq '.data.alerts[] | select(.labels.alertname=="HighRateLimitViolations")'
   
   # Check current block rate
   curl 'http://prometheus:9090/api/v1/query?query=sum(rate(limiter_blocked_total[5m]))'
   ```

2. **Identify Affected Limit:**
   ```bash
   # Check which limit is being hit
   curl 'http://prometheus:9090/api/v1/query?query=sum(rate(limiter_blocked_total[5m])) by (limit_name)'
   ```

3. **Check if Legitimate Traffic:**
   ```bash
   # View recent blocked requests
   curl http://localhost:8000/api/health/redis
   
   # Check logs for patterns
   grep "429" access.log | tail -50
   ```

#### Investigation (5-15 minutes)

**Is this legitimate traffic?**
- Check if new feature/deployment increased traffic
- Verify if users are making valid requests
- Check for automated scripts/clients

**Is this an attack?**
- Check for single IP/user causing violations
- Look for unusual patterns
- Check if violations are from known users

#### Remediation

**If Legitimate Traffic:**
```python
# Temporarily increase limits
# In backend/rate_limiter.py:
AUTH_LIMIT = "100/minute"  # Increase from 30
GENERAL_LIMIT = "200/minute"  # Increase from 100
```

**If Attack:**
```bash
# Identify attack source
grep "429" access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -10

# Block IP at firewall
iptables -A INPUT -s <ATTACK_IP> -j DROP
```

**If Misconfiguration:**
- Review recent deployments
- Check rate limit configuration
- Verify endpoint classifications

#### Verification

```bash
# Check if violations decreased
curl 'http://prometheus:9090/api/v1/query?query=sum(rate(limiter_blocked_total[5m]))'

# Run sanity check
./scripts/post_remediation_sanity_check.sh
```

#### Escalation

- Escalate if violations continue after 15 minutes
- Escalate if > 50 req/s blocked (Critical threshold)
- Escalate if legitimate users affected

---

### Critical Rate Limit Violations

**Alert:** `CriticalRateLimitViolations`  
**Severity:** Critical  
**Trigger:** > 50 blocked requests/sec for 2 minutes

#### Symptoms

- Very high 429 response rate
- System may be under attack
- Legitimate users likely affected

#### Immediate Actions (0-2 minutes)

1. **Assess Severity:**
   ```bash
   # Check current block rate
   curl 'http://prometheus:9090/api/v1/query?query=sum(rate(limiter_blocked_total[5m]))'
   
   # Check which endpoints affected
   curl 'http://prometheus:9090/api/v1/query?query=sum(rate(limiter_blocked_total[5m])) by (limit_name)'
   ```

2. **Check for Attack:**
   ```bash
   # Find top violating IPs
   grep "429" access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -20
   
   # Check for single user causing issues
   grep "429" access.log | grep -oP 'user:[^"]+' | sort | uniq -c | sort -rn | head -10
   ```

#### Investigation (2-10 minutes)

**Attack Indicators:**
- Single IP causing many violations
- Unusual request patterns
- Non-existent endpoints being hit
- SQL injection attempts in logs

**Legitimate Traffic Indicators:**
- Multiple known users/IPs
- Normal request patterns
- Recent deployment/feature launch

#### Remediation

**If Attack:**

1. **Block Attack Source:**
   ```bash
   # Identify attack IPs
   ATTACK_IPS=$(grep "429" access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -5 | awk '{print $2}')
   
   # Block at firewall
   for ip in $ATTACK_IPS; do
     iptables -A INPUT -s $ip -j DROP
     echo "Blocked $ip"
   done
   ```

2. **Increase Limits Temporarily (if needed):**
   ```python
   # Emergency increase to allow legitimate traffic
   AUTH_LIMIT = "200/minute"
   GENERAL_LIMIT = "500/minute"
   ```

**If Legitimate Traffic:**

1. **Increase Limits:**
   ```python
   # Increase limits based on actual usage
   AUTH_LIMIT = "100/minute"
   GENERAL_LIMIT = "300/minute"
   ```

2. **Deploy Fix:**
   ```bash
   # Restart backend
   systemctl restart your-backend-service
   
   # Verify
   curl http://localhost:8000/api/health/redis
   ```

#### Verification

```bash
# Monitor block rate
watch -n 5 'curl -s "http://prometheus:9090/api/v1/query?query=sum(rate(limiter_blocked_total[5m]))" | jq .data.result[0].value[1]'

# Should decrease below 50 req/s
```

#### Escalation

- **Immediate:** Notify security team if attack confirmed
- **Immediate:** Notify management if system unavailable
- **15 minutes:** Escalate if issue not resolved

---

### Auth Endpoint Rate Limit Violations

**Alert:** `AuthEndpointRateLimitViolations`  
**Severity:** Warning  
**Trigger:** > 5 auth endpoint blocks/sec for 5 minutes

#### Symptoms

- High 429 responses on `/api/users/*` endpoints
- User management operations failing
- Possible brute force attempts

#### Immediate Actions (0-5 minutes)

1. **Check Auth Endpoint Blocks:**
   ```bash
   # Check auth endpoint block rate
   curl 'http://prometheus:9090/api/v1/query?query=sum(rate(limiter_blocked_total{limit_name="auth"}[5m]))'
   
   # Check which auth endpoints affected
   grep "429" access.log | grep -E "(/api/users/|/api/slots/)" | tail -50
   ```

2. **Check for Brute Force:**
   ```bash
   # Find repeated failed attempts
   grep "authorization_denied" logs/json_pipeline.log | tail -100
   
   # Check for single user being targeted
   grep "authorization_denied" logs/json_pipeline.log | \
     grep -oP '"requested_user_id":"[^"]+"' | sort | uniq -c | sort -rn | head -10
   ```

#### Investigation (5-15 minutes)

**Brute Force Indicators:**
- Repeated authorization failures for same user
- Multiple IPs trying same user ID
- Invalid user ID formats
- SQL injection attempts

**Legitimate Indicators:**
- Known users making valid requests
- Recent feature launch
- Automated scripts (if authorized)

#### Remediation

**If Brute Force:**

1. **Block Attack IPs:**
   ```bash
   # Find attack IPs
   grep "authorization_denied" logs/json_pipeline.log | \
     awk '{print $1}' | sort | uniq -c | sort -rn | head -10
   
   # Block at firewall
   iptables -A INPUT -s <ATTACK_IP> -j DROP
   ```

2. **Notify Security Team:**
   - Share attack patterns
   - Provide log exports
   - Coordinate response

**If Legitimate:**

1. **Increase Auth Limits:**
   ```python
   # In backend/rate_limiter.py
   AUTH_LIMIT = "60/minute"  # Increase from 30
   ```

2. **Review Endpoint Classification:**
   - Verify endpoints are correctly classified
   - Consider per-user rate limiting

#### Verification

```bash
# Check if auth violations decreased
curl 'http://prometheus:9090/api/v1/query?query=sum(rate(limiter_blocked_total{limit_name="auth"}[5m]))'

# Should be < 5 req/s
```

---

## Circuit Breaker Alerts

### Redis Circuit Breaker Open

**Alert:** `RedisCircuitBreakerOpen`  
**Severity:** Critical  
**Trigger:** Circuit breaker open for 1 minute

#### Symptoms

- Rate limiting degraded (per-instance, not shared)
- Redis health check failing
- Circuit breaker status shows OPEN

#### Immediate Actions (0-2 minutes)

1. **Check Circuit Breaker Status:**
   ```bash
   # Check health endpoint
   curl http://localhost:8000/api/health/redis | jq .
   
   # Should show:
   # "circuit_open": true
   # "status": "unhealthy"
   ```

2. **Check Redis Connection:**
   ```bash
   # Test Redis directly
   redis-cli ping
   # Should return: PONG
   
   # Check Redis logs
   tail -50 /var/log/redis/redis-server.log
   ```

#### Investigation (2-10 minutes)

**Common Causes:**
- Redis server down/restarting
- Network connectivity issues
- Redis overloaded
- Firewall blocking connections
- Redis authentication failure

**Check:**
```bash
# Check if Redis is running
systemctl status redis-server
# or
docker ps | grep redis

# Check Redis connectivity from backend
redis-cli -h <redis-host> -p <redis-port> ping

# Check network connectivity
telnet <redis-host> <redis-port>

# Check Redis memory
redis-cli INFO memory

# Check Redis connections
redis-cli INFO clients
```

#### Remediation

**If Redis Down:**

1. **Restart Redis:**
   ```bash
   # Systemd
   sudo systemctl restart redis-server
   
   # Docker
   docker restart redis-container
   
   # Verify
   redis-cli ping
   ```

2. **Verify Backend Reconnects:**
   ```bash
   # Wait for circuit breaker to close (up to 60 seconds)
   # Check health endpoint
   watch -n 5 'curl -s http://localhost:8000/api/health/redis | jq .circuit_breaker.circuit_open'
   ```

**If Network Issue:**

1. **Check Firewall:**
   ```bash
   # Check if port is open
   sudo iptables -L -n | grep 6379
   
   # Check security groups (if cloud)
   # AWS: Check security group rules
   # Azure: Check NSG rules
   ```

2. **Check DNS:**
   ```bash
   # Resolve Redis hostname
   nslookup <redis-host>
   dig <redis-host>
   ```

**If Redis Overloaded:**

1. **Check Memory:**
   ```bash
   redis-cli INFO memory | grep used_memory_human
   
   # If near maxmemory, check eviction policy
   redis-cli CONFIG GET maxmemory-policy
   ```

2. **Scale Redis:**
   - Increase Redis instance size
   - Enable Redis Cluster
   - Add Redis replicas

#### Verification

```bash
# Circuit breaker should close automatically
curl http://localhost:8000/api/health/redis | jq .circuit_breaker

# Should show:
# "circuit_open": false
# "status": "healthy"
```

#### Escalation

- **5 minutes:** Escalate if Redis still down
- **10 minutes:** Escalate if circuit breaker still open (see Extended alert)

---

### Redis Circuit Breaker Open Extended

**Alert:** `RedisCircuitBreakerOpenExtended`  
**Severity:** Critical  
**Trigger:** Circuit breaker open for 10+ minutes

#### Symptoms

- Circuit breaker open for extended period
- Rate limiting severely degraded
- Redis likely unavailable

#### Immediate Actions (0-2 minutes)

1. **Assess Situation:**
   ```bash
   # Check circuit breaker status
   curl http://localhost:8000/api/health/redis | jq .
   
   # Check Redis directly
   redis-cli ping
   ```

2. **Check Impact:**
   ```bash
   # Check if rate limiting still working (in-memory)
   curl http://localhost:8000/api/users/test/slots
   # Should still work, but limits are per-instance
   ```

#### Investigation (2-15 minutes)

**This is a critical situation - Redis has been down for 10+ minutes.**

**Check:**
- Redis server status
- Network connectivity
- Redis logs for errors
- Cloud provider status (if managed Redis)
- Recent deployments/changes

#### Remediation

**Immediate Actions:**

1. **Check Redis Status:**
   ```bash
   # Systemd
   sudo systemctl status redis-server
   
   # Docker
   docker ps -a | grep redis
   
   # Cloud (check provider dashboard)
   ```

2. **Restart Redis:**
   ```bash
   # If local
   sudo systemctl restart redis-server
   
   # If Docker
   docker restart redis-container
   
   # If managed (AWS ElastiCache, etc.)
   # Check provider dashboard for issues
   ```

3. **Verify Reconnection:**
   ```bash
   # Backend should reconnect automatically
   # Circuit breaker will close after successful connection
   watch -n 5 'curl -s http://localhost:8000/api/health/redis | jq .circuit_breaker.circuit_open'
   ```

**If Redis Cannot Be Restored:**

1. **Continue with In-Memory Storage:**
   - System will continue working
   - Rate limits are per-instance (not shared)
   - Monitor for issues

2. **Plan Redis Recovery:**
   - Investigate root cause
   - Fix underlying issue
   - Restore Redis service

#### Verification

```bash
# Circuit breaker should close
curl http://localhost:8000/api/health/redis | jq .circuit_breaker.circuit_open
# Should be: false

# Redis should be healthy
curl http://localhost:8000/api/health/redis | jq .status
# Should be: "healthy"
```

#### Escalation

- **Immediate:** Notify on-call engineer
- **Immediate:** Notify database/infrastructure team
- **15 minutes:** Escalate to management if not resolved

---

## Redis Health Alerts

### High Redis Failures

**Alert:** `HighRedisFailures`  
**Severity:** Warning  
**Trigger:** > 5 failures/sec for 5 minutes

#### Symptoms

- Intermittent Redis connection failures
- Circuit breaker may open soon
- Rate limiting may be affected

#### Immediate Actions (0-5 minutes)

1. **Check Failure Rate:**
   ```bash
   # Check failure rate
   curl 'http://prometheus:9090/api/v1/query?query=sum(rate(redis_failure_total[5m]))'
   
   # Check error types
   curl 'http://prometheus:9090/api/v1/query?query=sum(rate(redis_failure_total[5m])) by (error_type)'
   ```

2. **Check Redis Health:**
   ```bash
   # Check health endpoint
   curl http://localhost:8000/api/health/redis | jq .
   
   # Check circuit breaker
   curl http://localhost:8000/api/health/redis | jq .circuit_breaker.circuit_open
   ```

#### Investigation (5-15 minutes)

**Common Causes:**
- Network instability
- Redis overloaded
- Connection pool exhausted
- Timeout issues

**Check:**
```bash
# Check Redis performance
redis-cli INFO stats | grep total_commands_processed
redis-cli INFO memory | grep used_memory_human

# Check connection count
redis-cli INFO clients | grep connected_clients

# Check for timeouts
redis-cli --latency-history
```

#### Remediation

**If Network Issues:**

1. **Check Network:**
   ```bash
   # Test connectivity
   ping <redis-host>
   telnet <redis-host> <redis-port>
   
   # Check for packet loss
   mtr <redis-host>
   ```

2. **Increase Timeouts:**
   ```python
   # In backend/rate_limiter.py test_redis_connection()
   socket_connect_timeout=5  # Increase from 2
   socket_timeout=5  # Increase from 2
   ```

**If Redis Overloaded:**

1. **Scale Redis:**
   - Increase instance size
   - Add replicas
   - Enable clustering

2. **Optimize Queries:**
   - Review Lua scripts
   - Check for slow operations
   - Optimize key patterns

#### Verification

```bash
# Monitor failure rate
watch -n 5 'curl -s "http://prometheus:9090/api/v1/query?query=sum(rate(redis_failure_total[5m]))" | jq .data.result[0].value[1]'

# Should decrease below 5 failures/sec
```

---

### Critical Redis Failures

**Alert:** `CriticalRedisFailures`  
**Severity:** Critical  
**Trigger:** > 20 failures/sec for 2 minutes

#### Symptoms

- Very high Redis failure rate
- Circuit breaker likely to open soon
- Rate limiting at risk

#### Immediate Actions (0-2 minutes)

1. **Check Failure Rate:**
   ```bash
   # Check current failure rate
   curl 'http://prometheus:9090/api/v1/query?query=sum(rate(redis_failure_total[5m]))'
   
   # Check circuit breaker status
   curl http://localhost:8000/api/health/redis | jq .circuit_breaker
   ```

2. **Check Redis:**
   ```bash
   # Test Redis directly
   redis-cli ping
   
   # Check Redis status
   systemctl status redis-server
   ```

#### Investigation (2-10 minutes)

**This is critical - circuit breaker may open soon.**

**Immediate Checks:**
- Redis server status
- Network connectivity
- Redis memory usage
- Connection limits

#### Remediation

**Immediate Actions:**

1. **Restart Redis (if needed):**
   ```bash
   sudo systemctl restart redis-server
   ```

2. **Check for Overload:**
   ```bash
   # Check memory
   redis-cli INFO memory
   
   # Check connections
   redis-cli INFO clients
   
   # Check slow operations
   redis-cli SLOWLOG GET 10
   ```

3. **Prepare for Circuit Breaker:**
   - System will fall back to in-memory storage
   - Rate limits will be per-instance
   - Monitor for issues

#### Verification

```bash
# Monitor failure rate
watch -n 2 'curl -s "http://prometheus:9090/api/v1/query?query=sum(rate(redis_failure_total[5m]))" | jq .data.result[0].value[1]'

# Should decrease below 20 failures/sec
```

#### Escalation

- **5 minutes:** Escalate if failures continue
- **Immediate:** Escalate if circuit breaker opens (see Circuit Breaker alerts)

---

### Redis Fallback Occurred

**Alert:** `RedisFallbackOccurred`  
**Severity:** Warning  
**Trigger:** Any fallback to memory in 5 minutes

#### Symptoms

- Redis unavailable
- Rate limiter using in-memory storage
- Limits are per-instance (not shared)

#### Immediate Actions (0-5 minutes)

1. **Check Fallback Status:**
   ```bash
   # Check health endpoint
   curl http://localhost:8000/api/health/redis | jq .
   
   # Should show:
   # "storage_type": "memory"
   # or circuit breaker open
   ```

2. **Check Redis:**
   ```bash
   # Test Redis connection
   redis-cli ping
   
   # Check Redis status
   systemctl status redis-server
   ```

#### Investigation (5-15 minutes)

**Single Fallback:**
- May be transient network issue
- Redis may have restarted
- Check if Redis recovered

**Multiple Fallbacks:**
- Persistent Redis issue
- See "Redis Fallback Sustained" alert

#### Remediation

**If Transient:**

1. **Monitor:**
   ```bash
   # Check if Redis recovers
   watch -n 5 'redis-cli ping'
   ```

2. **Verify Reconnection:**
   ```bash
   # Backend should reconnect automatically
   curl http://localhost:8000/api/health/redis | jq .storage_type
   # Should return to "redis"
   ```

**If Persistent:**

- See "Redis Fallback Sustained" remediation

#### Verification

```bash
# Check storage type
curl http://localhost:8000/api/health/redis | jq .storage_type
# Should be "redis" if recovered
```

---

### Redis Fallback Sustained

**Alert:** `RedisFallbackSustained`  
**Severity:** Critical  
**Trigger:** > 10 fallbacks in 10 minutes

#### Symptoms

- Multiple fallbacks to memory
- Redis connectivity issues persist
- Rate limiting degraded

#### Immediate Actions (0-5 minutes)

1. **Assess Situation:**
   ```bash
   # Check fallback count
   curl http://localhost:8000/api/health/redis | jq .circuit_breaker.fallback_count
   
   # Check Redis status
   redis-cli ping
   systemctl status redis-server
   ```

2. **Check Impact:**
   ```bash
   # Rate limiting should still work (in-memory)
   curl http://localhost:8000/api/users/test/slots
   ```

#### Investigation (5-15 minutes)

**This indicates persistent Redis issues.**

**Check:**
- Redis server status
- Network connectivity
- Redis logs
- Cloud provider status (if managed)

#### Remediation

**Fix Redis Connectivity:**

1. **Restart Redis:**
   ```bash
   sudo systemctl restart redis-server
   # or
   docker restart redis-container
   ```

2. **Check Network:**
   ```bash
   # Test connectivity
   telnet <redis-host> <redis-port>
   
   # Check firewall
   sudo iptables -L -n | grep 6379
   ```

3. **Verify Reconnection:**
   ```bash
   # Backend should reconnect
   watch -n 5 'curl -s http://localhost:8000/api/health/redis | jq .storage_type'
   ```

**If Redis Cannot Be Fixed:**

1. **Continue with In-Memory:**
   - System continues working
   - Monitor for issues
   - Plan Redis recovery

2. **Document Issue:**
   - Root cause analysis
   - Recovery plan
   - Prevention measures

#### Verification

```bash
# Check storage type
curl http://localhost:8000/api/health/redis | jq .storage_type
# Should be "redis"

# Check circuit breaker
curl http://localhost:8000/api/health/redis | jq .circuit_breaker.circuit_open
# Should be false
```

#### Escalation

- **10 minutes:** Escalate if Redis not restored
- **Immediate:** Escalate if system unavailable

---

## Performance Alerts

### High Rate Limit Latency

**Alert:** `HighRateLimitLatency`  
**Severity:** Warning  
**Trigger:** p95 latency > 0.1s for 5 minutes

#### Symptoms

- Rate limit checks taking longer than expected
- May impact user experience
- Redis performance may be degraded

#### Immediate Actions (0-5 minutes)

1. **Check Latency:**
   ```bash
   # Check p95 latency
   curl 'http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95, sum(rate(rate_limit_check_duration_seconds_bucket[5m])) by (le))'
   
   # Check by limit type
   curl 'http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95, sum(rate(rate_limit_check_duration_seconds_bucket[5m])) by (le, limit_name))'
   ```

2. **Check Redis Performance:**
   ```bash
   # Check Redis latency
   redis-cli --latency-history
   
   # Check Redis stats
   redis-cli INFO stats | grep total_commands_processed
   ```

#### Investigation (5-15 minutes)

**Common Causes:**
- Redis overloaded
- Network latency
- Lua script performance
- Connection pool issues

**Check:**
```bash
# Check Redis memory
redis-cli INFO memory

# Check Redis connections
redis-cli INFO clients

# Check slow operations
redis-cli SLOWLOG GET 10
```

#### Remediation

**If Redis Overloaded:**

1. **Scale Redis:**
   - Increase instance size
   - Add replicas
   - Enable clustering

2. **Optimize:**
   - Review Lua scripts
   - Optimize key patterns
   - Increase connection pool

**If Network Latency:**

1. **Check Network:**
   ```bash
   # Test latency
   ping <redis-host>
   mtr <redis-host>
   ```

2. **Optimize Connection:**
   - Use Redis connection pooling
   - Reduce connection overhead
   - Consider Redis Cluster

#### Verification

```bash
# Monitor latency
watch -n 5 'curl -s "http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95, sum(rate(rate_limit_check_duration_seconds_bucket[5m])) by (le))" | jq .data.result[0].value[1]'

# Should be < 0.1s
```

---

### Critical Rate Limit Latency

**Alert:** `CriticalRateLimitLatency`  
**Severity:** Critical  
**Trigger:** p95 latency > 0.5s for 2 minutes

#### Symptoms

- Very high rate limit check latency
- User experience impacted
- System may be degraded

#### Immediate Actions (0-2 minutes)

1. **Check Latency:**
   ```bash
   # Check current p95 latency
   curl 'http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95, sum(rate(rate_limit_check_duration_seconds_bucket[5m])) by (le))'
   ```

2. **Check Redis:**
   ```bash
   # Test Redis latency
   redis-cli --latency
   
   # Check Redis status
   redis-cli INFO stats
   ```

#### Investigation (2-10 minutes)

**This is critical - latency is very high.**

**Immediate Checks:**
- Redis server performance
- Network connectivity
- Redis memory/CPU usage
- Connection pool status

#### Remediation

**Immediate Actions:**

1. **Check Redis Performance:**
   ```bash
   # Check memory
   redis-cli INFO memory
   
   # Check CPU (if available)
   top -p $(pgrep redis-server)
   
   # Check slow operations
   redis-cli SLOWLOG GET 20
   ```

2. **Restart Redis (if needed):**
   ```bash
   sudo systemctl restart redis-server
   ```

3. **Scale Redis:**
   - Increase instance size immediately
   - Add replicas
   - Enable clustering

#### Verification

```bash
# Monitor latency
watch -n 2 'curl -s "http://prometheus:9090/api/v1/query?query=histogram_quantile(0.95, sum(rate(rate_limit_check_duration_seconds_bucket[5m])) by (le))" | jq .data.result[0].value[1]'

# Should decrease below 0.5s
```

#### Escalation

- **5 minutes:** Escalate if latency not improving
- **Immediate:** Escalate if system unavailable

---

## Ratio Alerts

### High Rate Limit Block Ratio

**Alert:** `HighRateLimitBlockRatio`  
**Severity:** Warning  
**Trigger:** > 10% of requests blocked for 5 minutes

#### Symptoms

- High percentage of requests being blocked
- May indicate limits too strict
- Or attack in progress

#### Immediate Actions (0-5 minutes)

1. **Check Block Ratio:**
   ```bash
   # Calculate block ratio
   curl 'http://prometheus:9090/api/v1/query?query=sum(rate(limiter_blocked_total[5m])) / sum(rate(limiter_allowed_total[5m]) + rate(limiter_blocked_total[5m]))'
   
   # Check by limit type
   curl 'http://prometheus:9090/api/v1/query?query=sum(rate(limiter_blocked_total[5m])) by (limit_name) / sum(rate(limiter_allowed_total[5m]) + rate(limiter_blocked_total[5m])) by (limit_name)'
   ```

2. **Check if Legitimate:**
   ```bash
   # Check blocked requests
   grep "429" access.log | tail -50
   
   # Check for attack patterns
   grep "429" access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -10
   ```

#### Investigation (5-15 minutes)

**Is this legitimate traffic?**
- Check if new feature increased traffic
- Verify users are making valid requests
- Check for automated scripts

**Is this an attack?**
- Check for single IP/user
- Look for unusual patterns
- Check for brute force attempts

#### Remediation

**If Legitimate:**

1. **Increase Limits:**
   ```python
   # Review actual usage and increase limits
   AUTH_LIMIT = "60/minute"  # Increase from 30
   GENERAL_LIMIT = "200/minute"  # Increase from 100
   ```

2. **Review Limits:**
   - Analyze usage patterns
   - Adjust limits based on data
   - Consider per-user limits

**If Attack:**

- See "Critical Rate Limit Violations" remediation

#### Verification

```bash
# Check block ratio
watch -n 5 'curl -s "http://prometheus:9090/api/v1/query?query=sum(rate(limiter_blocked_total[5m])) / sum(rate(limiter_allowed_total[5m]) + rate(limiter_blocked_total[5m]))" | jq .data.result[0].value[1]'

# Should be < 0.1 (10%)
```

---

### Critical Rate Limit Block Ratio

**Alert:** `CriticalRateLimitBlockRatio`  
**Severity:** Critical  
**Trigger:** > 30% of requests blocked for 2 minutes

#### Symptoms

- Very high percentage blocked
- System likely under attack
- Or severe misconfiguration

#### Immediate Actions (0-2 minutes)

1. **Assess Severity:**
   ```bash
   # Check block ratio
   curl 'http://prometheus:9090/api/v1/query?query=sum(rate(limiter_blocked_total[5m])) / sum(rate(limiter_allowed_total[5m]) + rate(limiter_blocked_total[5m]))'
   ```

2. **Check for Attack:**
   ```bash
   # Find top violating IPs
   grep "429" access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -20
   ```

#### Investigation (2-10 minutes)

**This is critical - 30%+ of requests blocked.**

**Immediate Checks:**
- Attack indicators
- Legitimate traffic patterns
- Recent deployments
- Configuration changes

#### Remediation

**If Attack:**

- See "Critical Rate Limit Violations" remediation
- Block attack sources immediately
- Notify security team

**If Legitimate:**

1. **Emergency Increase:**
   ```python
   # Temporarily increase limits significantly
   AUTH_LIMIT = "200/minute"
   GENERAL_LIMIT = "500/minute"
   ```

2. **Deploy Immediately:**
   ```bash
   # Restart backend
   systemctl restart your-backend-service
   ```

3. **Investigate Root Cause:**
   - Why are limits too strict?
   - What changed?
   - How to fix permanently?

#### Verification

```bash
# Monitor block ratio
watch -n 2 'curl -s "http://prometheus:9090/api/v1/query?query=sum(rate(limiter_blocked_total[5m])) / sum(rate(limiter_allowed_total[5m]) + rate(limiter_blocked_total[5m]))" | jq .data.result[0].value[1]'

# Should decrease below 0.3 (30%)
```

#### Escalation

- **Immediate:** Escalate if attack confirmed
- **5 minutes:** Escalate if not resolved
- **Immediate:** Escalate if system unavailable

---

## General Troubleshooting

### Common Commands

```bash
# Check all alerts
curl http://prometheus:9090/api/v1/alerts | jq '.data.alerts[] | {alertname, state, severity}'

# Check specific metric
curl 'http://prometheus:9090/api/v1/query?query=<metric_name>'

# Check Redis health
curl http://localhost:8000/api/health/redis | jq .

# Check rate limit status
curl http://localhost:8000/api/health/redis | jq .circuit_breaker

# View metrics
curl http://localhost:8000/metrics | grep <metric_name>
```

### Emergency Contacts

- **On-Call Engineer:** [Contact]
- **Security Team:** [Contact]
- **Database/Infrastructure:** [Contact]
- **Management:** [Contact]

---

## Related Documents

- `docs/security/INCIDENT_RESPONSE_CHECKLIST.md` - General incident response
- `docs/security/ROLLBACK_PROCEDURES.md` - Rollback procedures
- `prometheus/alerts.yml` - Alert definitions
- `docs/security/PROMETHEUS_METRICS.md` - Metrics documentation

---

**Last Updated:** January 2025  
**Status:** Production Ready ✅

