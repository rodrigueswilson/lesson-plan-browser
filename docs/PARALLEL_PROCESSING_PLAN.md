# Parallel Processing Implementation Plan

## Overview
Implement parallel AI processing for multiple lesson plan slots while keeping file operations sequential to prevent locking issues.

## Current Architecture

### Sequential Processing Flow
```
For each slot (1..N):
  1. Resolve primary file (sequential - file I/O)
  2. Open DOCX file (sequential - file I/O with retry logic)
  3. Extract content (sequential - file I/O)
  4. Call LLM API (sequential - HTTP request, ~2 min per slot)
  5. Process results (sequential - data processing)
```

**Current Time**: ~10 minutes for 5 slots (2 min × 5 slots), ~8 minutes for 4 slots

### Problem
- LLM API calls are independent and can run in parallel
- File operations must remain sequential to avoid locking
- Progress tracking needs to work with parallel operations

## Proposed Architecture

### Two-Phase Processing

#### Phase 1: Sequential File Operations (Unchanged)
```
For each slot (1..N):
  1. Resolve primary file
  2. Open DOCX file (with retry logic)
  3. Extract content
  4. Store extracted content for Phase 2
```

**Time**: ~30-40 seconds for 5 slots (unchanged)

#### Phase 2: Parallel LLM Processing
```
Gather all extracted content from Phase 1
Launch N parallel LLM API calls using asyncio.gather()
  - Each call runs in asyncio.to_thread() (non-blocking)
  - Progress callbacks update shared progress tracker
Wait for all to complete
Process results sequentially (if needed)
```

**Time**: ~2 minutes for 5 slots (parallel, vs ~10 min sequential)

### Total Time Reduction
- **Before**: ~10 minutes (5 slots sequential)
- **After**: ~2.5 minutes (30s file ops + 2min parallel LLM)
- **Improvement**: ~75% faster
- **4 slots**: ~8 minutes → ~2.5 minutes (~70% faster)

## Implementation Details

### 1. Data Structure Changes

#### New: Slot Processing Context
```python
@dataclass
class SlotProcessingContext:
    """Context for processing a single slot across phases."""
    slot: Dict[str, Any]
    slot_index: int
    total_slots: int
    primary_file: Optional[str] = None
    extracted_content: Optional[str] = None
    available_days: Optional[List[str]] = None
    lesson_json: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
```

### 2. Modified Processing Flow

#### Phase 1: Extract Content (Sequential)
```python
async def _extract_slot_content(
    self,
    context: SlotProcessingContext,
    week_of: str,
    week_folder_path: Optional[str],
    user_base_path: Optional[str],
    plan_id: Optional[str],
) -> SlotProcessingContext:
    """Extract content from DOCX file (sequential, file I/O)."""
    # 1. Resolve primary file
    # 2. Open DOCX with retry
    # 3. Extract content
    # 4. Store in context.extracted_content
    return context
```

#### Phase 2: Transform with LLM (Parallel)
```python
async def _transform_slot_with_llm(
    self,
    context: SlotProcessingContext,
    week_of: str,
    provider: str,
    plan_id: Optional[str],
) -> SlotProcessingContext:
    """Transform content with LLM (can run in parallel)."""
    # Call LLM service
    # Store result in context.lesson_json
    return context

async def _process_slots_parallel_llm(
    self,
    contexts: List[SlotProcessingContext],
    week_of: str,
    provider: str,
    plan_id: Optional[str],
) -> List[SlotProcessingContext]:
    """Process all slots' LLM calls in parallel."""
    tasks = [
        self._transform_slot_with_llm(ctx, week_of, provider, plan_id)
        for ctx in contexts
    ]
    return await asyncio.gather(*tasks)
```

### 3. Progress Tracking Updates

#### Challenge
- Multiple slots processing simultaneously
- Need to aggregate progress from all slots
- Maintain accurate overall progress percentage

#### Solution
```python
def update_parallel_progress(
    self,
    plan_id: str,
    slot_progresses: Dict[int, int],  # slot_index -> progress (0-100)
    total_slots: int,
    phase: str,  # "extracting" or "transforming"
):
    """Update progress based on multiple parallel operations."""
    # Calculate average progress across all slots
    avg_progress = sum(slot_progresses.values()) / len(slot_progresses)
    
    # Map to overall progress range
    if phase == "extracting":
        # Phase 1: 0-20% of total
        overall = int(avg_progress * 0.20)
    else:  # transforming
        # Phase 2: 20-80% of total
        overall = 20 + int(avg_progress * 0.60)
    
    progress_tracker.update(plan_id, "processing", overall, message)
```

### 4. Configuration Flag

#### Add to `backend/config.py`
```python
# Parallel Processing
PARALLEL_LLM_PROCESSING: bool = Field(
    default=True,
    description="Enable parallel LLM API calls for multiple slots (faster but uses more API quota)"
)
```

#### Usage
```python
if settings.PARALLEL_LLM_PROCESSING and len(slots) > 1:
    # Use parallel processing
    contexts = await self._process_slots_parallel_llm(...)
else:
    # Fall back to sequential (current behavior)
    for context in contexts:
        context = await self._transform_slot_with_llm(...)
```

### 5. Error Handling

#### Parallel Error Handling
- Use `asyncio.gather(..., return_exceptions=True)` to catch individual failures
- Continue processing other slots even if one fails
- Collect all errors and report at end
- Maintain current error reporting format

```python
results = await asyncio.gather(
    *tasks,
    return_exceptions=True
)

for i, result in enumerate(results):
    if isinstance(result, Exception):
        contexts[i].error = str(result)
        logger.error(...)
    else:
        contexts[i] = result
```

## Testing Strategy

### 1. Unit Tests

#### Test Phase 1 (Sequential File Operations)
- ✅ Test file resolution for each slot
- ✅ Test DOCX opening with retry logic
- ✅ Test content extraction
- ✅ Verify no file locking issues

#### Test Phase 2 (Parallel LLM Calls)
- ✅ Test parallel API calls (mock LLM service)
- ✅ Test progress tracking aggregation
- ✅ Test error handling (one slot fails, others continue)
- ✅ Test with 1 slot (should work same as sequential)
- ✅ Test with 5 slots (typical use case)
- ✅ Test with 4 slots (alternative use case)

### 2. Integration Tests

#### Test Full Flow
- ✅ Process 5 slots end-to-end (typical use case)
- ✅ Process 4 slots end-to-end (alternative)
- ✅ Verify all lessons generated correctly
- ✅ Verify progress updates correctly
- ✅ Verify error handling works
- ✅ Compare output with sequential processing (should be identical)

### 3. Performance Tests

#### Benchmark
- ✅ Measure time for 5 slots (sequential vs parallel) - typical use case
- ✅ Measure time for 4 slots (sequential vs parallel) - alternative
- ✅ Measure API quota usage (should be same)
- ✅ Measure memory usage (should be similar)
- ✅ Test with different numbers of slots (1, 2, 4, 5, 8)

### 4. Edge Cases

#### Test Scenarios
- ✅ One slot fails file opening (retry logic)
- ✅ One slot fails LLM call (others continue)
- ✅ All slots fail (proper error reporting)
- ✅ Mixed success/failure
- ✅ Very large number of slots (10+)
- ✅ Single slot (should use sequential path)

### 5. Manual Testing Checklist

#### Pre-Implementation
- [ ] Document current processing time for 5 slots (typical use case)
- [ ] Document current processing time for 4 slots (alternative)
- [ ] Document current API quota usage
- [ ] Test current error handling behavior

#### Post-Implementation
- [ ] Test with 1 slot (should work identically)
- [ ] Test with 4 slots (should be ~70% faster)
- [ ] Verify progress updates smoothly
- [ ] Verify error messages are clear
- [ ] Test with file locked (retry logic)
- [ ] Test with OneDrive syncing
- [ ] Verify output quality unchanged
- [ ] Test with parallel mode disabled (fallback)

## Risk Assessment

### Low Risk
- ✅ File operations remain sequential (no locking risk)
- ✅ LLM API supports parallel requests (confirmed)
- ✅ Progress tracking is read-only (thread-safe)

### Medium Risk
- ⚠️ API rate limits (mitigated by comprehensive rate limit handling - see `PARALLEL_PROCESSING_RATE_LIMITS.md`)
- ⚠️ Memory usage (mitigated by processing in batches if needed)
- ⚠️ Progress tracking accuracy (mitigated by averaging)

### Mitigation Strategies
1. **API Rate Limits**: 
   - Comprehensive rate limit handling with exponential backoff
   - Token usage tracking (TPM limits)
   - Request rate limiting (RPM limits)
   - Adaptive concurrency adjustment
   - See `docs/PARALLEL_PROCESSING_RATE_LIMITS.md` for full details
2. **Memory**: Process in batches of 4-8 slots if memory becomes issue
3. **Progress**: Use weighted averaging based on slot complexity
4. **Fallback**: Always have sequential mode as backup

## Rollout Plan (Updated)

### Phase 0: Prerequisites ✅
1. ✅ Analytics implementation (COMPLETED)
2. ✅ Database schema design (COMPLETED)
3. ✅ Migration scripts created (COMPLETED)

### Phase 1: Foundation
1. Run database migration (CRITICAL - must be first)
2. Add configuration flag (enables toggling)
3. Implement rate limit detection (before parallel processing)

### Phase 2: Core Implementation
1. Create `SlotProcessingContext` dataclass
2. Split `_process_slot` into `_extract_slot_content` and `_transform_slot_with_llm`
3. Implement `_process_slots_parallel_llm`
4. Update main processing flow

### Phase 3: Integration
1. Update progress tracking
2. Enhance error handling
3. Integrate rate limit tracking (optional - can be done later)

### Phase 4: Testing
1. Run unit tests
2. Run integration tests
3. Manual testing with real data
4. Performance benchmarking

### Phase 5: Deployment
1. Deploy with `PARALLEL_LLM_PROCESSING=False` (default sequential)
2. Enable for testing: `PARALLEL_LLM_PROCESSING=True`
3. Monitor for issues (use Analytics dashboard)
4. Make default if successful

## Success Criteria

### Functional
- ✅ All slots process correctly
- ✅ Progress tracking works accurately
- ✅ Error handling works correctly
- ✅ Output quality unchanged

### Performance
- ✅ 75%+ time reduction for 5 slots (typical use case)
- ✅ 70%+ time reduction for 4 slots (alternative)
- ✅ No increase in API quota usage
- ✅ No file locking issues
- ✅ Memory usage acceptable (<600MB for 5 slots)

### User Experience
- ✅ Progress updates smoothly
- ✅ Error messages are clear
- ✅ No regression in functionality

## Code Changes Summary

### Files to Modify
1. `tools/batch_processor.py`
   - Add `SlotProcessingContext` dataclass
   - Split `_process_slot` into two phases
   - Add `_process_slots_parallel_llm` method
   - Update `process_weekly_plan` to use two-phase approach

2. `backend/config.py`
   - Add `PARALLEL_LLM_PROCESSING` setting

3. `backend/progress.py` (if needed)
   - Update progress tracking for parallel operations

### Files to Test
1. `tests/test_batch_processor.py` (new or update)
2. `tests/test_parallel_processing.py` (new)

## Questions to Resolve

1. **API Rate Limits**: Confirm OpenAI API supports multiple parallel requests with same key
   - ✅ Confirmed: Same API key can handle parallel requests

2. **Progress Granularity**: How detailed should progress be for parallel operations?
   - Solution: Average progress across all slots, show "Processing 3/5 slots..." (typical)

3. **Error Reporting**: Should we stop on first error or continue?
   - Solution: Continue processing, collect all errors, report at end

4. **Configuration**: Should parallel mode be default or opt-in?
   - Solution: Default enabled, but can be disabled via config

## Next Steps (Updated Sequence)

### Phase 0: Prerequisites ✅
1. ✅ Review plan (current step)
2. ✅ Analytics implementation (COMPLETED)
3. ✅ Database schema design (COMPLETED)
4. ✅ Migration scripts created (COMPLETED)

### Phase 1: Foundation
1. ⏭️ **Run database migration** (CRITICAL - must be first)
   - Run: `python backend/migrations/add_parallel_processing_metrics.py`
   - For Supabase: Run SQL from `sql/add_parallel_processing_metrics_supabase.sql`
2. ⏭️ **Add configuration flag** (Early - enables toggling)
   - Add `PARALLEL_LLM_PROCESSING` to `backend/config.py`
3. ⏭️ **Implement rate limit detection** (Before parallel processing)
   - Update `backend/llm_service.py` with rate limit error handling
   - Add retry logic with exponential backoff

### Phase 2: Core Implementation
4. ⏭️ **Create SlotProcessingContext dataclass** (Foundation)
5. ⏭️ **Implement Phase 1** (extract content sequentially)
   - Create `_extract_slot_content()` method
6. ⏭️ **Implement Phase 2** (transform in parallel)
   - Create `_transform_slot_with_llm()` method
   - Create `_process_slots_parallel_llm()` method
7. ⏭️ **Update main processing flow**
   - Modify `process_weekly_plan()` to use two-phase approach

### Phase 3: Integration
8. ⏭️ **Update progress tracking** (After implementation)
9. ⏭️ **Enhance error handling** (After implementation)
10. ⏭️ **Integrate rate limit tracking** (Optional - can be done later)

### Phase 4: Testing
11. ⏭️ **Write unit tests**
12. ⏭️ **Write integration tests**
13. ⏭️ **Performance benchmarking**
14. ⏭️ **Manual testing**

### Phase 5: Deployment
15. ⏭️ **Deploy with feature disabled** (`PARALLEL_LLM_PROCESSING=False`)
16. ⏭️ **Enable for testing** (`PARALLEL_LLM_PROCESSING=True`)
17. ⏭️ **Monitor and optimize**
18. ⏭️ **Make default** (if successful)

**See `docs/IMPLEMENTATION_PLAN_REVIEW.md` for detailed review and dependency analysis.**
