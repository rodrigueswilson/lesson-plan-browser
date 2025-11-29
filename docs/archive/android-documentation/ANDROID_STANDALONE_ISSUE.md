# Android Standalone Mode Issue: "Cannot load the users!"

## Problem
The app is installed and launches, but shows error "Cannot load the users!"

## Root Cause
The frontend is configured for **remote-control mode** (WiFi mode), trying to connect to a PC backend at `http://192.168.12.153:8000/api`. In **standalone mode**, the app should use the local sidecar via IPC instead.

## Current State

### ✅ What's Working:
1. App installs successfully
2. App launches on tablet
3. Sidecar binary is bundled (37.11 MB)
4. Android bridge code is implemented
5. Tauri IPC commands exist (`sql_query`, `sql_execute`)

### ❌ What's Not Working:
1. Frontend still uses HTTP API calls instead of IPC
2. API client (`api.ts`) detects Android and uses WiFi mode URL
3. No users can be loaded because there's no HTTP backend

## Solution Options

### Option 1: Update Frontend API to Use Tauri Commands (Recommended)
Modify `frontend/src/lib/api.ts` to:
- Detect standalone mode (Android without WiFi connection)
- Use Tauri commands (`sql_query`) instead of HTTP requests
- Query local SQLite database directly

### Option 2: Use Sidecar via IPC
- Create new Tauri commands that proxy database queries through sidecar
- Frontend calls Tauri commands → Rust queries sidecar via IPC → Sidecar queries database

### Option 3: Hybrid Approach
- Try HTTP first (for remote-control mode)
- Fallback to IPC/Tauri commands if HTTP fails (for standalone mode)

## Next Steps

1. **Check logcat** for sidecar startup:
   ```powershell
   adb logcat | Select-String -Pattern "sidecar|python|Sidecar"
   ```

2. **Implement Option 1** - Update frontend to use local database via Tauri commands

3. **Test** - Verify users can be loaded from local SQLite database

## Files to Modify

1. `frontend/src/lib/api.ts` - Switch API calls to Tauri commands
2. `frontend/src/components/UserSelector.tsx` - Update error handling
3. May need new Tauri commands for user operations (or use generic `sql_query`)

