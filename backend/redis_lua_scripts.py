"""
Lua scripts for atomic Redis operations in rate limiting.

These scripts ensure atomic increment+expire operations to prevent race conditions
in high-concurrency scenarios.
"""

# Lua script for atomic rate limit check and increment
# Returns: [current_count, ttl, limit_exceeded]
# - current_count: current request count
# - ttl: time until reset in seconds
# - limit_exceeded: 1 if limit exceeded, 0 otherwise
RATE_LIMIT_CHECK_SCRIPT = """
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
"""

# Lua script for atomic increment with expiration
# Used for simpler cases where we just need to increment
RATE_LIMIT_INCREMENT_SCRIPT = """
local key = KEYS[1]
local window = tonumber(ARGV[1])
local current = redis.call('INCR', key)
if current == 1 then
    -- First increment, set expiration
    redis.call('EXPIRE', key, window)
end
return current
"""

# Lua script to get current count and TTL without incrementing
RATE_LIMIT_STATUS_SCRIPT = """
local key = KEYS[1]
local current = redis.call('GET', key)
if current == false then
    return {0, -1}
else
    local count = tonumber(current)
    local ttl = redis.call('TTL', key)
    return {count, ttl}
end
"""

