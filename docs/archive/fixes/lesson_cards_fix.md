# Lesson Cards Disappeared - Fix Applied

## Problem
After adding navigation functionality, lesson plan cards disappeared from the UI showing "No lessons scheduled".

## Root Cause
I changed the `onLessonClick` function signature in WeekView and DayView to include an additional `allDayLessons` parameter, but the calling code in LessonPlanBrowser was still using the old signature. This caused a runtime error that prevented the lesson cards from rendering.

## Solution
1. **Reverted interface changes** - Restored original `onLessonClick` signature in WeekView and DayView
2. **Implemented navigation differently** - Instead of passing all lessons through the callback, I fetch the day's lessons asynchronously when a lesson is selected
3. **Added helper function** - Copied `isNonClassPeriod` helper to LessonPlanBrowser for filtering lessons
4. **Updated navigation handlers** - Simplified them to work with the new approach

## Changes Made
- `WeekView.tsx`: Reverted onLessonClick interface and calls
- `DayView.tsx`: Reverted onLessonClick interface and calls  
- `LessonPlanBrowser.tsx`: 
  - Added isNonClassPeriod helper
  - Made handleLessonClick async to fetch day lessons
  - Updated navigation handlers
  - Added scheduleApi import

## Status
- Lesson cards should now be visible again
- Navigation functionality is preserved
- No TypeScript errors related to the changes
