# Metadata Fix Complete: Slots Now Include Full Metadata

## Problem Solved
Lesson plan slots were missing grade, homeroom, and time metadata, requiring complex frontend matching heuristics.

## Solution Implemented

### 1. Enrich Slots with Schedule Data (`batch_processor.py`)
**Lines 142-157:** After loading ClassSlot objects, now enriches them with schedule entry data:
- Queries all active schedule entries for the user
- For each slot, finds matching schedule entries by `slot_number`
- Extracts most common `start_time` and `end_time` (handles multi-day schedules)
- Adds these to the slot dict before processing

### 2. Preserve Time in Metadata (`batch_processor.py`)
**Lines 1226-1237:** Extended metadata preservation to include time:
```python
if slot.get("start_time"):
    lesson_json["metadata"]["start_time"] = slot["start_time"]
if slot.get("end_time"):
    lesson_json["metadata"]["end_time"] = slot["end_time"]
```

### 3. Extract Metadata to Slots (`json_merger.py`)
**Lines 136-152:** Already updated to copy metadata into slot_info:
- Copies `grade`, `homeroom`, `start_time`, `end_time` from lesson metadata
- These become part of each slot in the final merged JSON

## Result

**Before:**
```json
{
  "days": {
    "thursday": {
      "slots": [
        {
          "slot_number": 2,
          "subject": "ELA",
          // Missing: grade, homeroom, time
          "objective": {...},
          ...
        }
      ]
    }
  }
}
```

**After:**
```json
{
  "days": {
    "thursday": {
      "slots": [
        {
          "slot_number": 2,
          "subject": "ELA",
          "grade": "3",
          "homeroom": "T5",
          "start_time": "08:30",
          "end_time": "09:15",
          "objective": {...},
          ...
        }
      ]
    }
  }
}
```

## Frontend Impact

### Old Matching Logic (Complex)
```typescript
// Priority 1: Subject + Grade + Homeroom + Time (if all present)
// Priority 2: Subject + Grade + Homeroom (when missing time)  
// Priority 3: Slot number + subject compatibility
// Priority 4: Time as last resort
// Plus: Subject specificity ranking for compound subjects
```

### New Matching Logic (Simple)
```typescript
// Just match ALL fields:
slot.slot_number === entry.slot_number &&
slot.subject === entry.subject &&
slot.grade === entry.grade &&
slot.homeroom === entry.homeroom &&
slot.start_time === entry.start_time &&
slot.end_time === entry.end_time
```

## Files Modified

1. **`tools/batch_processor.py`**
   - Lines 142-157: Schedule data enrichment
   - Lines 1226-1237: Metadata preservation

2. **`tools/json_merger.py`**  
   - Lines 136-152: Metadata extraction to slot_info

## Testing

### To verify the fix works:
1. Generate a new lesson plan (backend will restart to pick up changes)
2. Check the saved `.json` file
3. Verify slots have complete metadata:
   ```bash
   python -c "import json; data=json.load(open('output/Wilson_...json')); print(data['days']['thursday']['slots'][0])"
   ```

4. Frontend matching should now be trivial and accurate

## Benefits

✅ **Eliminates ambiguity** - Each slot fully describes itself
✅ **Simplifies frontend** - No complex matching heuristics needed  
✅ **Prevents mismatches** - Exact field-by-field matching
✅ **Co-teaching friendly** - Multiple entries can still share slots
✅ **Future-proof** - Adding more metadata fields is now easy

## Next Steps

Once you've generated a new lesson plan, the frontend can be simplified to use direct metadata matching instead of the complex subject specificity logic.
