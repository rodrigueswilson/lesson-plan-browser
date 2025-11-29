# Start Here Tomorrow - Metadata Matching Fix

## Quick Status

✅ **Completed Today:**
- Fixed all Pydantic conversion errors (User, ClassSlot, PerformanceMetric)
- Implemented metadata enrichment in batch processor
- W47 successfully generated (no crashes)

❌ **Still Broken:**
- Slot matching is incorrect - wrong lessons showing for schedule entries
- Metadata enrichment logic is flawed

## The Problem

**Schedule Entry → Lesson Mismatch:**
- ELA Grade 2 • 209 • 09:18-10:03 → Shows **Science** lesson
- SOCIAL S. Grade 2 • 209 • 10:06-10:51 → Shows **Math** lesson  
- MATH Grade 2 • 209 • 14:06-15:00 → Shows same Math (duplicate)
- MATH Grade 3 • T2 • 12:30-13:15 → Shows **Grade 2 Math** (wrong grade)

## Root Cause Hypothesis

The enrichment code matches by `slot_number` alone:
```python
matching_entries = [e for e in schedule_entries if e.slot_number == slot['slot_number']]
```

**This is wrong because:**
- Slot numbers are not unique across subjects/grades/days
- Thursday slot 2 ≠ Friday slot 2
- Grade 2 slot 2 ≠ Grade 3 slot 2

The code picks "most common time" for a slot_number, which gives wrong metadata.

## First Steps Tomorrow

### 1. Check Generated JSON (2 min)
```bash
# Find the latest W47 JSON
dir output\Wilson*.json | sort -Descending | select -First 1

# Check metadata in slots
python -c "import json; data=json.load(open('output/Wilson_Weekly_W47_[TIMESTAMP].json')); import pprint; pprint.pprint(data['days']['thursday']['slots'][:2])"
```

**Look for:**
- Do slots have `grade`, `homeroom`, `start_time`, `end_time`?
- Are values correct or all the same?

### 2. Check ClassSlot Configuration (3 min)
```python
from backend.database import get_db
db = get_db(user_id='<wilson_id>')
slots = [s.model_dump() for s in db.get_user_slots('<wilson_id>')]

for s in slots:
    print(f"Slot {s['slot_number']}: {s['subject']} | Grade {s['grade']} | Homeroom {s.get('homeroom', 'N/A')}")
```

**Look for:**
- Multiple slots with same slot_number?
- Do subjects match what you expect?

### 3. Check Schedule Entries (3 min)
```python
entries = db.get_user_schedule('<wilson_id>', day_of_week='thursday')
for e in entries:
    print(f"Slot {e.slot_number}: {e.subject} | {e.grade} {e.homeroom} | {e.start_time}-{e.end_time}")
```

**Look for:**
- Are slot numbers unique per day?
- Do they match ClassSlot numbers?

## The Fix (Recommendation)

### Change Enrichment Logic
**File:** `tools/batch_processor.py` lines 142-169

**From:**
```python
matching_entries = [e for e in schedule_entries if e.slot_number == slot['slot_number'] and e.is_active]
```

**To:**
```python
# Match by subject + grade + homeroom, not slot_number
matching_entries = [
    e for e in schedule_entries 
    if e.subject.lower().strip() == slot['subject'].lower().strip()
    and e.grade == slot['grade'] 
    and (e.homeroom == slot.get('homeroom') or not slot.get('homeroom'))
    and e.is_active
]
```

### Why This Works:
- ClassSlots define **what** to teach (subject, grade, homeroom)
- ScheduleEntries define **when** to teach (times, days)
- Match them by the "what", extract the "when"

### Alternative: Use Day-Specific Matching
If a ClassSlot is used on multiple days with different times:
```python
# During per-day processing, match for that specific day
matching_entries = [
    e for e in schedule_entries 
    if e.day_of_week == current_day  # Add day filter
    and e.subject == slot['subject']
    and e.grade == slot['grade']
    and e.homeroom == slot.get('homeroom')
]
```

## Testing After Fix

1. Regenerate W47
2. Check these specific entries in browser:
   - ELA Grade 2 • 209 • 09:18-10:03 → Should show ELA lesson
   - SOCIAL S. Grade 2 • 209 • 10:06-10:51 → Should show Social Studies
   - MATH Grade 2 • 209 • 14:06-15:00 → Should show Math Grade 2
   - MATH Grade 3 • T2 • 12:30-13:15 → Should show Math Grade 3

## Files to Modify

1. `tools/batch_processor.py` - Fix enrichment matching logic (lines 142-169)
2. Possibly `tools/json_merger.py` - Verify metadata extraction is correct

## Documentation Created Today

- `docs/archive/fixes/METADATA_FIX_COMPLETE.md` - Original metadata implementation plan
- `PYDANTIC_CONVERSION_FIXES.md` - All conversion error fixes
- `METADATA_MATCHING_ISSUE.md` - Detailed problem analysis
- `TOMORROW_START_HERE.md` - This file

## Key Insight

**The core issue:** We're trying to enrich ClassSlots with schedule metadata by matching on `slot_number`, but slot numbers are not a stable identifier. They vary by day and context.

**The solution:** Match by semantic identity (subject + grade + homeroom) instead of positional identity (slot_number).
