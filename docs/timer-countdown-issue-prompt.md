# Timer Countdown Issue - Fix Prompt

## Problem Statement
The lesson timer in the Android tablet app does not count down. When the user presses "Play", the timer remains frozen at the current time and does not decrement. The timer should count down from the remaining time (e.g., 15:00) to zero, then automatically advance to the next lesson step.

## Current Behavior
- Timer displays the correct initial `remainingTime` value
- When "Play" is pressed, `isRunning` becomes `true`
- Timer does NOT count down (remains frozen)
- Timer does NOT auto-advance when reaching zero

## Expected Behavior
- When "Play" is pressed, timer should count down every second (15:00 → 14:59 → 14:58 → ... → 0:00)
- When timer reaches 0:00, it should automatically advance to the next step and start counting down from that step's duration
- Timer should work in both "Live Mode" (synced with actual time) and "Preview Mode" (manual control)

## Key Files
1. **`shared/lesson-mode/src/hooks/useLessonTimer.ts`** - Core timer logic with countdown interval
2. **`shared/lesson-mode/src/components/TimerDisplay.tsx`** - UI component that displays the timer
3. **`shared/lesson-mode/src/components/LessonMode.tsx`** - Parent component that uses the timer hook

## What Has Been Tried
1. ✅ Fixed React import issues and TypeScript configuration
2. ✅ Removed `remainingTime` from dependency array to prevent interval recreation
3. ✅ Simplified event handlers to avoid React type issues
4. ✅ Added condition to only create interval when `isRunning && remainingTime > 0`
5. ✅ Modified interval callback to stop timer when `remainingTime <= 0`
6. ✅ Removed dual countdown logic (TimerDisplay no longer has its own interval)

## Current Code State

### useLessonTimer.ts (Lines 373-511)
The countdown effect creates an interval when `timerState.isRunning` is true:
```typescript
useEffect(() => {
  if (timerState.isRunning) {
    if (!intervalRef.current && timerState.remainingTime > 0) {
      intervalRef.current = setInterval(() => {
        setTimerState(prev => {
          if (prev.remainingTime <= 0) {
            return { ...prev, isRunning: false };
          }
          const newRemaining = Math.max(0, prev.remainingTime - 1);
          // ... auto-advance logic when newRemaining === 0
          return { ...prev, remainingTime: newRemaining };
        });
      }, 1000);
    }
  } else {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }
  return () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };
}, [timerState.isRunning, timerState.currentStepIndex, steps, autoAdvance, onStepComplete, onLessonComplete, advanceToStep]);
```

### TimerDisplay.tsx
- Displays `remainingTime` directly from props (no local countdown)
- Calls `onComplete` callback when `remainingTime` transitions from >0 to 0
- No longer has its own `setInterval`

## Debugging Steps Needed

1. **Check if interval is being created:**
   - Add console.log in the countdown useEffect to verify interval creation
   - Check if `intervalRef.current` is being set correctly
   - Verify `timerState.isRunning` is actually `true` when Play is pressed

2. **Check if interval callback is executing:**
   - Add console.log inside the setInterval callback
   - Verify `setTimerState` is being called every second
   - Check if state updates are being applied

3. **Check for race conditions:**
   - Verify the interval isn't being cleared immediately after creation
   - Check if multiple intervals are being created
   - Ensure cleanup function isn't interfering

4. **Check React state updates:**
   - Verify `remainingTime` in state is actually changing
   - Check if component is re-rendering with new `remainingTime` value
   - Verify `TimerDisplay` is receiving updated `remainingTime` prop

5. **Check Android-specific issues:**
   - Verify `setInterval` works correctly on Android WebView
   - Check if background/foreground state affects timer
   - Test if performance.now() vs Date.now() causes issues

## Potential Root Causes

1. **Interval not being created:** Condition `timerState.isRunning && timerState.remainingTime > 0` might fail
2. **Interval being cleared immediately:** Cleanup function might run before interval executes
3. **State updates not propagating:** React state updates might be batched or not applied
4. **Android WebView limitations:** `setInterval` might not work as expected in Tauri Android WebView
5. **Dependency array issues:** Effect might not re-run when needed, or re-runs too often

## Success Criteria
- Timer counts down from initial value to zero
- Timer auto-advances to next step when reaching zero
- Timer works in both Live Mode and Preview Mode
- Timer can be paused and resumed
- Timer can be manually adjusted (drag slider) and continues counting from adjusted time

## Testing Instructions
1. Launch app on Android tablet
2. Navigate to Lesson Mode for any lesson plan
3. Press "Play" button
4. Observe timer - it should count down every second
5. Let timer reach zero - it should auto-advance to next step
6. Test pause/resume functionality
7. Test manual time adjustment (drag slider)

## Additional Context
- App is built with Tauri v2 for Android
- Frontend uses React + TypeScript
- Timer hook uses `setInterval` for countdown
- Timer state is managed in `useLessonTimer` hook
- UI component (`TimerDisplay`) is a pure display component
- App must work 100% offline (no network dependencies)

