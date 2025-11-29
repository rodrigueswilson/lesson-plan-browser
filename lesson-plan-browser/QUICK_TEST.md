# Quick Test Guide - Browser Data Flow

## Before Running Tauri App

Run this test to verify the backend API is ready before starting the browser app.

## Quick Commands

### 1. Start Backend (if not running)
```powershell
python -m uvicorn backend.api:app --reload --port 8000
```

### 2. Run Test (in new terminal)
```powershell
cd lesson-plan-browser
python test_browser_data_flow.py
```

## What It Does

Tests all API endpoints the browser app uses:
- ✅ Health check
- ✅ User listing and details
- ✅ Recent weeks (JSON file detection)
- ✅ Lesson plans from database
- ✅ Schedule entries
- ✅ Class slots
- ✅ Lesson steps
- ✅ Lesson mode sessions

## Expected Output

```
============================================================
BROWSER APP DATA FLOW TEST SUITE
============================================================
Testing API endpoints at: http://localhost:8000/api

✅ Health Check
   Version: 1.0.0

Testing Browser App Endpoints...
------------------------------------------------------------
✅ List Users
   Found 1 user(s)
✅ Get User
   User: Your Name
✅ Recent Weeks
   Found 3 week(s) from JSON files
✅ List Plans
   Found 5 plan(s) in database
...

============================================================
TEST SUMMARY
============================================================
✅ Passed: 13
❌ Failed: 0
⚠️  Warnings: 2

✅ ALL TESTS PASSED - Backend is ready for browser app!
```

## If Tests Fail

1. **Backend not running**: Start backend first
2. **Connection errors**: Check backend is on port 8000
3. **Missing data**: Warnings are OK (app will show empty views)

## Next Step

Once tests pass:
```powershell
cd lesson-plan-browser\frontend
npm run tauri:dev
```

