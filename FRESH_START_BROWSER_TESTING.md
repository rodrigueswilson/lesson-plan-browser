# Fresh Start - Browser Testing Guide

## Quick Start Instructions

### Prerequisites Check
- Python 3.8+ installed
- Node.js 18+ installed
- Virtual environment activated (if using)
- Database migration completed

### Step 1: Start Backend Server

Open a terminal and run:
```bash
cd D:\LP
python -m uvicorn backend.api:app --reload --port 8000
```

Or use the batch file:
```bash
start-backend.bat
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verify Backend:**
- Open http://localhost:8000/api/docs in browser
- Should see FastAPI documentation page
- Check for any startup errors in terminal

### Step 2: Start Frontend Dev Server (Browser Mode)

Open a **NEW** terminal and run:
```bash
cd D:\LP\frontend
npm run dev
```

**Expected Output:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**Note**: This runs Vite dev server for browser testing (NOT Tauri desktop app)

### Step 3: Open in Chrome Browser

1. Open Google Chrome browser
2. Navigate to: **http://localhost:5173**
3. Open Developer Tools:
   - Press `F12` or `Ctrl+Shift+I`
   - Go to "Console" tab
4. Check for any console errors

### Step 4: Test Lesson Mode

1. **Select a User** (if user selector is visible)
2. **Navigate to Browser Module** (click "Browser" in navigation)
3. **Enter Lesson Mode**:
   - Click "Enter Lesson Mode" on current lesson card, OR
   - Click on a lesson in the browser to view details, then "Enter Lesson Mode"
4. **Observe Console**:
   - Check for errors during initialization
   - Look for session creation/loading messages
   - Verify timer synchronization messages

### Step 5: Test Persistence

1. **Start a lesson** and let timer run for a few seconds
2. **Change to next step** (click "Next" or wait for auto-advance)
3. **Pause timer**
4. **Refresh browser** (F5)
5. **Verify**:
   - Lesson Mode should restore automatically
   - Timer should be paused at the same step
   - Console should show "Restored session state" message

## Common Issues to Check

### Console Errors to Look For

1. **API Connection Errors**:
   - `Failed to fetch`
   - `Network request failed`
   - `CORS error`
   - **Fix**: Ensure backend is running on port 8000

2. **Session Errors**:
   - `Failed to load active session`
   - `Failed to save session`
   - `Session not found`
   - **Fix**: Check database migration was run

3. **Plan ID Resolution Errors**:
   - `Could not find matching lesson plan`
   - `Missing lesson plan information`
   - **Fix**: Ensure lesson plans exist for the current week

4. **Timer Errors**:
   - `Failed to initialize lesson`
   - `No lesson steps available`
   - **Fix**: Ensure lesson plan has steps generated

5. **Type Errors**:
   - `Cannot read property of undefined`
   - `TypeError: ...`
   - **Fix**: Check component props and state initialization

### Terminal Errors to Check

**Backend Terminal:**
- Database connection errors
- Import errors
- API endpoint registration errors

**Frontend Terminal (Vite):**
- Module resolution errors
- TypeScript compilation errors
- Build errors

## Quick Verification Checklist

- [ ] Backend server running (http://localhost:8000/api/docs works)
- [ ] Frontend dev server running (http://localhost:5173 loads)
- [ ] No console errors on page load
- [ ] User can be selected (if applicable)
- [ ] Browser module is accessible
- [ ] Lesson Mode can be entered
- [ ] Timer displays and syncs correctly
- [ ] Steps can be navigated
- [ ] Timer adjustment dialog works
- [ ] Session persists across refresh
- [ ] Session restores state correctly

## Testing Session Persistence

### Test 1: Create Session
1. Enter Lesson Mode
2. Start timer
3. Wait 10 seconds
4. Check console for: "Session created" or API call to `/api/lesson-mode/session`
5. Verify session exists: Check Network tab → Filter: "session"

### Test 2: Restore Session
1. Refresh browser (F5)
2. Re-enter Lesson Mode
3. Check console for: "Restored session state"
4. Verify timer state is restored

### Test 3: Adjust Timer
1. Open timer adjustment dialog
2. Add 5 minutes
3. Wait for save (check Network tab)
4. Refresh browser
5. Verify adjusted duration persists

## Debugging Tips

1. **Check Network Tab**: Look for API calls to `/api/lesson-mode/session*`
   - Should see POST/PUT on state changes
   - Should see GET on mount to load active session

2. **Check Console Logs**: Look for:
   - "Restored session state: ..."
   - "Failed to save session: ..."
   - Timer synchronization messages

3. **Check Application Tab** (Chrome DevTools):
   - Local Storage / Session Storage (if used)
   - IndexedDB (if used)

4. **Backend Logs**: Check terminal for:
   - API request logs
   - Database query logs
   - Error messages

## Stopping Services

1. **Stop Frontend**: Press `Ctrl+C` in frontend terminal
2. **Stop Backend**: Press `Ctrl+C` in backend terminal
3. Or close the terminal windows

## Files to Review for Errors

If you encounter errors, check these files:
- `frontend/src/components/LessonMode.tsx` - Main component logic
- `frontend/src/hooks/useLessonTimer.ts` - Timer synchronization
- `frontend/src/lib/api.ts` - API client functions
- `backend/api.py` - API endpoint handlers
- `backend/database.py` or `backend/supabase_database.py` - Database methods

