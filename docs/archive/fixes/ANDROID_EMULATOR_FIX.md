# Android Emulator Dev Server Fix

## Issue
The app shows "Hello Android!" instead of the frontend because the emulator can't access the dev server.

## Root Cause
- Android emulators use special IP `10.0.2.2` to access the host machine's localhost
- Tauri was trying to use `192.168.12.153` which the emulator can't reach
- The dev server needs to be running and accessible

## Solution

### Option 1: Use Environment Variable (Recommended)
```powershell
$env:TAURI_DEV_HOST="10.0.2.2"
cd frontend
npm run tauri android dev
```

### Option 2: Manual Dev Server
1. Start dev server manually:
   ```powershell
   cd frontend
   npm run dev
   ```

2. Rebuild Android app:
   ```powershell
   cd frontend
   npm run tauri android dev
   ```

## Verification
Test connectivity from emulator:
```powershell
adb shell "curl http://10.0.2.2:1420"
```

Should return HTML content.

## Note
- For physical devices, use your computer's actual IP (e.g., `192.168.12.153`)
- For emulators, always use `10.0.2.2`
- The dev server must be running before building/deploying

