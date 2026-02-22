# Date Flow Audit: Database → API → Frontend → Views

## Overview
This document traces how dates flow from the database through APIs to the frontend views.

## 1. Database Layer

### Schema (backend/schema.py)
```python
class WeeklyPlan(SQLModel, table=True):
    week_of: str  # Format: "MM-DD-MM-DD" (e.g., "12-01-12-05")
```

**Key Points:**
- `week_of` is stored as a STRING, not a date
- Format: "MM-DD-MM-DD" (Monday to Friday)
- No year information stored
- No timezone information

### Database Retrieval (backend/database_interface.py)
- `get_user_plans(user_id, limit)` → Returns List[WeeklyPlan]
- `get_weekly_plan(plan_id)` → Returns WeeklyPlan
- Both return `week_of` as-is from database (no transformation)

## 2. Backend API Layer

### Endpoint: GET /api/users/{user_id}/plans
**Location:** backend/api.py:3646
**Returns:** List[WeeklyPlanResponse]
**Response Model:**
```python
class WeeklyPlanResponse(BaseModel):
    week_of: str  # Passed through unchanged from database
```

**Flow:**
1. `get_user_plans()` → calls `db.get_user_plans(user_id, limit)`
2. Returns plans with `week_of` unchanged from database
3. No date transformation or normalization

### Endpoint: GET /api/plans/{plan_id}
**Location:** backend/api.py:1964
**Returns:** LessonPlanDetailResponse
**Flow:**
1. `get_plan_detail()` → calls `db.get_weekly_plan(plan_id)`
2. Returns plan with `week_of` unchanged from database
3. No date transformation

## 3. Frontend API Layer (shared/lesson-api/src/index.ts)

### planApi.list()
**Location:** shared/lesson-api/src/index.ts:863
**Flow:**
1. Queries database: `SELECT week_of FROM weekly_plans WHERE user_id = ?`
2. Maps result using `rowToPlan()` function
3. Returns `week_of` unchanged

### planApi.getPlanDetail()
**Location:** shared/lesson-api/src/index.ts:1240
**Flow:**
1. Queries database: `SELECT week_of, lesson_json FROM weekly_plans WHERE id = ?`
2. Returns `week_of` unchanged

## 4. Frontend Component Layer

### LessonPlanBrowser
**Location:** shared/lesson-browser/src/components/LessonPlanBrowser.tsx
**State:**
- `selectedWeek: string | null` - The currently selected week
- `selectedLesson.weekOf?: string` - Week stored when lesson was clicked

**Flow:**
1. `fetchPlans()` → calls `planApi.list()`
2. Sets `selectedWeek` from first plan's `week_of` if not set
3. Passes `selectedWeek` to `WeekView` as `weekOf` prop

### WeekView
**Location:** shared/lesson-browser/src/components/WeekView.tsx
**Props:**
- `weekOf: string` - Received from LessonPlanBrowser

**Flow:**
1. Receives `weekOf` prop from parent
2. Loads plan: `plans.find(p => p.week_of === weekOf)`
3. When clicking lesson: `onLessonClick(entry, day, slot, ..., weekOf)`

### handleLessonClick
**Location:** shared/lesson-browser/src/components/LessonPlanBrowser.tsx:603
**Priority for weekOf:**
1. `weekOfFromView` (from WeekView/DayView) - HIGHEST
2. `scheduleEntry.week_of` (usually null)
3. `selectedWeek` (state) - FALLBACK

**Flow:**
1. Determines `lessonWeekOf` using priority above
2. Stores in `selectedLesson.weekOf`
3. Updates `selectedWeek` state if different

### LessonDetailView
**Location:** shared/lesson-browser/src/components/LessonDetailView.tsx
**Props:**
- `weekOf: string` - Received from LessonPlanBrowser

**Flow:**
1. Receives `weekOf` prop
2. Normalizes: `weekOf.replace(/\//g, '-')`
3. Finds plan: `plans.find(p => p.week_of === weekOf)`
4. If not found, tries normalized comparison
5. Loads plan detail: `lessonApi.getPlanDetail(plan.id)`

### LessonMetadataDisplay
**Location:** shared/lesson-browser/src/components/LessonMetadataDisplay.tsx
**Date Calculation:**
1. Parses `weekOf`: "MM-DD-MM-DD" → extracts startMonth, startDay
2. Determines year:
   - Gets current year
   - If date is >30 days in past → uses next year
3. Calculates Monday date: `new Date(year, startMonth - 1, startDay)`
4. Adds day index to get lesson date

## 5. Critical Issues Identified

### Issue 1: Year Detection Logic
**Location:** LessonMetadataDisplay.tsx:102
**Problem:** Uses current year, then adjusts if date is >30 days in past
**Impact:** May calculate wrong year for dates near year boundary

### Issue 2: Plan Matching
**Location:** LessonDetailView.tsx:72
**Problem:** Exact string match may fail if formats differ
**Current Fix:** Added normalization, but may still miss edge cases

### Issue 3: State Synchronization
**Location:** LessonPlanBrowser.tsx
**Problem:** `selectedWeek` state may be stale when clicking lessons
**Current Fix:** Using `weekOfFromView` from WeekView, but need to verify it's always correct

### Issue 4: No Year in week_of
**Problem:** `week_of` format "MM-DD-MM-DD" doesn't include year
**Impact:** Year must be inferred, which can be wrong

## 6. Data Flow Diagram

```
Database (week_of: "12-01-12-05")
    ↓
Backend API (returns unchanged)
    ↓
Frontend API (planApi.list/getPlanDetail - returns unchanged)
    ↓
LessonPlanBrowser (stores in selectedWeek state)
    ↓
WeekView (receives as weekOf prop)
    ↓
handleLessonClick (uses weekOfFromView)
    ↓
selectedLesson.weekOf (stored)
    ↓
LessonDetailView (receives as weekOf prop)
    ↓
Plan Matching (normalizes and matches)
    ↓
LessonMetadataDisplay (calculates date from weekOf)
    ↓
Screen Display (shows calculated date)
```

## 7. Debugging Points Added

1. **WeekView:** Logs weekOf when clicking lesson
2. **handleLessonClick:** Logs week resolution priority
3. **LessonPlanBrowser:** Logs weekOf when rendering LessonDetailView
4. **LessonDetailView:** Logs plan matching process
5. **LessonMetadataDisplay:** Logs year calculation reasoning

## 8. Recommendations

1. **Add year to week_of format:** "YYYY-MM-DD-MM-DD" or separate year field
2. **Standardize week_of format:** Always use one format (dash or slash)
3. **Add validation:** Ensure week_of matches expected format
4. **Cache invalidation:** Clear cached plans when week changes
5. **Better error handling:** Show user-friendly message when plan not found

