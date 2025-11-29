# Plan: Add Metadata to Lesson Plan Slots

## Problem
Lesson plan slots don't have grade, homeroom, or time metadata, making frontend matching complex and error-prone.

## Root Cause
1. **ClassSlot table** has: `slot_number`, `subject`, `grade`, `homeroom` (no time)
2. **ScheduleEntry table** has: all above PLUS `start_time`, `end_time`, `day_of_week`
3. **Batch processor** uses ClassSlot objects (no time data)
4. **json_merger.py** creates slot_info from lesson metadata (which had grade/homeroom but not time)

## Solution

### Step 1: Enrich slots with schedule data ✅ (DONE)
- Modified `json_merger.py` to copy `grade`, `homeroom`, `start_time`, `end_time` from lesson metadata to slot_info
- This works IF the metadata has this information

### Step 2: Ensure metadata has schedule time
Need to add schedule time information to lesson_json metadata when creating lessons.

Two options:
**A. Add to batch_processor._process_slot** (before transform_lesson)
- Enrich slot dict with schedule time before processing
- Pass to LLM service which adds to metadata

**B. Add time to ClassSlot table**
- Store start_time/end_time in ClassSlot (derive from most common schedule entry)
- No code changes needed - slots would have time automatically

## Recommendation: Option A
Simpler and doesn't require schema migration. The schedule entry times are the source of truth.

### Implementation:
1. In `batch_processor.process_user_week`, before processing each slot:
   - Query schedule entries for this user
   - Find matching schedule entry by slot_number
   - Add start_time/end_time to slot dict

2. In `batch_processor._process_slot`:
   - Pass start_time/end_time to LLM metadata
   
3. json_merger already extracts this metadata into slot_info ✅

## Files to Modify
1. `tools/batch_processor.py` - Add schedule enrichment
2. (Already done) `tools/json_merger.py` - Extract metadata to slots ✅

## Testing
After fix, verify:
```python
lesson_json['days']['thursday']['slots'][0] == {
    'slot_number': 2,
    'subject': 'ELA',
    'grade': '3',
    'homeroom': 'T5',
    'start_time': '08:30',
    'end_time': '09:15',
    ...  # rest of lesson content
}
```

This will make frontend matching trivial - just match all fields!
