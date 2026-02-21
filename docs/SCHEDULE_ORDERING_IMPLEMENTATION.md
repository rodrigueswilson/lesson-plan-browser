# Schedule Ordering Implementation

## Overview

This document explains how the codebase ensures that objectives and sentence frames PDFs display slots in the correct chronological order based on the daily schedule. The system handles day-specific schedule variations where subjects, grades, and rooms can differ from day to day.

## Architecture

The ordering system consists of three main components:

1. **Time Enrichment** (`backend/api.py`): Matches lesson JSON slots to schedule entries and adds day-specific `start_time` and `end_time` values
2. **Slot Sorting** (`backend/services/sorting_utils.py`): Sorts slots chronologically by `start_time`
3. **PDF Generation** (`backend/services/objectives_pdf_generator.py` and `backend/services/sentence_frames_pdf_generator.py`): Extracts and renders data in sorted order

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Schedule Table (schedules)                               │
│    - day_of_week, slot_number, start_time, end_time         │
│    - subject, grade, homeroom (varies by day)               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Lesson JSON Generation                                   │
│    - Slots created from class_slots configuration          │
│    - May have incorrect or missing start_time values        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Time Enrichment                                          │
│    enrich_lesson_json_with_times()                         │
│    - Matches slots to schedule by (day, subject, grade,    │
│      homeroom)                                              │
│    - Updates start_time and end_time from schedule         │
│    - Reorders slots chronologically                         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Slot Sorting                                             │
│    sort_slots()                                             │
│    - Sorts by start_time (chronological)                   │
│    - Fallback to slot_number if no time                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. PDF Generation                                           │
│    - Objectives: extract_objectives() → sort_slots()        │
│    - Sentence Frames: extract_sentence_frames() →          │
│      sort_slots() → sort results                            │
│    - Both render in chronological order                     │
└─────────────────────────────────────────────────────────────┘
```

## Component 1: Time Enrichment

### Location
`backend/api.py` - `enrich_lesson_json_with_times()`

### Purpose
Matches lesson JSON slots to schedule entries and enriches them with day-specific `start_time` and `end_time` values. This is critical because schedule slot numbers may differ from class slot numbers, and schedules vary by day.

### Matching Strategy

The function uses a multi-level matching strategy (in order of specificity):

1. **Exact Match**: `(day, slot_number, subject)`
   - Tries to match by exact slot number and subject first

2. **Full Match**: `(day, subject, grade, homeroom)` ⭐ **Primary Strategy**
   - Matches by all three attributes: subject, grade, and room
   - Handles cases where schedule slot numbers differ from class slot numbers

3. **Subject + Grade Match**: `(day, subject, grade)`
   - Fallback if homeroom doesn't match exactly

4. **Subject Only Match**: `(day, subject)`
   - Final fallback if grade/homeroom don't match

### Implementation Details

```python
def enrich_lesson_json_with_times(lesson_json: Dict[str, Any], user_id: str) -> None:
    """Enrich lesson_json with start_time and end_time from schedules table."""
    
    # Build maps for flexible matching
    full_match_map = {}      # (day, subject, grade, homeroom) -> entries
    subject_grade_map = {}   # (day, subject, grade) -> entries
    subject_time_map = {}    # (day, subject) -> entries
    exact_map = {}           # (day, slot_number, subject) -> entry
    
    # Populate maps from schedule entries
    for entry in schedule:
        # Normalize values for comparison
        subject = normalize_value(entry.subject)
        grade = normalize_value(entry.grade)
        homeroom = normalize_value(entry.homeroom)
        
        # Build all matching keys
        key_full = (day, subject, grade, homeroom)
        key_sg = (day, subject, grade)
        key_subj = (day, subject)
        
        # Add to maps...
    
    # For each day, match slots to schedule entries
    for day_name, day_data in lesson_json["days"].items():
        slots = day_data.get("slots", [])
        
        # Sort slots by current start_time (if available) or slot_number
        sorted_slots = sorted(slots, key=get_slot_sort_key)
        
        # Match each slot to schedule entries
        for slot in sorted_slots:
            times = get_times(slot)  # Uses matching strategies above
            if times:
                slot["start_time"] = times[0]
                slot["end_time"] = times[1]
        
        # Update slots list with sorted order
        day_data["slots"] = sorted_slots
```

### Key Features

- **Normalization**: Values are normalized (lowercase, trimmed) for consistent comparison
- **Chronological Matching**: Slots are matched in chronological order to avoid conflicts
- **Used Entry Tracking**: Prevents matching the same schedule entry to multiple slots
- **Day-Specific**: Each day's slots are enriched independently

### When Called

1. **After Merging Lesson JSONs** (`tools/batch_processor.py:4241`):
   ```python
   # After merging all lesson JSONs
   enrich_lesson_json_with_times(merged_json, user_id)
   ```

2. **When Retrieving Plan Details** (`backend/api.py:904`):
   ```python
   # When API endpoint returns plan details
   enrich_lesson_json_with_times(lesson_json, user_id)
   ```

## Component 2: Slot Sorting

### Location
`backend/services/sorting_utils.py` - `sort_slots()`

### Purpose
Sorts slots chronologically by their `start_time` values, ensuring correct order for PDF generation.

### Sorting Logic

```python
def sort_slots(slots: Union[List[Any], Dict[str, Any]]) -> List[Any]:
    """Sort lesson plan slots by start_time (chronological) with slot_number as fallback."""
    
    def get_sort_key(slot: Any) -> tuple:
        start_time = slot.get("start_time", "") or ""
        slot_num = slot.get("slot_number", 0)
        
        # Convert time to sortable format (HH:MM -> minutes since midnight)
        time_sort = 0
        if start_time:
            try:
                parts = str(start_time).split(":")
                if len(parts) >= 2:
                    time_sort = int(parts[0]) * 60 + int(parts[1])
            except (ValueError, TypeError):
                pass
            return (0, time_sort, slot_num)  # Has time: sort by time, then slot_number
        else:
            return (1, 0, slot_num)  # No time: sort by slot_number only
    
    return sorted(slot_list, key=get_sort_key)
```

### Sort Key Structure

The sort key is a tuple: `(has_time_flag, time_in_minutes, slot_number)`

- **Primary Key**: `has_time_flag` (0 if has time, 1 if no time)
  - Ensures slots with times come before slots without times
  
- **Secondary Key**: `time_in_minutes` (converted from HH:MM format)
  - Ensures chronological ordering
  
- **Tertiary Key**: `slot_number`
  - Fallback for slots without times or with same time

### Example

Given slots:
- Slot 1: `start_time = "08:30"` → `(0, 510, 1)`
- Slot 2: `start_time = "09:18"` → `(0, 558, 2)`
- Slot 6: `start_time = "11:42"` → `(0, 702, 6)`
- Slot 4: `start_time = "14:06"` → `(0, 846, 4)`
- Slot 5: `start_time = "14:06"` → `(0, 846, 5)`

Sorted order: `[1, 2, 6, 4, 5]` (chronological by time, then by slot_number for same time)

## Component 3: Objectives PDF Generation

### Location
`backend/services/objectives_pdf_generator.py`

### Extraction Process

```python
def extract_objectives(self, lesson_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract objectives from lesson JSON, ordered by schedule."""
    
    objectives = []
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    
    for day_name in day_names:
        day_data = days[day_name]
        
        if "slots" in day_data and isinstance(day_data["slots"], list):
            # Multi-slot: sort slots chronologically
            sorted_slots = sort_slots(day_data["slots"])
            
            # Process slots in sorted order
            for slot in sorted_slots:
                self._extract_from_slot(slot, day_name, ..., objectives, ...)
    
    return objectives
```

### Key Points

1. **Day-by-Day Processing**: Processes days in order (Monday → Friday)
2. **Slot Sorting**: Calls `sort_slots()` for each day's slots
3. **Chronological Extraction**: Extracts objectives in sorted order
4. **Result Order**: Objectives list maintains chronological order

### Rendering

```python
def generate_html(self, lesson_json, output_path, user_name):
    """Generate HTML with objectives pages."""
    
    objectives = self.extract_objectives(lesson_json)
    
    # Render pages in order (already sorted)
    for obj in objectives:
        pages.append(self._render_objective_page(obj))
    
    # Generate HTML
    final_html = self.html_template.format(pages="\n".join(pages))
```

## Component 4: Sentence Frames PDF Generation

### Location
`backend/services/sentence_frames_pdf_generator.py`

### Extraction Process

```python
def extract_sentence_frames(self, lesson_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract sentence frame payloads, ordered by schedule."""
    
    results = []
    day_names = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    
    for day_name in day_names:
        day_data = days.get(day_name)
        slots = day_data.get("slots") or []
        
        if isinstance(slots, list) and len(slots) > 0:
            # Sort slots chronologically
            sorted_slots = sort_slots(slots)
            
            # Process slots in sorted order
            for slot in sorted_slots:
                results.append({
                    "day": day_name.capitalize(),
                    "slot_number": slot.get("slot_number", 0),
                    "start_time": slot.get("start_time", ""),  # Include for sorting
                    # ... other fields
                })
    
    # CRITICAL: Sort results after extraction
    # This ensures correct order across all days
    results.sort(key=get_result_sort_key)
    return results
```

### Post-Extraction Sorting

After extracting all results, the function explicitly sorts them:

```python
def get_result_sort_key(result: Dict[str, Any]) -> tuple:
    """Sort key for results: (day_index, time_in_minutes, slot_number)."""
    day = result.get("day", "")
    day_idx = day_order.get(day, 99)  # Monday=0, Tuesday=1, etc.
    start_time = result.get("start_time", "") or ""
    slot_num = result.get("slot_number", 0)
    
    # Convert time to minutes
    time_sort = 0
    if start_time:
        try:
            parts = str(start_time).split(":")
            if len(parts) >= 2:
                time_sort = int(parts[0]) * 60 + int(parts[1])
        except (ValueError, TypeError):
            pass
    
    return (day_idx, time_sort, slot_num)

day_order = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4}
results.sort(key=get_result_sort_key)
```

### Why Post-Extraction Sorting?

Unlike objectives, sentence frames results are built across all days before rendering. The post-extraction sort ensures:

1. **Day Order**: Monday → Friday
2. **Time Order**: Chronological within each day
3. **Consistency**: Same order as objectives and schedule

### Rendering

```python
def generate_html(self, lesson_json, output_path, user_name):
    """Generate HTML with sentence frames pages."""
    
    payloads = self.extract_sentence_frames(lesson_json)
    # payloads are already sorted by day and start_time
    
    # Render pages in order
    for payload in payloads:
        pages.append(self._render_page_pair(payload, metadata))
    
    # Generate HTML
    final_html = self.html_template.format(pages="\n".join(pages))
```

## Complete Example

### Input: Schedule (varies by day)

**Monday Schedule**:
- 08:30-09:15: Slot 2 = ELA (Grade 3, T5)
- 09:18-10:03: Slot 3 = ELA/SS (Grade 3, T5)
- 11:42-12:27: Slot 6 = SCIENCE (Grade 3, T5)
- 13:18-14:03: Slot 8 = MATH (Grade 3, T5)
- 14:06-15:00: Slot 9 = MATH (Grade 3, T5)

**Wednesday Schedule**:
- 08:30-09:15: Slot 2 = ELA (Grade 3, T5)
- 09:18-10:03: Slot 3 = ELA/SS (Grade 3, T5)
- 11:42-12:27: Slot 6 = ELA/SS (Grade 2, 209)  ← Different grade/room!
- 12:30-13:15: Slot 7 = SCIENCE (Grade 2, 209)
- 13:18-14:03: Slot 8 = MATH (Grade 2, 209)
- 14:06-15:00: Slot 9 = MATH (Grade 2, 209)

### Step 1: Lesson JSON (Before Enrichment)

```json
{
  "days": {
    "monday": {
      "slots": [
        {"slot_number": 1, "subject": "ELA", "grade": "3", "homeroom": "T5"},
        {"slot_number": 2, "subject": "ELA/SS", "grade": "3", "homeroom": "T5"},
        {"slot_number": 6, "subject": "Science", "grade": "3", "homeroom": "T5"},
        {"slot_number": 4, "subject": "Math", "grade": "3", "homeroom": "T5"},
        {"slot_number": 5, "subject": "Math", "grade": "3", "homeroom": "T5"}
      ]
    },
    "wednesday": {
      "slots": [
        {"slot_number": 1, "subject": "ELA", "grade": "3", "homeroom": "T5"},
        {"slot_number": 2, "subject": "ELA/SS", "grade": "3", "homeroom": "T5"},
        {"slot_number": 6, "subject": "Science", "grade": "3", "homeroom": "T5"},
        {"slot_number": 4, "subject": "Math", "grade": "3", "homeroom": "T5"},
        {"slot_number": 5, "subject": "Math", "grade": "3", "homeroom": "T5"}
      ]
    }
  }
}
```

### Step 2: Time Enrichment

**Monday**:
- Slot 1 (ELA, Grade 3, T5) → Matches Schedule Slot 2 → `start_time = "08:30"`
- Slot 2 (ELA/SS, Grade 3, T5) → Matches Schedule Slot 3 → `start_time = "09:18"`
- Slot 6 (Science, Grade 3, T5) → Matches Schedule Slot 6 → `start_time = "11:42"`
- Slot 4 (Math, Grade 3, T5) → Matches Schedule Slot 8 → `start_time = "13:18"`
- Slot 5 (Math, Grade 3, T5) → Matches Schedule Slot 9 → `start_time = "14:06"`

**Wednesday**:
- Slot 1 (ELA, Grade 3, T5) → Matches Schedule Slot 2 → `start_time = "08:30"`
- Slot 2 (ELA/SS, Grade 3, T5) → Matches Schedule Slot 3 → `start_time = "09:18"`
- Slot 6 (Science, Grade 3, T5) → **No exact match** (Schedule has Grade 2, 209)
  - Falls back to subject match → Matches Schedule Slot 7 → `start_time = "12:30"`
- Slot 4 (Math, Grade 3, T5) → **No exact match** (Schedule has Grade 2, 209)
  - Falls back to subject match → Matches Schedule Slot 8 → `start_time = "13:18"`
- Slot 5 (Math, Grade 3, T5) → **No exact match** (Schedule has Grade 2, 209)
  - Falls back to subject match → Matches Schedule Slot 9 → `start_time = "14:06"`

### Step 3: Slot Sorting

**Monday** (after `sort_slots()`):
```python
[
  {"slot_number": 1, "start_time": "08:30"},  # 510 minutes
  {"slot_number": 2, "start_time": "09:18"},  # 558 minutes
  {"slot_number": 6, "start_time": "11:42"},  # 702 minutes
  {"slot_number": 4, "start_time": "13:18"},  # 798 minutes
  {"slot_number": 5, "start_time": "14:06"}   # 846 minutes
]
```

**Wednesday** (after `sort_slots()`):
```python
[
  {"slot_number": 1, "start_time": "08:30"},  # 510 minutes
  {"slot_number": 2, "start_time": "09:18"},  # 558 minutes
  {"slot_number": 6, "start_time": "12:30"},  # 750 minutes (different from Monday!)
  {"slot_number": 4, "start_time": "13:18"},  # 798 minutes
  {"slot_number": 5, "start_time": "14:06"}   # 846 minutes
]
```

### Step 4: PDF Generation

**Objectives PDF**:
- Monday: Pages in order [1, 2, 6, 4, 5] (chronological)
- Wednesday: Pages in order [1, 2, 6, 4, 5] (chronological, but Slot 6 has different time)

**Sentence Frames PDF**:
- All days: Pages sorted by (day_index, start_time, slot_number)
- Monday: [1, 2, 6, 4, 5]
- Wednesday: [1, 2, 6, 4, 5] (Slot 6 appears at 12:30, not 11:42)

## Key Design Decisions

### 1. Why Match by (Subject, Grade, Homeroom)?

Schedule slot numbers can differ from class slot numbers. Matching by content attributes ensures correct time assignment even when slot numbers don't align.

### 2. Why Sort After Extraction for Sentence Frames?

Sentence frames results are built across all days before rendering. Post-extraction sorting ensures consistent ordering matching the schedule, even if extraction order varies.

### 3. Why Include `start_time` in Results?

Including `start_time` in sentence frames results enables post-extraction sorting by chronological order, matching objectives and schedule.

### 4. Why Day-Specific Enrichment?

Each day's schedule can vary (different subjects, grades, rooms). Day-specific enrichment ensures each day's slots get the correct times from that day's schedule.

## Testing

To verify correct ordering:

1. **Check Enrichment**: Verify slots have correct `start_time` values after enrichment
2. **Check Sorting**: Verify `sort_slots()` produces chronological order
3. **Check PDFs**: Verify objectives and sentence frames appear in same order
4. **Check Schedule Match**: Verify PDF order matches schedule order for each day

## Troubleshooting

### Issue: Slots in wrong order

**Check**:
- Are slots enriched with `start_time`? (Check `enrich_lesson_json_with_times` is called)
- Do schedule entries exist for all days?
- Are subject/grade/homeroom values matching correctly?

### Issue: Different order between objectives and sentence frames

**Check**:
- Are both using `sort_slots()`?
- Are sentence frames results sorted after extraction?
- Do both include `start_time` in their data structures?

### Issue: Same order for all days

**Check**:
- Is enrichment running day-by-day?
- Are schedule entries day-specific?
- Are slots being reordered after enrichment?

## Code References

- **Time Enrichment**: `backend/api.py:197-407`
- **Slot Sorting**: `backend/services/sorting_utils.py:4-62`
- **Objectives Extraction**: `backend/services/objectives_pdf_generator.py:399-466`
- **Sentence Frames Extraction**: `backend/services/sentence_frames_pdf_generator.py:408-598`
- **Enrichment Call**: `tools/batch_processor.py:4238-4246`
