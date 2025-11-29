# Black Screen Fix - Emulator

## Problem
App installed but emulator shows black screen with no visible UI.

## Root Cause
After removing `devUrl` from `tauri.conf.json`, the native Android project files need to be refreshed. The Android project was still configured to look for a dev server instead of bundled assets.

## Solution

### Step 1: Refresh Native Configuration
```powershell
cd d:\LP\frontend
npx tauri android init
```

This regenerates the Android project files with the correct configuration for bundled assets.

### Step 2: Rebuild Everything
Follow the exact build sequence from `07_ANDROID_DEBUGGING_AND_FIXES.md`:

1. **Build frontend:**
   ```powershell
   cd d:\LP\frontend
   npm run build:skip-check
   ```

2. **Copy assets:**
   ```powershell
   Remove-Item "d:\LP\frontend\src-tauri\gen\android\app\src\main\assets" -Recurse -Force -ErrorAction SilentlyContinue
   New-Item -ItemType Directory -Path "d:\LP\frontend\src-tauri\gen\android\app\src\main\assets" -Force
   Copy-Item "d:\LP\frontend\dist\*" "d:\LP\frontend\src-tauri\gen\android\app\src\main\assets\" -Recurse -Force
   ```

3. **Clean and rebuild APK:**
   ```powershell
   cd d:\LP\frontend\src-tauri\gen\android
   .\gradlew.bat clean
   .\gradlew.bat assembleX86_64Debug -x rustBuildX86_64Debug
   ```

4. **Reinstall:**
   ```powershell
   adb -s emulator-5554 uninstall com.lessonplanner.bilingual
   adb -s emulator-5554 install -r "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\x86_64\debug\app-x86_64-debug.apk"
   adb -s emulator-5554 shell am start -n com.lessonplanner.bilingual/.MainActivity
   ```

## Verification

After following these steps, the app should:
- ✅ Launch successfully
- ✅ Show UI (not black screen)
- ✅ WebView renders correctly
- ✅ JavaScript executes

**Note:** If you see "Failed to fetch" errors, ensure the backend is running:
```powershell
cd d:\LP
python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000
```

---

**Status:** ✅ Fixed - App now visible on emulator

