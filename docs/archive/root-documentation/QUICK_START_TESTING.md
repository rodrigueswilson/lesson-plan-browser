# Quick Start - Browser Testing with Chrome

## Summary of Current Implementation

**Status**: All Lesson Mode v2 features are complete and integrated.

### Completed Features:
1. ✅ **Plan ID Mapping** - Resolves lesson plans from schedule entries using week context
2. ✅ **Timer Synchronization** - Auto-syncs with actual lesson time
3. ✅ **Auto-Advance** - Automatically moves to next step when timer expires
4. ✅ **Timer Adjustment** - Dialog to add/subtract time, reset, or skip steps
5. ✅ **Step Recalculation** - Proportionally adjusts remaining step durations
6. ✅ **State Persistence** - Saves and restores session state across refresh/navigation
7. ✅ **Enhanced Timer Display** - Shows sync status, adjust button, original vs adjusted durations

### Key Components:
- `useLessonTimer` hook - Timer synchronization logic
- `TimerAdjustmentDialog` - Timer adjustment UI
- `planIdResolver` - Plan ID resolution utility
- `lessonStepRecalculation` - Proportional recalculation algorithm
- Session persistence API - Complete backend and frontend integration

## Fresh Start Instructions

### Option 1: Use Startup Script (Recommended)

Double-click: **`START_FRESH_BROWSER_TEST.bat`**

This script will:
1. Start backend server on port 8000
2. Start frontend dev server on port 5173
3. Open Chrome browser with DevTools console automatically

### Option 2: Manual Start

#### Terminal 1: Backend Server
```bash
cd D:\LP
python -m uvicorn backend.api:app --reload --port 8000
```

**Verify**: Open http://localhost:8000/api/docs - Should see FastAPI docs

#### Terminal 2: Frontend Dev Server
```bash
cd D:\LP\frontend
npm run dev
```

**Verify**: Should see "VITE v5.x.x ready" on http://localhost:1420

#### Browser: Chrome with DevTools
1. Open Chrome browser
2. Press `F12` to open DevTools
3. Go to "Console" tab
4. Navigate to: **http://localhost:1420** (Vite dev server port)

## What to Check in Console

### Expected Console Messages (Normal)
- React app initialization messages
- API calls to `/api/lesson-mode/session`
- "Restored session state: ..." when session exists
- Timer synchronization messages

### Errors to Look For (Issues)

1. **Backend Connection Errors**:
   ```
   Failed to fetch
   NetworkError
   CORS error
   ```
   **Action**: Verify backend is running on port 8000

2. **Session API Errors**:
   ```
   Failed to load active session
   Failed to save session
   404 Session not found
   ```
   **Action**: Check database migration was run

3. **Plan Resolution Errors**:
   ```
   Could not find matching lesson plan
   Missing lesson plan information
   ```
   **Action**: Ensure lesson plans exist for current week

4. **Timer Initialization Errors**:
   ```
   Failed to initialize lesson
   No lesson steps available
   ```
   **Action**: Ensure lesson plan has generated steps

5. **Type/Import Errors**:
   ```
   Cannot read property of undefined
   Module not found
   ```
   **Action**: Check for missing imports or component errors

## Quick Test Sequence

1. **Start Services** (use script or manual)
2. **Open Chrome** (http://localhost:5173) with DevTools console
3. **Select User** (if user selector visible)
4. **Navigate to Browser** module
5. **Enter Lesson Mode** from current lesson card
6. **Check Console** for:
   - Any red error messages
   - Session creation/loading messages
   - Timer sync messages
7. **Test Timer**:
   - Start timer
   - Let it run 5-10 seconds
   - Click "Next Step"
   - Pause timer
8. **Test Persistence**:
   - Refresh browser (F5)
   - Should restore to same step with timer paused
   - Check console for "Restored session state"

## Database Migration Reminder

**Before testing**, ensure database migration is run:

### SQLite:
```bash
python backend/migrations/create_lesson_mode_sessions_table.py
```

### Supabase:
- Open Supabase SQL Editor
- Run contents of `sql/create_lesson_mode_sessions_table_supabase.sql`

## Troubleshooting

### Frontend won't start
- Check Node.js version: `node --version` (need 18+)
- Install dependencies: `cd frontend && npm install`
- Check port 1420 is available

### Backend won't start
- Check Python version: `python --version` (need 3.8+)
- Install dependencies: `pip install -r requirements.txt`
- Check port 8000 is available

### Chrome won't open with DevTools
- Manually open Chrome
- Press F12 to open DevTools
- Navigate to http://localhost:5173
- Go to Console tab

### No console errors but features not working
- Check Network tab in DevTools
- Look for failed API requests
- Check backend terminal for errors
- Verify database migration completed

## Files Summary

### New Files Created:
- `frontend/src/utils/planIdResolver.ts`
- `frontend/src/hooks/useLessonTimer.ts`
- `frontend/src/components/TimerAdjustmentDialog.tsx`
- `frontend/src/utils/lessonStepRecalculation.ts`
- `backend/migrations/create_lesson_mode_sessions_table.py`
- `sql/create_lesson_mode_sessions_table_supabase.sql`

### Modified Files:
- `frontend/src/components/LessonMode.tsx` - Full persistence integration
- `frontend/src/components/TimerDisplay.tsx` - Enhanced with adjust button
- `frontend/src/lib/api.ts` - Added session API
- `backend/schema.py` - Added LessonModeSession model
- `backend/models.py` - Added session models
- `backend/database_interface.py` - Added session methods
- `backend/database.py` - Implemented SQLite session methods
- `backend/supabase_database.py` - Implemented Supabase session methods
- `backend/api.py` - Added 5 session API endpoints

## Next Steps After Testing

1. **Fix any console errors** found during testing
2. **Verify persistence** works across refresh
3. **Test timer adjustments** persist correctly
4. **Check timer synchronization** with actual time
5. **Validate auto-advance** functionality
6. **Test session restore** on navigation

