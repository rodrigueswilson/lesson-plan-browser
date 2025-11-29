# Manual Installation Steps - Follow These

## Quick Diagnostic Commands

Run these commands **one at a time** in PowerShell or Command Prompt and tell me the output:

### 1. Check Device Connection
```cmd
adb devices
```
**Expected:** Should show your tablet with "device" status

### 2. Check Tablet Architecture
```cmd
adb shell getprop ro.product.cpu.abi
```
**Expected:** Should show `arm64-v8a` for ARM64 tablets, or `x86_64` for x86 tablets

### 3. Check if App is Already Installed
```cmd
adb shell pm list packages | findstr lessonplanner
```
**Expected:** Either shows `package:com.lessonplanner.bilingual` or nothing

### 4. Install the APK
```cmd
adb install -r "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"
```
**Watch for:** 
- `Success` = installed correctly
- `INSTALL_FAILED_*` = error (check the error message)

### 5. Launch App Directly (Even if No Icon)
```cmd
adb shell am start -n com.lessonplanner.bilingual/.MainActivity
```
**Then check your tablet** - the app should open

---

## If Installation Fails

### Option A: Architecture Mismatch
If tablet shows `x86_64` architecture, we need to build an x86_64 APK instead:
```cmd
cd d:\LP\frontend\src-tauri\gen\android
.\gradlew.bat assembleX86_64Debug
```

### Option B: Try Universal APK
Build a universal APK that works on all architectures:
```cmd
cd d:\LP\frontend\src-tauri\gen\android
.\gradlew.bat assembleUniversalDebug
```

### Option C: Install via File Manager
1. Copy APK to tablet:
   ```cmd
   adb push "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk" /sdcard/Download/app.apk
   ```
2. On tablet: Open File Manager → Downloads → Tap `app.apk` → Install

---

## If App Installs But No Icon Shows

The app might be installed but not showing in launcher. Try:

1. **Launch directly:**
   ```cmd
   adb shell am start -n com.lessonplanner.bilingual/.MainActivity
   ```

2. **Check if it's hidden:**
   - Go to tablet Settings → Apps
   - Look for "Bilingual Lesson Planner" 
   - If found, tap it and see if you can launch from there

3. **Search for it:**
   - Open app drawer on tablet
   - Search for "Bilingual" or "Lesson Planner"

---

## Quick Batch File

I've created `install-app.bat` in the project root. You can:
1. Double-click it, OR
2. Run: `.\install-app.bat` from PowerShell

This will run all diagnostic steps automatically.

