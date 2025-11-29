# Detailed Workflow Tracking Implementation Plan

**Goal**: Add granular performance tracking for each step in the lesson plan generation workflow

---

## 📊 Current Tracking (3 operations)

Currently tracked:
1. `parse_slot` - Parse input DOCX
2. `process_slot` - LLM processing  
3. `render_document` - Generate output DOCX

**Problem**: These are too broad. We need to see what's happening INSIDE each operation.

---

## 🔍 Detailed Workflow Breakdown

### Phase 1: PARSE (parse_slot)
**Sub-operations to track:**
1. `parse_locate_file` - Find input DOCX file
2. `parse_read_docx` - Read DOCX with python-docx
3. `parse_extract_text` - Extract text content
4. `parse_extract_tables` - Extract table data
5. `parse_extract_images` - Extract embedded images
6. `parse_extract_hyperlinks` - Extract hyperlinks
7. `parse_structure_data` - Structure into lesson format

**Expected times:**
- File I/O: ~100-300ms
- DOCX parsing: ~500-800ms
- Data extraction: ~200-400ms
- **Total**: ~1000-1500ms

### Phase 2: PROCESS (process_slot)
**Sub-operations to track:**
1. `process_prepare_prompt` - Build LLM prompt
2. `process_llm_call` - **SLOWEST** - API call to OpenAI/Anthropic
3. `process_parse_response` - Parse LLM JSON response
4. `process_validate_output` - Validate against schema
5. `process_apply_wida` - Apply WIDA enhancements
6. `process_apply_strategies` - Apply teaching strategies
7. `process_generate_objectives` - Generate learning objectives

**Expected times:**
- Prompt prep: ~50-100ms
- **LLM API call: ~2000-4000ms** ⚠️ (bottleneck!)
- Response parsing: ~100-200ms
- Enhancements: ~500-1000ms
- **Total**: ~3000-5000ms

### Phase 3: RENDER (render_document)
**Sub-operations to track:**
1. `render_load_template` - Load DOCX template
2. `render_apply_header_footer` - Set header/footer
3. `render_create_tables` - Generate lesson tables
4. `render_apply_formatting` - Apply styles and formatting
5. `render_insert_images` - Insert images
6. `render_insert_hyperlinks` - Insert hyperlinks
7. `render_save_docx` - Save final DOCX file

**Expected times:**
- Template loading: ~200-400ms
- Table generation: ~800-1200ms
- Formatting: ~400-600ms
- File save: ~200-400ms
- **Total**: ~2000-3000ms

---

## 🎯 Implementation Steps

### Step 1: Add Tracking Points to Code

**File**: `tools/batch_processor.py`

```python
# Example for parse phase
async def _parse_slot(self, slot, input_file):
    tracker = get_tracker()
    
    # Track file location
    with tracker.track_operation(plan_id, "parse_locate_file"):
        file_path = self._locate_input_file(input_file)
    
    # Track DOCX reading
    with tracker.track_operation(plan_id, "parse_read_docx"):
        doc = Document(file_path)
    
    # Track text extraction
    with tracker.track_operation(plan_id, "parse_extract_text"):
        text = self._extract_text(doc)
    
    # ... etc
```

### Step 2: Update Performance Tracker

**File**: `backend/performance_tracker.py`

Add context manager for easier tracking:

```python
from contextlib import contextmanager

@contextmanager
def track_operation(self, plan_id: str, operation_type: str, **metadata):
    """Context manager for tracking operations."""
    if not self.enabled:
        yield
        return
    
    start_time = datetime.now()
    try:
        yield
    finally:
        end_time = datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        self.record_operation(
            plan_id=plan_id,
            operation_type=operation_type,
            duration_ms=duration_ms,
            started_at=start_time,
            completed_at=end_time,
            **metadata
        )
```

### Step 3: Update Analytics Dashboard

**Frontend changes needed:**

1. **Group operations by phase** in the chart
2. **Show sub-operations** in a drill-down view
3. **Color-code by phase**:
   - Parse: Blue
   - Process: Orange (highlight bottlenecks)
   - Render: Green

4. **Add a detailed table view**:
```
Operation                    | Avg Time | Count | % of Total
----------------------------|----------|-------|------------
PARSE PHASE                 | 1.4s     | 43    | 15%
  ├─ parse_locate_file      | 0.1s     | 43    | 1%
  ├─ parse_read_docx        | 0.6s     | 43    | 6%
  ├─ parse_extract_text     | 0.3s     | 43    | 3%
  └─ ...                    |          |       |
PROCESS PHASE               | 3.3s     | 34    | 36%
  ├─ process_prepare_prompt | 0.1s     | 34    | 1%
  ├─ process_llm_call       | 2.8s     | 34    | 30% ⚠️
  ├─ process_parse_response | 0.2s     | 34    | 2%
  └─ ...                    |          |       |
RENDER PHASE                | 2.4s     | 43    | 26%
  ├─ render_load_template   | 0.3s     | 43    | 3%
  ├─ render_create_tables   | 1.0s     | 43    | 11%
  └─ ...                    |          |       |
```

---

## 📈 Expected Insights

With detailed tracking, you'll be able to see:

### Bottleneck Identification
- **LLM API call** is likely 80%+ of process_slot time
- **Table generation** might be slow in render phase
- **File I/O** might be slow if files are on network drive

### Optimization Opportunities
1. **If `process_llm_call` is slow**:
   - Use faster models (gpt-4o-mini)
   - Implement response caching
   - Reduce prompt size
   - Batch multiple slots

2. **If `render_create_tables` is slow**:
   - Simplify table structure
   - Reduce formatting complexity
   - Optimize template

3. **If `parse_read_docx` is slow**:
   - Cache parsed results
   - Optimize file reading
   - Use faster DOCX library

---

## 🚀 Quick Win: Add LLM Call Tracking First

**Priority 1**: Track just the LLM call separately since it's the biggest bottleneck.

**Minimal change** to `backend/llm_service.py`:

```python
async def transform_lesson(self, ...):
    tracker = get_tracker()
    
    # Track prompt preparation
    with tracker.track_operation(plan_id, "llm_prepare_prompt"):
        prompt = self._build_prompt(...)
    
    # Track actual API call
    with tracker.track_operation(plan_id, "llm_api_call", 
                                 model=model, provider=provider):
        response = await self.client.chat.completions.create(...)
    
    # Track response parsing
    with tracker.track_operation(plan_id, "llm_parse_response"):
        result = self._parse_response(response)
    
    return result
```

This alone would show you:
- How much time is spent building prompts
- **Exact API call time** (the real bottleneck)
- How much time parsing takes

---

## 📊 Updated Dashboard View

With detailed tracking, the Workflow Performance chart would show:

```
Time (ms)
4000 |                                    ████
3500 |                                    ████
3000 |                                    ████ llm_api_call
2500 |                                    ████
2000 |              ████                  ████
1500 |    ████      ████      ████        ████
1000 |    ████      ████      ████        ████
 500 |    ████      ████      ████        ████
   0 |────────────────────────────────────────
      parse  parse  render  render  llm    llm
      file   docx   table   format  prep   call
```

**Instantly see**: LLM API call is the bottleneck!

---

## 🎯 Next Steps

1. **Quick win**: Add LLM call tracking (30 min)
2. **Phase 1**: Add parse sub-operations (1 hour)
3. **Phase 2**: Add process sub-operations (1 hour)
4. **Phase 3**: Add render sub-operations (1 hour)
5. **Dashboard**: Update to show detailed breakdown (2 hours)

**Total effort**: ~5-6 hours for complete detailed tracking

---

## 💡 Alternative: Use Existing Tools

Instead of custom tracking, consider:

1. **Python profiler** (`cProfile`)
2. **OpenTelemetry** for distributed tracing
3. **Datadog/New Relic** for APM

But custom tracking gives you:
- ✅ User-specific insights
- ✅ Historical data in your database
- ✅ Custom dashboard in your app
- ✅ No external dependencies

---

**Recommendation**: Start with LLM call tracking (quick win), then expand to full detailed tracking if needed.
