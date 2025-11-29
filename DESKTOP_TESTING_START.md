# Desktop IPC Testing - Quick Start

## Start the Tauri App

Run this command in the `frontend` directory:

```bash
cd frontend
npm run tauri:dev
```

This will:
1. Start the Vite dev server
2. Build the Rust backend
3. Launch the Tauri application window

## Test the IPC Bridge

### Step 1: Select a User
- When the app opens, select or create a user
- The sync test button will appear on the home page

### Step 2: Click "Test Sync" Button
- Click the "Test Sync" button on the home page
- This will trigger the IPC bridge:
  - Frontend → Rust (`trigger_sync` command)
  - Rust → Python (spawns sidecar, sends command)
  - Python → Rust (SQL queries)
  - Rust → Python (SQL results)
  - Python → Rust (final response)
  - Rust → Frontend (sync result)

### Step 3: Check Results
- Success: You'll see "Sync completed! Pulled: X, Pushed: Y"
- Error: Check the error message and logs

## Monitor Logs

### Rust Logs
Watch the terminal where you ran `npm run tauri:dev` for:
- Database initialization messages
- IPC bridge activity
- SQL execution logs

### Python Logs
Python sidecar logs go to stderr, which should appear in the Rust terminal.

### Frontend Logs
Open browser DevTools (if available) or check the console for:
- API call logs
- Sync result messages
- Error messages

## Expected Behavior

### First Sync
- Python sidecar should spawn
- Database should be initialized (if not already)
- Sync should attempt to pull from Supabase (if configured)
- Sync should attempt to push local changes (if any)

### Subsequent Syncs
- Sidecar should reuse existing process (if still running)
- Sync should complete faster

## Troubleshooting

### "No user selected"
- Make sure you've selected a user from the dropdown

### "Sync failed: ..."
- Check Rust terminal for detailed error
- Verify Python is in PATH
- Check that `backend/sidecar_main.py` exists
- Verify Supabase configuration (if testing sync)

### Database errors
- Check that database file was created
- Verify migrations ran successfully
- Check file permissions

### Python import errors
- Make sure you're in the project root when running
- Verify Python can import `backend` modules
- Check that all dependencies are installed

## Test Checklist

- [ ] App launches successfully
- [ ] User can be selected
- [ ] Sync test button appears
- [ ] Clicking sync button triggers IPC
- [ ] Python sidecar starts
- [ ] Database operations work
- [ ] Sync completes (or shows appropriate error)
- [ ] Results are displayed correctly

## Next Steps

After successful desktop testing:
1. Document any issues
2. Fix bugs if found
3. Remove test button (or keep for production)
4. Proceed to Android deployment

