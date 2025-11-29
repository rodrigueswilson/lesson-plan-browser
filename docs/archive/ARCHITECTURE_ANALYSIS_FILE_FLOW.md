# Architecture Analysis: File Flow & Single Source of Truth

**Date**: 2025-10-05  
**Issue**: Conflicting file location strategies causing confusion and errors

---

## 🔍 Current Problems Identified

### Problem 1: Dual File Location Strategy
The system has **TWO conflicting approaches** for finding teacher files:

#### Approach A: Direct File Path (Database)
- **Location**: `class_slots.primary_teacher_file` column
- **Example**: `"input/primary_math.docx"`
- **Used by**: Test scripts, initial setup
- **Issue**: Hardcoded paths, not dynamic

#### Approach B: Pattern-Based Discovery (File Manager)
- **Location**: `FileManager.find_primary_teacher_file()`
- **Searches in**: Week folders (e.g., `F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W41`)
- **Uses**: `primary_teacher_name` or `primary_teacher_file_pattern`
- **Issue**: Requires week folder structure, doesn't work for testing

### Problem 2: Batch Processor Confusion
```python
# Current logic in batch_processor.py line 134-150
file_mgr = get_file_manager()
week_folder = file_mgr.get_week_folder(week_of)  # Gets F:\...\25 W41

teacher_pattern = slot.get('primary_teacher_name') or slot.get('primary_teacher_file_pattern', '')
primary_file = file_mgr.find_primary_teacher_file(week_folder, teacher_pattern, slot['subject'])
# Searches in week folder, ignores slot['primary_teacher_file']!
```

**The batch processor IGNORES the direct file path** and always uses pattern matching!

### Problem 3: No Week Folder Selection
- Users cannot select which week folder to work with
- System auto-detects "most recent" which may not be desired
- No UI for week selection

---

## 🎯 Recommended Solution: Single Source of Truth

### Architecture Decision: Hybrid Approach

#### 1. **Database Schema Enhancement**
Add week folder selection to users or weekly plans:

```sql
-- Option A: Per user (default week folder)
ALTER TABLE users ADD COLUMN current_week_folder TEXT;

-- Option B: Per weekly plan (better)
ALTER TABLE weekly_plans ADD COLUMN week_folder_path TEXT;
```

#### 2. **File Resolution Priority**
Establish clear priority for finding files:

```python
def resolve_primary_file(slot, week_folder):
    """
    Priority order:
    1. Direct path if absolute and exists
    2. Direct path relative to week folder if exists
    3. Pattern-based search in week folder
    4. Fallback to input/ directory for testing
    """
    
    # Priority 1: Absolute path
    if slot.get('primary_teacher_file'):
        file_path = Path(slot['primary_teacher_file'])
        if file_path.is_absolute() and file_path.exists():
            return str(file_path)
        
        # Priority 2: Relative to week folder
        relative_path = week_folder / file_path.name
        if relative_path.exists():
            return str(relative_path)
    
    # Priority 3: Pattern-based search
    teacher_pattern = slot.get('primary_teacher_name') or slot.get('primary_teacher_file_pattern')
    if teacher_pattern and week_folder.exists():
        found = find_primary_teacher_file(week_folder, teacher_pattern, slot['subject'])
        if found:
            return found
    
    # Priority 4: Fallback to input/ for testing
    if slot.get('primary_teacher_file'):
        fallback = Path('input') / Path(slot['primary_teacher_file']).name
        if fallback.exists():
            return str(fallback)
    
    return None
```

#### 3. **UI Enhancement: Week Folder Selector**

Add to frontend workflow:

```
1. User Login
2. **[NEW] Select Week Folder** 
   - Show available weeks from FileManager.get_available_weeks()
   - Display: "25 W41 (10/06-10/10) - 15 files"
   - Allow manual path entry for custom locations
3. Configure Slots (auto-detect files in selected week)
4. Generate Plan
```

#### 4. **Database Update**

```python
# When user selects week folder
db.update_user(user_id, current_week_folder="F:/rodri/Documents/OneDrive/AS/Lesson Plan/25 W41")

# OR when creating weekly plan
plan_id = db.create_weekly_plan(user_id, week_of, week_folder_path=selected_folder)
```

---

## 📋 Implementation Steps

### Phase 1: Fix Immediate Issues (Day 7)
1. ✅ Fix Unicode encoding in batch_processor
2. ✅ Add None check for teacher_pattern in file_manager
3. **[IN PROGRESS]** Update batch_processor to use hybrid file resolution
4. **[PENDING]** Add week_folder_path to weekly_plans table
5. **[PENDING]** Update batch_processor to use plan's week folder

### Phase 2: Database Schema (Day 7)
```sql
-- Migration script
ALTER TABLE weekly_plans ADD COLUMN week_folder_path TEXT;
ALTER TABLE users ADD COLUMN default_week_folder TEXT;
```

### Phase 3: UI Enhancement (Day 8)
1. Add week folder selector component
2. Show available weeks with file counts
3. Allow custom path entry
4. Store selection in database

### Phase 4: Slot Auto-Configuration (Day 8)
When week folder selected:
1. Scan for teacher files
2. Auto-suggest slot configurations
3. Allow manual override

---

## 🔄 Updated Workflow

### Current (Broken)
```
User → Configure Slots (with hardcoded paths) → Process Week
         ↓
    Batch Processor ignores paths, searches in auto-detected week folder
         ↓
    FAILS if week folder doesn't match expectations
```

### Proposed (Fixed)
```
User → Select Week Folder → Auto-detect Teacher Files → Configure Slots → Process Week
         ↓                      ↓                          ↓                ↓
    Store in DB          Suggest mappings         Store file refs    Use stored refs
```

---

## 🚨 Critical Fixes Needed Now

### Fix 1: Batch Processor File Resolution
```python
# In batch_processor.py _process_slot method
def _process_slot(self, slot, week_of, provider, week_folder_override=None):
    # Use override if provided, otherwise get from file manager
    if week_folder_override:
        week_folder = Path(week_folder_override)
    else:
        file_mgr = get_file_manager()
        week_folder = file_mgr.get_week_folder(week_of)
    
    # NEW: Hybrid file resolution
    primary_file = self._resolve_primary_file(slot, week_folder)
    
    if not primary_file:
        raise ValueError(f"No primary teacher file found for slot {slot['slot_number']}")
    
    # Continue with parsing...
```

### Fix 2: Add week_folder_path to process_user_week
```python
async def process_user_week(self, user_id, week_of, provider="openai", week_folder=None):
    # If week_folder not provided, try to get from plan or user
    if not week_folder:
        # Check if plan already has week folder
        # Or use user's default
        # Or auto-detect
        pass
    
    # Pass week_folder to _process_slot
    for slot in slots:
        lesson_json = await self._process_slot(slot, week_of, provider, week_folder)
```

---

## 📊 Testing Strategy

### Test Scenarios
1. **Production Mode**: Files in week folders (F:\...\25 W41)
2. **Development Mode**: Files in input/ directory
3. **Mixed Mode**: Some files direct path, some pattern-based

### Test Cases
- ✅ Single slot with direct path
- ✅ Multiple slots with pattern matching
- ✅ Week folder selection
- ✅ Fallback to input/ for testing
- ✅ Error handling for missing files

---

## 🎯 Success Criteria

1. **Single Source of Truth**: Week folder stored in database
2. **Flexible File Resolution**: Works in production and testing
3. **User Control**: Can select specific week folder
4. **No Conflicts**: Clear priority order for file resolution
5. **Backward Compatible**: Existing tests still work

---

## 📝 Next Actions

1. **Immediate** (Day 7):
   - Implement hybrid file resolution in batch_processor
   - Add week_folder_path column to database
   - Update tests to work with new logic

2. **Short-term** (Day 8):
   - Add week folder selector to UI
   - Auto-detect and suggest teacher files
   - Update documentation

3. **Long-term** (Day 9+):
   - Add duplicate detection
   - Add file conflict resolution
   - Add week folder management UI

---

**Status**: Analysis Complete - Ready for Implementation
