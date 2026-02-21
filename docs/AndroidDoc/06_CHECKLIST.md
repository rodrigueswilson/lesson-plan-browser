# Implementation Checklist

## Phase 0: Version Validation & Minimal IPC Test

- [x] **Decision:** Using Tauri v2.0 (tested and working on desktop)
- [ ] Create minimal Python echo script for IPC testing
- [ ] Create minimal Rust bridge test
- [ ] Verify bidirectional JSON IPC works on desktop
- [ ] Test process lifecycle (spawn, send, receive, shutdown)

## Phase 1: Environment Setup

- [ ] Install Rust Android targets
  ```bash
  rustup target add aarch64-linux-android
  ```
- [ ] **Note:** Tauri CLI v2.0 - Android support available
- [ ] Install Android SDK + NDK v26+
- [ ] Set environment variables (`ANDROID_HOME`, `ANDROID_NDK_HOME`)
- [ ] Initialize Tauri Android project (if supported in v1.5)
  ```bash
  cargo tauri android init
  ```
- [ ] Create `.cargo/config.toml` with NDK linker paths

## Phase 2: Rust Implementation

- [x] Update `Cargo.toml` with new dependencies
  - [x] Use `tauri = "2.0"` with plugins (`tauri-plugin-dialog`, `tauri-plugin-fs`, `tauri-plugin-http`, `tauri-plugin-shell`)
  - [x] Add `rusqlite = { version = "0.30", features = ["bundled", "serde_json"] }`
  - [x] Add `tokio`, `uuid`, `chrono`, `thiserror`, `log`
  - [x] Keep existing `serde`, `serde_json`
- [ ] Create `src/bridge.rs`
  - [ ] `PythonMessage` enum (SqlQuery, SqlExecute, Response)
  - [ ] `RustMessage` struct
  - [ ] `SidecarBridge` struct with spawn/send/receive
- [ ] Create `src/db_commands.rs`
  - [ ] Database initialization with `rusqlite`
  - [ ] Migration system (run SQL files)
  - [ ] `sql_query` command (SELECT operations)
  - [ ] `sql_execute` command (INSERT/UPDATE/DELETE)
  - [ ] JSON serialization helpers
  - [ ] Error handling
- [ ] Create migration SQL files
  - [ ] `migrations/001_users.sql`
  - [ ] `migrations/002_class_slots.sql`
  - [ ] `migrations/003_weekly_plans.sql`
  - [ ] `migrations/004_schedule_entries.sql`
- [ ] Update `src/main.rs`
  - [ ] Import bridge and db_commands modules
  - [ ] Initialize database on startup
  - [ ] Implement `trigger_sync` command
  - [ ] Register commands (no plugins needed for v1.5)
  - [ ] Initialize SidecarBridge as managed state
  - [ ] Test IPC with Python echo script

## Phase 3: Python Adaptation

- [ ] Create `backend/ipc_database.py`
  - [ ] `IPCDatabaseAdapter` class
  - [ ] `_ipc_call()` method for stdin/stdout with error handling
  - [ ] `execute()` and `query()` methods
  - [ ] `query_one()` helper method
  - [ ] Request ID tracking and validation
- [ ] Create `backend/sidecar_main.py`
  - [ ] `SyncSidecar` class
  - [ ] `handle_command()` router with error handling
  - [ ] `sync_from_supabase()` method (use `list_users()`, `get_user_slots()`)
  - [ ] `sync_to_supabase()` method (handle pending plans)
  - [ ] `full_sync()` method (bidirectional)
  - [ ] Main loop reading from stdin with error recovery
  - [ ] Logging to stderr (stdout reserved for IPC)
- [ ] Modify `backend/database.py`
  - [ ] Add `use_ipc: bool = False` parameter to `__init__`
  - [ ] **Start with critical methods only:**
    - [ ] `get_user()` - IPC adapter
    - [ ] `get_user_slots()` - IPC adapter
    - [ ] `create_weekly_plan()` - IPC adapter
    - [ ] `get_weekly_plan()` - IPC adapter
  - [ ] Expand to other methods as needed
  - [ ] Keep SQLAlchemy code for desktop/backend mode

## Phase 4: Configuration

- [ ] Update `tauri.conf.json` (keep v1.5 format)
  - [ ] Add shell scope for Python sidecar binary
  - [ ] Add HTTP scope for Supabase URLs
  - [ ] Keep existing allowlist structure
  - [ ] **Note:** No plugin configuration needed (using rusqlite directly)
- [ ] Update Android manifest permissions
  - [ ] `INTERNET`
  - [ ] `ACCESS_NETWORK_STATE`
  - [ ] `READ_EXTERNAL_STORAGE` / `WRITE_EXTERNAL_STORAGE`
- [ ] Create `network_security_config.xml`
- [ ] Update frontend API (`api.ts`)
  - [ ] Add `triggerSync()` function

## Phase 5: Python Bundling

- [x] Choose bundling method (Nuitka/PyInstaller/Docker) - PyInstaller for desktop, Nuitka for Android
- [x] Create standalone Python executable - Desktop binaries exist
- [x] Place binary in `src-tauri/binaries/` - Windows and Linux binaries present
- [x] Verify binary naming convention matches target triple - ✅ Correct naming
- [x] Update Rust code to use bundled binary - ✅ Code updated with fallback logic
- [x] Test bundled binary on desktop - ✅ Binary works, responds to IPC commands
- [ ] Build Android binary (aarch64-linux-android) - Pending (requires Docker/WSL/Linux)

## Phase 6: Build & Deploy

- [ ] Build desktop version (verify IPC works)
  ```bash
  cargo tauri dev
  ```
- [ ] Build Android APK
  ```bash
  cargo tauri android build --target aarch64
  ```
- [ ] Install on tablet
  ```bash
  adb install -r path/to/app.apk
  ```
- [ ] Run all test scenarios (see below)

## Testing Checklist

### Basic Functionality
- [ ] App launches without crash
- [ ] SQLite database created
- [ ] UI renders correctly
- [ ] Navigation works

### Local Database
- [ ] Can query users
- [ ] Can query class slots
- [ ] Can save weekly plan
- [ ] Data persists after app restart

### Sync Functionality
- [ ] Pull from Supabase works
- [ ] Push to Supabase works
- [ ] Conflict resolution works
- [ ] Sync status updates correctly

### Offline Mode
- [ ] App works with airplane mode
- [ ] Local changes queued for sync
- [ ] Reconnect triggers sync

### Performance
- [ ] App startup < 3 seconds
- [ ] Sync completes < 10 seconds
- [ ] UI remains responsive during sync

## Post-Deployment

- [ ] Create GitHub Actions workflow for CI/CD
- [ ] Set up crash reporting (optional)
- [ ] Document troubleshooting steps
- [ ] Create user guide for tablet usage

---

## Progress Tracking

| Phase | Status | Notes |
|-------|--------|-------|
| 0. Version Validation | [x] Complete | IPC tested on desktop |
| 1. Environment Setup | [x] Complete | Rust targets ready |
| 2. Rust Implementation | [x] Complete | Using rusqlite, Tauri v1.5 |
| 3. Python Adaptation | [x] Complete | Critical methods implemented |
| 4. Configuration | [x] Complete | Sidecar config added |
| 5. Python Bundling | [x] Desktop Complete | Windows binary built and tested |
| 6. Build & Deploy | [ ] Not Started | Ready after bundling |
| 7. Testing | [x] Desktop Complete | Android testing pending |

**Last Updated:** _____________

**Blockers:** 
- 

**Next Action:**
- 
