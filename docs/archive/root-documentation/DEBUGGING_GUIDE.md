# Date Flow Debugging Guide

## Overview
This guide explains how to use the comprehensive logging added throughout the date flow to debug week/date mismatches.

## Logging Points

### 1. Database → Backend API

#### Backend: GET /api/users/{user_id}/plans
**Location:** `backend/api.py:3671`
**Log:** `plans_retrieved`
**Shows:**
- User ID
- Plan count
- All week_of values from database
- First plan's week_of

**Example:**
```
[INFO] plans_retrieved: {
  "user_id": "04fe8898-cb89-4a73-affb-64a97a98f820",
  "plan_count": 10,
  "week_of_values": ["12-01-12-05", "11-17-11-21", "11-10-11-14"],
  "first_plan_week_of": "12-01-12-05"
}
```

#### Backend: GET /api/plans/{plan_id}
**Location:** `backend/api.py:1978`
**Log:** `plan_detail_retrieved`
**Shows:**
- Plan ID
- week_of from database
- User ID
- Whether lesson_json exists

**Example:**
```
[INFO] plan_detail_retrieved: {
  "plan_id": "6dc1bd72-9481-44f4-9ee7-123c7dc2d1b0",
  "week_of": "12-01-12-05",
  "user_id": "04fe8898-cb89-4a73-affb-64a97a98f820",
  "has_lesson_json": true
}
```

### 2. Frontend API Layer

#### planApi.list() - Local Database
**Location:** `shared/lesson-api/src/index.ts:867`
**Log:** `[API] planApi.list (local)`
**Shows:**
- User ID
- Limit
- Plan count
- All week_of values
- First plan's week_of

#### planApi.list() - HTTP
**Location:** `shared/lesson-api/src/index.ts:880`
**Log:** `[API] planApi.list (HTTP)`
**Shows:** Same as local

#### planApi.getPlanDetail() - Local Database
**Location:** `shared/lesson-api/src/index.ts:1244`
**Log:** `[API] planApi.getPlanDetail (local)`
**Shows:**
- Plan ID
- week_of from database
- Whether lesson_json exists
- lesson_json type

#### planApi.getPlanDetail() - HTTP
**Location:** `shared/lesson-api/src/index.ts:1283`
**Log:** `[API] planApi.getPlanDetail (HTTP)`
**Shows:** Same as local

### 3. Frontend Component Layer

#### LessonPlanBrowser.fetchPlans()
**Location:** `shared/lesson-browser/src/components/LessonPlanBrowser.tsx:361`
**Log:** `[LessonPlanBrowser] fetchPlans result`
**Shows:**
- Plan count
- Week count
- All week_of values from plans
- All week_of values from weeks
- Current selectedWeek

**Log:** `[LessonPlanBrowser] Auto-selecting week` (if auto-selecting)
**Shows:**
- Available weeks
- Selected week

**Log:** `[LessonPlanBrowser] Keeping existing selectedWeek` (if keeping)
**Shows:**
- Current selectedWeek

#### WeekView - Lesson Click
**Location:** `shared/lesson-browser/src/components/WeekView.tsx:417`
**Log:** `[WeekView] Clicking lesson`
**Shows:**
- Subject
- Day
- Slot
- weekOf being passed
- Entry ID

#### handleLessonClick
**Location:** `shared/lesson-browser/src/components/LessonPlanBrowser.tsx:635`
**Log:** `[handleLessonClick] Week resolution`
**Shows:**
- weekOfFromView (from WeekView)
- scheduleEntry.week_of
- selectedWeek (state)
- Final weekOf being used
- Day
- Priority explanation

**Log:** `[handleLessonClick] Storing lesson`
**Shows:**
- Subject
- Day
- Slot
- weekOf being stored
- Note that this will be used by LessonDetailView

#### LessonPlanBrowser - Rendering LessonDetailView
**Location:** `shared/lesson-browser/src/components/LessonPlanBrowser.tsx:1637`
**Log:** `[LessonPlanBrowser] Rendering LessonDetailView with weekOf`
**Shows:**
- selectedLesson.weekOf
- scheduleEntry.week_of
- selectedWeek (state)
- Final weekOfForLesson
- Subject, day, slot
- Priority explanation

#### LessonDetailView - Loading Plan
**Location:** `shared/lesson-browser/src/components/LessonDetailView.tsx:54`
**Log:** `[LessonDetailView] Loading lesson plan with weekOf`
**Shows:**
- weekOf received as prop
- Day
- Slot

**Log:** `[LessonDetailView] Normalized weekOf`
**Shows:**
- Normalized weekOf
- All available plans with their week_of values

**Log:** `[LessonDetailView] Plan matching result`
**Shows:**
- Requested weekOf
- Normalized weekOf
- Match method (exact/normalized/reverse_normalized)
- Whether plan was found
- Matched plan ID and week_of
- All available plans with normalized values

#### LessonMetadataDisplay - Date Calculation
**Location:** `shared/lesson-browser/src/components/LessonMetadataDisplay.tsx:102`
**Log:** `[LessonMetadataDisplay] Year calculation`
**Shows:**
- weekOf
- Start month and day
- Current year
- Calculated year
- Days difference
- Reasoning for year choice

## How to Use This for Debugging

### Step 1: Identify the Problem
1. Note which date is showing incorrectly (e.g., "11/20/25" instead of "12/04/25")
2. Note which view you're in (WeekView, DayView, LessonDetailView, Lesson Mode)

### Step 2: Check the Console
1. Open browser DevTools Console
2. Filter logs by component name (e.g., `[LessonDetailView]`)
3. Look for the flow:
   - `[API] planApi.list` → Shows what weeks are available
   - `[LessonPlanBrowser] fetchPlans` → Shows which week is selected
   - `[WeekView] Clicking lesson` → Shows weekOf when clicking
   - `[handleLessonClick] Week resolution` → Shows how weekOf is determined
   - `[LessonDetailView] Plan matching result` → Shows if plan was found
   - `[LessonMetadataDisplay] Year calculation` → Shows date calculation

### Step 3: Identify the Mismatch
Look for discrepancies:
- Is `weekOfFromView` different from `selectedWeek`?
- Is the plan matching failing?
- Is the year calculation wrong?
- Is a cached plan being used?

### Step 4: Common Issues

#### Issue: Wrong weekOf from WeekView
**Check:** `[WeekView] Clicking lesson` log
**Fix:** Ensure WeekView receives correct weekOf prop

#### Issue: Plan not found
**Check:** `[LessonDetailView] Plan matching result` log
**Fix:** Check if weekOf format matches (dash vs slash)

#### Issue: Wrong year
**Check:** `[LessonMetadataDisplay] Year calculation` log
**Fix:** Adjust year detection logic if needed

#### Issue: Stale selectedWeek
**Check:** `[handleLessonClick] Week resolution` log
**Fix:** Ensure weekOfFromView is used (highest priority)

## Example Debugging Session

```
1. User clicks Thursday 12/04
2. Console shows:
   [WeekView] Clicking lesson: { weekOf: "12-01-12-05", ... }
   ✓ WeekView has correct weekOf
   
3. Console shows:
   [handleLessonClick] Week resolution: { 
     weekOfFromView: "12-01-12-05",
     selectedWeek: "11-17-11-21",
     using_weekOf: "12-01-12-05"
   }
   ✓ Correct weekOf is being used
   
4. Console shows:
   [LessonDetailView] Plan matching result: {
     requestedWeekOf: "12-01-12-05",
     matchMethod: "exact",
     found: "YES",
     matchedPlanWeekOf: "12-01-12-05"
   }
   ✓ Plan found correctly
   
5. Console shows:
   [LessonMetadataDisplay] Year calculation: {
     weekOf: "12-01-12-05",
     calculatedYear: 2025,
     ...
   }
   ✓ Year calculated correctly
   
6. But screen shows: 11/20/25
   ✗ Problem: Date calculation is wrong despite correct weekOf
   → Check if lesson_json has wrong data or if date calculation logic is wrong
```

## Next Steps

If the issue persists after checking all logs:
1. Share the complete console log output
2. Note which step shows the wrong value
3. Check if there are multiple plans with similar week_of values
4. Verify the database actually has the correct week_of for the plan

