# Desktop Testing Troubleshooting

## Issue: Backend Not Running

### Symptom
```
Error: connect ECONNREFUSED 127.0.0.1:8000
HTTP 500 Error
```

### Solution
The backend API server needs to be running for the app to function. Start it with:

```bash
# Option 1: Use the batch script
start-backend.bat

# Option 2: Direct command
python -m uvicorn backend.api:app --reload --port 8000
```

The backend should start on `http://localhost:8000`.

## Testing IPC Bridge Without Backend

If you want to test **only** the IPC bridge (sync functionality) without the full backend:

1. The sync function uses Tauri commands, not HTTP
2. It should work even if the backend isn't running
3. However, the app UI needs the backend to load users/slots

### Workaround for IPC Testing

1. Start backend (for UI functionality)
2. Select a user
3. Click "Test Sync" button
4. The sync will use IPC bridge (not HTTP)

## Expected Behavior

### With Backend Running
- ✅ App loads users from backend API
- ✅ App can display slots, plans, etc.
- ✅ Sync button works via IPC bridge

### Without Backend Running
- ❌ App cannot load users (HTTP error)
- ❌ Most UI features won't work
- ⚠️ Sync button might work (uses IPC, not HTTP)

## Quick Test Sequence

1. **Terminal 1**: Start backend
   ```bash
   python -m uvicorn backend.api:app --reload --port 8000
   ```

2. **Terminal 2**: Start Tauri app
   ```bash
   cd frontend
   npm run tauri:dev
   ```

3. **In App**:
   - Select a user
   - Click "Test Sync"
   - Watch both terminals for logs

## Verifying Backend is Running

Check if backend is running:
```bash
curl http://localhost:8000/api/health
```

Or open in browser:
```
http://localhost:8000/api/docs
```

