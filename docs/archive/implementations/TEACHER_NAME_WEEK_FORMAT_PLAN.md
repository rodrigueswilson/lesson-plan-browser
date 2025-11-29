# Teacher Name & Week Format - Complete Implementation Plan

**Date:** October 26, 2025  
**Goal:** Structured teacher names + standardized week dates

---

## Requirements

### Teacher Names
**Current:** `Name: Lang` or `Name: Daniela`  
**Target:** `Name: Sarah Lang / Daniela Silva`

### Week Dates
**Current:** `10-27-10-31` or `10/27-10/31` (inconsistent)  
**Target:** `10/27-10/31` (always slashes)

---

## Complete Implementation Checklist

### ✅ Phase 1: Database

**Schema Changes:**
```sql
ALTER TABLE users ADD COLUMN first_name TEXT;
ALTER TABLE users ADD COLUMN last_name TEXT;
ALTER TABLE class_slots ADD COLUMN primary_teacher_first_name TEXT;
ALTER TABLE class_slots ADD COLUMN primary_teacher_last_name TEXT;
```

**Migration Script:**
- Split existing `name` → `first_name` + `last_name`
- Split existing `primary_teacher_name` → first/last
- Flag records needing manual review

**CRUD Updates:**
- `create_user(first_name, last_name, email)`
- `update_user(user_id, first_name, last_name, email)`
- `update_class_slot(slot_id, primary_teacher_first_name, primary_teacher_last_name, ...)`

---

### ✅ Phase 2: Backend API

**Models (`backend/models.py`):**
```python
class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    name: str  # Computed for backward compat
    first_name: str
    last_name: str
    email: Optional[str]
    created_at: str

class ClassSlotCreate(BaseModel):
    # ... existing fields ...
    primary_teacher_first_name: Optional[str] = None
    primary_teacher_last_name: Optional[str] = None
```

**API Endpoints (`backend/api.py`):**
- Update `/api/users` POST to require first/last
- Update `/api/users/{id}` PUT to accept first/last
- Update `/api/users/{id}/slots` to accept primary teacher first/last

---

### ✅ Phase 3: Frontend UI

**User Registration/Profile:**
- Add "First Name" field (required)
- Add "Last Name" field (required)
- Validate both are non-empty
- Show preview: "First Last"

**Slot Configuration:**
- Add "Primary Teacher First Name" field
- Add "Primary Teacher Last Name" field
- Show preview: "Primary First Last / User First Last"

**Migration Warning:**
- Show alert if user.first_name or user.last_name is empty
- Prompt to update profile

**Display Logic:**
- Build combined name: `buildTeacherName(primaryFirst, primaryLast, userFirst, userLast)`
- Format week dates: `formatWeekDates(weekOf)`

---

### ✅ Phase 4: Week Date Formatting

**Utility Function (`backend/utils/date_formatter.py`):**
```python
def format_week_dates(week_of: str) -> str:
    """
    Standardize to MM/DD-MM/DD.
    
    Handles:
    - "10-27-10-31" → "10/27-10/31"
    - "10/27-10/31" → "10/27-10/31"
    - "10-27 to 10-31" → "10/27-10/31"
    - "Week of 10/27" → "10/27-10/31"
    """
    # Implementation details...
```

**Apply at Creation (`backend/api.py`):**
```python
@app.post("/api/process-week")
async def process_week(request: BatchProcessRequest, ...):
    normalized_week = format_week_dates(request.week_of)
    # Use normalized_week throughout
```

**Why at creation?** Database stores canonical format, consistent everywhere.

---

### ✅ Phase 5: Rendering with Fallbacks

**Build Teacher Name (`tools/batch_processor.py`):**
```python
def build_teacher_name(user_data: Dict, slot_data: Dict) -> str:
    """
    Build "Primary First Last / Bilingual First Last".
    
    Fallback strategy:
    1. Try first_name + last_name
    2. Fall back to legacy 'name' field
    3. Return "Unknown" if all fail
    """
    # Primary teacher
    primary_first = slot_data.get('primary_teacher_first_name', '').strip()
    primary_last = slot_data.get('primary_teacher_last_name', '').strip()
    
    if primary_first and primary_last:
        primary_name = f"{primary_first} {primary_last}"
    else:
        primary_name = slot_data.get('primary_teacher_name', '').strip()
    
    # Bilingual teacher
    bilingual_first = user_data.get('first_name', '').strip()
    bilingual_last = user_data.get('last_name', '').strip()
    
    if bilingual_first and bilingual_last:
        bilingual_name = f"{bilingual_first} {bilingual_last}"
    else:
        bilingual_name = user_data.get('name', '').strip()
    
    # Combine
    if primary_name and bilingual_name:
        return f"{primary_name} / {bilingual_name}"
    return primary_name or bilingual_name or "Unknown"
```

**Update Metadata Building:**
```python
metadata = {
    "teacher_name": build_teacher_name(user, slot),
    "week_of": format_week_dates(week_of),
    "grade": slot["grade"],
    "subject": slot["subject"],
    "homeroom": slot.get("homeroom", "")
}
```

---

### ✅ Phase 6: CSV Import (if applicable)

**Update CSV Format:**
```csv
first_name,last_name,email
Sarah,Lang,sarah.lang@school.edu
Daniela,Silva,daniela.silva@school.edu
```

**Import Script:**
```python
def import_users_from_csv(csv_path: str):
    for row in reader:
        db.create_user(
            first_name=row['first_name'],
            last_name=row['last_name'],
            email=row.get('email')
        )
```

---

## Migration Execution

### Step 1: Backup
```bash
cp lesson_plans.db lesson_plans.db.backup
```

### Step 2: Run Migration
```bash
python backend/migrations/add_structured_names.py
```

### Step 3: Review Warnings
- Check output for incomplete names
- Manually update flagged records

### Step 4: Deploy Code
- Backend: Database, API, models
- Frontend: UI components
- Utils: Date formatter

### Step 5: Test
- Create new user → verify first/last required
- Update existing user → verify fallback works
- Configure slot → verify primary teacher name
- Process lesson plan → verify output format

---

## Edge Cases Handled

### Single-Word Names
- Migration: "Daniela" → first="Daniela", last="" (flag for review)
- Runtime: Falls back to legacy `name` field

### Missing Names
- Migration: Flags for manual update
- Runtime: Shows "Unknown" if all fields empty

### Week Date Formats
- "10-27-10-31" → "10/27-10/31" ✅
- "10/27-10/31" → "10/27-10/31" ✅
- "Week of 10/27" → "10/27-10/31" ✅
- "10-27 to 10-31" → "10/27-10/31" ✅

### Backward Compatibility
- Keep legacy `name` and `primary_teacher_name` fields
- Fallback logic in rendering
- Gradual migration (no breaking changes)

---

## Files to Create/Modify

### New Files
1. `backend/migrations/add_structured_names.py` - Migration script
2. `backend/utils/date_formatter.py` - Week date formatter
3. `frontend/src/utils/dateFormatter.ts` - Frontend formatter

### Modified Files
1. `backend/database.py` - CRUD methods
2. `backend/models.py` - Request/response models
3. `backend/api.py` - Endpoints + week normalization
4. `tools/batch_processor.py` - build_teacher_name() + metadata
5. `frontend/src/components/UserProfile.tsx` - Registration/edit UI
6. `frontend/src/components/SlotConfiguration.tsx` - Slot config UI
7. `frontend/src/components/MigrationWarning.tsx` - Warning banner

---

## Summary

**Approach:** Gradual migration with fallbacks

**Benefits:**
- ✅ Clean, professional output
- ✅ Consistent formatting
- ✅ No breaking changes
- ✅ Backward compatible

**Output Example:**
```
Name: Sarah Lang / Daniela Silva
Grade: 3
Homeroom: T5
Subject: ELA
Week of: 10/27-10/31
```

**Ready to implement?** Start with Phase 1 (database migration).
