# Lesson Navigation Test

## Changes Made
1. **LessonDetailView** - Added navigation buttons (Previous/Next) with props:
   - `onPreviousLesson`, `onNextLesson` handlers
   - `canGoPrevious`, `canGoNext` state for button disabling
   - Shows current lesson number and day

2. **LessonPlanBrowser** - Added navigation logic:
   - Tracks `currentDayLessons` state
   - `handlePreviousLesson` and `handleNextLesson` functions
   - Calculates navigation state based on current lesson index

3. **WeekView & DayView** - Updated to pass all day's lessons:
   - Updated `onLessonClick` signature to include `allDayLessons` parameter
   - Passes the day's lesson array for navigation context

## How to Test
1. Open the app and navigate to a week with multiple lessons
2. Click on any lesson to open LessonDetailView
3. Verify navigation buttons appear at the top
4. Test Previous/Next buttons to navigate between lessons
5. Check that buttons are disabled at first/last lesson
6. Verify lesson number and day display correctly

## Expected Behavior
- Previous button disabled on first lesson of the day
- Next button disabled on last lesson of the day
- Navigation preserves lesson plan data correctly
- Smooth transitions between lessons
