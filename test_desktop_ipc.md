# Desktop IPC Bridge Testing Guide

## Prerequisites

1. ✅ Rust code compiles successfully
2. ✅ Python modules are importable
3. ✅ Database migrations are ready
4. ✅ Tauri configuration is correct

## Testing Steps

### Step 1: Start the Tauri Development Server

```bash
cd frontend
npm run tauri:dev
```

This will:
- Start the Vite dev server
- Build the Rust backend
- Launch the Tauri application window

### Step 2: Test Database Initialization

When the app starts, check:
- [ ] App launches without errors
- [ ] Database file is created (check `%APPDATA%\lesson_planner.db` on Windows)
- [ ] No errors in console about database initialization

### Step 3: Test IPC Bridge - Manual Test

#### Option A: Using Browser Console (if app has devtools)

1. Open the Tauri app
2. Open DevTools (if available)
3. In the console, run:
```javascript
// Test sync function
import { triggerSync } from './lib/api';
triggerSync('test-user-id').then(result => {
  console.log('Sync result:', result);
}).catch(error => {
  console.error('Sync error:', error);
});
```

#### Option B: Add Test Button to UI

Add a temporary sync button to test the IPC bridge.

### Step 4: Test Database Operations

Verify that database operations work through IPC:

1. **Test User Query**
   - The app should be able to list users
   - Check if users are loaded from database

2. **Test Slot Query**
   - The app should be able to list class slots
   - Verify slots are retrieved correctly

3. **Test Plan Operations**
   - Create a test weekly plan
   - Verify it's saved to database
   - Retrieve it back

### Step 5: Test Python Sidecar

The Python sidecar should:
- [ ] Start when sync is triggered
- [ ] Receive commands from Rust
- [ ] Send SQL queries back to Rust
- [ ] Receive SQL responses
- [ ] Complete sync operation

### Step 6: Monitor Logs

Check for:
- Rust logs (in terminal where `cargo tauri dev` is running)
- Python logs (stderr output from sidecar)
- Frontend console logs

## Expected Behavior

### Successful IPC Flow

1. **Frontend** calls `triggerSync(userId)`
2. **Rust** receives `trigger_sync` command
3. **Rust** spawns Python sidecar process
4. **Rust** sends command to Python via stdin
5. **Python** processes command and sends SQL queries via stdout
6. **Rust** receives SQL queries and executes them
7. **Rust** sends SQL results back to Python via stdin
8. **Python** completes sync and sends final response
9. **Rust** returns result to frontend
10. **Frontend** receives sync result

### Error Handling

If something fails:
- Check Rust terminal for errors
- Check Python stderr output
- Check frontend console for errors
- Verify database file exists and is accessible

## Troubleshooting

### Issue: Python sidecar doesn't start

**Solution:**
- Verify Python is in PATH
- Check that `backend/sidecar_main.py` exists
- Verify Python can import required modules

### Issue: IPC communication fails

**Solution:**
- Check that stdin/stdout are properly piped
- Verify JSON message format is correct
- Check for encoding issues

### Issue: Database operations fail

**Solution:**
- Verify database file path is correct
- Check that migrations ran successfully
- Verify SQL syntax is correct

### Issue: Sync doesn't complete

**Solution:**
- Check Supabase configuration
- Verify network connectivity
- Check Python sidecar logs for errors

## Test Checklist

- [ ] App launches successfully
- [ ] Database initializes correctly
- [ ] IPC bridge can spawn Python sidecar
- [ ] IPC messages are sent/received correctly
- [ ] Database queries work through IPC
- [ ] Database writes work through IPC
- [ ] Sync operation completes successfully
- [ ] Error handling works correctly
- [ ] App can be closed cleanly

## Next Steps After Testing

Once desktop testing is complete:
1. Document any issues found
2. Fix any bugs discovered
3. Proceed to Android deployment (Phase 5 & 6)

