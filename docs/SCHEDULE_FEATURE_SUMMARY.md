# Schedule Feature Implementation Summary

## Overview
The schedule management feature allows teachers to input, view, and manage their weekly class schedules with subjects, grades, and homerooms. The feature includes a grid-based input interface with color coding for visual organization.

## Current Status
✅ **Fully Implemented and Working**

## Key Features

### 1. Schedule Input Interface
- **Location**: `frontend/src/components/ScheduleInput.tsx`
- Grid-based table with time slots (rows) and days of week (columns)
- Inline editing: Click any cell to add/edit subject, grade, and homeroom
- Auto-loads existing schedule when user is selected
- Save/Clear/Load functionality

### 2. Color Coding System
- **Location**: `frontend/src/utils/scheduleColors.ts`
- **Strategy**: One color per homeroom (all subjects in same homeroom share color)
- **Non-class periods** get specific colors:
  - **PREP**: Slate gray (`bg-slate-200`, `border-slate-400`, `text-slate-900`)
  - **Lunch**: Orange (`bg-orange-100`, `border-orange-400`, `text-orange-900`)
  - **A.M. Routine**: Blue (`bg-blue-50`, `border-blue-200`, `text-blue-800`)
  - **Dismissal**: Purple (`bg-purple-50`, `border-purple-200`, `text-purple-800`)
- **Homerooms**: Each homeroom gets a unique color from a palette (green, blue, purple, yellow, pink, indigo, teal, orange, cyan, emerald)
- Colors are assigned deterministically based on homeroom hash

### 3. Database Schema
- **Table**: `schedules`
- **Location**: `backend/database.py` (SQLite) and `backend/supabase_database.py` (Supabase)
- **Fields**:
  - `id` (TEXT PRIMARY KEY)
  - `user_id` (TEXT, FK to users)
  - `day_of_week` (TEXT: 'monday', 'tuesday', 'wednesday', 'thursday', 'friday')
  - `start_time` (TEXT, format: 'HH:MM')
  - `end_time` (TEXT, format: 'HH:MM')
  - `subject` (TEXT, normalized: 'ELA', 'MATH', 'PREP', 'Lunch', etc.)
  - `homeroom` (TEXT, nullable: 'T5', 'T2', '209', etc.)
  - `grade` (TEXT, nullable: '2', '3', 'K', etc.)
  - `slot_number` (INTEGER, sequential)
  - `plan_slot_group_id` (TEXT, nullable) – shared identifier for multi-period lessons
  - `is_active` (BOOLEAN, false for non-class periods)
  - `created_at`, `updated_at` (TIMESTAMP)
- **Related table**: `class_slots` now includes `plan_group_label` so slot defaults can suggest a linked lesson label.

### 4. API Endpoints
- **Location**: `backend/api.py`
- **Endpoints**:
  - `GET /api/schedules/{user_id}` - Get all schedule entries for a user
  - `GET /api/schedules/{user_id}/current` - Get current lesson based on time
  - `POST /api/schedules` - Create single schedule entry
  - `POST /api/schedules/{user_id}/bulk` - Bulk create schedule entries
  - `PUT /api/schedules/{schedule_id}` - Update schedule entry
  - `DELETE /api/schedules/{schedule_id}` - Delete schedule entry

### 5. Frontend API Client
- **Location**: `frontend/src/lib/api.ts`
- **Functions**:
  - `scheduleApi.getSchedule(userId, dayOfWeek?, homeroom?, grade?)`
  - `scheduleApi.getCurrentLesson(userId)`
  - `scheduleApi.createEntry(entry)`
  - `scheduleApi.updateEntry(scheduleId, update)`
  - `scheduleApi.deleteEntry(scheduleId)`
  - `scheduleApi.bulkCreate(userId, entries)`

### 6. Data Normalization
- **Location**: `backend/utils/schedule_utils.py`
- **Functions**:
  - `normalize_subject(subject)` - Normalizes subject names (e.g., 'PREP TIME' → 'PREP')
  - `is_non_class_period(subject)` - Checks if subject is non-class period
  - `prepare_schedule_entry(...)` - Applies normalization and sets `is_active` flag
- **Non-class periods**: PREP, Prep Time, A.M. Routine, AM Routine, Morning Routine, Lunch, LUNCH, Dismissal, DISMISSAL
- **Behavior**: Non-class periods automatically clear `homeroom` and `grade`, set `is_active = false`

### 7. Multi-Period Lesson Linking
- **Schedule metadata**: `plan_slot_group_id` ties any number of periods (even with Lunch between them) to the same lesson plan slot. Validation warnings appear if linked periods disagree on subject/grade/homeroom.
- **Slot metadata**: `plan_group_label` (configured in `SlotConfigurator.tsx`) provides a reusable, human-friendly label that appears in the schedule grid’s datalist.
- **Planner surface**: `WeekView.tsx` and `LessonDetailView.tsx` show a “Group” badge so navigators can confirm which lesson plan slot they are viewing.
- **Matching logic**: `frontend/src/utils/planMatching.ts` reuses cached plan slot data for every period in the same group ID before falling back to heuristic matching.

## Technical Implementation Details

### Frontend Components
1. **ScheduleInput.tsx**
   - Main component for schedule management
   - Manages local state for schedule grid
   - Handles save/load/clear operations
   - Auto-loads on user selection change

2. **ScheduleCell.tsx**
   - Individual editable cell component
   - Inline editing with subject, grade, homeroom inputs
   - Applies color coding based on subject/homeroom
   - Handles non-class period normalization

3. **scheduleColors.ts**
   - Color utility functions
   - `getSubjectColors(subject, grade, homeroom)` - Returns color scheme
   - `generateColorFromHomeroom(homeroom)` - Assigns unique color to homeroom
   - `getScheduleCellClasses(...)` - Returns CSS classes for cells

### Backend Implementation
1. **Database Layer**
   - SQLite: `backend/database.py` - `SQLiteDatabase` class
   - Supabase: `backend/supabase_database.py` - `SupabaseDatabase` class
   - Both implement same interface for schedule CRUD operations

2. **API Layer**
   - FastAPI endpoints with authentication
   - User access verification
   - Error handling and logging
   - Bulk operations support

3. **Data Models**
   - **Location**: `backend/models.py`
   - `ScheduleEntryCreate` - For creating entries
   - `ScheduleEntryUpdate` - For updating entries
   - `ScheduleEntryResponse` - API response model
   - `ScheduleBulkCreateRequest` - Bulk create request
   - `ScheduleBulkCreateResponse` - Bulk create response

## Data Flow

1. **Loading Schedule**:
   - User selects user → `useEffect` triggers → `loadExistingSchedule()` → API call → Parse entries → Map to grid cells → Display with colors

2. **Saving Schedule**:
   - User clicks "Save Schedule" → Collect all cells → Convert to entries → Bulk create API call → Success/error feedback

3. **Color Assignment**:
   - Cell renders → `getSubjectColors(subject, grade, homeroom)` → Check if non-class period → If yes, return specific color → If no, hash homeroom → Return color from palette

## Current Schedule Data (Wilson Rodrigues)
- **User ID**: `04fe8898-cb89-4a73-affb-64a97a98f820`
- **Homerooms**:
  - **T5**: Grade 3 (ELA)
  - **T2**: Grade 3 (MATH, SCIENCE)
  - **209**: Grade 2 (ELA, SOCIAL S., SCIENCE, MATH)
- **Time Slots**: 10 slots from 08:15 to 15:05
- **Total Entries**: 50 (10 slots × 5 days)

## Known Issues / Fixed Issues

### Fixed
1. ✅ Schedule not loading - Fixed API response format (`getSchedule` now extracts `data` property)
2. ✅ Color coding not working - Fixed by passing `homeroom` parameter to color functions
3. ✅ Time format mismatches - Standardized to `HH:MM` format

### Current State
- All features working as expected
- Color coding displays correctly
- Schedule persists and loads correctly
- Bulk operations work

## Integration Points

### Navigation
- **Desktop**: `frontend/src/components/desktop/DesktopNav.tsx` - Added "Schedule" nav item
- **Mobile**: `frontend/src/components/mobile/MobileNav.tsx` - Added "Schedule" tab
- **App Router**: `frontend/src/App.tsx` - Added schedule route

### State Management
- Uses Zustand store (`frontend/src/store/useStore.ts`) for current user
- Local component state for schedule data

## Next Steps / Potential Enhancements

1. **Current Lesson Detection**
   - Implement real-time current lesson highlighting
   - Add countdown timer for current lesson
   - Visual indicator for "now" in schedule

2. **Schedule Filtering**
   - Filter by day of week
   - Filter by homeroom
   - Filter by grade
   - Filter by subject

3. **Schedule Templates**
   - Save schedule as template
   - Apply template to new week
   - Multiple templates per user

4. **Schedule Validation**
   - Check for time conflicts
   - Validate time ranges
   - Warn about gaps in schedule

5. **Export/Import**
   - Export schedule to CSV
   - Import schedule from CSV
   - Print-friendly view

6. **Visual Enhancements**
   - Drag-and-drop to rearrange schedule
   - Copy/paste cells
   - Bulk edit operations

7. **Lesson Mode Integration**
   - Use schedule to determine current lesson
   - Display lesson steps based on schedule
   - Timer synchronization with schedule

## Files Modified/Created

### Frontend
- `frontend/src/components/ScheduleInput.tsx` - Main schedule component
- `frontend/src/components/ScheduleCell.tsx` - Individual cell component
- `frontend/src/utils/scheduleColors.ts` - Color coding utilities
- `frontend/src/lib/api.ts` - Schedule API client functions
- `frontend/src/components/desktop/DesktopNav.tsx` - Added Schedule nav
- `frontend/src/components/mobile/MobileNav.tsx` - Added Schedule tab
- `frontend/src/App.tsx` - Added schedule route

### Backend
- `backend/database.py` - Schedule CRUD for SQLite
- `backend/supabase_database.py` - Schedule CRUD for Supabase
- `backend/api.py` - Schedule API endpoints
- `backend/models.py` - Schedule data models
- `backend/utils/schedule_utils.py` - Schedule normalization utilities

### Database
- `sql/create_schedules_table_supabase.sql` - Supabase migration script
- `backend/migrations/create_schedules_table.py` - SQLite migration

### Scripts
- `create_wilson_schedule.py` - Bulk schedule creation script (deleted, but pattern available)

## Testing
- Schedule loads correctly for Wilson Rodrigues
- Color coding displays correctly
- Save/load operations work
- Non-class periods normalize correctly
- Homeroom colors are consistent

## Notes
- Schedule data is user-specific (filtered by `user_id`)
- Non-class periods don't require homeroom/grade
- Time format is standardized to `HH:MM` (24-hour format)
- Colors are deterministic (same homeroom = same color always)
- Frontend automatically loads schedule when user changes

