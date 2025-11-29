# IPC Testing Guide - Desktop

**Purpose:** Test IPC communication between Rust and Python sidecar on desktop

## Prerequisites

- ✅ Desktop app working
- ✅ Backend running on `http://localhost:8000`
- ✅ Python installed and accessible
- ✅ `backend` module importable

## Test 1: Verify Python Sidecar Can Be Spawned

### Manual Test

1. **Open app console** (F12)
2. **Find Sync button** in UI (or use SyncTestButton component)
3. **Trigger sync** (click button or call from console)
4. **Check terminal** where `tauri:dev` is running for:
   - Python process spawn messages
   - IPC communication logs
   - Any errors

### Expected Behavior

**Success:**
- Sidecar spawns without errors
- IPC messages flow (check terminal)
- Sync completes or shows progress

**Failure Indicators:**
- "Failed to spawn Python sidecar" error
- "Python not found" error
- "Module not found" error
- No IPC traffic in terminal

### Console Test (Alternative)

If there's no UI button, test from browser console:

```javascript
// Get current user ID first
const store = window.__ZUSTAND_STORE__; // or however store is accessed
const userId = store.getState().currentUser?.id;

// Then trigger sync
const { invoke } = await import('@tauri-apps/api/core');
const result = await invoke('trigger_sync', { userId: userId || 'test-user-id' });
console.log('Sync result:', result);
```

## Test 2: Verify IPC Message Flow

### What to Check

1. **Rust → Python:**
   - Command message sent
   - JSON format correct
   - Request ID present

2. **Python → Rust:**
   - SQL query/execute messages
   - Response messages
   - Error handling

3. **Rust → Python:**
   - SQL responses
   - Error responses

### Terminal Output to Look For

**Rust side (Tauri terminal):**
- "Spawn failed" or "Spawn successful"
- IPC send/receive logs (if logging enabled)

**Python side (stderr):**
- "Sidecar started"
- Command received logs
- SQL query logs
- Sync progress logs

## Test 3: Database Operations via IPC

### Test Queries

The sidecar should make SQL queries through IPC:

1. **Query users:**
   ```sql
   SELECT * FROM users WHERE id = ?
   ```

2. **Query slots:**
   ```sql
   SELECT * FROM class_slots WHERE user_id = ?
   ```

3. **Insert/Update plans:**
   ```sql
   INSERT INTO weekly_plans ...
   ```

### What to Verify

- ✅ SQL queries execute successfully
- ✅ Data returned correctly
- ✅ JSON serialization works
- ✅ Error handling works

## Test 4: Sync Functionality

### Full Sync Test

1. **Trigger full sync** from UI
2. **Check:**
   - Users pulled from Supabase
   - Slots pulled from Supabase
   - Plans pushed to Supabase
   - Local SQLite updated

### Expected Flow

1. Frontend calls `trigger_sync(userId)`
2. Rust spawns Python sidecar (if not running)
3. Rust sends `full_sync` command to Python
4. Python pulls from Supabase → makes SQL queries to Rust
5. Rust executes SQL → returns results to Python
6. Python pushes to Supabase → makes SQL updates to Rust
7. Python sends final response to Rust
8. Rust returns result to frontend

## Troubleshooting

### Issue: "Failed to spawn Python sidecar"

**Possible Causes:**
- Python not in PATH
- `backend` module not importable
- Project root detection failed

**Solutions:**
1. Verify Python: `python --version`
2. Test import: `python -c "from backend import sidecar_main"`
3. Check project root detection in `lib.rs` lines 110-132

### Issue: "No response from Rust bridge"

**Possible Causes:**
- IPC pipe broken
- Sidecar crashed
- Message format incorrect

**Solutions:**
1. Check Python stderr for errors
2. Verify JSON message format
3. Check request ID matching

### Issue: "SQL query failed"

**Possible Causes:**
- Database not initialized
- Table doesn't exist
- SQL syntax error

**Solutions:**
1. Check database file exists
2. Verify migrations ran
3. Check SQL syntax in sidecar

## Success Criteria

- [ ] Python sidecar spawns successfully
- [ ] IPC messages flow (Rust ↔ Python)
- [ ] SQL queries execute via IPC
- [ ] Sync completes without errors
- [ ] Data persists in local SQLite
- [ ] Supabase sync works (if configured)

---

**Status:** Testing guide ready

