# Progress Bar Connection Fixed

## Problem Identified

The progress bar was showing **fake/simulated progress** instead of real processing status because:

1. **API creates plan_id** but doesn't initialize progress tracker
2. **Batch processor creates its own plan_id** internally
3. **Frontend polls with API's plan_id** but progress tracker has processor's plan_id
4. **Result**: No match, so progress tracker returns empty/simulated data

## Root Cause

```
API (plan_id: ABC123)
  ↓
  Creates DB record
  ↓
  Returns ABC123 to frontend
  ↓
  Starts background task
    ↓
    BatchProcessor creates NEW plan_id (XYZ789)
    ↓
    Updates progress with XYZ789
    
Frontend polls for ABC123 ← No match! Shows fake progress
```

## Solution Implemented

### 1. Initialize Progress Tracker in API (`backend/api.py`)

```python
# Create plan record immediately
plan_id = db.create_weekly_plan(...)
db.update_weekly_plan(plan_id, status="processing")

# Initialize progress tracker with this plan_id
from backend.progress import progress_tracker
progress_tracker.tasks[plan_id] = {
    "progress": 0,
    "stage": "initialized",
    "message": "Processing started",
    "updates": []
}
```

### 2. Pass plan_id to Batch Processor

```python
# Process in background
async def process_in_background():
    result = await processor.process_user_week(
        request.user_id, 
        request.week_of, 
        request.provider, 
        slot_ids=request.slot_ids,
        plan_id=plan_id  # ← Pass the plan_id
    )
```

### 3. Use Provided plan_id in Batch Processor (`tools/batch_processor.py`)

```python
async def process_user_week(
    self,
    user_id: str,
    week_of: str,
    provider: str = "openai",
    week_folder_path: Optional[str] = None,
    slot_ids: Optional[list] = None,
    plan_id: Optional[str] = None,  # ← New parameter
) -> Dict[str, Any]:
    # ...
    
    # Create or use existing weekly plan record
    if not plan_id:
        # Create new plan if not provided
        plan_id = self.db.create_weekly_plan(...)
    
    # Use this plan_id for all progress updates
    progress_tracker.update(plan_id, "processing", 0, "Starting...")
```

## How It Works Now

```
API (plan_id: ABC123)
  ↓
  Creates DB record with ABC123
  ↓
  Initializes progress_tracker.tasks[ABC123]
  ↓
  Returns ABC123 to frontend
  ↓
  Starts background task with plan_id=ABC123
    ↓
    BatchProcessor uses ABC123 (doesn't create new one)
    ↓
    Updates progress with ABC123
    
Frontend polls for ABC123 ← MATCH! Shows real progress ✅
```

## Files Modified

| File | Changes | Purpose |
|------|---------|---------|
| `backend/api.py` | +8 lines | Initialize progress tracker, pass plan_id |
| `tools/batch_processor.py` | +3 lines | Accept plan_id parameter, use if provided |

## Expected Behavior

### Before Fix
- Progress bar shows canned stages (fake progress)
- No connection to actual processing
- Always completes in ~3 seconds regardless of real work

### After Fix
- Progress bar shows real processing stages
- Updates as slots are processed
- Reflects actual LLM calls and rendering
- Shows accurate progress percentage

## Testing

### Manual Test
1. Start backend and frontend
2. Process a lesson plan
3. Watch progress bar
4. Should see:
   - "Processing slot 1/3: ELA (Teacher Name)"
   - "Processing slot 2/3: Math (Teacher Name)"
   - Progress percentage increases with actual work
   - Final: "Rendering complete!"

### Verify in Logs
```bash
# Check that progress updates are being recorded
grep "progress_tracker.update" logs/*.log
```

## Backward Compatibility

✅ **Maintains backward compatibility**:
- If `plan_id` is not provided, batch processor creates one (old behavior)
- Existing code that doesn't pass `plan_id` still works
- No breaking changes to API

## Status

✅ **Implementation complete**  
⏭️ **Ready for testing**  

The progress bar will now show real processing status instead of fake progress.
