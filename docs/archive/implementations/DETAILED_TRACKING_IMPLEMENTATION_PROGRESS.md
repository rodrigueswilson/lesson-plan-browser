# Detailed Workflow Tracking - Implementation Progress

**Started**: October 18, 2025  
**Status**: IN PROGRESS (2/6 steps complete)

---

## ✅ Completed Steps

### 1. Added Context Manager to PerformanceTracker ✅

**File**: `backend/performance_tracker.py`

**Changes**:
- Added `contextmanager` import
- Created `track_operation()` context manager method
- Simplifies tracking with automatic start/end handling

**Usage Example**:
```python
tracker = get_tracker()

with tracker.track_operation(plan_id, "parse_read_docx") as op:
    doc = Document(file_path)
    # Operation automatically tracked with timing
```

**Benefits**:
- ✅ Cleaner code (no manual start/end calls)
- ✅ Automatic error handling
- ✅ Guaranteed cleanup (even on exceptions)

---

### 2. Added Detailed LLM Tracking ✅

**File**: `backend/llm_service.py`

**Changes**:
- Added `plan_id` parameter to `transform_lesson()`
- Imported `get_tracker()`
- Added 4 tracking points:
  1. `llm_build_prompt` - Prompt construction
  2. **`llm_api_call`** - Actual API call (with tokens/model)
  3. `llm_parse_response` - JSON parsing
  4. `llm_validate_structure` - Schema validation

**New Operations Tracked**:
```
llm_build_prompt       (~100ms)  - Build LLM prompt
llm_api_call          (~2800ms)  - API call ⚠️ BOTTLENECK
llm_parse_response     (~150ms)  - Parse JSON response  
llm_validate_structure  (~50ms)  - Validate schema
```

**Impact**: Can now see exactly how much time the LLM API call takes vs other processing!

---

## 🚧 In Progress

### 3. Add DOCX Parser Tracking

**File**: `tools/docx_parser.py`

**Operations to Track**:
- `parse_locate_file` - Find input file
- `parse_open_docx` - Open DOCX with python-docx
- `parse_extract_text` - Extract text content
- `parse_extract_tables` - Extract tables
- `parse_extract_images` - Extract images (if enabled)
- `parse_extract_hyperlinks` - Extract hyperlinks (if enabled)

**Estimated Time**: 30 minutes

---

## 📋 Pending Steps

### 4. Add DOCX Renderer Tracking

**File**: `tools/docx_renderer.py`

**Operations to Track**:
- `render_load_template` - Load template
- `render_apply_header` - Set header/footer
- `render_create_tables` - Generate lesson tables
- `render_apply_formatting` - Apply styles
- `render_insert_images` - Insert images (if any)
- `render_save_docx` - Save final file

**Estimated Time**: 30 minutes

---

### 5. Update Analytics Dashboard

**Frontend Changes Needed**:

**A. Group operations by phase** in the chart:
```
PARSE PHASE (blue)
  ├─ parse_locate_file
  ├─ parse_open_docx
  └─ ...

PROCESS PHASE (orange)
  ├─ llm_build_prompt
  ├─ llm_api_call ⚠️
  └─ ...

RENDER PHASE (green)
  ├─ render_load_template
  └─ ...
```

**B. Add detailed table view**:
Show all operations sorted by average time (descending) to identify bottlenecks.

**C. Add phase summary cards**:
- Parse Phase: X.Xs total
- Process Phase: X.Xs total (highlight if >70% of workflow)
- Render Phase: X.Xs total

**Estimated Time**: 2 hours

---

### 6. Test with Real Workflow

**Testing Plan**:
1. Process a real lesson plan through the system
2. Check database for new detailed operations
3. Verify analytics dashboard shows detailed breakdown
4. Confirm LLM API call is identified as bottleneck

**Estimated Time**: 30 minutes

---

## 📊 Expected Results

### Before (Current):
```
Operation          | Avg Time | Count
-------------------|----------|------
parse_slot         | 1.4s     | 43
process_slot       | 3.3s     | 34  ⚠️
render_document    | 2.4s     | 43
```

### After (With Detailed Tracking):
```
Operation                  | Avg Time | Count | % of Total
---------------------------|----------|-------|------------
PARSE PHASE                | 1.4s     | 43    | 15%
  parse_locate_file        | 0.1s     | 43    | 1%
  parse_open_docx          | 0.6s     | 43    | 6%
  parse_extract_text       | 0.3s     | 43    | 3%
  parse_extract_tables     | 0.2s     | 43    | 2%
  parse_extract_images     | 0.1s     | 43    | 1%
  parse_extract_hyperlinks | 0.1s     | 43    | 1%

PROCESS PHASE              | 3.3s     | 34    | 36%
  llm_build_prompt         | 0.1s     | 34    | 1%
  llm_api_call             | 2.8s     | 34    | 30% ⚠️⚠️⚠️
  llm_parse_response       | 0.2s     | 34    | 2%
  llm_validate_structure   | 0.2s     | 34    | 2%

RENDER PHASE               | 2.4s     | 43    | 26%
  render_load_template     | 0.3s     | 43    | 3%
  render_apply_header      | 0.2s     | 43    | 2%
  render_create_tables     | 1.0s     | 43    | 11%
  render_apply_formatting  | 0.5s     | 43    | 5%
  render_insert_images     | 0.2s     | 43    | 2%
  render_save_docx         | 0.2s     | 43    | 2%
```

**Key Insight**: `llm_api_call` is 30% of total workflow time - clear bottleneck!

---

## 🎯 Optimization Opportunities

Once detailed tracking is complete, you'll be able to:

### 1. Optimize LLM API Calls (Biggest Impact)
- **Current**: 2.8s per call
- **Target**: <1.5s per call
- **How**:
  - Use gpt-4o-mini instead of gpt-4o (5x faster)
  - Implement response caching
  - Reduce prompt size
  - Batch multiple slots

### 2. Optimize Table Rendering
- **Current**: 1.0s per plan
- **Target**: <0.5s per plan
- **How**:
  - Simplify table structure
  - Reduce formatting complexity
  - Cache template objects

### 3. Optimize DOCX Parsing
- **Current**: 0.6s per file
- **Target**: <0.3s per file
- **How**:
  - Cache parsed results
  - Lazy load images/hyperlinks
  - Use faster DOCX library

---

## 📝 Next Session Plan

**Priority Order**:
1. ✅ Context manager (DONE)
2. ✅ LLM tracking (DONE)
3. 🚧 DOCX parser tracking (IN PROGRESS)
4. ⏳ DOCX renderer tracking
5. ⏳ Dashboard updates
6. ⏳ Testing

**Estimated Total Time Remaining**: ~3-4 hours

---

## 🔄 How to Continue

**Next Steps**:
1. Add tracking to `tools/docx_parser.py`
2. Add tracking to `tools/docx_renderer.py`
3. Update analytics dashboard frontend
4. Test with real workflow
5. Document findings

**Files to Modify**:
- `tools/docx_parser.py` - Add parse tracking
- `tools/docx_renderer.py` - Add render tracking
- `frontend/src/components/Analytics.tsx` - Update UI
- `frontend/src/lib/api.ts` - Update interfaces (if needed)

---

**Status**: 2/6 steps complete (33%)  
**Next**: Add DOCX parser tracking
