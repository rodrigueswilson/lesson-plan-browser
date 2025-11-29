# APK Signing Issue - Fix Applied

## Issue

**Error:** `INSTALL_PARSE_FAILED_NO_CERTIFICATES: Failed to collect certificates from /data/app/vmdl462329857.tmp/base.apk: Attempt to get length of null array`

**Cause:** The universal release APK is unsigned. Android requires APKs to be signed before installation.

## Solution

### Option 1: Build Debug APK (Recommended for Testing)

Debug APKs are automatically signed with a debug key:

```powershell
cd D:\LP\lesson-plan-browser\frontend
npm run android:dev
```

**Output Location:**
- `frontend\src-tauri\gen\android\app\build\outputs\apk\debug\app-debug.apk`

**Then install:**
```powershell
cd D:\LP\lesson-plan-browser
adb install -r "frontend\src-tauri\gen\android\app\build\outputs\apk\debug\app-debug.apk"
```

### Option 2: Sign the Universal APK Manually

If you need to use the universal APK, you can sign it manually:

```powershell
# Navigate to Android SDK build-tools
cd $env:ANDROID_HOME\build-tools\*\ 

# Sign the APK
apksigner sign --ks debug.keystore --ks-key-alias androiddebugkey --ks-pass pass:android --key-pass pass:android --out signed-app.apk "D:\LP\lesson-plan-browser\frontend\src-tauri\gen\android\app\build\outputs\apk\universal\release\app-universal-release-unsigned.apk"
```

**Note:** This requires creating a debug keystore first if it doesn't exist.

---

## Current Status

**Action:** Building debug APK now...

**Next Steps:**
1. Wait for debug build to complete
2. Install debug APK (automatically signed)
3. Test app launch

---

**Debug APK is recommended for testing** as it's automatically signed and faster to build.

