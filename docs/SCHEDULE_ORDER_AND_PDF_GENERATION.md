# Schedule Order and PDF Generation

## Overview

This document explains how the schedule order from the `schedules` table determines the order of objectives and sentence frames in the generated PDFs. The system ensures that each day's slots are ordered chronologically based on their actual schedule times, accounting for the fact that subjects, grades, and rooms can vary from day to day.

## Key Concepts

### 1. Schedule vs. Class Slots

**Schedule Entries** (`schedules` table):
- Represent the actual daily schedule with specific times
- Each entry has: `day_of_week`, `slot_number`, `start_time`, `end_time`, `subject`, `grade`, `homeroom`
- Schedule slot numbers may differ from class slot numbers
- Example: Schedule might have Slot 2, 3, 6, 7, 8, 9, but class slots are 1, 2, 4, 5, 6

**Class Slots** (`class_slots` table):
- Represent the configured lesson slots for a teacher
- Each slot has: `slot_number`, `subject`, `grade`, `homeroom`
- These are the slots that get lesson plans generated

### 2. Day-Specific Variations

**Critical Understanding**: The schedule can vary by day:
- **Time slots are consistent**: The same time periods exist across all days (e.g., 08:30-09:15, 09:18-10:03)
- **Content varies by day**: Subject, grade, and room assignments can differ for each day
- **Example**:
  - Monday: Slot 2 = ELA (Grade 3, T5) at 08:30
  - Wednesday: Slot 2 = ELA/SS (Grade 2, 209) at 08:30
  - Wednesday: Slot 4 = PLC Meeting (not a lesson slot)

## The Enrichment Process

### Step 1: Lesson JSON Generation

When lesson plans are generated, the system creates a `lesson_json` structure with slots based on class slot configurations. Initially, these slots may not have accurate `start_time` and `end_time` values that match the day-specific schedule.

### Step 2: Time Enrichment (`enrich_lesson_json_with_times`)

**Location**: `backend/api.py`

**Purpose**: Matches lesson JSON slots to schedule entries and enriches them with day-specific times.

**Matching Strategy** (in order of specificity):

1. **Exact Match**: `(day, slot_number, subject)`
   - Tries to match by exact slot number and subject first

2. **Full Match**: `(day, subject, grade, homeroom)`
   - Primary matching strategy
   - Matches by all three attributes: subject, grade, and room
   - Handles cases where schedule slot numbers differ from class slot numbers

3. **Subject + Grade Match**: `(day, subject, grade)`
   - Fallback if homeroom doesn't match exactly

4. **Subject Only Match**: `(day, subject)`
   - Final fallback if grade/homeroom don't match

**Process**:
1. Builds maps of schedule entries indexed by various combinations of (day, subject, grade, homeroom)
2. For each day in the lesson JSON:
   - Sorts slots by their current `start_time` (if available) or `slot_number`
   - Matches each slot to schedule entries using the matching strategies above
   - Updates `start_time` and `end_time` from the matched schedule entry
   - Reorders slots chronologically based on their new `start_time` values

**When Called**: 
- After merging lesson JSONs in `tools/batch_processor.py` (before PDF generation)
- When retrieving plan details via API (for real-time viewing)

### Step 3: Slot Sorting (`sort_slots`)

**Location**: `backend/services/sorting_utils.py`

**Purpose**: Sorts slots chronologically by their schedule times.

**Sorting Logic**:
1. **Primary Key**: Presence of `start_time` (slots with times come first)
2. **Secondary Key**: `start_time` value (chronological order - converted to minutes since midnight)
3. **Tertiary Key**: `slot_number` (fallback if no time available)

**Result**: Slots are ordered by their actual schedule times, ensuring chronological order for each day.

## PDF Generation

### Objectives PDF Generation

**Location**: `backend/services/objectives_pdf_generator.py`

**Process**:
1. Extracts objectives from `lesson_json` for each day
2. For each day, calls `sort_slots()` to order slots chronologically
3. Processes slots in sorted order (by `start_time`)
4. Generates PDF pages with objectives in chronological order

**Key Code**:
```python
# Sort slots by start_time (chronological) with slot_number as fallback
sorted_slots = sort_slots(day_data["slots"])
for slot in sorted_slots:
    # Extract objectives from slot in chronological order
    self._extract_from_slot(...)
```

### Sentence Frames PDF Generation

**Location**: `backend/services/sentence_frames_pdf_generator.py`

**Process**:
1. Extracts sentence frames from `lesson_json` for each day
2. For each day, calls `sort_slots()` to order slots chronologically
3. Processes slots in sorted order (by `start_time`)
4. Generates PDF pages with sentence frames in chronological order

**Key Code**:
```python
# Sort slots by start_time (chronological) with slot_number as fallback
sorted_slots = sort_slots(slots)
for slot in sorted_slots:
    # Extract sentence frames from slot in chronological order
    # ... process slot
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Schedule Table (schedules)                               │
│    - day_of_week, slot_number, start_time, end_time         │
│    - subject, grade, homeroom                                │
│    - Varies by day (subject/grade/room can differ)          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Class Slots (class_slots)                                │
│    - slot_number, subject, grade, homeroom                  │
│    - Used to generate lesson plans                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Lesson JSON Generation                                   │
│    - Creates slots based on class slot configs              │
│    - May have incorrect or missing start_time values        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Time Enrichment (enrich_lesson_json_with_times)         │
│    - Matches slots to schedule by (day, subject, grade,     │
│      homeroom)                                               │
│    - Updates start_time and end_time from schedule           │
│    - Reorders slots chronologically                         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Slot Sorting (sort_slots)                                │
│    - Sorts by start_time (chronological)                    │
│    - Ensures correct order for PDF generation               │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. PDF Generation                                           │
│    - Objectives PDF: Extracts in sorted order               │
│    - Sentence Frames PDF: Extracts in sorted order          │
│    - Result: PDFs reflect actual daily schedule order        │
└─────────────────────────────────────────────────────────────┘
```

## Example Scenario

### Schedule Configuration

**Monday Schedule**:
- 08:30-09:15: Slot 2 = ELA (Grade 3, T5)
- 09:18-10:03: Slot 3 = ELA/SS (Grade 3, T5)
- 11:42-12:27: Slot 6 = SCIENCE (Grade 3, T5)
- 13:18-14:03: Slot 8 = MATH (Grade 3, T5)
- 14:06-15:00: Slot 9 = MATH (Grade 3, T5)

**Wednesday Schedule**:
- 08:30-09:15: Slot 2 = ELA (Grade 3, T5)
- 09:18-10:03: Slot 3 = ELA/SS (Grade 3, T5)
- 10:06-10:51: Slot 4 = PLC Meeting (not a lesson)
- 11:42-12:27: Slot 6 = ELA/SS (Grade 2, 209)
- 12:30-13:15: Slot 7 = SCIENCE (Grade 2, 209)
- 13:18-14:03: Slot 8 = MATH (Grade 2, 209)
- 14:06-15:00: Slot 9 = MATH (Grade 2, 209)

### Class Slots Configuration

- Slot 1: ELA (Grade 3, T5)
- Slot 2: ELA/SS (Grade 3, T5)
- Slot 4: Math (Grade 3, T5)
- Slot 5: Math (Grade 3, T5)
- Slot 6: Science (Grade 3, T5)

### Enrichment Process

**Monday**:
1. Slot 1 (ELA, Grade 3, T5) → Matches Schedule Slot 2 → `start_time = 08:30`
2. Slot 2 (ELA/SS, Grade 3, T5) → Matches Schedule Slot 3 → `start_time = 09:18`
3. Slot 6 (Science, Grade 3, T5) → Matches Schedule Slot 6 → `start_time = 11:42`
4. Slot 4 (Math, Grade 3, T5) → Matches Schedule Slot 8 → `start_time = 13:18`
5. Slot 5 (Math, Grade 3, T5) → Matches Schedule Slot 9 → `start_time = 14:06`

**Sorted Order**: 1 (08:30), 2 (09:18), 6 (11:42), 4 (13:18), 5 (14:06)

**Wednesday**:
1. Slot 1 (ELA, Grade 3, T5) → Matches Schedule Slot 2 → `start_time = 08:30`
2. Slot 2 (ELA/SS, Grade 3, T5) → Matches Schedule Slot 3 → `start_time = 09:18`
3. Slot 6 (Science, Grade 3, T5) → **No match** (Schedule has Science at Grade 2, 209)
   - Falls back to subject match → Matches Schedule Slot 7 → `start_time = 12:30`
4. Slot 4 (Math, Grade 3, T5) → **No match** (Schedule has Math at Grade 2, 209)
   - Falls back to subject match → Matches Schedule Slot 8 → `start_time = 13:18`
5. Slot 5 (Math, Grade 3, T5) → **No match** (Schedule has Math at Grade 2, 209)
   - Falls back to subject match → Matches Schedule Slot 9 → `start_time = 14:06`

**Sorted Order**: 1 (08:30), 2 (09:18), 6 (12:30), 4 (13:18), 5 (14:06)

### PDF Output

**Monday Objectives PDF**:
- Page 1: ELA (08:30) - Grade 3 | T5
- Page 2: ELA/SS (09:18) - Grade 3 | T5
- Page 3: Science (11:42) - Grade 3 | T5
- Page 4: Math (13:18) - Grade 3 | T5
- Page 5: Math (14:06) - Grade 3 | T5

**Wednesday Objectives PDF**:
- Page 1: ELA (08:30) - Grade 3 | T5
- Page 2: ELA/SS (09:18) - Grade 3 | T5
- Page 3: Science (12:30) - Grade 3 | T5 (note: schedule shows Grade 2, 209, but lesson JSON has Grade 3)
- Page 4: Math (13:18) - Grade 3 | T5
- Page 5: Math (14:06) - Grade 3 | T5

**Note**: The PDF shows the grade/room from the lesson JSON (class slot config), but the time and order come from the schedule.

## Important Notes

1. **Matching Priority**: The system prioritizes exact matches (subject + grade + homeroom) but falls back gracefully if exact matches aren't found.

2. **Chronological Ordering**: Slots are always sorted by `start_time` to ensure chronological order, regardless of their `slot_number`.

3. **Day-Specific**: Each day's slots are enriched and sorted independently, ensuring correct ordering even when schedules vary by day.

4. **Fallback Behavior**: If a slot cannot be matched to a schedule entry, it retains its original `start_time` (if any) and is sorted accordingly.

5. **PDF Consistency**: Both Objectives and Sentence Frames PDFs use the same sorting logic, ensuring consistent ordering across document types.

## Troubleshooting

### Issue: Slots appear in wrong order in PDFs

**Check**:
1. Verify schedule entries exist for all days in `schedules` table
2. Verify schedule entries have correct `subject`, `grade`, `homeroom` values
3. Check if `enrich_lesson_json_with_times` is being called before PDF generation
4. Verify slots in `lesson_json` have `start_time` values after enrichment

### Issue: Slots not matching schedule entries

**Check**:
1. Verify subject names match exactly (case-insensitive, but spelling must match)
2. Verify grade values match (e.g., "3" vs "Grade 3")
3. Verify homeroom values match (e.g., "T5" vs "T-5")
4. Check debug logs for "NO MATCH FOUND" messages

### Issue: Same order for all days

**Cause**: Enrichment may not be running, or slots may not have day-specific times.

**Solution**: Ensure `enrich_lesson_json_with_times` is called after merging lesson JSONs and before PDF generation.
