# Rate Limit Handling for Parallel Processing

## Overview
This document outlines how the parallel processing system will handle OpenAI API rate limits for `gpt-5-mini` model.

## OpenAI API Limits for gpt-5-mini

### Rate Limits by Tier

| Tier | RPM (Requests/Min) | TPM (Tokens/Min) | Batch Queue Limit |
|------|-------------------|------------------|-------------------|
| 1    | 500               | 500,000          | 5,000,000         |
| 2    | 5,000             | 2,000,000        | 20,000,000        |
| 3    | 5,000             | 4,000,000        | 40,000,000        |
| 4    | 10,000            | 10,000,000       | 1,000,000,000     |
| 5    | 30,000            | 180,000,000      | 15,000,000,000    |

**Note**: Your tier is automatically determined by usage and spending. Most users start at Tier 1.

### Typical Usage Per Slot
- **Input tokens**: ~8,000-12,000 (prompt + content)
- **Output tokens**: ~15,000-20,000 (full lesson plan)
- **Total per slot**: ~25,000-32,000 tokens
- **Time per request**: ~2 minutes

### Parallel Processing Impact
- **5 slots in parallel** (typical use case): 5 simultaneous requests
- **Total tokens**: ~125,000-160,000 tokens
- **Time**: ~2 minutes (vs ~10 minutes sequential)
- **4 slots in parallel**: 4 simultaneous requests, ~100,000-128,000 tokens

## Rate Limit Challenges

### 1. Requests Per Minute (RPM)
- **Tier 1**: 500 RPM = ~8 requests/second
- **5 parallel requests** (typical use case): Well within limit (even Tier 1)
- **Risk**: Low (unless processing many batches simultaneously)

### 2. Tokens Per Minute (TPM)
- **Tier 1**: 500,000 TPM = ~8,333 tokens/second
- **5 slots** (typical): ~125,000-160,000 tokens total
- **Time**: ~2 minutes
- **Rate**: ~62,500-80,000 tokens/minute (well within Tier 1 limit of 500K TPM)
- **4 slots**: ~100,000-128,000 tokens total, ~50,000-64,000 tokens/minute
- **Risk**: Low for 5 slots, but could be an issue with 8+ slots

### 3. Concurrent Request Limits
- OpenAI doesn't explicitly limit concurrent requests
- But rate limits apply to all requests combined
- **Risk**: Medium (need to track aggregate usage)

## Implementation Strategy

### Phase 1: Rate Limit Detection and Handling

#### 1.1 Detect Rate Limit Errors
```python
from openai import RateLimitError, APIError

def _call_llm_with_retry(self, prompt: str, max_retries: int = 3) -> Tuple[str, Dict[str, int]]:
    """Call LLM with automatic rate limit handling."""
    for attempt in range(max_retries):
        try:
            return self._call_openai_chat_completion(prompt)
        except RateLimitError as e:
            # Extract retry-after header if available
            retry_after = self._extract_retry_after(e)
            wait_time = retry_after or (2 ** attempt)  # Exponential backoff
            
            logger.warning(
                "openai_rate_limit_retry",
                extra={
                    "attempt": attempt + 1,
                    "max_retries": max_retries,
                    "wait_time": wait_time,
                    "retry_after": retry_after,
                }
            )
            
            if attempt < max_retries - 1:
                time.sleep(wait_time)
                continue
            else:
                raise
        except APIError as e:
            # Handle other API errors
            if "429" in str(e) or "rate limit" in str(e).lower():
                # Rate limit error without proper exception type
                wait_time = 2 ** attempt
                logger.warning("openai_rate_limit_detected", extra={"wait_time": wait_time})
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                    continue
            raise
```

#### 1.2 Extract Retry-After Header
```python
def _extract_retry_after(self, error: Exception) -> Optional[float]:
    """Extract retry-after time from rate limit error."""
    if hasattr(error, "response") and error.response:
        retry_after = error.response.headers.get("retry-after")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
    return None
```

### Phase 2: Token Usage Tracking

#### 2.1 Token Usage Tracker
```python
from collections import deque
from threading import Lock
import time

class TokenUsageTracker:
    """Track token usage to prevent exceeding TPM limits."""
    
    def __init__(self, tpm_limit: int = 500_000, window_seconds: int = 60):
        self.tpm_limit = tpm_limit
        self.window_seconds = window_seconds
        self.usage_history = deque()  # List of (timestamp, tokens) tuples
        self.lock = Lock()
    
    def record_usage(self, tokens: int):
        """Record token usage."""
        with self.lock:
            now = time.time()
            # Remove old entries outside window
            cutoff = now - self.window_seconds
            while self.usage_history and self.usage_history[0][0] < cutoff:
                self.usage_history.popleft()
            
            # Add new usage
            self.usage_history.append((now, tokens))
    
    def get_current_usage(self) -> int:
        """Get total tokens used in current window."""
        with self.lock:
            now = time.time()
            cutoff = now - self.window_seconds
            return sum(
                tokens for timestamp, tokens in self.usage_history
                if timestamp >= cutoff
            )
    
    def can_make_request(self, estimated_tokens: int) -> Tuple[bool, Optional[float]]:
        """
        Check if request can be made without exceeding TPM limit.
        
        Returns:
            (can_proceed, wait_time_if_needed)
        """
        with self.lock:
            current_usage = self.get_current_usage()
            projected_usage = current_usage + estimated_tokens
            
            if projected_usage <= self.tpm_limit:
                return True, None
            
            # Need to wait - calculate wait time
            if self.usage_history:
                oldest_timestamp = self.usage_history[0][0]
                wait_time = (oldest_timestamp + self.window_seconds) - time.time()
                return False, max(0, wait_time)
            
            return True, None
```

#### 2.2 Estimate Token Usage
```python
def _estimate_tokens(self, prompt: str, max_output_tokens: int) -> int:
    """Estimate total tokens for a request."""
    # Rough estimation: ~4 characters per token
    input_tokens = len(prompt) // 4
    output_tokens = max_output_tokens  # Use max_completion_tokens
    return input_tokens + output_tokens
```

### Phase 3: Request Throttling

#### 3.1 Request Rate Limiter
```python
from collections import deque
from threading import Lock
import time

class RequestRateLimiter:
    """Limit request rate to stay within RPM limits."""
    
    def __init__(self, rpm_limit: int = 500, window_seconds: int = 60):
        self.rpm_limit = rpm_limit
        self.window_seconds = window_seconds
        self.request_times = deque()
        self.lock = Lock()
    
    def wait_if_needed(self):
        """Wait if necessary to stay within RPM limit."""
        with self.lock:
            now = time.time()
            cutoff = now - self.window_seconds
            
            # Remove old requests
            while self.request_times and self.request_times[0] < cutoff:
                self.request_times.popleft()
            
            # Check if we're at limit
            if len(self.request_times) >= self.rpm_limit:
                # Wait until oldest request expires
                oldest_time = self.request_times[0]
                wait_time = (oldest_time + self.window_seconds) - now
                if wait_time > 0:
                    time.sleep(wait_time)
                    # Remove expired requests after wait
                    now = time.time()
                    cutoff = now - self.window_seconds
                    while self.request_times and self.request_times[0] < cutoff:
                        self.request_times.popleft()
            
            # Record this request
            self.request_times.append(time.time())
```

### Phase 4: Parallel Processing with Rate Limits

#### 4.1 Semaphore-Based Concurrency Control
```python
import asyncio
from asyncio import Semaphore

class ParallelLLMProcessor:
    """Process multiple LLM calls in parallel with rate limiting."""
    
    def __init__(
        self,
        llm_service: LLMService,
        max_concurrent: int = 5,  # Typical use case: 5 slots
        tpm_limit: int = 500_000,
        rpm_limit: int = 500,
    ):
        self.llm_service = llm_service
        self.semaphore = Semaphore(max_concurrent)
        self.token_tracker = TokenUsageTracker(tpm_limit)
        self.request_limiter = RequestRateLimiter(rpm_limit)
    
    async def process_slot(
        self,
        context: SlotProcessingContext,
        week_of: str,
        plan_id: Optional[str],
    ) -> SlotProcessingContext:
        """Process a single slot with rate limiting."""
        async with self.semaphore:
            # Wait for request rate limit
            await asyncio.to_thread(self.request_limiter.wait_if_needed)
            
            # Estimate tokens and check TPM limit
            estimated_tokens = self.llm_service._estimate_tokens(
                context.extracted_content,
                self.llm_service.max_completion_tokens
            )
            
            can_proceed, wait_time = self.token_tracker.can_make_request(estimated_tokens)
            if not can_proceed and wait_time:
                logger.info(
                    "waiting_for_tpm_limit",
                    extra={"wait_time": wait_time, "estimated_tokens": estimated_tokens}
                )
                await asyncio.sleep(wait_time)
            
            # Make LLM call with retry
            try:
                success, lesson_json, error = await asyncio.to_thread(
                    self.llm_service.transform_lesson,
                    primary_content=context.extracted_content,
                    grade=context.slot["grade"],
                    subject=context.slot["subject"],
                    week_of=week_of,
                    plan_id=plan_id,
                    available_days=context.available_days,
                )
                
                # Record actual token usage
                if success and lesson_json:
                    actual_tokens = lesson_json.get("_usage", {}).get("tokens_total", estimated_tokens)
                    self.token_tracker.record_usage(actual_tokens)
                
                context.lesson_json = lesson_json if success else None
                context.error = error
                
            except Exception as e:
                context.error = str(e)
                logger.error("llm_call_failed", extra={"error": str(e)})
            
            return context
```

#### 4.2 Adaptive Concurrency
```python
class AdaptiveConcurrencyController:
    """Dynamically adjust concurrency based on rate limit errors."""
    
    def __init__(self, initial_concurrent: int = 5, min_concurrent: int = 1, max_concurrent: int = 8):
        self.current_concurrent = initial_concurrent
        self.min_concurrent = min_concurrent
        self.max_concurrent = max_concurrent
        self.rate_limit_errors = 0
        self.successful_requests = 0
        self.lock = Lock()
    
    def get_concurrent_limit(self) -> int:
        """Get current concurrency limit."""
        with self.lock:
            return self.current_concurrent
    
    def record_rate_limit_error(self):
        """Record rate limit error and reduce concurrency."""
        with self.lock:
            self.rate_limit_errors += 1
            if self.rate_limit_errors >= 3:
                # Reduce concurrency
                self.current_concurrent = max(
                    self.min_concurrent,
                    self.current_concurrent - 1
                )
                self.rate_limit_errors = 0
                logger.warning(
                    "reducing_concurrency",
                    extra={"new_limit": self.current_concurrent}
                )
    
    def record_success(self):
        """Record successful request and potentially increase concurrency."""
        with self.lock:
            self.successful_requests += 1
            if self.successful_requests >= 10 and self.current_concurrent < self.max_concurrent:
                # Increase concurrency
                self.current_concurrent = min(
                    self.max_concurrent,
                    self.current_concurrent + 1
                )
                self.successful_requests = 0
                logger.info(
                    "increasing_concurrency",
                    extra={"new_limit": self.current_concurrent}
                )
```

## Configuration

### Environment Variables
```python
# backend/config.py
class Settings(BaseSettings):
    # OpenAI Rate Limits (default to Tier 1)
    OPENAI_RPM_LIMIT: int = Field(
        default=500,
        description="OpenAI requests per minute limit (based on tier)"
    )
    OPENAI_TPM_LIMIT: int = Field(
        default=500_000,
        description="OpenAI tokens per minute limit (based on tier)"
    )
    
    # Parallel Processing
    PARALLEL_LLM_PROCESSING: bool = Field(
        default=True,
        description="Enable parallel LLM API calls"
    )
    MAX_CONCURRENT_LLM_REQUESTS: int = Field(
        default=5,
        description="Maximum concurrent LLM requests (typical: 5 slots, adjust based on tier)"
    )
    
    # Rate Limit Handling
    RATE_LIMIT_RETRY_ATTEMPTS: int = Field(
        default=3,
        description="Number of retry attempts for rate limit errors"
    )
    RATE_LIMIT_BACKOFF_MULTIPLIER: float = Field(
        default=2.0,
        description="Exponential backoff multiplier"
    )
```

## Implementation Plan

### Step 1: Add Rate Limit Error Handling
- Update `_call_llm` to catch `RateLimitError`
- Add exponential backoff with retry-after header support
- Log rate limit events

### Step 2: Add Token Usage Tracking
- Implement `TokenUsageTracker` class
- Track token usage per request
- Check TPM limits before making requests

### Step 3: Add Request Rate Limiting
- Implement `RequestRateLimiter` class
- Enforce RPM limits
- Queue requests if needed

### Step 4: Integrate with Parallel Processing
- Add `ParallelLLMProcessor` wrapper
- Use semaphore for concurrency control
- Coordinate rate limiting across parallel requests

### Step 5: Add Adaptive Concurrency
- Implement `AdaptiveConcurrencyController`
- Adjust concurrency based on rate limit errors
- Monitor and log adjustments

## Testing Strategy

### Unit Tests
- Test rate limit error detection
- Test token usage tracking
- Test request rate limiting
- Test exponential backoff

### Integration Tests
- Test parallel processing with rate limits
- Test adaptive concurrency adjustment
- Test TPM limit enforcement
- Test RPM limit enforcement

### Load Tests
- Test with 4 slots (typical use case)
- Test with 8 slots (stress test)
- Test with Tier 1 limits (most restrictive)
- Test with Tier 2+ limits (higher throughput)

## Monitoring

### Metrics to Track
- Rate limit errors per minute
- Token usage per minute
- Request rate per minute
- Average wait time for rate limits
- Concurrency adjustments
- Successful vs failed requests

### Alerts
- Rate limit errors > 5 per minute
- Token usage > 80% of limit
- Request rate > 80% of limit
- Concurrency reduced below minimum

## Recommendations

### For Tier 1 Users (500 RPM, 500K TPM)
- **Max concurrent**: 5 slots (typical use case, safe)
- **Can handle**: 5 slots in parallel easily, up to 8 slots if needed
- **Risk**: Low for typical use cases (5 slots)

### For Tier 2+ Users (5K+ RPM, 2M+ TPM)
- **Max concurrent**: 8-16 slots (depending on tier)
- **Can handle**: Many slots in parallel
- **Risk**: Very low

### Best Practices
1. **Start with typical use case**: Use 5 concurrent requests (typical: 5 slots)
2. **Monitor usage**: Track token and request rates
3. **Adapt dynamically**: Adjust concurrency based on errors
4. **Respect limits**: Always stay below 80% of limits
5. **Handle errors gracefully**: Retry with backoff

## Fallback Strategy

If rate limits are consistently hit:
1. Reduce concurrent requests automatically
2. Fall back to sequential processing
3. Queue requests and process when limits allow
4. Notify user of delays

## Summary

The parallel processing system will:
- ✅ Handle rate limit errors with exponential backoff
- ✅ Track token usage to prevent TPM limit violations
- ✅ Throttle requests to stay within RPM limits
- ✅ Coordinate rate limiting across parallel requests
- ✅ Adapt concurrency based on rate limit errors
- ✅ Provide clear error messages and logging
- ✅ Work safely with Tier 1 limits (5 slots in parallel - typical use case)
