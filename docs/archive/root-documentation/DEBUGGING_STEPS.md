# Debugging Steps for Date Mismatch Issue

## Current Issue
Clicking on Thursday 12/04 shows lesson from 11/20/25 instead of 12/04/25.

## Comprehensive Logging Added

All components now log their weekOf values. When you click on Thursday 12/04, check the browser console for these logs in order:

### 1. WeekView Initialization
**Look for:** `[WeekView] Component rendered/re-rendered with weekOf prop:`
- Should show: `weekOf: "12-01-12-05"` (or the week containing 12/04)
- If it shows a different week, that's the problem

### 2. WeekView Plan Loading
**Look for:** `[WeekView] Plan lookup for weekOf:`
- Shows which plan was found for the weekOf
- Check if `planFound: true` and `planWeekOf` matches the weekOf

### 3. WeekView Lesson Click
**Look for:** `[WeekView] Clicking lesson:`
- Should show: `weekOf: "12-01-12-05"` (or the week containing 12/04)
- This is the weekOf being passed to handleLessonClick

### 4. handleLessonClick Week Resolution
**Look for:** `[handleLessonClick] Week resolution:`
- Should show:
  - `weekOfFromView: "12-01-12-05"` (from WeekView)
  - `using_weekOf: "12-01-12-05"` (final week being used)
- If `using_weekOf` is different from `weekOfFromView`, that's the problem

### 5. handleLessonClick Cache Check
**Look for:** `[handleLessonClick] Cache check:`
- Shows if cached data is being used
- Check if `cachedLessonPlanWeek` matches `lessonWeekOf`

### 6. handleLessonClick Plan Selection
**Look for:** `[handleLessonClick] Plan selection:`
- Shows which plan was selected
- **CRITICAL:** Check `selectedPlanWeekOf` - it should match `lessonWeekOf`

### 7. LessonPlanBrowser Rendering
**Look for:** `[LessonPlanBrowser] Rendering LessonDetailView with weekOf:`
- Shows what weekOf is being passed to LessonDetailView
- **CRITICAL:** Check `final_weekOfForLesson` - should be "12-01-12-05"

### 8. LessonDetailView Component Render
**Look for:** `[LessonDetailView] Component rendered with props:`
- Shows the weekOf prop received
- Should match what was passed from LessonPlanBrowser

### 9. LessonDetailView Plan Matching
**Look for:** `[LessonDetailView] Plan matching result:`
- Shows if plan was found
- **CRITICAL:** Check `matchedPlanWeekOf` - should match `requestedWeekOf`

### 10. LessonDetailView Week Validation
**Look for:** `[LessonDetailView] WEEK MISMATCH DETECTED!` (if there's a problem)
- This is a new validation that will catch if the wrong plan was loaded
- If you see this, it means the plan matching found the wrong plan

### 11. LessonMetadataDisplay Date Calculation
**Look for:** `[LessonMetadataDisplay] Year calculation:`
- Shows how the date is calculated from weekOf
- Check `calculatedYear` and the final date

## What to Check

1. **Is WeekView receiving the correct weekOf?**
   - Check log #1
   - If wrong, the week selector might not be updating `selectedWeek` correctly

2. **Is the correct weekOf being passed when clicking?**
   - Check logs #3 and #4
   - `weekOfFromView` should be the week containing 12/04

3. **Is the correct plan being loaded?**
   - Check logs #6 and #9
   - `selectedPlanWeekOf` and `matchedPlanWeekOf` should match the requested week

4. **Is the date being calculated correctly?**
   - Check log #11
   - The calculated date should be 12/04/25

## Expected Flow for Thursday 12/04

1. WeekView receives: `weekOf="12-01-12-05"` (week containing 12/04)
2. WeekView passes: `weekOf="12-01-12-05"` to handleLessonClick
3. handleLessonClick uses: `lessonWeekOf="12-01-12-05"`
4. handleLessonClick finds plan with: `week_of="12-01-12-05"`
5. LessonDetailView receives: `weekOf="12-01-12-05"`
6. LessonDetailView finds plan with: `week_of="12-01-12-05"`
7. LessonMetadataDisplay calculates: Thursday = 12/04/25

## If Issue Persists

Please share the complete console log output when clicking on Thursday 12/04. The logs will show exactly where the weekOf value changes or where the wrong plan is being selected.

