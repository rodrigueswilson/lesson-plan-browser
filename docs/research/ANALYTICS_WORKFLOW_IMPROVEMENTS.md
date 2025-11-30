# Analytics Dashboard - Workflow Performance Improvements

**Date**: October 18, 2025  
**Changes**: Analytics dashboard redesigned to show workflow bottlenecks

---

## 🎯 Problem Identified

The original analytics dashboard showed:
- "Avg Time" - Average time **per operation** (~2.3s)
- Generic "Operation Breakdown" chart

**Issue**: This didn't help identify which part of the workflow was slow.

---

## 🔍 Workflow Analysis

The complete workflow for generating a weekly lesson plan consists of 3 operations:

### 1. **parse_slot** (~1.4s average)
- Reads and parses input DOCX files
- Extracts lesson content
- **Fastest step** ✅

### 2. **process_slot** (~3.3s average)  
- LLM processing (OpenAI/Anthropic)
- WIDA enhancements
- Strategy generation
- **SLOWEST STEP** ⚠️ (bottleneck!)

### 3. **render_document** (~2.4s average)
- Generates output DOCX
- Applies formatting
- **Medium speed**

### Total Time Per Plan
- **Average**: ~7-15 seconds for complete workflow
- **Varies by**: Number of slots, LLM model used, content complexity

---

## ✅ Improvements Made

### 1. Changed "Avg Time" Card
**Before**: 
- Label: "Avg Time"
- Value: 2.3s
- Subtitle: "per operation"

**After**:
- Label: "Avg Time Per Plan"
- Value: 9.3s (example)
- Subtitle: "total workflow time"

**Why**: Shows the actual time to generate one complete weekly plan, which is what users care about.

### 2. Renamed Chart: "Workflow Performance"
**Before**: "Operation Breakdown"

**After**: "Workflow Performance"
- Subtitle: "Average time per operation (identify bottlenecks)"
- Shows both time (ms) and count
- Better tooltip formatting (shows seconds too)
- Y-axis labeled "Time (ms)"

**Why**: Makes it clear this is for performance optimization.

### 3. Changed to Weekly Activity
**Before**: "Daily Activity"

**After**: "Weekly Activity"
- Aggregates daily data into weeks
- Shows week starting dates
- Better for lesson planning context

**Why**: Lesson plans are organized by week, so weekly view makes more sense.

---

## 📊 How to Use This Data

### Identifying Bottlenecks

Look at the **Workflow Performance** chart:

1. **If `process_slot` is slowest** (typical):
   - LLM API calls are the bottleneck
   - Solutions:
     - Use faster models (gpt-4o-mini vs gpt-4o)
     - Reduce prompt complexity
     - Implement caching
     - Batch multiple slots together

2. **If `render_document` is slowest**:
   - DOCX generation is slow
   - Solutions:
     - Optimize template complexity
     - Reduce image processing
     - Simplify formatting

3. **If `parse_slot` is slowest**:
   - Input file reading is slow
   - Solutions:
     - Optimize DOCX parsing
     - Cache parsed results
     - Reduce file size

### Optimization Priorities

Based on current data:
1. **Priority 1**: Optimize `process_slot` (3.3s → target 2s)
   - Switch to faster LLM models
   - Implement prompt caching
   - Reduce token usage

2. **Priority 2**: Optimize `render_document` (2.4s → target 1.5s)
   - Template optimization
   - Reduce formatting complexity

3. **Priority 3**: `parse_slot` is already fast (1.4s) ✅

---

## 🎯 Performance Goals

### Current Performance
- **Total time per plan**: ~7-15 seconds
- **Slowest operation**: process_slot (3.3s)

### Target Performance
- **Total time per plan**: <5 seconds
- **All operations**: <2 seconds each

### How to Achieve
1. Use gpt-4o-mini for most operations (5x faster than gpt-4o)
2. Implement LLM response caching
3. Optimize DOCX template
4. Parallel processing where possible

---

## 📈 Monitoring

Use the analytics dashboard to:

1. **Track improvements**: Compare weekly averages
2. **Identify regressions**: Sudden increases in operation time
3. **Model comparison**: See which LLM models are fastest
4. **Cost vs Speed**: Balance performance with API costs

---

## 🔧 Technical Changes

### Backend (`backend/performance_tracker.py`)
```python
# Added calculation for average time per plan
stats['avg_duration_per_plan_ms'] = stats['total_duration_ms'] / stats['total_plans']
```

### Frontend (`frontend/src/lib/api.ts`)
```typescript
// Added new field to interface
export interface AnalyticsSummary {
  // ... existing fields
  avg_duration_per_plan_ms: number;  // NEW
}
```

### Frontend (`frontend/src/components/Analytics.tsx`)
- Updated "Avg Time" card to show per-plan time
- Renamed "Operation Breakdown" to "Workflow Performance"
- Added descriptive subtitle
- Improved chart tooltips
- Changed to weekly activity aggregation

---

## 📝 Files Modified

1. `backend/performance_tracker.py` - Added avg_duration_per_plan_ms calculation
2. `frontend/src/lib/api.ts` - Updated AnalyticsSummary interface
3. `frontend/src/components/Analytics.tsx` - UI improvements
4. `check_operations.py` - NEW: Script to analyze workflow operations

---

## 🎉 Result

The analytics dashboard now provides **actionable insights** for performance optimization:

✅ Shows total time per plan (what users care about)  
✅ Identifies workflow bottlenecks clearly  
✅ Provides data to guide optimization efforts  
✅ Weekly view matches lesson planning workflow  

**Next Steps**: Use this data to optimize the `process_slot` operation (LLM calls) for faster plan generation!
