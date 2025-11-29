# UI Specification: Week-Based Folder System

## Overview

This document specifies the UI design for the Bilingual Lesson Plan Builder with dynamic week-based folder management.

---

## File Organization Strategy

### Base Path Configuration
```
F:\rodri\Documents\OneDrive\AS\Lesson Plan\
```

### Folder Structure
```
F:\rodri\Documents\OneDrive\AS\Lesson Plan\
├── 25 W41\                    # Week 41 of 2025
│   ├── Smith_Math_W41.docx    # Primary teacher files
│   ├── Johnson_Science.docx
│   ├── Davis_ELA_10-07.docx
│   └── Rodriguez_Lesson plan_W41_10-07-10-11.docx  # OUTPUT
│
├── 25 W42\                    # Week 42 of 2025
│   ├── Smith_Math_W42.docx
│   ├── Johnson_Science.docx
│   └── Rodriguez_Lesson plan_W42_10-14-10-18.docx  # OUTPUT
│
└── 25 W43\                    # Week 43 of 2025
    └── ...
```

### File Naming Patterns

**Primary Teacher Files (Input):**
- Must contain teacher name somewhere in filename
- Examples:
  - `Smith_Math_W41.docx`
  - `Johnson_Science_Lesson_Plan.docx`
  - `Davis_W41_ELA.docx`
  - `Teacher_Name_Subject.docx`

**Output Files:**
- Format: `{User Name}_Lesson plan_W{##}_{MM-DD-MM-DD}.docx`
- Example: `Rodriguez_Lesson plan_W41_10-07-10-11.docx`

---

## Backend Implementation

### 1. File Manager Module ✅

**Location:** `backend/file_manager.py`

**Key Functions:**
- `get_week_folder(week_of)` - Get folder path for week
- `find_primary_teacher_file(week_folder, teacher_pattern, subject)` - Auto-find files
- `list_primary_teacher_files(week_folder)` - List all available files
- `get_output_path(week_folder, user_name, week_of)` - Generate output path
- `get_available_weeks()` - List existing week folders

### 2. Updated Database Schema ✅

**New Fields in `class_slots` table:**
- `primary_teacher_name` - Teacher name/pattern to match
- `primary_teacher_file_pattern` - Alternative pattern for matching

**Removed:**
- `primary_teacher_file` - No longer stores fixed paths

### 3. Updated Batch Processor ✅

**Changes:**
- Auto-finds files based on teacher pattern
- Saves output to week folder (not `output/`)
- Uses FileManager for all path operations

---

## UI Workflow

### Step 1: Initial Setup (One-Time)

**Screen: Settings**

```
┌─────────────────────────────────────────────────┐
│  Settings                                        │
├─────────────────────────────────────────────────┤
│                                                  │
│  Base Folder Path:                               │
│  ┌─────────────────────────────────────────┐    │
│  │ F:\rodri\Documents\OneDrive\AS\Lesson...│ 📁 │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  ✅ Path is valid and accessible                │
│                                                  │
│  [Save Settings]                                 │
└─────────────────────────────────────────────────┘
```

### Step 2: User Selection

**Screen: Home / User Selection**

```
┌─────────────────────────────────────────────────┐
│  Select User                                     │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │ ▼ Select User                           │    │
│  │   - Maria Rodriguez                     │    │
│  │   - John Smith                          │    │
│  │   + Add New User                        │    │
│  └─────────────────────────────────────────┘    │
│                                                  │
│  [Continue]                                      │
└─────────────────────────────────────────────────┘
```

### Step 3: Class Slot Configuration

**Screen: Configure Slots**

```
┌─────────────────────────────────────────────────────────────┐
│  Configure Class Slots - Maria Rodriguez                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Slot 1:  Math, Grade 6, Room 6A                            │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Primary Teacher: [Smith            ▼]              │     │
│  │ Subject:         [Math             ▼]              │     │
│  │ Grade:           [6                ▼]              │     │
│  │ Homeroom:        [6A                ]              │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  Slot 2:  Science, Grade 6, Room 6B                         │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Primary Teacher: [Johnson          ▼]              │     │
│  │ Subject:         [Science          ▼]              │     │
│  │ Grade:           [6                ▼]              │     │
│  │ Homeroom:        [6B                ]              │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ... (Slots 3-6)                                             │
│                                                              │
│  [Save Configuration]                                        │
└─────────────────────────────────────────────────────────────┘
```

### Step 4: Week Selection & Processing

**Screen: Generate Lesson Plan**

```
┌─────────────────────────────────────────────────────────────┐
│  Generate Lesson Plan - Maria Rodriguez                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Select Week:                                                │
│  ┌────────────────────────────────────────────────────┐     │
│  │ ▼ 25 W41 (10/07-10/11)                             │     │
│  │   - 25 W41 (10/07-10/11) [6 files]                 │     │
│  │   - 25 W42 (10/14-10/18) [6 files]                 │     │
│  │   - 25 W43 (10/21-10/25) [5 files]                 │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  Week Folder: F:\...\Lesson Plan\25 W41                     │
│                                                              │
│  Primary Teacher Files Found:                                │
│  ┌────────────────────────────────────────────────────┐     │
│  │ ✅ Slot 1 (Math):    Smith_Math_W41.docx           │     │
│  │ ✅ Slot 2 (Science): Johnson_Science.docx          │     │
│  │ ✅ Slot 3 (ELA):     Davis_ELA_10-07.docx          │     │
│  │ ✅ Slot 4 (SS):      Brown_SocialStudies.docx      │     │
│  │ ✅ Slot 5 (Math):    Smith_Math_W41.docx           │     │
│  │ ✅ Slot 6 (Science): Johnson_Science.docx          │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  Output will be saved to:                                    │
│  F:\...\25 W41\Rodriguez_Lesson plan_W41_10-07-10-11.docx   │
│                                                              │
│  [Generate Lesson Plan]                                      │
└─────────────────────────────────────────────────────────────┘
```

### Step 5: Processing Progress

**Screen: Processing**

```
┌─────────────────────────────────────────────────────────────┐
│  Processing Lesson Plan...                                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ████████████████████░░░░░░░░░░  60%                        │
│                                                              │
│  ✅ Slot 1 (Math):    Completed                             │
│  ✅ Slot 2 (Science): Completed                             │
│  ✅ Slot 3 (ELA):     Completed                             │
│  ⏳ Slot 4 (SS):      Processing...                         │
│  ⏸  Slot 5 (Math):    Pending                               │
│  ⏸  Slot 6 (Science): Pending                               │
│                                                              │
│  Estimated time remaining: 45 seconds                        │
└─────────────────────────────────────────────────────────────┘
```

### Step 6: Completion

**Screen: Success**

```
┌─────────────────────────────────────────────────────────────┐
│  ✅ Lesson Plan Generated Successfully!                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Output File:                                                │
│  F:\...\25 W41\Rodriguez_Lesson plan_W41_10-07-10-11.docx   │
│                                                              │
│  Processed: 6 slots                                          │
│  Failed: 0 slots                                             │
│  Total time: 1m 23s                                          │
│                                                              │
│  [Open File] [Open Folder] [Generate Another Week]          │
└─────────────────────────────────────────────────────────────┘
```

---

## API Endpoints Needed

### File Management

```
GET  /api/file-manager/validate-path
     Query: base_path
     Returns: {valid: bool, exists: bool, writable: bool}

GET  /api/file-manager/weeks
     Returns: [{folder_name, path, year, week, file_count}, ...]

GET  /api/file-manager/week/{week_of}/files
     Returns: [{name, path, size, modified}, ...]

POST /api/file-manager/find-file
     Body: {week_of, teacher_pattern, subject}
     Returns: {found: bool, path: string}
```

### User & Slot Management (Already Exist ✅)

```
GET    /api/users
POST   /api/users
GET    /api/users/{user_id}/slots
POST   /api/users/{user_id}/slots
PUT    /api/slots/{slot_id}
DELETE /api/slots/{slot_id}
```

### Batch Processing (Already Exists ✅)

```
POST /api/process-week
     Body: {user_id, week_of, provider}
     Returns: {success, plan_id, output_file, ...}
```

---

## Configuration

### Environment Variables

Add to `.env`:
```
LESSON_PLAN_BASE_PATH=F:/rodri/Documents/OneDrive/AS/Lesson Plan
```

### User Settings (Stored in Database)

```sql
CREATE TABLE user_settings (
    user_id TEXT PRIMARY KEY,
    base_path_override TEXT,
    default_provider TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## Implementation Phases

### Phase 1: Backend Complete ✅
- [x] FileManager module
- [x] Updated database schema
- [x] Updated batch processor
- [x] Auto-file finding logic

### Phase 2: API Endpoints (Next)
- [ ] File manager endpoints
- [ ] Week folder listing
- [ ] File validation

### Phase 3: Tauri + React UI (After)
- [ ] Settings screen
- [ ] User selection
- [ ] Slot configuration
- [ ] Week selection
- [ ] Progress tracking
- [ ] File browser integration

---

## Key Features

### 1. **Auto-File Detection**
- System finds files by teacher name pattern
- No need to manually select files each week
- Supports multiple naming conventions

### 2. **Week-Based Organization**
- All files for a week in one folder
- Input and output together
- Easy to archive/share

### 3. **Flexible Matching**
- Match by teacher name
- Match by subject (optional)
- Fallback to any match

### 4. **Error Handling**
- Clear messages if files not found
- Suggestions for file naming
- Manual file selection fallback

---

## Testing Checklist

### Backend Tests
- [ ] FileManager finds files correctly
- [ ] Week folder creation works
- [ ] Output path generation correct
- [ ] File matching with various patterns
- [ ] Handles missing files gracefully

### UI Tests
- [ ] Base path configuration
- [ ] User selection works
- [ ] Slot configuration saves
- [ ] Week selection shows correct files
- [ ] Progress updates in real-time
- [ ] Success screen shows correct path

---

## Next Steps

1. ✅ Backend file management - COMPLETE
2. ⏳ Add file manager API endpoints
3. ⏳ Build Tauri + React UI
4. ⏳ Integration testing
5. ⏳ User acceptance testing

---

**Status:** Backend Ready, UI Design Complete, Ready for Implementation
