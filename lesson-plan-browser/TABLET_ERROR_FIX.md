# Fixing Tablet Error: "Bilingual Lesson Planner" Crash

## Problem Identified

**Error Message:** "Something went wrong with Bilingual Lesson Planner... this app has a bug. Try updating...."

**Root Cause:**
- The **old app** (`com.lessonplanner.bilingual`) is installed on the tablet
- The **new browser app** (`com.lessonplanner.browser`) is **NOT** installed
- The error is from the old app, not the new one

## Solution

### Step 1: Uninstall Old App (Optional but Recommended)

```powershell
adb uninstall com.lessonplanner.bilingual
```

This removes the conflicting old app.

### Step 2: Verify APK Was Built

Check if the new browser app APK exists:

```powershell
cd D:\LP\lesson-plan-browser

# Check release APK
Test-Path "frontend\src-tauri\gen\android\app\build\outputs\apk\release\app-release.apk"

# Check debug APK  
Test-Path "frontend\src-tauri\gen\android\app\build\outputs\apk\debug\app-debug.apk"
```

**If APK doesn't exist:** You need to build it first (see "Build APK" section below).

### Step 3: Install New Browser App

**Option A: Using Installation Script**
```powershell
cd D:\LP\lesson-plan-browser
.\install-android-app.ps1
```

**Option B: Manual Installation**
```powershell
# Find the APK path first
cd D:\LP\lesson-plan-browser

# Try release APK first
$apkPath = "frontend\src-tauri\gen\android\app\build\outputs\apk\release\app-release.apk"
if (-not (Test-Path $apkPath)) {
    $apkPath = "frontend\src-tauri\gen\android\app\build\outputs\apk\debug\app-debug.apk"
}

# Install
adb install -r $apkPath
```

### Step 4: Launch New App

```powershell
adb shell am start -n com.lessonplanner.browser/.MainActivity
```

Or tap the "Lesson Plan Browser" icon on the tablet.

---

## If APK Doesn't Exist: Build It

### Build the Android APK

```powershell
cd D:\LP\lesson-plan-browser\frontend
npm run android:build
```

**Expected time:** 10-20 minutes for first build.

**Output location:**
- Release: `frontend\src-tauri\gen\android\app\build\outputs\apk\release\app-release.apk`
- Debug: `frontend\src-tauri\gen\android\app\build\outputs\apk\debug\app-debug.apk`

---

## Verify Installation

### Check Installed Apps

```powershell
# Should show com.lessonplanner.browser
adb shell pm list packages | Select-String -Pattern "lessonplanner"
```

**Expected output:**
```
package:com.lessonplanner.browser
```

If you see `com.lessonplanner.bilingual`, that's the old app (you can uninstall it).

### Test App Launch

```powershell
adb shell am start -n com.lessonplanner.browser/.MainActivity
```

**Expected:** App should launch without the error message.

---

## Troubleshooting

### Issue: "Package not found" when launching

**Solution:** App not installed. Install the APK first (Step 3).

### Issue: "Installation failed" 

**Possible causes:**
- APK doesn't exist (build first)
- Storage full on tablet
- Unknown sources not enabled
- Architecture mismatch

**Solutions:**
1. Check APK exists: `Test-Path "frontend\src-tauri\gen\android\app\build\outputs\apk\release\app-release.apk"`
2. Free up space on tablet
3. Enable "Install from unknown sources" in tablet settings
4. Check tablet architecture matches APK

### Issue: App still crashes after installation

**Check logs:**
```powershell
adb logcat -d *:E | Select-String -Pattern "lessonplanner|browser|FATAL|Exception" | Select-Object -Last 50
```

Common causes:
- Missing backend connection (app tries to connect to localhost)
- Missing permissions
- Corrupted installation

**Solutions:**
1. **Backend not accessible:** Configure API URL (see below)
2. **Uninstall and reinstall:**
   ```powershell
   adb uninstall com.lessonplanner.browser
   adb install -r "frontend\src-tauri\gen\android\app\build\outputs\apk\release\app-release.apk"
   ```

---

## Configure Backend Connection (After Installation)

The app needs to connect to your PC's backend. 

### Step 1: Get PC IP Address

```powershell
ipconfig | Select-String -Pattern "IPv4"
```

Save the IP address (e.g., `192.168.1.100`).

### Step 2: Create .env File

Create `lesson-plan-browser/frontend/.env`:
```
VITE_API_BASE_URL=http://YOUR_PC_IP:8000/api
```

Replace `YOUR_PC_IP` with your actual IP.

### Step 3: Rebuild and Reinstall

```powershell
cd D:\LP\lesson-plan-browser\frontend
npm run android:build
# Then install again (Step 3 above)
```

### Step 4: Start Backend

```powershell
cd D:\LP
.\start-backend-all-interfaces.bat
```

**Important:** 
- PC and tablet must be on same WiFi network
- Backend must be running before launching app

---

## Summary

**Current Issue:**
- Old app (`com.lessonplanner.bilingual`) is installed and crashing
- New app (`com.lessonplanner.browser`) is not installed

**Solution:**
1. Uninstall old app (optional)
2. Build new app APK (if not built yet)
3. Install new app APK
4. Configure backend connection
5. Launch new app

**Next Steps:**
- Follow Step 1-4 above to install and configure the new app
- See `CURRENT_STATUS.md` for overall progress

