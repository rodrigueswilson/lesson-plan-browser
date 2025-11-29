# Android Timer Issues and Solutions

## Problem Summary
The timer code was originally developed for Windows and is not working correctly on Android tablets. The timer uses JavaScript `setInterval` which can behave differently in Android WebView compared to desktop browsers.

## Key Findings from Documentation

### 1. **Android WebView Timer Limitations**

**Issue**: JavaScript `setInterval` in Android WebView can be:
- **Throttled** when the app is in the background
- **Paused** when the screen is locked
- **Inaccurate** due to battery optimization
- **Delayed** during high CPU usage

**Source**: Android WebView documentation and React Native timer warnings

### 2. **Date API Accuracy Issues**

**Current Implementation**: The code uses `new Date()` and `Date.getTime()` for time calculations:
```typescript
const now = new Date();
const elapsedSeconds = Math.max(0, (now.getTime() - lessonStart.getTime()) / 1000);
```

**Problem**: `Date` objects can be affected by:
- System clock changes
- Timezone adjustments
- Daylight saving time transitions
- Device sleep/wake cycles

### 3. **Recommended Solutions**

#### Option A: Use `performance.now()` for Relative Time
Instead of relying on absolute time, track elapsed time using `performance.now()`:

```typescript
// Store start time using performance.now() (monotonic clock)
const startTime = performance.now();

// Calculate elapsed time (not affected by system clock changes)
const elapsed = (performance.now() - startTime) / 1000;
```

**Advantages**:
- Monotonic clock (always increases, never goes backwards)
- Not affected by system time changes
- More accurate for relative timing
- Works better on Android

#### Option B: Use Timestamp-Based Countdown
Instead of decrementing a counter, calculate remaining time from a start timestamp:

```typescript
// When timer starts
const startTimestamp = Date.now();
const durationSeconds = 300; // 5 minutes

// In interval, calculate remaining time
const elapsed = (Date.now() - startTimestamp) / 1000;
const remaining = Math.max(0, durationSeconds - elapsed);
```

**Advantages**:
- Self-correcting if interval is delayed
- More resilient to background throttling
- Accurate even if interval fires late

#### Option C: Hybrid Approach (Recommended)
Combine both approaches for maximum reliability:

```typescript
// Use performance.now() for countdown accuracy
// Use Date.now() for wall-clock sync (if needed)

const startPerformanceTime = performance.now();
const startWallClockTime = Date.now();
const durationSeconds = 300;

// In interval
const elapsedPerformance = (performance.now() - startPerformanceTime) / 1000;
const remaining = Math.max(0, durationSeconds - elapsedPerformance);
```

### 4. **Android-Specific Considerations**

#### Background Timer Behavior
- Android may throttle `setInterval` to 1Hz (once per second) when in background
- Screen lock can pause JavaScript execution
- Battery saver mode can affect timer accuracy

#### Solutions:
1. **Request Wake Lock** (if needed for critical timers)
2. **Use Web Workers** for background timers (if supported)
3. **Implement drift correction** to compensate for missed intervals

### 5. **Current Code Issues**

#### Issue 1: Dependency Array Problem (FIXED)
- **Location**: `shared/lesson-mode/src/hooks/useLessonTimer.ts:448`
- **Problem**: `timerState.remainingTime` in dependency array caused interval to be cleared/recreated every second
- **Status**: ✅ Fixed - removed from dependencies

#### Issue 2: Dual Countdown Problem (FIXED)
- **Location**: `shared/lesson-mode/src/components/TimerDisplay.tsx`
- **Problem**: Both `useLessonTimer` and `TimerDisplay` were running separate countdowns
- **Status**: ✅ Fixed - removed local countdown, now uses `remainingTime` directly

#### Issue 3: Potential Date Accuracy Issue (TO INVESTIGATE)
- **Location**: `shared/lesson-mode/src/hooks/useLessonTimer.ts:128-130, 166-168`
- **Problem**: Using `new Date()` for elapsed time calculations may be inaccurate on Android
- **Recommendation**: Consider using `performance.now()` for relative timing

### 6. **Recommended Implementation Changes**

#### Change 1: Use Performance-Based Timing
```typescript
// In useLessonTimer.ts
const [startTime, setStartTime] = useState<number | null>(null);

// When timer starts
setStartTime(performance.now());

// In interval
if (startTime !== null) {
  const elapsed = (performance.now() - startTime) / 1000;
  const remaining = Math.max(0, durationSeconds - elapsed);
  setTimerState(prev => ({ ...prev, remainingTime: remaining }));
}
```

#### Change 2: Add Drift Correction
```typescript
// Track expected vs actual time
const expectedElapsed = (Date.now() - startTimestamp) / 1000;
const actualElapsed = (performance.now() - startPerformanceTime) / 1000;
const drift = actualElapsed - expectedElapsed;

// Correct if drift is significant (> 1 second)
if (Math.abs(drift) > 1) {
  // Adjust remaining time
}
```

#### Change 3: Handle Background/Resume
```typescript
// Listen for visibility changes
useEffect(() => {
  const handleVisibilityChange = () => {
    if (document.visibilityState === 'visible') {
      // Recalculate remaining time when app becomes visible
      // Compensate for time spent in background
    }
  };
  
  document.addEventListener('visibilitychange', handleVisibilityChange);
  return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
}, []);
```

## Testing Recommendations

1. **Test with screen locked**: Verify timer continues counting
2. **Test in background**: Switch to another app and verify timer accuracy
3. **Test with battery saver**: Enable battery saver mode and check timer behavior
4. **Test time changes**: Manually change device time and verify timer doesn't break
5. **Test long durations**: Run timer for 30+ minutes to check for drift

## References

- [Android WebView Documentation](https://developer.android.com/reference/android/webkit/WebView)
- [MDN: performance.now()](https://developer.mozilla.org/en-US/docs/Web/API/Performance/now)
- [MDN: setInterval](https://developer.mozilla.org/en-US/docs/Web/API/setInterval)
- React Native Timer Warnings (similar issues apply to WebView)

## Next Steps

1. ✅ Fix dependency array issue (DONE)
2. ✅ Remove dual countdown (DONE)
3. ⏳ Implement performance.now() for timing (RECOMMENDED)
4. ⏳ Add visibility change handler (RECOMMENDED)
5. ⏳ Test on actual Android device (REQUIRED)

