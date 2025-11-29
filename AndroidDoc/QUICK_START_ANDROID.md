# Quick Start: Android Emulator Setup

## First Time Setup (After `npx tauri android init`)

After running `npx tauri android init`, **always** run the network security fix:

```powershell
cd d:\LP\frontend\src-tauri
.\apply-android-network-fix.ps1
```

This ensures the app can connect to the PC backend at `http://10.0.2.2:8000/api`.

## Complete Build & Install Process

### Step 1: Build Frontend
```powershell
cd d:\LP\frontend
npm run build:skip-check
```

### Step 2: Copy Assets to Android Project
```powershell
Remove-Item "d:\LP\frontend\src-tauri\gen\android\app\src\main\assets" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path "d:\LP\frontend\src-tauri\gen\android\app\src\main\assets" -Force
Copy-Item "d:\LP\frontend\dist\*" "d:\LP\frontend\src-tauri\gen\android\app\src\main\assets\" -Recurse -Force
```

### Step 3: Build APK
```powershell
cd d:\LP\frontend\src-tauri\gen\android
.\gradlew.bat assembleX86_64Debug -x rustBuildX86_64Debug
```

### Step 4: Install on Emulator
```powershell
adb -s emulator-5554 uninstall com.lessonplanner.bilingual
adb -s emulator-5554 install -r "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\x86_64\debug\app-x86_64-debug.apk"
adb -s emulator-5554 shell am start -n com.lessonplanner.bilingual/.MainActivity
```

### Step 5: Start Backend (if not running)
```powershell
cd d:\LP
python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

### Black Screen
- Run `npx tauri android init` again
- Run `.\apply-android-network-fix.ps1`
- Rebuild and reinstall

### "Failed to fetch" Error
- Ensure backend is running: `python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000`
- Verify network security config: Check that `network_security_config.xml` exists
- Run `.\apply-android-network-fix.ps1` again

### App Not Visible
- Check app drawer (swipe up from bottom)
- Check recent apps (press square button)
- Force restart: `adb -s emulator-5554 shell "am force-stop com.lessonplanner.bilingual; am start -n com.lessonplanner.bilingual/.MainActivity"`

---

**See `07_ANDROID_DEBUGGING_AND_FIXES.md` for detailed troubleshooting.**

