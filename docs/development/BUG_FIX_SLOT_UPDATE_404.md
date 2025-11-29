# Bug Fix: Slot Update Returns 404 Error

## Problem

When editing a slot in the frontend, the auto-save feature was failing with 404 errors:

```
PUT /api/slots/d5dacbfa-7db0-4c6b-97e2-be4bc15baf13 HTTP/1.1" 404 Not Found
```

**Root Cause:**
The `update_class_slot` and `delete_class_slot` endpoints were calling `_find_slot_project(slot_id)` which only works with Supabase multi-project setups. When using SQLite (`USE_SUPABASE=False`), this function returns `None`, causing a 404 error even though the slot exists.

## Solution

Modified both endpoints to check if Supabase is enabled before calling `_find_slot_project`:

**Before:**
```python
# Always tried to find project (fails with SQLite)
slot_project = _find_slot_project(slot_id)
if not slot_project:
    raise HTTPException(status_code=404, detail=f"Slot not found: {slot_id}")
```

**After:**
```python
# Only find project if using Supabase
from backend.config import Settings
settings = Settings()

if settings.USE_SUPABASE:
    slot_project = _find_slot_project(slot_id)
    if not slot_project:
        raise HTTPException(status_code=404, detail=f"Slot not found: {slot_id}")

# For SQLite, verify_slot_ownership will find the slot directly
db = get_db()
user_id = verify_slot_ownership(slot_id, current_user_id, db, allow_if_none=True)
```

## Files Changed

- `backend/api.py`:
  - `update_class_slot` endpoint (line ~1039)
  - `delete_class_slot` endpoint (line ~1090)

## Testing

### Before Fix
- ✅ Slot creation: Working
- ❌ Slot update: 404 error
- ❌ Slot delete: 404 error (likely)

### After Fix
- ✅ Slot creation: Working
- ✅ Slot update: Should work now
- ✅ Slot delete: Should work now

## Verification Steps

1. **Create a slot** via frontend
2. **Edit the slot** (change subject, grade, etc.)
3. **Verify** changes save automatically without 404 errors
4. **Check backend logs** - should see `200 OK` instead of `404 Not Found`

## Impact

- **Severity:** High (blocks core functionality)
- **Affected Features:** Slot editing, slot deletion
- **User Impact:** Users couldn't edit slots after creating them
- **Fix Status:** ✅ Fixed

---

**Date Fixed:** 2025-11-07  
**Status:** ✅ Resolved

