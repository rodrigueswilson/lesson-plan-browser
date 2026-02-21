# Metadata Analysis: Slots, Lessons, and Document Generation

## Executive Summary

This analysis examines how metadata (teacher name, subject, room, date, etc.) is handled across slots, lessons, and document outputs (PDF/DOCX/HTML). Several inconsistencies were identified in how metadata flows through the system and is used in objectives and sentence frames.

## 1. Slot and Lesson Metadata Structure

### 1.1 Slot Metadata Model (`backend/models_slot.py`)

The `SlotMetadata` model defines the following fields:

```python
class SlotMetadata(BaseModel):
    slot_number: int  # 1-10
    subject: str
    grade: str
    homeroom: Optional[str]
    primary_teacher_name: str
    primary_teacher_first_name: Optional[str]
    primary_teacher_last_name: Optional[str]
    primary_teacher_file: Optional[str]
    proficiency_levels: Optional[List[str]]
```

**Key Observations:**
- **Room number is NOT included** in the SlotMetadata model
- Teacher name has multiple representations: `primary_teacher_name` (full), `primary_teacher_first_name`, `primary_teacher_last_name`
- `homeroom` is optional and may represent room number in some contexts
- No explicit `date` field - dates are derived from `week_of` in lesson metadata

### 1.2 Lesson Metadata Schema (`schemas/lesson_output_schema.json`)

The lesson-level metadata structure:

```json
{
  "metadata": {
    "week_of": "MM/DD-MM/DD",
    "grade": "string",
    "subject": "string",
    "homeroom": "string",
    "teacher_name": "string"
  }
}
```

**Key Observations:**
- No `room` field at lesson level
- No `date` field (only `week_of` range)
- `homeroom` may serve dual purpose (class identifier OR room number)
- Single `teacher_name` field (no structured name components)

### 1.3 Slot-Level Metadata in Multi-Slot Structure

In multi-slot lessons, each slot can have its own metadata:

```json
{
  "slots": [{
    "slot_number": 1,
    "subject": "Math",
    "grade": "7",
    "homeroom": "302",
    "teacher_name": "Ms. Smith",
    "unit_lesson": "...",
    ...
  }]
}
```

**Key Observations:**
- Slots can override lesson-level metadata
- Subject can vary per slot (e.g., Math slot vs. Science slot)
- Grade and homeroom can vary per slot
- Teacher name can vary per slot (co-teaching scenarios)

## 2. Inconsistencies in Metadata Handling

### 2.1 Room Number Handling

**Problem:** Room number is inconsistently represented or missing entirely.

**Evidence:**
1. **SlotMetadata model** (`backend/models_slot.py:279-299`): No `room` field
2. **Lesson schema** (`schemas/lesson_output_schema.json`): No `room` field
3. **DOCX renderer** (`tools/docx_renderer.py:341-372`): Only fills `Name`, `Grade`, `Homeroom`, `Subject`, `Week of` - no room field
4. **PDF generators**: No room field in headers

**Impact:**
- Room information cannot be stored or displayed consistently
- `homeroom` field is overloaded (may represent class identifier OR room number)
- No way to distinguish between "Homeroom 302" (class) and "Room 302" (location)

### 2.2 Teacher Name Representation

**Problem:** Teacher names are stored in multiple formats with inconsistent usage.

**Evidence:**
1. **SlotMetadata** has three name fields:
   - `primary_teacher_name` (full name, required)
   - `primary_teacher_first_name` (optional)
   - `primary_teacher_last_name` (optional)

2. **Lesson metadata** has only:
   - `teacher_name` (single field)

3. **Document generators** use different sources:
   - `objectives_pdf_generator.py:188`: Uses `user_name` OR `metadata.get("teacher_name")`
   - `sentence_frames_pdf_generator.py:64`: Uses `user_name` OR `metadata.get("teacher_name")`
   - `docx_renderer.py:126-128`: Uses `metadata.get("teacher_name")`

**Inconsistencies:**
- Slot-level uses `primary_teacher_name`, lesson-level uses `teacher_name`
- No consistent fallback chain when structured names are available
- File naming uses different teacher name sources

### 2.3 Subject Detection and Priority

**Problem:** Subject is detected from `unit_lesson` text when it should prioritize slot metadata.

**Evidence:**
1. **Objectives PDF Generator** (`backend/services/objectives_pdf_generator.py:497-512`):
   ```python
   # Prioritize slot subject over detection
   if slot_subject and slot_subject != "Unknown":
       detected_subject = slot_subject
   elif unit_lesson and unit_lesson.strip():
       detected_subject = extract_subject_from_unit_lesson(unit_lesson)
   ```
   - **GOOD:** Prioritizes slot metadata
   - **ISSUE:** Falls back to text detection which can be unreliable

2. **Single-slot extraction** (`objectives_pdf_generator.py:574-585`):
   ```python
   if subject and subject != "Unknown":
       detected_subject = subject
   elif unit_lesson and unit_lesson.strip():
       detected_subject = extract_subject_from_unit_lesson(unit_lesson)
   ```
   - Similar pattern, but uses lesson-level metadata

3. **Sentence Frames Generator** (`backend/services/sentence_frames_pdf_generator.py:460-514`):
   ```python
   slot_subject = slot.get("subject", default_subject)
   # ...
   "subject": slot_subject if slot_subject and slot_subject != "Unknown" else default_subject
   ```
   - Uses slot subject with fallback to default
   - No text detection fallback (better)

**Inconsistencies:**
- Objectives generator uses text detection as fallback
- Sentence frames generator uses metadata fallback only
- Different fallback strategies across generators

### 2.4 Date Handling

**Problem:** Dates are derived from `week_of` string with inconsistent parsing.

**Evidence:**
1. **Objectives PDF Generator** (`objectives_pdf_generator.py:602-632`):
   - Parses `week_of` to calculate specific day dates
   - Handles formats: "11/17-11/21" or "11-17-11-21"
   - Assumes current year, adjusts if date is in future

2. **Sentence Frames Generator** (`sentence_frames_pdf_generator.py:577-634`):
   - Similar parsing logic
   - Hardcodes year as 2025
   - Different fallback behavior

**Inconsistencies:**
- Different year assumptions (current year vs. hardcoded 2025)
- Different date format handling
- No validation that parsed dates are correct

### 2.5 Homeroom Handling in Multi-Slot Contexts

**Problem:** Homeroom can leak between slots in multi-slot lessons.

**Evidence:**
1. **Sentence Frames Generator** (`sentence_frames_pdf_generator.py:462-503`):
   ```python
   # CRITICAL FIX: Only use default_homeroom if slot doesn't have homeroom key at all
   slot_homeroom = slot.get("homeroom")
   if slot_homeroom is None:
       slot_homeroom = default_homeroom
   ```
   - Attempts to prevent homeroom leakage
   - Complex logic to handle empty strings vs. None vs. "N/A"

2. **Objectives Generator** (`objectives_pdf_generator.py:519-523`):
   ```python
   "homeroom": slot_homeroom if slot_homeroom and slot_homeroom != "N/A" else homeroom
   ```
   - Simpler fallback logic
   - May use wrong homeroom if slot has empty string

**Inconsistencies:**
- Different strategies for handling missing/empty homeroom
- Risk of using Math slot's homeroom for Science slot
- No clear distinction between "no homeroom" and "use default"

### 2.6 Grade Handling

**Problem:** Grade can vary per slot but fallback logic is inconsistent.

**Evidence:**
1. **Objectives Generator** (`objectives_pdf_generator.py:519`):
   ```python
   "grade": slot_grade if slot_grade and slot_grade != "N/A" else grade
   ```
   - Simple fallback to lesson-level grade

2. **Sentence Frames Generator** (`sentence_frames_pdf_generator.py:509-511`):
   ```python
   "grade": slot_grade if slot_grade and slot_grade != "N/A" else default_grade
   ```
   - Similar pattern

**Observation:**
- Generally consistent, but "N/A" check may not catch all edge cases
- No validation that grade format is consistent

## 3. Metadata Usage in Objectives and Sentence Frames

### 3.1 Objectives PDF/HTML Generation

**Header Format** (`objectives_pdf_generator.py:664-673`):
```
Date | Time (if present) | Subject | Grade (if not Unknown) | Homeroom (if not Unknown)
```

**Metadata Sources:**
1. Date: Calculated from `week_of` + day name
2. Time: From slot metadata (`slot.get("time")`)
3. Subject: Slot subject (prioritized) OR detected from `unit_lesson`
4. Grade: Slot grade OR lesson grade
5. Homeroom: Slot homeroom OR lesson homeroom

**Issues:**
- Time field may not exist in all slot metadata
- Subject detection can fail, resulting in "Unknown"
- No room number displayed
- Teacher name not in header (only in filename)

### 3.2 Sentence Frames PDF/HTML Generation

**Header Format** (`sentence_frames_pdf_generator.py:636-672`):
```
Date | Day | Subject | Grade (if not Unknown) | Homeroom (if not Unknown)
```

**Metadata Sources:**
1. Date: Calculated from `week_of` + day name
2. Day: Day name (e.g., "Wednesday")
3. Subject: Slot subject OR default subject (no text detection)
4. Grade: Slot grade OR default grade
5. Homeroom: Complex fallback logic to prevent leakage

**Issues:**
- Different header format than objectives (includes Day name)
- No time field
- No room number
- Teacher name not in header

### 3.3 DOCX Generation

**Metadata Table** (`tools/docx_renderer.py:341-372`):
```
Name: | Grade: | Homeroom: | Subject: | Week of:
```

**Metadata Sources:**
- Uses lesson-level metadata only
- Does not extract slot-specific metadata for multi-slot lessons
- No room number field
- No date field (only week range)

**Issues:**
- Single-slot lessons: Uses lesson metadata (correct)
- Multi-slot lessons: Uses lesson metadata (may be incorrect if slots differ)
- No slot-specific metadata extraction for DOCX header

### 3.4 Inconsistencies in Document Headers

| Field | Objectives PDF | Sentence Frames PDF | DOCX |
|-------|---------------|-------------------|------|
| Date | Yes (calculated) | Yes (calculated) | No (only week range) |
| Day | No | Yes | No |
| Time | Yes (if present) | No | No |
| Subject | Yes | Yes | Yes |
| Grade | Yes (if not Unknown) | Yes (if not Unknown) | Yes |
| Homeroom | Yes (if not Unknown) | Yes (if not Unknown) | Yes |
| Room | No | No | No |
| Teacher | No (filename only) | No (filename only) | Yes (Name field) |

**Key Inconsistencies:**
1. **Date format**: PDFs show specific dates, DOCX shows week range
2. **Day name**: Only sentence frames PDF includes day name
3. **Time**: Only objectives PDF includes time
4. **Room**: Not displayed in any format
5. **Teacher**: DOCX shows in header, PDFs only in filename

## 4. Recommendations

### 4.1 Add Room Number Field

1. **Add to SlotMetadata model:**
   ```python
   room: Optional[str] = Field(None, description="Room number/location")
   ```

2. **Add to lesson schema:**
   ```json
   "room": {
     "type": "string",
     "description": "Room number or location"
   }
   ```

3. **Update document generators** to include room in headers

### 4.2 Standardize Teacher Name Handling

1. **Create helper function:**
   ```python
   def get_teacher_name(metadata: Dict, slot: Optional[Dict] = None, user_name: Optional[str] = None) -> str:
       """Get teacher name with consistent priority: user_name > slot > lesson metadata"""
       if user_name:
           return user_name
       if slot and slot.get("primary_teacher_name"):
           return slot["primary_teacher_name"]
       if slot and slot.get("teacher_name"):
           return slot["teacher_name"]
       return metadata.get("teacher_name") or metadata.get("primary_teacher_name") or "Unknown"
   ```

2. **Use consistently** across all generators

### 4.3 Standardize Subject Priority

1. **Remove text detection fallback** - always use metadata
2. **If subject is missing/Unknown**, log warning but don't guess
3. **Use same logic** in all generators:
   ```python
   subject = slot.get("subject") or metadata.get("subject") or "Unknown"
   ```

### 4.4 Standardize Date Handling

1. **Create shared date utility:**
   ```python
   def get_day_date(week_of: str, day_name: str, year: Optional[int] = None) -> str:
       """Calculate specific date for a day in the week"""
       # Consistent parsing and year handling
   ```

2. **Use in all generators** instead of duplicated logic

### 4.5 Fix Homeroom Leakage

1. **Never use default homeroom** for slots that explicitly have empty/None homeroom
2. **Use explicit "None" marker** instead of empty string
3. **Validate** that homeroom is slot-specific in multi-slot contexts

### 4.6 Standardize Document Headers

1. **Create header format specification:**
   ```
   Objectives PDF: Date | Time? | Subject | Grade? | Homeroom? | Room?
   Sentence Frames PDF: Date | Day | Subject | Grade? | Homeroom? | Room?
   DOCX: Name | Grade | Homeroom | Subject | Week of | Room?
   ```

2. **Implement consistently** across all generators

### 4.7 Add Metadata Validation

1. **Validate slot metadata** before document generation
2. **Warn** when metadata is missing or inconsistent
3. **Log** metadata extraction for debugging

## 5. Summary of Critical Issues

1. **Room number missing** - Cannot store or display room information
2. **Teacher name inconsistency** - Multiple representations, inconsistent usage
3. **Subject detection fallback** - Unreliable text detection used as fallback
4. **Date parsing inconsistency** - Different year assumptions and formats
5. **Homeroom leakage** - Risk of using wrong homeroom in multi-slot lessons
6. **Header format inconsistency** - Different fields shown in different document types
7. **Multi-slot metadata** - DOCX doesn't extract slot-specific metadata

## 6. Files Requiring Updates

1. `backend/models_slot.py` - Add room field to SlotMetadata
2. `schemas/lesson_output_schema.json` - Add room field
3. `backend/services/objectives_pdf_generator.py` - Standardize metadata extraction
4. `backend/services/sentence_frames_pdf_generator.py` - Standardize metadata extraction
5. `tools/docx_renderer.py` - Extract slot-specific metadata, add room field
6. Create `backend/utils/metadata_utils.py` - Shared metadata extraction utilities
