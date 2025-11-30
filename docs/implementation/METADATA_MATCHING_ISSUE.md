# Metadata Matching Issue - Needs Investigation Tomorrow

## Problem Report (Nov 19, 2025)

After implementing metadata enrichment, the new W47 lesson plan still has **incorrect slot matching**:

### Mismatches Found:

| Schedule Entry | Expected Lesson | Actual Lesson Shown | Issue |
|---|---|---|---|
| ELA Grade 2 • 209 • 09:18 - 10:03 | ELA lesson | 2nd grade **science** | Wrong subject |
| SOCIAL S. Grade 2 • 209 • 10:06 - 10:51 | Social Studies | **Math** lesson | Wrong subject |
| MATH Grade 2 • 209 • 14:06 - 15:00 | Math lesson | Math lesson (same as above) | Duplicate? |
| MATH Grade 3 • T2 • 12:30 - 13:15 | Math Grade 3 | **Same Math Grade 2** lesson | Wrong grade/homeroom |

## What We Implemented Today

### Backend Changes:
1. **`batch_processor.py`** (lines 142-169) - Enriched slots with schedule data
   - Queries schedule entries after loading ClassSlots
   - Finds matching entries by `slot_number`
   - Extracts `start_time` and `end_time` from most common schedule entry
   - Adds to slot dict

2. **`batch_processor.py`** (lines 1226-1237) - Preserved metadata
   - Added `start_time` and `end_time` to `lesson_json["metadata"]`

3. **`json_merger.py`** (lines 136-152) - Extracted metadata to slots
   - Copies `grade`, `homeroom`, `start_time`, `end_time` from lesson metadata to slot_info
   - These become part of each slot in merged JSON

### Expected Result:
```json
{
  "days": {
    "thursday": {
      "slots": [
        {
          "slot_number": 2,
          "subject": "ELA",
          "grade": "2",
          "homeroom": "209",
          "start_time": "09:18",
          "end_time": "10:03",
          ...
        }
      ]
    }
  }
}
```

## Why It's Still Failing

### Possible Causes:

#### 1. Schedule Data Enrichment Not Working
The enrichment code in `batch_processor.py` might not be finding matching schedule entries:
```python
matching_entries = [e for e in schedule_entries if e.slot_number == slot['slot_number'] and e.is_active]
```

**Problem:** This matches by `slot_number` only, but:
- Different subjects can share the same `slot_number` across different days
- Multiple grades/homerooms might use the same `slot_number`
- The "most common" time might not be correct for this specific context

#### 2. ClassSlot Configuration Issue
ClassSlot records might have:
- Wrong `slot_number` assignments
- Missing or incorrect `grade`/`homeroom` data
- Multiple slots with same `slot_number` but different subjects

#### 3. Metadata Not Being Used in Matching
Even if metadata is in the JSON, the frontend might not be using it for matching. The frontend matching logic in `planMatching.ts` might still be using old logic.

#### 4. Multiple Slots Mapped to Same Source
If multiple ClassSlots reference the same source DOCX file but extract different slot numbers, they could get mixed up content.

## Investigation Plan for Tomorrow

### Step 1: Verify Metadata in Generated JSON
Check the actual generated JSON file:
```bash
python -c "import json; data=json.load(open('output/Wilson_Weekly_W47_[timestamp].json')); print(json.dumps(data['days']['thursday']['slots'], indent=2))"
```

**Questions:**
- Do slots have `grade`, `homeroom`, `start_time`, `end_time`?
- Are the values correct for each slot?
- Are multiple slots sharing the same metadata?

### Step 2: Check ClassSlot Configuration
Query the database to see ClassSlot records:
```python
from backend.database import get_db
db = get_db(user_id='<wilson_user_id>')
slots = db.get_user_slots('<wilson_user_id>')
for slot in slots:
    print(f"Slot {slot.slot_number}: {slot.subject} | Grade {slot.grade} | Homeroom {slot.homeroom}")
```

**Questions:**
- Are there duplicate `slot_number` values?
- Do the slot numbers match the schedule?
- Are grade/homeroom values correct?

### Step 3: Check Schedule Entries
Query schedule entries to verify data:
```python
entries = db.get_user_schedule('<wilson_user_id>', day_of_week='thursday')
for e in entries:
    print(f"Slot {e.slot_number}: {e.subject} | Grade {e.grade} | {e.homeroom} | {e.start_time}-{e.end_time}")
```

**Questions:**
- Do schedule entries have correct slot numbers?
- Are there conflicts (same slot_number, different subjects)?
- Do the times match the reported schedule?

### Step 4: Trace the Enrichment Logic
Add debug logging to see what's happening:
```python
# In batch_processor.py, after enrichment
for slot in slots:
    print(f"Enriched slot {slot['slot_number']} ({slot['subject']}):")
    print(f"  Grade: {slot.get('grade')}")
    print(f"  Homeroom: {slot.get('homeroom')}")
    print(f"  Time: {slot.get('start_time')}-{slot.get('end_time')}")
```

### Step 5: Check Frontend Matching
Verify the frontend is using the new metadata:
- Open browser console
- Check what `slotData` contains for the problematic entries
- Verify `planMatching.ts` is using metadata fields for matching

## Likely Root Cause Hypothesis

**The enrichment logic is fundamentally flawed** because it matches by `slot_number` alone:

```python
matching_entries = [e for e in schedule_entries if e.slot_number == slot['slot_number'] and e.is_active]
```

This assumes:
- Each `slot_number` uniquely identifies a lesson across all days
- One `slot_number` = one subject/grade/homeroom combination

But in reality:
- **Slot numbers are per-day**, not global
- Thursday slot 2 could be "ELA Grade 2 209"
- Friday slot 2 could be "Math Grade 3 T2"
- The enrichment picks "most common" time, which might be wrong

## Better Approach for Tomorrow

### Option A: Match by Subject + Grade + Homeroom (Not Slot Number)
Instead of enriching by `slot_number`, match ClassSlots to ScheduleEntries by:
```python
matching_entries = [
    e for e in schedule_entries 
    if e.subject == slot['subject'] 
    and e.grade == slot['grade'] 
    and e.homeroom == slot.get('homeroom')
    and e.is_active
]
```

This ensures each ClassSlot gets metadata from the correct schedule context.

### Option B: Include Day Context in Enrichment
Since slots are processed per-week, we need day-specific metadata:
- Don't store single `start_time`/`end_time` on slot
- Store per-day times: `times_by_day = {'monday': '08:30-09:15', ...}`
- Add to metadata during per-day processing

### Option C: Rethink ClassSlot Design
Maybe ClassSlot shouldn't exist independently - it should be derived from ScheduleEntries:
- ScheduleEntries are the source of truth (they have all metadata)
- Processing should iterate over unique subject/grade/homeroom combinations from schedule
- Each combination becomes a "virtual slot" for that week

## Files to Check Tomorrow
1. `output/Wilson_Weekly_W47_[timestamp].json` - Check actual metadata
2. `backend/database.py` or UI - Check ClassSlot records
3. `backend/database.py` or UI - Check ScheduleEntry records  
4. `tools/batch_processor.py` lines 142-169 - Review enrichment logic
5. `frontend/src/utils/planMatching.ts` - Verify matching uses metadata

## Expected Outcome Tomorrow
- Understand why metadata is wrong/missing
- Implement correct metadata enrichment strategy
- Verify frontend uses metadata for matching
- Test with W47 regeneration
- Confirm all 4 reported mismatches are fixed
