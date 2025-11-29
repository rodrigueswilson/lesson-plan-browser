# IPC Testing Steps - Desktop

**Goal:** Verify Rust ↔ Python sidecar IPC communication works

## Step 1: Locate Sync Test Button

The app should have a "IPC Sync Test" button in the UI (from `SyncTestButton` component).

**Where to find it:**
- Look for a section with "IPC Sync Test" heading
- Should have a "Test Sync" button
- Only visible if a user is selected

**If not visible:**
- Make sure a user is selected first
- Check browser console for any errors

## Step 2: Test Sidecar Spawn

### Action:
1. **Select a user** in the app (if not already selected)
2. **Click "Test Sync" button**
3. **Watch terminal** where `tauri:dev` is running

### Expected Terminal Output:

**Success:**
```
[No errors]
Python sidecar should spawn silently
```

**Failure:**
```
Failed to spawn Python sidecar: [error message]
```

### Check Python Process:

**Windows PowerShell:**
```powershell
Get-Process python | Where-Object {$_.Path -like "*LP*"}
```

**Should see:** Python process running with `-m backend.sidecar_main`

## Step 3: Verify IPC Communication

### What to Look For:

1. **In App Console (F12):**
   - `[API] Attempting sync via Tauri command...`
   - `[API] Invoking trigger_sync with userId: ...`
   - `[API] Sync successful via Tauri: {...}` OR error message

2. **In Terminal (Tauri dev):**
   - Python process spawns (no error)
   - IPC messages (if logging enabled)
   - Any error messages

3. **In App UI:**
   - Button shows "Syncing..." while processing
   - Success message: "Sync completed! Pulled: X, Pushed: Y"
   - OR error message displayed

## Step 4: Check Database Operations

### Verify SQLite Database:

**Location:** `%APPDATA%\lesson_planner.db` (Windows)

**Check if database exists:**
```powershell
Test-Path "$env:APPDATA\lesson_planner.db"
```

**If database exists, verify tables:**
```powershell
# Install sqlite3 if needed: choco install sqlite
sqlite3 "$env:APPDATA\lesson_planner.db" ".tables"
```

**Expected tables:**
- users
- class_slots
- weekly_plans
- schedule_entries

## Step 5: Test Error Handling

### Test Cases:

1. **No user selected:**
   - Should show: "No user selected" error

2. **Python not found:**
   - Should show: "Failed to start Python sidecar" error
   - Check error message details

3. **Backend module not found:**
   - Should show import error
   - Verify: `python -c "from backend import sidecar_main"`

## Troubleshooting

### Issue: "Failed to spawn Python sidecar"

**Check:**
1. Python installed: `python --version`
2. Backend module: `python -c "from backend import sidecar_main"`
3. Project root detection in `lib.rs` (lines 110-132)

**Fix:**
- Ensure Python is in PATH
- Run from correct directory
- Check project structure

### Issue: "No response from sidecar"

**Check:**
1. Python process running? (Task Manager / `Get-Process python`)
2. Check Python stderr for errors
3. Verify IPC pipe setup

**Fix:**
- Check Python sidecar logs
- Verify JSON message format
- Check request ID matching

### Issue: "Sync completes but no data"

**Check:**
1. Supabase configured? (check `backend/supabase_database.py`)
2. Network connectivity
3. Database tables exist?

**Fix:**
- Verify Supabase credentials
- Check network connection
- Verify database initialization

## Success Indicators

✅ **Sidecar spawns:** No "Failed to spawn" error  
✅ **IPC works:** Sync command executes  
✅ **Database operations:** SQL queries succeed  
✅ **Sync completes:** Shows "Pulled: X, Pushed: Y"  
✅ **No crashes:** App remains stable  

## Next: Database Testing

Once IPC works, test:
- Direct database queries via Tauri commands
- Data persistence
- Migration system

---

**Status:** Ready for testing

