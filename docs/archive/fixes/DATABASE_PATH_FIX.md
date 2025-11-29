# Database Path Configuration Fix

## Problem Identified

The database path was inconsistent across the codebase:

1. **Config default**: `data/lesson_plans.db` (in `backend/config.py`)
2. **Database class default**: `data/lesson_planner.db` (hardcoded in `database.py`)
3. **.env file**: May override with either path
4. **Actual file**: `data/lesson_planner.db` (with all the user data)

**Result**: Backend created a NEW empty database, so users disappeared from the UI.

## Root Cause

```python
# backend/database.py (OLD)
def __init__(self, db_path: str = "data/lesson_planner.db"):  # Hardcoded!
```

This ignored `settings.DATABASE_URL` entirely.

## Solution Implemented

### 1. Fixed Database Class to Use Settings

```python
# backend/database.py (NEW)
def __init__(self, db_path: str = None):
    if db_path is None:
        from backend.config import settings
        # Extract path from sqlite:///./data/lesson_planner.db format
        db_path = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")
    self.db_path = Path(db_path)
```

### 2. Updated Config Default

```python
# backend/config.py
DATABASE_URL: str = "sqlite:///./data/lesson_planner.db"  # Match actual file
```

## Files Modified

| File | Change | Purpose |
|------|--------|---------|
| `backend/database.py` | +4 lines | Use settings.DATABASE_URL by default |
| `backend/config.py` | 1 line | Update default to lesson_planner.db |

## What This Fixes

**Before**:
- Config says: `lesson_plans.db`
- Database class uses: `lesson_planner.db` (hardcoded)
- Backend creates: NEW `lesson_planner.db` (empty)
- Users query: `lesson_planner.db` (has data)
- API reads: NEW empty database
- **Result**: No users in UI ❌

**After**:
- Config says: `lesson_planner.db`
- Database class uses: `settings.DATABASE_URL` → `lesson_planner.db`
- Backend uses: EXISTING `lesson_planner.db` (with data)
- **Result**: Users appear in UI ✅

## Testing

### Verify Configuration
```bash
python check_config.py
```
Should show: `DATABASE_URL: sqlite:///./data/lesson_planner.db`

### Verify Database Has Users
```bash
python check_recent_plans.py
```
Should show users and plans.

### Restart Backend
The backend must be restarted to load the new code:
```bash
# Stop current backend (Ctrl+C)
# Start again
python -m uvicorn backend.api:app --reload
```

### Check API
```bash
curl http://localhost:8000/api/users
```
Should return list of users (not empty array).

## Note on .env File

If you have a `.env` file that sets `DATABASE_URL`, it will override the default. Make sure it points to the correct file:

```env
DATABASE_URL=sqlite:///./data/lesson_planner.db
```

## Status

✅ **Code fixed**  
⏭️ **Restart backend to apply**  
⏭️ **Verify users appear in UI**
