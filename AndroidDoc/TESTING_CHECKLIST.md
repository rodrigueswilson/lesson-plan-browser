# Testing Checklist: Current State Verification

**Purpose:** Verify current implementation before proceeding with next steps  
**Date:** Pre-implementation testing phase

---

## Pre-Testing Setup

### 1. Verify Current Tauri Version

**Check:**
```bash
cd d:\LP\frontend\src-tauri
cargo tree | grep tauri
```

**Expected:**
- `tauri = "2.0"`
- `tauri-plugin-shell = "2.0"`
- `tauri-plugin-fs = "2.0"`
- `tauri-plugin-http = "2.0"`
- `tauri-plugin-dialog = "2.0"`

**Action if different:** Note the actual versions

---

## Desktop Testing

### 2. Desktop App Launch

**Test:**
```bash
cd d:\LP\frontend
cargo tauri dev
```

**Check:**
- [ ] App launches without errors
- [ ] UI renders correctly
- [ ] No console errors in terminal
- [ ] No console errors in browser dev tools (if accessible)

**Expected Issues:**
- If Python sidecar spawn fails, that's expected (we'll test that separately)

**Document:** Any errors or warnings

---

### 3. Desktop IPC - Python Sidecar (Source Mode)

**Prerequisites:**
- Python installed and accessible
- `backend` module importable from project root

**Test:**
1. Launch app: `cargo tauri dev`
2. Navigate to sync functionality (or trigger sync)
3. Check terminal output for:
   - Python sidecar spawn messages
   - IPC communication logs
   - Any errors

**Check:**
- [ ] Python sidecar spawns successfully
- [ ] IPC messages flow (check terminal)
- [ ] No "Failed to spawn" errors
- [ ] Database operations work (if tested)

**Expected Behavior:**
- Sidecar should spawn using `python -m backend.sidecar_main`
- IPC should work via stdin/stdout

**Document:** 
- Does sidecar spawn? (Yes/No)
- Any errors? (List them)
- IPC working? (Yes/No)

---

### 4. Desktop Database Operations

**Test:**
1. Launch app
2. Try to:
   - List users
   - List slots
   - Create a plan (if UI allows)
   - Query database

**Check:**
- [ ] Database file created (check location)
- [ ] Tables exist (users, class_slots, weekly_plans, schedule_entries)
- [ ] Queries return data (or empty results, not errors)
- [ ] Inserts/updates work

**Database Location:**
- Windows: `%APPDATA%\lesson_planner.db` or similar
- Check `lib.rs` line 185-188 for exact path

**Document:**
- Database file location: _______________
- Tables created: (Yes/No)
- Operations working: (Yes/No)

---

### 5. Desktop - FastAPI Backend (If Still Using)

**Test:**
1. Start FastAPI backend:
   ```bash
   cd d:\LP\backend
   python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000
   ```

2. In app, try API calls:
   - Health check
   - List users
   - Other API operations

**Check:**
- [ ] Backend starts without errors
- [ ] App can connect to backend
- [ ] API calls succeed
- [ ] No CORS errors

**Document:**
- Backend accessible: (Yes/No)
- API calls working: (Yes/No)

---

## Android Emulator Testing

### 6. Android Build Process

**Test:**
1. Build frontend:
   ```powershell
   cd d:\LP\frontend
   npm run build:skip-check
   ```

2. Copy assets:
   ```powershell
   Remove-Item "frontend\src-tauri\gen\android\app\src\main\assets" -Recurse -Force -ErrorAction SilentlyContinue
   New-Item -ItemType Directory -Path "frontend\src-tauri\gen\android\app\src\main\assets" -Force
   Copy-Item "frontend\dist\*" "frontend\src-tauri\gen\android\app\src\main\assets\" -Recurse -Force
   ```

3. Build APK:
   ```powershell
   cd d:\LP\frontend\src-tauri\gen\android
   .\gradlew.bat assembleX86_64Debug -x rustBuildX86_64Debug
   ```

**Check:**
- [ ] Frontend builds without errors
- [ ] Assets copy successfully
- [ ] APK builds without errors
- [ ] APK file exists: `app\build\outputs\apk\x86_64\debug\app-x86_64-debug.apk`

**Document:**
- Build successful: (Yes/No)
- APK location: _______________
- Any build errors: _______________

---

### 7. Android App Installation

**Prerequisites:**
- Emulator running
- ADB connected: `adb devices`

**Test:**
1. Uninstall old app (if exists):
   ```powershell
   adb -s emulator-5554 uninstall com.lessonplanner.bilingual
   ```

2. Install new APK:
   ```powershell
   adb -s emulator-5554 install -r "app\build\outputs\apk\x86_64\debug\app-x86_64-debug.apk"
   ```

3. Launch app:
   ```powershell
   adb -s emulator-5554 shell am start -n com.lessonplanner.bilingual/.MainActivity
   ```

**Check:**
- [ ] Uninstall succeeds (or "not installed" is OK)
- [ ] Install succeeds
- [ ] App launches
- [ ] No immediate crash

**Document:**
- Installation successful: (Yes/No)
- App launches: (Yes/No)
- Any errors: _______________

---

### 8. Android App Functionality

**Test:**
1. Open app on emulator
2. Check UI renders
3. Try basic navigation
4. Check logs: `adb logcat | grep -E "(bilingual|python|sidecar|rust)"`

**Check:**
- [ ] UI renders correctly
- [ ] No blank screen
- [ ] Navigation works
- [ ] No crash logs

**Expected:**
- "Android Python sidecar not yet implemented" error is expected
- App should still work via FastAPI backend (if configured)

**Document:**
- UI working: (Yes/No)
- Any errors in logs: _______________

---

### 9. Android - FastAPI Backend Connection

**Prerequisites:**
- FastAPI backend running on PC
- Emulator and PC on same network (or using 10.0.2.2)

**Test:**
1. Check `api.ts` has correct URL:
   - Emulator: `http://10.0.2.2:8000/api`
   - Real device: `http://<PC_IP>:8000/api`

2. In app, try API calls:
   - Health check
   - List users
   - Other operations

**Check:**
- [ ] API URL correct in code
- [ ] Backend accessible from emulator
- [ ] API calls succeed
- [ ] Data loads in UI

**Document:**
- Backend connection: (Yes/No)
- API calls working: (Yes/No)
- Current API URL: _______________

---

### 10. Android - Sidecar Error Verification

**Test:**
1. Try to trigger sync (or any sidecar operation)
2. Check logs: `adb logcat | grep -i "sidecar\|python\|android"`
3. Check for expected error message

**Expected:**
- Error: "Android Python sidecar not yet implemented"
- This is correct - confirms stub is working

**Check:**
- [ ] Error message appears (expected)
- [ ] Error is handled gracefully (app doesn't crash)
- [ ] Error message matches expected text

**Document:**
- Error appears: (Yes/No)
- Error text: _______________
- App handles error gracefully: (Yes/No)

---

## Code Verification

### 11. Rust Bridge Implementation

**Check Files:**
- `frontend/src-tauri/src/bridge.rs`
- `frontend/src-tauri/src/lib.rs`
- `frontend/src-tauri/src/db_commands.rs`

**Verify:**
- [ ] `bridge.rs` has Android stubs (lines 137-145, 157-160, 173-176)
- [ ] Desktop implementation exists (lines 112-135, 147-155, 162-171)
- [ ] `lib.rs` has `trigger_sync()` command
- [ ] `db_commands.rs` has SQL functions

**Document:**
- Bridge structure: (OK/Issues)
- Any missing implementations: _______________

---

### 12. Python Sidecar Implementation

**Check Files:**
- `backend/sidecar_main.py`
- `backend/ipc_database.py`

**Verify:**
- [ ] `sidecar_main.py` exists and is complete
- [ ] `ipc_database.py` exists and is complete
- [ ] Both files have proper error handling
- [ ] Sync functions implemented

**Test (Optional):**
```bash
cd d:\LP
python -m backend.sidecar_main
# Should start and wait for stdin input
# Press Ctrl+C to exit
```

**Document:**
- Sidecar files exist: (Yes/No)
- Can import modules: (Yes/No)
- Any import errors: _______________

---

### 13. Configuration Files

**Check:**
- `frontend/src-tauri/Cargo.toml`
- `frontend/src-tauri/tauri.conf.json`
- `frontend/src/lib/api.ts`

**Verify:**
- [ ] Tauri version is 2.0
- [ ] Plugins configured correctly
- [ ] `tauri.conf.json` is valid JSON
- [ ] `api.ts` has Android URL detection

**Document:**
- Config files valid: (Yes/No)
- Any issues: _______________

---

## Summary Checklist

### Desktop
- [ ] App launches
- [ ] IPC works (or fails gracefully)
- [ ] Database operations work
- [ ] FastAPI backend works (if using)

### Android
- [ ] Build succeeds
- [ ] Installation works
- [ ] App launches
- [ ] UI renders
- [ ] FastAPI backend connection works
- [ ] Sidecar error appears (expected)

### Code
- [ ] Bridge structure correct
- [ ] Sidecar files exist
- [ ] Configuration valid

---

## Test Results Summary

**Date:** _______________

**Tauri Version:** _______________

**Desktop Status:**
- App Launch: (✅/❌)
- IPC: (✅/❌/N/A)
- Database: (✅/❌/N/A)
- Backend: (✅/❌/N/A)

**Android Status:**
- Build: (✅/❌)
- Installation: (✅/❌)
- App Launch: (✅/❌)
- UI: (✅/❌)
- Backend Connection: (✅/❌)
- Sidecar Error: (✅ Expected/❌)

**Issues Found:**
1. _______________
2. _______________
3. _______________

**Ready to Proceed:**
- [ ] All critical tests pass
- [ ] Known issues documented
- [ ] Ready for next implementation phase

---

## Next Steps After Testing

1. **If all tests pass:**
   - Update documentation to reflect v2.0
   - Proceed with Phase 5 (Python bundling)

2. **If issues found:**
   - Document all issues
   - Prioritize fixes
   - Resolve blocking issues before proceeding

3. **If version conflicts:**
   - Decide on Tauri version
   - Update code if needed
   - Re-test

---

**Last Updated:** Testing phase  
**Status:** Pre-implementation verification

