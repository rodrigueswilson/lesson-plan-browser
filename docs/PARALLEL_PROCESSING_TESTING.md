# Parallel Processing Testing Strategy

## Testing Approach

### 1. Test Environment Setup

#### Prerequisites
- Python 3.8+ with asyncio support
- Mock LLM service for unit tests
- Real LLM service for integration tests
- Test data: 4 slots with different subjects
- Test files: DOCX files in week folder

#### Test Data Structure
```
test_data/
  week_folder/
    slot1_ela.docx
    slot2_science.docx
    slot3_math.docx
    slot4_science.docx
```

### 2. Unit Tests

#### Test File: `tests/test_parallel_processing.py`

#### Test 2.1: SlotProcessingContext Creation
```python
def test_slot_processing_context_creation():
    """Test SlotProcessingContext dataclass creation."""
    slot = {"slot_number": 1, "subject": "ELA"}
    context = SlotProcessingContext(
        slot=slot,
        slot_index=1,
        total_slots=4
    )
    assert context.slot == slot
    assert context.slot_index == 1
    assert context.total_slots == 4
    assert context.primary_file is None
    assert context.extracted_content is None
```

#### Test 2.2: Phase 1 - Extract Content (Sequential)
```python
@pytest.mark.asyncio
async def test_extract_slot_content_sequential():
    """Test that content extraction happens sequentially."""
    processor = BatchProcessor(...)
    contexts = [SlotProcessingContext(...) for _ in range(4)]
    
    # Extract content for all slots
    results = []
    for ctx in contexts:
        result = await processor._extract_slot_content(ctx, ...)
        results.append(result)
    
    # Verify all have extracted content
    assert all(ctx.extracted_content for ctx in results)
    # Verify files were accessed sequentially (check timestamps)
```

#### Test 2.3: Phase 2 - Transform in Parallel
```python
@pytest.mark.asyncio
async def test_transform_slots_parallel():
    """Test that LLM calls happen in parallel."""
    processor = BatchProcessor(...)
    contexts = [SlotProcessingContext(...) for _ in range(4)]
    # Set extracted_content for each
    
    start_time = time.time()
    results = await processor._process_slots_parallel_llm(contexts, ...)
    elapsed = time.time() - start_time
    
    # With parallel processing, should take ~2 min (not ~8 min)
    assert elapsed < 180  # Less than 3 minutes
    assert len(results) == 4
    assert all(ctx.lesson_json for ctx in results)
```

#### Test 2.4: Progress Tracking Aggregation
```python
@pytest.mark.asyncio
async def test_progress_tracking_parallel():
    """Test progress tracking with parallel operations."""
    processor = BatchProcessor(...)
    plan_id = "test_plan"
    
    # Simulate parallel progress updates
    slot_progresses = {1: 50, 2: 75, 3: 25, 4: 100}
    processor._update_parallel_progress(plan_id, slot_progresses, 4, "transforming")
    
    # Verify progress tracker was updated with average
    progress = progress_tracker.get_progress(plan_id)
    assert progress["progress"] > 0
    assert progress["progress"] < 100
```

#### Test 2.5: Error Handling - One Slot Fails
```python
@pytest.mark.asyncio
async def test_parallel_error_handling_one_fails():
    """Test that one slot failure doesn't stop others."""
    processor = BatchProcessor(...)
    contexts = [SlotProcessingContext(...) for _ in range(4)]
    
    # Mock LLM service to fail for slot 2
    processor.llm_service.transform_lesson = Mock(side_effect=[
        (True, {"lesson": "1"}, None),  # Slot 1: success
        (False, None, "API Error"),     # Slot 2: failure
        (True, {"lesson": "3"}, None),  # Slot 3: success
        (True, {"lesson": "4"}, None),  # Slot 4: success
    ])
    
    results = await processor._process_slots_parallel_llm(contexts, ...)
    
    # Verify slot 2 has error, others succeeded
    assert results[0].lesson_json is not None
    assert results[1].error is not None
    assert results[2].lesson_json is not None
    assert results[3].lesson_json is not None
```

#### Test 2.6: Sequential Fallback
```python
@pytest.mark.asyncio
async def test_sequential_fallback():
    """Test that sequential mode works when parallel is disabled."""
    settings.PARALLEL_LLM_PROCESSING = False
    processor = BatchProcessor(...)
    contexts = [SlotProcessingContext(...) for _ in range(4)]
    
    # Should process sequentially
    results = []
    for ctx in contexts:
        result = await processor._transform_slot_with_llm(ctx, ...)
        results.append(result)
    
    assert len(results) == 4
    assert all(ctx.lesson_json for ctx in results)
```

### 3. Integration Tests

#### Test File: `tests/test_batch_processor_integration.py`

#### Test 3.1: Full Flow - 5 Slots Parallel (Typical Use Case)
```python
@pytest.mark.asyncio
async def test_full_flow_parallel_5_slots():
    """Test complete flow with 5 slots in parallel mode (typical use case)."""
    processor = BatchProcessor(...)
    slots = [get_test_slot(i) for i in range(1, 6)]
    
    start_time = time.time()
    result = await processor.process_weekly_plan(
        user=test_user,
        slots=slots,
        week_of="01/05-01/09",
        provider="openai",
        plan_id="test_plan_parallel"
    )
    elapsed = time.time() - start_time
    
    # Verify completion
    assert result["status"] == "completed"
    assert len(result["lessons"]) == 5
    
    # Verify performance improvement
    assert elapsed < 180  # Less than 3 minutes (vs ~10 min sequential)
    
    # Verify output quality
    for lesson in result["lessons"]:
        assert "days" in lesson["lesson_json"]
        assert "monday" in lesson["lesson_json"]["days"]
```

#### Test 3.2: Full Flow - Sequential Mode
```python
@pytest.mark.asyncio
async def test_full_flow_sequential_mode():
    """Test complete flow with sequential mode (baseline)."""
    settings.PARALLEL_LLM_PROCESSING = False
    processor = BatchProcessor(...)
    slots = [get_test_slot(i) for i in range(1, 5)]
    
    start_time = time.time()
    result = await processor.process_weekly_plan(...)
    elapsed = time.time() - start_time
    
    # Verify completion (should work, just slower)
    assert result["status"] == "completed"
    assert len(result["lessons"]) == 4
    
    # Sequential should take longer
    assert elapsed > 300  # More than 5 minutes
```

#### Test 3.3: Output Comparison
```python
@pytest.mark.asyncio
async def test_output_identical_parallel_vs_sequential():
    """Test that parallel and sequential produce identical output."""
    slots = [get_test_slot(i) for i in range(1, 5)]
    
    # Run parallel
    settings.PARALLEL_LLM_PROCESSING = True
    processor_parallel = BatchProcessor(...)
    result_parallel = await processor_parallel.process_weekly_plan(...)
    
    # Run sequential
    settings.PARALLEL_LLM_PROCESSING = False
    processor_sequential = BatchProcessor(...)
    result_sequential = await processor_sequential.process_weekly_plan(...)
    
    # Compare outputs (should be identical)
    assert result_parallel["lessons"] == result_sequential["lessons"]
```

### 4. Performance Tests

#### Test File: `tests/test_performance_parallel.py`

#### Test 4.1: Benchmark - 5 Slots (Typical Use Case)
```python
@pytest.mark.asyncio
async def test_performance_benchmark_5_slots():
    """Benchmark performance improvement for 5 slots (typical use case)."""
    slots = [get_test_slot(i) for i in range(1, 6)]
    
    # Sequential
    settings.PARALLEL_LLM_PROCESSING = False
    start = time.time()
    await processor.process_weekly_plan(...)
    sequential_time = time.time() - start
    
    # Parallel
    settings.PARALLEL_LLM_PROCESSING = True
    start = time.time()
    await processor.process_weekly_plan(...)
    parallel_time = time.time() - start
    
    # Calculate improvement
    improvement = (sequential_time - parallel_time) / sequential_time
    print(f"Sequential: {sequential_time:.1f}s")
    print(f"Parallel: {parallel_time:.1f}s")
    print(f"Improvement: {improvement*100:.1f}%")
    
    assert improvement > 0.5  # At least 50% improvement
```

#### Test 4.2: Scalability - Different Slot Counts
```python
@pytest.mark.asyncio
@pytest.mark.parametrize("num_slots", [1, 2, 4, 5, 8])
async def test_scalability_different_slot_counts(num_slots):
    """Test performance with different numbers of slots."""
    slots = [get_test_slot(i) for i in range(1, num_slots + 1)]
    
    start = time.time()
    result = await processor.process_weekly_plan(...)
    elapsed = time.time() - start
    
    # Verify completion
    assert result["status"] == "completed"
    assert len(result["lessons"]) == num_slots
    
    # Log performance
    print(f"{num_slots} slots: {elapsed:.1f}s")
    
    # For parallel mode, time should scale better
    if settings.PARALLEL_LLM_PROCESSING:
        # 8 slots should take less than 4x time of 2 slots
        if num_slots == 8:
            assert elapsed < 300  # Less than 5 minutes
```

### 5. Edge Case Tests

#### Test 5.1: Single Slot (Should Use Sequential Path)
```python
@pytest.mark.asyncio
async def test_single_slot_uses_sequential():
    """Test that single slot doesn't use parallel overhead."""
    slots = [get_test_slot(1)]
    
    # Even with parallel enabled, single slot should work
    settings.PARALLEL_LLM_PROCESSING = True
    result = await processor.process_weekly_plan(...)
    
    assert result["status"] == "completed"
    assert len(result["lessons"]) == 1
```

#### Test 5.2: File Locking During Parallel Processing
```python
@pytest.mark.asyncio
async def test_file_locking_parallel():
    """Test that file operations remain sequential even in parallel mode."""
    # Phase 1 (file ops) should still be sequential
    # This is tested by ensuring files are accessed one at a time
    # and retry logic works correctly
```

#### Test 5.3: All Slots Fail
```python
@pytest.mark.asyncio
async def test_all_slots_fail():
    """Test handling when all slots fail."""
    processor.llm_service.transform_lesson = Mock(return_value=(False, None, "Error"))
    
    contexts = [SlotProcessingContext(...) for _ in range(4)]
    results = await processor._process_slots_parallel_llm(contexts, ...)
    
    # All should have errors
    assert all(ctx.error for ctx in results)
    assert all(ctx.lesson_json is None for ctx in results)
```

### 6. Manual Testing Checklist

#### Pre-Implementation Baseline
- [ ] Record current processing time for 4 slots (sequential)
- [ ] Record current API quota usage per slot
- [ ] Test current error handling behavior
- [ ] Verify current progress tracking accuracy

#### Post-Implementation Validation
- [ ] **Functionality**
  - [ ] Process 1 slot (should work identically)
  - [ ] Process 5 slots (typical use case, should complete successfully)
  - [ ] Process 4 slots (alternative, should complete successfully)
  - [ ] Verify all lessons generated correctly
  - [ ] Verify output file created correctly
  - [ ] Verify database records updated correctly

- [ ] **Performance**
  - [ ] Measure processing time for 5 slots (should be ~75% faster)
  - [ ] Measure processing time for 4 slots (should be ~70% faster)
  - [ ] Measure API quota usage (should be same)
  - [ ] Monitor memory usage (should be acceptable)
  - [ ] Test with different slot counts (1, 2, 4, 5, 8)

- [ ] **Progress Tracking**
  - [ ] Progress updates smoothly during Phase 1 (extraction)
  - [ ] Progress updates smoothly during Phase 2 (transformation)
  - [ ] Progress percentage is accurate
  - [ ] Progress messages are clear

- [ ] **Error Handling**
  - [ ] Test with file locked (retry logic works)
  - [ ] Test with OneDrive syncing (retry logic works)
  - [ ] Test with one slot failing LLM call (others continue)
  - [ ] Test with all slots failing (proper error reporting)
  - [ ] Error messages are clear and actionable

- [ ] **Configuration**
  - [ ] Test with `PARALLEL_LLM_PROCESSING=True` (parallel mode)
  - [ ] Test with `PARALLEL_LLM_PROCESSING=False` (sequential fallback)
  - [ ] Verify configuration is read correctly

- [ ] **Regression**
  - [ ] Compare output quality (should be identical)
  - [ ] Compare output structure (should be identical)
  - [ ] Verify no new bugs introduced
  - [ ] Verify existing features still work

### 7. Test Execution Plan

#### Phase 1: Unit Tests (Automated)
```bash
# Run unit tests
pytest tests/test_parallel_processing.py -v

# Run with coverage
pytest tests/test_parallel_processing.py --cov=tools.batch_processor --cov-report=html
```

#### Phase 2: Integration Tests (Automated)
```bash
# Run integration tests (requires real API key or mock)
pytest tests/test_batch_processor_integration.py -v

# Run with real API (slower)
pytest tests/test_batch_processor_integration.py -v --use-real-api
```

#### Phase 3: Performance Tests (Automated)
```bash
# Run performance benchmarks
pytest tests/test_performance_parallel.py -v -s

# Compare sequential vs parallel
pytest tests/test_performance_parallel.py::test_performance_benchmark_4_slots -v -s
```

#### Phase 4: Manual Testing (Interactive)
1. Start backend with logging enabled
2. Process 4 slots via UI
3. Monitor logs for errors
4. Verify output quality
5. Measure processing time
6. Test error scenarios

### 8. Success Criteria

#### Functional
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ Manual testing checklist completed
- ✅ No regressions in existing functionality

#### Performance
- ✅ 70%+ time reduction for 4 slots
- ✅ No increase in API quota usage
- ✅ Memory usage acceptable (<500MB for 4 slots)
- ✅ No file locking issues

#### Quality
- ✅ Output quality unchanged (identical to sequential)
- ✅ Error handling works correctly
- ✅ Progress tracking accurate
- ✅ Code coverage >80%

### 9. Test Data Requirements

#### Real Test Data
- 4 DOCX files in week folder
- Different subjects (ELA, Science, Math)
- Different teachers
- Valid week folder structure

#### Mock Data (for unit tests)
- Mock DOCXParser
- Mock LLMService
- Mock file system
- Mock progress tracker

### 10. Continuous Testing

#### Pre-Commit
- Run unit tests
- Run linter
- Check code coverage

#### Pre-Deploy
- Run full test suite
- Run performance benchmarks
- Manual smoke test

#### Post-Deploy
- Monitor logs for errors
- Monitor performance metrics
- Collect user feedback
