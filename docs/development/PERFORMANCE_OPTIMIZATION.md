# Performance Optimization: Recent Weeks Endpoint

## Issue Observed

Multiple calls to `/api/recent-weeks` endpoint in quick succession:

```
INFO: GET /api/recent-weeks?user_id=... HTTP/1.1" 200 OK
INFO: GET /api/recent-weeks?user_id=... HTTP/1.1" 200 OK  
INFO: GET /api/recent-weeks?user_id=... HTTP/1.1" 200 OK
```

## Root Cause

The `useEffect` hook in `BatchProcessor.tsx` was depending on the entire `currentUser` object:

```typescript
useEffect(() => {
  if (currentUser) {
    loadRecentWeeks();
  }
}, [currentUser]); // ❌ Triggers on any object reference change
```

This causes the effect to run whenever the `currentUser` object reference changes, even if the actual user ID hasn't changed.

## Fix Applied

Changed dependency to only track the user ID:

```typescript
useEffect(() => {
  if (currentUser?.id) {
    loadRecentWeeks();
  }
}, [currentUser?.id]); // ✅ Only triggers when user ID changes
```

## Expected Behavior After Fix

- ✅ Effect only runs when user actually changes
- ✅ No duplicate API calls for same user
- ✅ Better performance
- ✅ Reduced server load

## Base Path Warning

The warning `"Base path does not exist: F:\test\lesson-plans"` is expected behavior:

- User set a test path that doesn't exist
- Function handles this gracefully by returning `[]`
- Warning is informational, not an error
- Frontend handles empty array correctly

**To resolve:** User should either:
1. Create the folder: `F:\test\lesson-plans`
2. Set a valid path in user settings
3. Leave empty if not using weekly plans feature

## Files Changed

- `frontend/src/components/BatchProcessor.tsx` (line ~43)

## Status

✅ **Optimized** - Effect now only triggers on user ID change

---

**Date:** 2025-11-07  
**Impact:** Low (performance improvement, not a bug fix)

