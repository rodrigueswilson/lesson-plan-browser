# Tablet Tab Implementation Plan

**Date:** January 2026  
**Status:** **Implemented.** See [../IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md) (Tablet Tab, TabletSync).  
**Goal:** Add a "Tablet" tab to the PC app that allows each user to update their own database for tablet deployment.

---

## Overview

Currently, the sync scripts (`sync-database-to-tablet.ps1` and `sync_browser_plans_to_tablet_db.py`) update all users' data in the tablet database. The new "Tablet" tab will provide a user-scoped interface where each user can sync only their own data to the tablet database.

**Terminology note:** in this project there is no real authentication yet; “current user” means the **currently selected user** in `UserSelector` (from `useStore().currentUser`).

---

## Current Architecture

### Existing Scripts

1. **`sync-database-to-tablet.ps1`**
   - Orchestrates the sync process
   - Calls `scripts/sync_browser_plans_to_tablet_db.py` with `--include-existing` flag
   - Updates `data/lesson_planner.db` for all users (or specific users if `--user` is provided)

2. **`scripts/sync_browser_plans_to_tablet_db.py`**
   - Python script that syncs plans from backend API to SQLite database
   - Supports `--user` parameter to restrict syncing to specific user IDs or names
   - Default behavior: syncs all users in the local database
   - Creates backups before syncing
   - Fetches plans, lesson JSON, and lesson steps from the API

3. **`build-apk.ps1`**
   - Builds Android APK with the updated database bundled
   - Requires `data/lesson_planner.db` to exist

4. **`install-apk.ps1`**
   - Installs the APK on connected Android device
   - Optional `-PushDb` flag to push database directly

### Current User Management

- Current user is available via `useStore()` hook: `const { currentUser } = useStore()`
- User ID is stored in `currentUser.id`
- User name is stored in `currentUser.name` or `currentUser.first_name` + `currentUser.last_name`

### Unified Frontend (Important for file targeting)

- The PC app entry `frontend/src/App.tsx` is a re-export of the unified app: it points to `lesson-plan-browser/frontend/src/App.tsx`.
- Most PC-only components (Slot Configurator, Batch Processor, etc.) are lazily imported by the unified app from `frontend/src/components/*`.

---

## Implementation Plan

### Phase 1: Add Navigation Item

**File:** `frontend/src/components/desktop/DesktopNav.tsx`

1. Add "tablet" to the `NavItem` type:
   ```typescript
   type NavItem = 'home' | 'plans' | 'schedule' | 'browser' | 'lesson-mode' | 'history' | 'analytics' | 'settings' | 'database' | 'tablet';
   ```

2. Add tablet navigation item to `allNavItems` array:
   ```typescript
   { id: 'tablet' as NavItem, label: 'Tablet', icon: Tablet }, // Need to import Tablet from lucide-react
   ```

**File:** `frontend/src/components/layouts/DesktopLayout.tsx`

1. Update `NavItem` type to include 'tablet'

**File:** `lesson-plan-browser/frontend/src/App.tsx` (this is the real unified App used by PC)

1. Add 'tablet' case to the switch statement in `renderContent()`
2. Render the `TabletSync` component (to be created)
3. Update the `NavItem` union type inside this file to include `'tablet'`
4. Add a lazy import for the PC-only component similar to other PC-only imports:
   - `const TabletSync = lazy(() => import('../../../frontend/src/components/TabletSync').then(m => ({ default: m.TabletSync })));`

---

### Phase 2: Create TabletSync Component

**File:** `frontend/src/components/TabletSync.tsx` (new file)

#### Component Structure

```typescript
interface TabletSyncProps {
  // Component will use useStore() to get currentUser
}

export function TabletSync() {
  const { currentUser } = useStore();
  // State management for sync process
  // UI for sync controls and status
}
```

#### Features

1. **User Information Display**
   - Show current user name and ID
   - Warning if no user is selected
   - Display last sync time (if available)

2. **Sync Controls**
   - "Sync My Database" button (disabled if no user selected)
   - Options:
     - `--include-existing` flag (checkbox: "Update existing plans")
     - `--plan-limit` (input field, default: 20)
     - `--timeout` (input field, default: 120 seconds)
   - Progress indicator during sync
   - Status messages (success/error)

3. **Database Status**
   - Show **exported user-only tablet DB** file path (see “User-only tablet DB export” below)
   - Show database size and last modified time
   - Link to view database location

4. **Build & Install Options** (Optional, can be Phase 3)
   - "Build APK" button (calls build-apk.ps1)
   - "Install APK" button (calls install-apk.ps1)
   - ADB device connection status

#### Implementation Details

**Backend Integration Options:**

**Option A: Backend API Endpoint (Recommended)**
- Add a FastAPI endpoint such as `POST /api/tablet/sync` that runs the same sync logic **inside the already-running Python backend**.
- This avoids bundling Python/scripts into the Tauri app and avoids adding another Rust↔Python execution path.
- The endpoint can accept `user_id`, `include_existing`, `plan_limit`, `timeout`, and `db_path` (optional).
- Progress can be returned as:
  - A simple JSON response (first version), or
  - An existing SSE/progress-task pattern if you want streaming UI updates.

**Option B: Tauri → existing Python sidecar IPC**
- The desktop app already has a Rust “sidecar bridge” pattern (`trigger_sync`) for talking to a Python process.
- We can add a new IPC command (e.g. `"tablet_db_sync"`) and implement it in the Python sidecar to run the tablet DB sync without spawning a separate Python process.
- This is still “Tauri-driven”, but reuses the existing sidecar architecture instead of introducing a second one.

**Option C: Spawn the script from Tauri (Not recommended)**
- Spawning `python scripts/sync_browser_plans_to_tablet_db.py ...` from Tauri is workable in dev, but complicates production packaging (you must ship Python + scripts and manage PATH).

**Recommended: Option A (Backend endpoint)** for KISS/SSOT; **Option B (sidecar IPC)** if you prefer to keep it entirely in the Tauri process model.

---

### Phase 3: Backend integration (choose one)

#### 3A. Backend endpoint approach (recommended)

**File:** `backend/api.py` (or wherever API routes live today)

- Add `POST /api/tablet/sync`
- It should run the existing sync logic with an explicit user filter (equivalent to passing `--user <current_user_id>` to the script).

#### 3B. Sidecar IPC approach

**Files:** `frontend/src-tauri/src/main.rs` + Python sidecar module (see `backend/sidecar_main.py`)

- Add an IPC command to the Rust↔Python bridge (similar to how `"full_sync"` is requested).
- Implement `"tablet_db_sync"` in the Python sidecar:
  - Invoke the sync logic for exactly one user
  - Return a summary payload to the UI

If you go with 3B, you may expose a new Tauri command like:

```rust
#[tauri::command]
async fn sync_tablet_db(
    user_id: String,
    include_existing: bool,
    plan_limit: i32,
    timeout: f64,
    app_handle: tauri::AppHandle,
) -> Result<SyncResult, String> {
    // 1. Validate user_id
    // 2. Build Python command with arguments
    // 3. Spawn Python process
    // 4. Stream output and emit progress events
    // 5. Return result
}
```

**Progress Events (optional, both approaches):**
- First version can return a simple “done + summary” response.
- If you want streaming progress, prefer reusing the existing progress/SSE patterns already used elsewhere in the app.

**Error Handling:**
- Handle Python script not found
- Handle database file not found
- Handle API connection errors
- Return user-friendly error messages

---

### Phase 4: Frontend Integration

**File:** `frontend/src/components/TabletSync.tsx`

1. **State Management:**
   ```typescript
   const [isSyncing, setIsSyncing] = useState(false);
   const [syncProgress, setSyncProgress] = useState<string>('');
   const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
   const [error, setError] = useState<string | null>(null);
   const [includeExisting, setIncludeExisting] = useState(true);
   const [planLimit, setPlanLimit] = useState(20);
   const [timeout, setTimeout] = useState(120);
   ```

2. **Sync Function:**
   ```typescript
   const handleSync = async () => {
     if (!currentUser) return;
     
     setIsSyncing(true);
     setError(null);
     setSyncProgress('Starting sync...');
     
     try {
       const result = await invoke('sync_tablet_db', {
         userId: currentUser.id,
         includeExisting,
         planLimit,
         timeout,
       });
       
       setSyncResult(result);
       setSyncProgress('Sync complete!');
     } catch (err) {
       setError(err.message);
     } finally {
       setIsSyncing(false);
     }
   };
   ```

3. **Progress Listener:**
   ```typescript
   useEffect(() => {
     const unlisten = listen('sync-progress', (event) => {
       setSyncProgress(event.payload.message);
     });
     
     return () => {
       unlisten.then(fn => fn());
     };
   }, []);
   ```

4. **UI Components:**
   - User info card
   - Sync options form
   - Progress indicator
   - Results display
   - Error display

---

### Phase 5: Python Script Integration

**File:** `scripts/sync_browser_plans_to_tablet_db.py`

**No changes needed** - the script already supports:
- `--user` parameter for user filtering
- `--include-existing` flag
- `--plan-limit` parameter
- `--timeout` parameter
- Progress output to stdout

**Considerations:**
- Script outputs progress to stdout/stderr
- Tauri command should capture and forward these messages
- Consider adding JSON output mode for structured progress (optional enhancement)

---

## User Experience Flow

1. **User opens Tablet tab**
   - Sees current user information
   - Sees database status
   - Sees sync options

2. **User clicks "Sync My Database"**
   - Button becomes disabled
   - Progress indicator appears
   - Real-time progress messages displayed
   - Database backup is created automatically

3. **Sync completes**
   - Success message with summary (plans synced, steps added)
   - Database status updated
   - Option to build APK appears

4. **User can build APK** (optional)
   - Calls `build-apk.ps1` script
   - Shows build progress
   - Displays APK location when complete

5. **User can install APK** (optional)
   - Checks for connected device
   - Calls `install-apk.ps1` script
   - Shows installation status

---

## Security Considerations

1. **User Authorization:**
   - Only sync data for the currently selected user
   - Backend API authorization header (`X-Current-User-Id`) exists, but because selection is not real auth, the main protection is: the UI only offers “sync selected user”.

2. **Database Access:**
   - Ensure database file permissions are correct
   - Backup is created before any modifications
   - User cannot accidentally sync other users' data

3. **Script Execution:**
   - Validate Python script path
   - Sanitize user input (plan_limit, timeout)
   - Prevent command injection

---

## Error Handling

### Common Errors

1. **No user selected:**
   - Disable sync button
   - Show message: "Please select a user first"

2. **Database not found:**
   - Show error: "Database file not found. Please run the desktop app once to create it."
   - Provide link to create database

3. **Backend API not accessible:**
   - Show error: "Cannot connect to backend API. Ensure the backend is running."
   - Show API URL and connection test button

4. **Python script not found:**
   - Show error: "Sync script not found. Please check installation."
   - Show expected path

5. **Sync failed:**
   - Show error message from Python script
   - Provide option to retry
   - Show backup location if backup was created

---

## Testing Plan

### Unit Tests

1. **TabletSync Component:**
   - Renders correctly with user selected
   - Disables sync when no user selected
   - Handles sync errors gracefully
   - Updates progress correctly

2. **Tauri Command:**
   - Validates user_id
   - Executes Python script correctly
   - Returns proper error messages
   - Emits progress events

### Integration Tests

1. **End-to-end sync:**
   - Select user
   - Click sync
   - Verify database is updated
   - Verify only current user's data is synced

2. **Error scenarios:**
   - Backend not running
   - Database locked
   - Invalid user_id
   - Python script failure

### Manual Testing

1. **Happy path:**
   - Select user → Sync → Verify database → Build APK → Install APK

2. **Edge cases:**
   - Sync with no plans
   - Sync with existing plans (include-existing on/off)
   - Sync with large number of plans
   - Multiple users, verify isolation

---

## Future Enhancements (Out of Scope)

1. **Batch sync for multiple users** (admin feature)
2. **Scheduled automatic syncs**
3. **Sync history and logs**
4. **Database comparison tools**
5. **Selective week syncing** (UI for `--week` parameter)
6. **Direct ADB push from UI** (without building APK)

---

## File Structure

```
frontend/
  src/
    components/
      TabletSync.tsx          # New: Main tablet sync component
    ...
  src-tauri/
    src/
      commands.rs             # New: Tauri command for sync
      main.rs                 # Update: Register command
    ...

scripts/
  sync_browser_plans_to_tablet_db.py  # No changes (already supports --user)

docs/
  planning/
    TABLET_TAB_PLAN.md        # This file
```

---

## Implementation Order

1. ✅ **Phase 1:** Add navigation item and route
2. ✅ **Phase 2:** Create basic TabletSync component (UI only, no sync yet)
3. ✅ **Phase 3:** Implement Tauri command for sync
4. ✅ **Phase 4:** Connect frontend to Tauri command
5. ✅ **Phase 5:** Test and refine
6. ⏸️ **Phase 6:** Optional - Add build/install UI

---

## Dependencies

- **Frontend:**
  - `@tauri-apps/api` - For Tauri commands and events
  - `lucide-react` - For Tablet icon
  - Existing `useStore` hook

- **Backend (Tauri):**
  - `tauri` crate - For command registration
  - `std::process::Command` - For executing Python script
  - `serde` - For serialization

- **Python:**
  - No new dependencies (uses existing script)

---

## Questions to Resolve

1. **Should we add build/install UI in Phase 1, or keep it separate?**
   - Recommendation: Keep separate (Phase 6), focus on sync first

2. **Should sync be automatic on tab open, or manual only?**
   - Recommendation: Manual only (user clicks button)

3. **Should we show other users' data in the database, or hide it?**
   - Recommendation: Show only current user's sync status, but allow viewing database info

4. **Should we support syncing multiple users from the UI?**
   - Recommendation: No, keep it single-user focused. Admin can use scripts directly.

---

## Success Criteria

✅ User can navigate to "Tablet" tab  
✅ User sees their own user information  
✅ User can sync only their own database  
✅ Sync progress is visible in real-time  
✅ Sync results are displayed clearly  
✅ Errors are handled gracefully  
✅ Database is backed up before sync  
✅ Only current user's data is synced (verified)  

---

## Notes

- The existing sync scripts already support user filtering via `--user` parameter
- The main change is providing a UI that automatically filters to the current user
- We will implement **Option B**: **produce a user-only tablet DB file** (privacy + smaller APK DB).

---

## User-only tablet DB export (Option B) — Detailed Design

### Goal

Create a **separate SQLite database file per user** that contains **only that user’s data**, while keeping schema compatible with the tablet app.

This explicitly avoids trying to “make the master DB single-user”. The master DB can keep multiple users; the export step produces a clean single-user artifact.

### Tablet DB schema scope (what tables exist)

The tablet app schema (as reflected by the Tauri migrations) is essentially:

- `users`
- `class_slots`
- `weekly_plans`
- `schedules`
- `lesson_steps`
- `lesson_mode_sessions`

Important: the backend/master DB may contain additional tables (e.g., metrics). The export should **not** include them.

### Single Source of Truth for schema (avoid drift)

To avoid duplicating schema definitions, the export process should **clone schema from the existing master SQLite DB** using `sqlite_master` introspection, but only for the tablet tables listed above.

That gives us:
- Exact column set and order (safe `INSERT INTO ... SELECT * ...`)
- Indexes and triggers (if any) copied consistently
- Automatic compatibility with any future schema tweaks, without needing to update export code constantly

### Export location and naming

Produce exactly **one export DB per user** at a stable path:

- `data/tablet_db_exports/<user_id>/lesson_planner.db`

Rules:
- Always write to a temporary file first, then rename (atomic replace) to prevent partial/corrupt outputs.
- Optionally keep a timestamped backup of the previous export in the same folder.

### Export algorithm (table-by-table filters)

Given:
- `source_db`: the existing multi-user SQLite DB (master)
- `target_user_id`: the selected user
- `dest_db`: the exported user-only DB path

Steps:

1. **Validate user exists**
   - `SELECT 1 FROM users WHERE id = ?`

2. **Create destination DB (temp file)**
   - `dest_tmp = dest_db + ".tmp"`
   - Ensure parent folder exists
   - If `dest_tmp` exists, delete it first

3. **Clone schema for tablet tables only**
   - Connect to `dest_tmp`
   - `ATTACH DATABASE <source_db> AS src`
   - For each `table` in `{users, class_slots, weekly_plans, schedules, lesson_steps, lesson_mode_sessions}`:
     - `SELECT sql FROM src.sqlite_master WHERE type='table' AND name=?`
     - Execute returned SQL in `main`
   - For each table, also copy indexes:
     - `SELECT sql FROM src.sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL`
     - Execute in `main`
   - Optionally copy triggers similarly (`type='trigger'`)

4. **Copy filtered data in dependency order**
   - Users first:
     - `INSERT INTO users SELECT * FROM src.users WHERE id = :uid`
   - Then user-scoped tables:
     - `INSERT INTO class_slots SELECT * FROM src.class_slots WHERE user_id = :uid`
     - `INSERT INTO weekly_plans SELECT * FROM src.weekly_plans WHERE user_id = :uid`
     - `INSERT INTO schedules SELECT * FROM src.schedules WHERE user_id = :uid`
   - Then plan-scoped tables (filter by the user’s plans copied into `main.weekly_plans`):
     - `INSERT INTO lesson_steps
        SELECT * FROM src.lesson_steps
        WHERE lesson_plan_id IN (SELECT id FROM main.weekly_plans)`
   - Then sessions (both user-scoped and plan-scoped):
     - `INSERT INTO lesson_mode_sessions
        SELECT * FROM src.lesson_mode_sessions
        WHERE user_id = :uid
          AND lesson_plan_id IN (SELECT id FROM main.weekly_plans)`
     - This ensures no session references other users’ plans.

5. **Integrity checks**
   - `PRAGMA foreign_key_check;` should return no rows
   - Basic counts (returned to UI):
     - users: 1
     - weekly_plans: N
     - lesson_steps: M
     - schedules: K

6. **Compact and finalize**
   - `VACUUM;` (optional but recommended; makes the export smaller)
   - `DETACH DATABASE src`
   - Close connection

7. **Atomic replace**
   - Rename `dest_tmp` → `dest_db` (overwrite existing)

### Security / privacy properties

- Exported DB contains **exactly one row** in `users`
- No other user IDs appear in `class_slots`, `weekly_plans`, `schedules`, `lesson_mode_sessions`
- `lesson_steps` contains only rows tied to this user’s plans

### How the Tablet tab uses this

The Tablet tab should display:
- The **export DB path** for the selected user
- Buttons:
  - **Sync (user) → update master DB rows for this user**
  - **Export (user) → produce user-only tablet DB file**
  - (Optional later) **Build APK** using this exported DB path

