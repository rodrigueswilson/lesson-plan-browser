# Fix: get_current_user_id Dependency Issue

## Problem

The frontend was showing "Failed to fetch" errors when trying to load user data, even though the API was returning users correctly. The backend logs showed:

```
TypeError: object of type 'function' has no len()
```

This occurred in `backend/authorization.py` at line 104 when trying to check the length of `current_user_id`.

## Root Cause

In `backend/api.py`, the `get_current_user_id` function was being used incorrectly as a default parameter value instead of as a FastAPI dependency:

**Before (incorrect):**
```python
current_user_id: Optional[str] = get_current_user_id,
```

This set `current_user_id` to the function object itself, not the result of calling it.

## Solution

Changed all instances to use FastAPI's `Depends()` wrapper:

**After (correct):**
```python
from fastapi import Depends, ...

current_user_id: Optional[str] = Depends(get_current_user_id),
```

This tells FastAPI to inject the result of calling `get_current_user_id()` as the dependency.

## Changes Made

1. **Added `Depends` to imports:**
   ```python
   from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
   ```

2. **Updated all 11 endpoint functions** that use `current_user_id`:
   - `get_recent_weeks`
   - `get_user`
   - `update_user`
   - `update_user_base_path`
   - `delete_user`
   - `create_class_slot`
   - `get_class_slots`
   - `update_class_slot`
   - `delete_class_slot`
   - `get_weekly_plans`
   - `process_week`

## Verification

After restarting FastAPI:
- ✅ `/api/users` should return users correctly
- ✅ Individual user endpoints should work without errors
- ✅ Frontend should load user data successfully
- ✅ No more `TypeError: object of type 'function' has no len()` errors

## Next Steps

1. Restart FastAPI
2. Test `/api/users` endpoint
3. Verify frontend loads users correctly
4. Test individual user endpoints (e.g., `/api/users/{user_id}`)

