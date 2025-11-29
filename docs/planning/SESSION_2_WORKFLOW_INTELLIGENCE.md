# Session 2: Workflow Intelligence - IMPLEMENTATION PLAN

**Date**: 2025-10-18  
**Status**: VALIDATION PHASE  
**Estimated Time**: 3-4 hours  
**Risk Level**: MEDIUM (database changes)

---

## 🎯 Session 2 Overview

**Goal**: Implement performance measurement and tracking system

**Features**:
1. Performance tracking module (timing, tokens, costs)
2. Database schema for metrics storage
3. Optional tracking via environment variable
4. CSV export for research analysis

**Prerequisites**: Session 1 complete ✅

---

## 📋 Validation Phase - Critical Questions

### Q1: Database Schema Design
**Decision**: Track per-day operations with detailed metrics

**Fields to Track**:
- ✅ Duration (ms)
- ✅ Token counts (input, output, total)
- ✅ Cost (USD)
- ✅ Model name & provider
- ✅ Slot/day numbers
- ✅ Timestamps
- ❌ Lesson content (privacy)
- ❌ Student names (privacy)

---

### Q2: Cost Calculation
**Decision**: Token-based with model pricing table

**Pricing (per 1K tokens)**:
```python
MODEL_PRICING = {
    "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
}
```

---

### Q3: Performance Overhead
**Analysis**: ~10-15ms per operation (negligible)

**Mitigation**:
- Async database writes
- Batch inserts
- Silent failure on errors
- Optional via environment variable

---

### Q4: Data Retention
**Decision**: 90 days default, configurable

**Environment Variables**:
```bash
ENABLE_PERFORMANCE_TRACKING=true  # Default: true
PERFORMANCE_RETENTION_DAYS=90     # Default: 90
```

---

### Q5: Token Counting
**Decision**: Use LLM API response (most accurate)

**OpenAI Response**:
```python
{"usage": {"prompt_tokens": 1234, "completion_tokens": 567}}
```

**Anthropic Response**:
```python
{"usage": {"input_tokens": 1234, "output_tokens": 567}}
```

---

## ✅ Validation Tasks

### Task 2.1: Verify API Token Counts ✅
**Status**: VERIFIED - Both OpenAI and Anthropic return token counts

### Task 2.2: Test Database Migration ⏳
**Status**: PENDING - Create test migration script

### Task 2.3: Measure Overhead ⏳
**Status**: PENDING - Benchmark with/without tracking

### Task 2.4: Validate Cost Accuracy ⏳
**Status**: PENDING - Test with known token counts

---

## 📋 Implementation Scope

### Feature 1: Model Pricing Module 💰
**Time**: 30 minutes

**File**: `backend/model_pricing.py`

**Functions**:
- `calculate_cost(model, input_tokens, output_tokens) -> float`
- `get_model_pricing(model) -> Dict`
- `list_supported_models() -> List[str]`

---

### Feature 2: Performance Tracker 📊
**Time**: 60 minutes

**File**: `backend/performance_tracker.py`

**Class**: `PerformanceTracker`

**Methods**:
- `start_operation(plan_id, operation_type, metadata) -> str`
- `end_operation(operation_id, result) -> None`
- `get_plan_metrics(plan_id) -> List[Dict]`
- `get_plan_summary(plan_id) -> Dict`
- `export_to_csv(plan_id, output_path) -> str`

---

### Feature 3: Database Schema 🗄️
**Time**: 45 minutes

**New Table**: `performance_metrics`
```sql
CREATE TABLE performance_metrics (
    id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    slot_number INTEGER,
    day_number INTEGER,
    operation_type TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_ms REAL,
    tokens_input INTEGER,
    tokens_output INTEGER,
    tokens_total INTEGER,
    llm_provider TEXT,
    llm_model TEXT,
    cost_usd REAL,
    error_message TEXT,
    FOREIGN KEY (plan_id) REFERENCES weekly_plans(id) ON DELETE CASCADE
);
```

**Alter Table**: `weekly_plans`
```sql
ALTER TABLE weekly_plans ADD COLUMN processing_time_ms REAL;
ALTER TABLE weekly_plans ADD COLUMN total_tokens INTEGER;
ALTER TABLE weekly_plans ADD COLUMN total_cost_usd REAL;
ALTER TABLE weekly_plans ADD COLUMN llm_model TEXT;
```

---

### Feature 4: Batch Processor Integration 🔄
**Time**: 45 minutes

**File**: `tools/batch_processor.py`

**Integration**:
```python
# Start tracking
op_id = tracker.start_operation(plan_id, "process_day", {
    "slot_number": slot_num,
    "day_number": day_num
})

try:
    # Process with LLM
    result = await llm_service.transform(...)
    
    # End tracking with token counts
    tracker.end_operation(op_id, {
        "tokens_input": result["usage"]["prompt_tokens"],
        "tokens_output": result["usage"]["completion_tokens"],
        "llm_model": self.llm_service.model,
        "llm_provider": self.llm_service.provider
    })
except Exception as e:
    tracker.end_operation(op_id, {"error": str(e)})
    raise
```

---

### Feature 5: Configuration Updates ⚙️
**Time**: 15 minutes

**File**: `backend/config.py`

**Add Settings**:
```python
class Settings:
    # Performance tracking
    ENABLE_PERFORMANCE_TRACKING: bool = True
    PERFORMANCE_RETENTION_DAYS: int = 90
```

**File**: `.env.example`

**Add Variables**:
```bash
# Performance Tracking
ENABLE_PERFORMANCE_TRACKING=true
PERFORMANCE_RETENTION_DAYS=90
```

---

## 📁 File Changes Summary

### New Files (3)
```
backend/model_pricing.py            # LLM pricing data
backend/performance_tracker.py      # Tracking module
tests/test_performance_tracker.py   # Unit tests
```

### Modified Files (4)
```
backend/database.py                 # Add schema + migration
tools/batch_processor.py            # Integrate tracking
backend/config.py                   # Add settings
.env.example                        # Add variables
```

---

## 🔧 Implementation Steps

### Phase 1: Model Pricing (30 min)
1. Create `backend/model_pricing.py`
2. Add pricing table for all models
3. Implement `calculate_cost()` function
4. Add tests

### Phase 2: Database Schema (45 min)
1. Add `performance_metrics` table to `database.py`
2. Add columns to `weekly_plans` table
3. Create migration in `_run_migrations()`
4. Test migration with existing data

### Phase 3: Performance Tracker (60 min)
1. Create `backend/performance_tracker.py`
2. Implement `PerformanceTracker` class
3. Add start/end operation methods
4. Add CSV export function
5. Add tests

### Phase 4: Integration (45 min)
1. Update `batch_processor.py` to use tracker
2. Track per-day operations
3. Update weekly plan with summary
4. Handle errors gracefully

### Phase 5: Configuration (15 min)
1. Add settings to `backend/config.py`
2. Update `.env.example`
3. Test enable/disable functionality

---

## 🧪 Testing Strategy

### Unit Tests
```bash
python -m pytest tests/test_model_pricing.py -v
python -m pytest tests/test_performance_tracker.py -v
```

### Integration Test
```bash
# Process test lesson with tracking enabled
python tests/test_tracking_integration.py
```

### Manual Verification
1. Enable tracking in `.env`
2. Process test week
3. Check `performance_metrics` table
4. Export to CSV
5. Verify metrics accuracy

---

## ✅ Success Criteria

### Functional
- [ ] Model pricing calculations accurate
- [ ] Performance tracker records all operations
- [ ] Database schema migrated successfully
- [ ] Batch processor integrates tracking
- [ ] CSV export works correctly
- [ ] Environment variable control works
- [ ] No performance degradation (< 5% overhead)

### Code Quality
- [ ] Follows DRY, SSOT, KISS principles
- [ ] Comprehensive logging
- [ ] Error handling (silent failures)
- [ ] All tests pass
- [ ] No breaking changes

---

## 📊 Estimated Timeline

| Phase | Task | Time | Cumulative |
|-------|------|------|------------|
| 1 | Model Pricing | 30 min | 30 min |
| 2 | Database Schema | 45 min | 1h 15min |
| 3 | Performance Tracker | 60 min | 2h 15min |
| 4 | Integration | 45 min | 3h |
| 5 | Configuration | 15 min | 3h 15min |
| Testing | All features | 30 min | 3h 45min |

**Total**: 3-4 hours

---

## 🎯 Next Session Preview

### Session 3: Frontend UX (3-4 hours)
- Slot-level reprocessing checkboxes
- Source folder path confirmation
- Processing button states (Done/Error)
- Progress bar real-time updates

---

## 📚 References

- **Session 1 Complete**: `docs/archive/sessions/SESSION_1_COMPLETE.md` (archived)
- **Current Database**: `backend/database.py`
- **Batch Processor**: `tools/batch_processor.py`
- **LLM Service**: `backend/llm_service.py`

---

**Status**: ✅ READY FOR VALIDATION TASKS  
**Risk**: MEDIUM (database changes)  
**Confidence**: HIGH  
**Next Action**: Complete validation tasks, then implement
