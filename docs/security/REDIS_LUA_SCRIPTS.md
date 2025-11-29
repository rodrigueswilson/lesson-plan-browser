# Redis Lua Scripts for Atomic Rate Limiting

**Date:** January 2025  
**Purpose:** Atomic Lua scripts for race-condition-free rate limiting operations

---

## Overview

This document describes the Lua scripts used for atomic Redis operations in rate limiting. These scripts ensure that increment and expiration operations happen atomically, preventing race conditions in high-concurrency scenarios.

---

## Lua Scripts

### 1. Rate Limit Check Script

**Purpose:** Atomically check current count, increment if under limit, and set expiration.

**Script:**
```lua
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local current = redis.call('GET', key)

if current == false then
    -- Key doesn't exist, create it with count=1
    redis.call('SET', key, 1)
    redis.call('EXPIRE', key, window)
    return {1, window, 0}
else
    local count = tonumber(current)
    if count >= limit then
        -- Limit exceeded, return TTL
        local ttl = redis.call('TTL', key)
        return {count, ttl, 1}
    else
        -- Increment and return
        local new_count = redis.call('INCR', key)
        -- Refresh TTL if needed (in case key was about to expire)
        redis.call('EXPIRE', key, window)
        return {new_count, window, 0}
    end
end
```

**Usage:**
```python
result = script(keys=[redis_key], args=[limit, window])
current_count, ttl, limit_exceeded = result
```

**Returns:**
- `current_count`: Current request count
- `ttl`: Time until reset in seconds
- `limit_exceeded`: 1 if limit exceeded, 0 otherwise

### 2. Rate Limit Increment Script

**Purpose:** Simple atomic increment with expiration.

**Script:**
```lua
local key = KEYS[1]
local window = tonumber(ARGV[1])
local current = redis.call('INCR', key)
if current == 1 then
    -- First increment, set expiration
    redis.call('EXPIRE', key, window)
end
return current
```

**Usage:**
```python
count = script(keys=[redis_key], args=[window])
```

### 3. Rate Limit Status Script

**Purpose:** Get current count and TTL without incrementing.

**Script:**
```lua
local key = KEYS[1]
local current = redis.call('GET', key)
if current == false then
    return {0, -1}
else
    local count = tonumber(current)
    local ttl = redis.call('TTL', key)
    return {count, ttl}
end
```

**Usage:**
```python
count, ttl = script(keys=[redis_key])
```

---

## Benefits of Lua Scripts

### Atomic Operations

- **Single Command:** Increment + expire happens in one atomic operation
- **No Race Conditions:** Prevents concurrent requests from bypassing limits
- **Consistent State:** Ensures count and expiration are always in sync

### Performance

- **Server-Side Execution:** Scripts run on Redis server (low latency)
- **Reduced Round-Trips:** Single command instead of multiple operations
- **Efficient:** Scripts are cached by Redis after first load

### Reliability

- **Transaction-Like:** Scripts execute atomically (all or nothing)
- **Error Handling:** Scripts handle edge cases (key doesn't exist, etc.)
- **TTL Refresh:** Automatically refreshes expiration on increment

---

## Loading Scripts into Redis

### Option 1: Register Scripts (Recommended)

```python
import redis

client = redis.Redis(...)

# Register script (cached server-side)
script = client.register_script(RATE_LIMIT_CHECK_SCRIPT)

# Use script
result = script(keys=["rate_limit:user:123"], args=[30, 60])
```

### Option 2: Load Script on Each Use

```python
import redis

client = redis.Redis(...)

# Execute script directly
result = client.eval(RATE_LIMIT_CHECK_SCRIPT, 1, "rate_limit:user:123", 30, 60)
```

### Option 3: Preload Scripts (Production)

```bash
# Load script into Redis at startup
redis-cli SCRIPT LOAD "$(cat rate_limit_check.lua)"
# Returns: SHA1 hash

# Use SHA1 hash for faster execution
redis-cli EVALSHA <sha1_hash> 1 "rate_limit:user:123" 30 60
```

---

## Key Naming Convention

### Format

```
{env}:{service}:{prefix}:{limit_name}:{identifier}
```

### Examples

```
prod:lesson_planner:rate_limit:auth:user:abc123
staging:lesson_planner:rate_limit:general:192.168.1.1
dev:lesson_planner:rate_limit:batch:user:xyz789
```

### Benefits

- **Environment Isolation:** Different keys per environment
- **Service Namespacing:** Prevents conflicts with other services
- **Easy Debugging:** Clear key structure for troubleshooting
- **Safe Key Sweeps:** Can delete all keys for a service/environment

---

## Circuit Breaker Integration

### How It Works

1. **Monitor Failures:** Track Redis connection failures
2. **Open Circuit:** After threshold failures, open circuit breaker
3. **Fail Fast:** Return error immediately when circuit is open
4. **Half-Open:** After timeout, attempt reconnection
5. **Close Circuit:** On successful connection, close circuit

### Configuration

```python
REDIS_CIRCUIT_BREAKER_THRESHOLD = 5  # Failures before opening
REDIS_CIRCUIT_BREAKER_TIMEOUT = 60   # Seconds to keep open
```

### Monitoring

Check circuit breaker status via health endpoint:

```bash
curl http://localhost:8000/api/health/redis
```

Response includes:
```json
{
  "circuit_breaker": {
    "circuit_open": false,
    "connection_failures": 0,
    "last_failure_time": null,
    "circuit_open_until": null,
    "fallback_count": 0
  }
}
```

---

## Redis Memory Policy

### Recommended Configuration

For rate limiting keys, use `volatile-lru` eviction policy:

```bash
# Set max memory
redis-cli CONFIG SET maxmemory 256mb

# Set eviction policy
redis-cli CONFIG SET maxmemory-policy volatile-lru
```

### Why `volatile-lru`?

- **Preserves Non-Expiring Keys:** Only evicts keys with TTL
- **LRU Eviction:** Removes least recently used expired keys first
- **Automatic Cleanup:** Redis handles expired key cleanup
- **Memory Safety:** Prevents Redis from running out of memory

### Monitoring Memory

```bash
# Check memory usage
redis-cli INFO memory

# Check evicted keys count
redis-cli INFO stats | grep evicted_keys

# Check key count
redis-cli DBSIZE
```

---

## Testing Lua Scripts

### Manual Testing

```bash
# Load script
redis-cli SCRIPT LOAD "$(cat backend/redis_lua_scripts.py | grep -A 20 'RATE_LIMIT_CHECK_SCRIPT')"

# Test script
redis-cli EVAL "
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local current = redis.call('GET', key)
if current == false then
    redis.call('SET', key, 1)
    redis.call('EXPIRE', key, window)
    return {1, window, 0}
else
    local count = tonumber(current)
    if count >= limit then
        local ttl = redis.call('TTL', key)
        return {count, ttl, 1}
    else
        local new_count = redis.call('INCR', key)
        redis.call('EXPIRE', key, window)
        return {new_count, window, 0}
    end
end
" 1 "test:key" 30 60
```

### Unit Tests

See `tests/test_rate_limiter_redis.py` for examples.

---

## Production Checklist

- [ ] Lua scripts loaded into Redis
- [ ] Key naming convention configured (`env:service:prefix`)
- [ ] Circuit breaker thresholds set appropriately
- [ ] Redis memory policy set to `volatile-lru`
- [ ] Max memory configured
- [ ] Health endpoint monitoring circuit breaker
- [ ] Alerts configured for circuit breaker opens
- [ ] Fallback behavior tested

---

## Related Documents

- `backend/redis_lua_scripts.py` - Lua script definitions
- `backend/redis_storage.py` - Custom Redis storage wrapper
- `docs/security/REDIS_RATE_LIMITER_MIGRATION.md` - Migration guide
- `docs/security/REDIS_MIGRATION_SUMMARY.md` - Quick reference

---

**Last Updated:** January 2025  
**Status:** Production Ready ✅

