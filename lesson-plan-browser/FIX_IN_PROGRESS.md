# Fixing Tablet Error - In Progress

## Steps Completed

### ✅ Step 1: Uninstall Old App
- Command executed: `adb uninstall com.lessonplanner.bilingual`
- Status: Old "Bilingual Lesson Planner" app should be uninstalled

### 🔄 Step 2: Build Android APK
- Command executed: `npm run android:build`
- Status: Build started (may take 10-20 minutes)

**Build Command:**
```powershell
cd D:\LP\lesson-plan-browser\frontend
npm run android:build
```

## Next Steps (After Build Completes)

### Step 3: Verify APK Built Successfully

Check if APK exists:
```powershell
cd D:\LP\lesson-plan-browser

# Check Tauri v2 path
Test-Path "frontend\src-tauri\gen\android\app\build\outputs\apk\release\app-release.apk"

# Check alternative path
Test-Path "frontend\src-tauri\target\android\app\build\outputs\apk\release\app-release.apk"
```

### Step 4: Install New Browser App

**Option A: Using Script**
```powershell
cd D:\LP\lesson-plan-browser
.\install-android-app.ps1
```

**Option B: Manual Installation**
```powershell
cd D:\LP\lesson-plan-browser

# Find APK (try release first)
$apkPath = "frontend\src-tauri\gen\android\app\build\outputs\apk\release\app-release.apk"
if (-not (Test-Path $apkPath)) {
    $apkPath = "frontend\src-tauri\gen\android\app\build\outputs\apk\debug\app-debug.apk"
}

# Install
adb install -r $apkPath
```

### Step 5: Launch and Test

```powershell
adb shell am start -n com.lessonplanner.browser/.MainActivity
```

Or tap the "Lesson Plan Browser" icon on the tablet.

---

## Monitoring Build Progress

### Check if Build is Still Running

```powershell
Get-Process | Where-Object {$_.ProcessName -like "*java*" -or $_.ProcessName -like "*cargo*" -or $_.ProcessName -like "*gradle*"} | Select-Object ProcessName, Id, CPU
```

### Check Build Logs

```powershell
cd D:\LP\lesson-plan-browser\frontend
if (Test-Path "build-log.txt") {
    Get-Content build-log.txt -Tail 50
}
```

### Expected Build Time

- **First Build:** 10-20 minutes
- **Subsequent Builds:** 2-5 minutes

**What's happening during build:**
1. Frontend build (npm/vite) - ~1-2 minutes
2. Rust compilation for Android (4 architectures) - ~10-15 minutes
3. Gradle build and APK packaging - ~2-3 minutes

---

## Troubleshooting

### Build Failed?

**Check for errors:**
```powershell
cd D:\LP\lesson-plan-browser\frontend
Get-Content build-log.txt | Select-String -Pattern "ERROR|FAILED|Exception" -Context 5
```

**Common issues:**
1. **Java not found** - Install JDK 17+ and set `JAVA_HOME`
2. **Android SDK not found** - Verify `ANDROID_HOME` is set
3. **Rust targets missing** - Run: `rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android`
4. **Network issues** - First build downloads dependencies, ensure stable connection

**Try building again:**
```powershell
cd D:\LP\lesson-plan-browser\frontend
npm run android:build
```

### APK Not Found After Build?

**Check all possible locations:**
```powershell
cd D:\LP\lesson-plan-browser
Get-ChildItem -Path "frontend\src-tauri" -Recurse -Filter "*.apk" | Select-Object FullName, Length, LastWriteTime
```

**Possible APK locations:**
- `frontend\src-tauri\gen\android\app\build\outputs\apk\release\app-release.apk` (Tauri v2)
- `frontend\src-tauri\gen\android\app\build\outputs\apk\debug\app-debug.apk` (Tauri v2)
- `frontend\src-tauri\target\android\app\build\outputs\apk\release\app-release.apk` (Alternative)

---

## Current Status

**Time:** 2025-01-27  
**Status:** Building Android APK (Step 2 in progress)

**Completed:**
- ✅ Old app uninstalled
- ✅ Build command executed

**Pending:**
- ⏳ Build completion (10-20 minutes)
- ⏳ APK installation
- ⏳ App testing

---

**Next Action:** Wait for build to complete, then proceed with Step 3 (verify APK) and Step 4 (install).

