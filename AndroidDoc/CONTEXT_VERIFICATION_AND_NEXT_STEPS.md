# Context Verification and Next Steps

**Date:** Based on current codebase state  
**Purpose:** Verify user's architectural understanding and provide concrete next steps

## Context Verification

### ✅ CORRECT: Architecture Description

Your understanding of the sidecar architecture is **correct**:

```
React UI → Rust Bridge → Python Sidecar → Supabase
                ↓
           SQLite (local)
```

This matches exactly what's documented in `README.md` and implemented in the codebase.

### ✅ CORRECT: Current State Assessment

Your assessment of completion status is **accurate**:

- **Phases 0-4:** ✅ Complete (IPC, Rust, Python adapter, config)
- **Phase 5:** ❌ Not started (Python bundling)
- **Phase 6:** ❌ Not started (Android sidecar on device)
- **Current mode:** Emulator + PC backend (working)

### ⚠️ CLARIFICATIONS: Implementation Details

#### 1. Rust Bridge Android Support

**Current State:**
- Desktop implementation: ✅ Complete (spawns Python process)
- Android implementation: ❌ Stub only (returns error)

**Location:** `frontend/src-tauri/src/bridge.rs` lines 137-145, 157-160, 173-176

```rust
#[cfg(target_os = "android")]
pub fn spawn(&self, _python_exe: &str, _args: &[&str], _working_dir: Option<&std::path::Path>) -> Result<(), String> {
    Err("Android Python sidecar not yet implemented...".to_string())
}
```

**Implication:** The sidecar architecture is implemented but **not yet functional on Android**. The error message you see ("Android Python sidecar not yet implemented") is expected and correct.

#### 2. Python Sidecar Implementation

**Status:** ✅ **Fully implemented** but not bundled

- `backend/sidecar_main.py`: ✅ Complete (260 lines)
- `backend/ipc_database.py`: ✅ Complete (74 lines)
- Sync logic: ✅ Implemented (pull/push/full_sync)
- Supabase integration: ✅ Working

**Missing:** Binary bundling (Phase 5) and Android integration (Phase 6)

#### 3. FastAPI Backend Status

**Current State:** ✅ Still exists and is actively used

- Location: `backend/api.py` (3700+ lines)
- Purpose: Currently serves as the backend for tablet (via WiFi)
- Future: Will be replaced by sidecar once Phase 5-6 complete

**Your understanding is correct:** The PC FastAPI backend is the current working solution, and it will be replaced by the sidecar once bundling is complete.

#### 4. Database Adapter Status

**Current State:** ✅ Implemented with IPC support

- `backend/database.py` has `use_ipc` parameter
- `IPCDatabaseAdapter` is fully implemented
- **Note:** The sidecar uses `IPCDatabaseAdapter` directly (not through `SQLiteDatabase` with `use_ipc=True`)

This is actually **better** than the plan - the sidecar uses the adapter directly, which is cleaner.

## Next Steps (Refined Based on Codebase)

### Immediate: Short-Term Path (Tablet + PC Backend)

**Status:** ✅ Your steps are correct

1. **Point app to PC backend over WiFi**
   - File: `frontend/src/lib/api.ts` line 12
   - Change: `http://10.0.2.2:8000/api` → `http://<PC_LAN_IP>:8000/api`
   - Ensure FastAPI is running on `0.0.0.0:8000` (not just `localhost`)

2. **Build + install APK for tablet**
   - Follow exact sequence from `07_ANDROID_DEBUGGING_AND_FIXES.md` §2
   - Use `assembleArm64Debug` (or `assembleArm64Release`) for physical tablet
   - Note: Currently using x86_64 for emulator, need arm64 for real device

3. **Verify**
   - App launches
   - Calls hit PC backend (check PC logs)
   - Ignore "Android Python sidecar not yet implemented" (expected)

### Medium-Term: Sidecar on Device (Phase 5-6)

#### Step 2.1: Complete Phase 5 (Desktop First) ✅ Your plan is correct

**Goal:** Get standalone Python sidecar binary that Rust can spawn

**Actions:**
1. **Choose bundling method**
   - Options: Nuitka (recommended), PyInstaller, Docker cross-compile
   - See `05_BUILD_DEPLOY.md` §5.1 for details

2. **Build sidecar binary for desktop**
   ```bash
   # Example with PyInstaller (Windows/Desktop)
   cd backend
   pyinstaller --onefile \
       --name python-sync-processor \
       --hidden-import=backend.ipc_database \
       --hidden-import=backend.supabase_database \
       --hidden-import=backend.schema \
       sidecar_main.py
   ```

3. **Place binary in Tauri binaries folder**
   - Location: `frontend/src-tauri/binaries/`
   - Naming: `python-sync-processor` (desktop) or `python-sync-processor-{target-triple}` (Android)

4. **Update Rust bridge to use bundled binary**
   - Modify `bridge.rs` `spawn()` method
   - For desktop: Use bundled binary instead of `python -m backend.sidecar_main`
   - Test IPC on desktop first

5. **Verify desktop IPC works**
   - Run `cargo tauri dev`
   - Test `trigger_sync()` command
   - Verify SQL queries flow through IPC

#### Step 2.2: Wire Sidecar into Android Build ⚠️ Additional Details Needed

**Goal:** Package sidecar binary and spawn it on tablet

**Actions:**
1. **Build Android-compatible binary**
   - Use Nuitka with cross-compile OR Docker approach
   - Target: `aarch64-linux-android`
   - See `05_BUILD_DEPLOY.md` §5.1 Option A or C

2. **Place binary in Android assets**
   - Location: `frontend/src-tauri/gen/android/app/src/main/assets/` or
   - Use Tauri's sidecar configuration in `tauri.conf.json`

3. **Update Rust bridge for Android**
   - **Current:** Stub returns error
   - **Needed:** Implement using Tauri shell plugin API
   - Reference: `bridge.rs` lines 137-145
   - Use `tauri_plugin_shell::ShellExt` to spawn sidecar binary

4. **Update `tauri.conf.json`**
   - Add sidecar binary configuration
   - Ensure binary is included in APK

5. **Test IPC on tablet**
   - Build APK with bundled sidecar
   - Install on device
   - Use `adb logcat` to verify sidecar starts
   - Test minimal IPC flow

#### Step 2.3: Local SQLite + Plans on Tablet ✅ Your plan is correct

**Actions:**
1. **Verify rusqlite DB creation on device**
   - Check: `db_commands.rs` already handles Android path (line 182 in `lib.rs`)
   - Location: `/data/data/com.lessonplanner.bilingual/databases/lesson_planner.db`
   - Verify tables created via `adb shell run-as com.lessonplanner.bilingual`

2. **Route app workflows through sidecar+SQLite**
   - Current: App calls FastAPI backend
   - Needed: App calls Rust commands → Rust → Python sidecar → SQLite
   - **Note:** This requires updating frontend to use Tauri commands instead of HTTP API

3. **Test end-to-end scenario**
   - Create plan via sidecar
   - Verify persistence
   - Close/reopen app
   - Verify data persists

#### Step 2.4: Supabase Sync from Tablet ✅ Your plan is correct

**Actions:**
1. **Enable Supabase calls from sidecar**
   - Already implemented in `sidecar_main.py`
   - Verify network permissions in Android manifest
   - Test HTTPS connectivity

2. **Test sync scenarios**
   - Pull from Supabase
   - Push to Supabase
   - Offline mode (airplane mode)
   - Reconnect and sync

## Critical Implementation Notes

### 1. Frontend API Migration

**Current:** Frontend uses HTTP API (`api.ts`) to call FastAPI backend

**Future:** Frontend should use Tauri commands to call Rust → Python sidecar

**Migration Path:**
- Keep HTTP API for now (works with PC backend)
- Add Tauri command wrappers
- Switch to Tauri commands when sidecar is ready
- Eventually remove HTTP API calls

### 2. Android Bridge Implementation

The Android bridge stub needs to be implemented using Tauri's shell plugin:

```rust
#[cfg(target_os = "android")]
pub fn spawn(&self, app: &tauri::AppHandle, binary_name: &str) -> Result<(), String> {
    use tauri_plugin_shell::ShellExt;
    
    let sidecar = app.shell()
        .sidecar(binary_name)
        .map_err(|e| format!("Failed to create sidecar: {}", e))?;
    
    // Configure stdin/stdout pipes
    // Store sidecar handle for send/receive
    Ok(())
}
```

### 3. Binary Naming Convention

For Tauri sidecars:
- Desktop: `python-sync-processor` or `python-sync-processor.exe`
- Android: `python-sync-processor-aarch64-linux-android`

Configure in `tauri.conf.json`:
```json
{
  "tauri": {
    "bundle": {
      "resources": ["../binaries"]
    }
  }
}
```

## Summary

### ✅ What You Got Right

1. Architecture understanding (sidecar pattern)
2. Current state assessment (Phases 0-4 done, 5-6 pending)
3. Short-term path (tablet + PC backend)
4. Long-term path (sidecar on device)
5. Supabase as central backend (not replaced)

### ⚠️ What Needs Clarification

1. **Android bridge is stub only** - needs implementation using Tauri shell plugin
2. **Frontend still uses HTTP API** - will need migration to Tauri commands
3. **Binary bundling method** - choose Nuitka vs PyInstaller vs Docker
4. **Sidecar configuration** - needs `tauri.conf.json` updates

### 🎯 Recommended Next Steps Order

1. **Immediate:** Get tablet working with PC backend (your Step 1)
2. **Next:** Bundle Python sidecar for desktop and test IPC
3. **Then:** Implement Android bridge using Tauri shell plugin
4. **Finally:** Bundle for Android and test on device

## Questions to Resolve

1. **Bundling method preference?** (Nuitka recommended for Android cross-compile)
2. **Frontend migration strategy?** (Gradual vs big-bang switch to Tauri commands)
3. **Testing approach?** (Desktop first vs direct to Android)

---

**Last Updated:** Based on codebase review  
**Status:** Context verified with minor clarifications needed

