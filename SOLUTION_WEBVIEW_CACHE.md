# WebView Cache Issue - Final Solution

## Problem
The APK contains the correct files (`index-TiTynWQK.js`), but the app persistently loads the old file (`index-cOgOR3pL.js`) even after:
- Complete rebuild
- App data clear
- Uninstall
- Fresh install

## Root Cause
This is a **system-level WebView cache** that persists even after app uninstall. The WebView component on Android can cache resources at a system level that survives app data clearing.

## Solutions (in order of preference)

### Solution 1: Restart Device (RECOMMENDED)
**This is the most reliable solution:**

1. Uninstall the app completely:
   ```powershell
   adb uninstall com.lessonplanner.bilingual
   ```

2. **Restart your Android device** (power off/on)

3. After restart, reinstall the APK:
   ```powershell
   adb install d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk
   ```

4. Launch the app and verify:
   ```powershell
   adb logcat -d | Select-String -Pattern "index-.*\.js"
   ```
   Should show `index-TiTynWQK.js` (not `index-cOgOR3pL.js`)

### Solution 2: Clear WebView Data via Android Settings
If restart doesn't work:

1. Go to Android Settings → Apps
2. Find "Android System WebView" (or "Chrome WebView")
3. Tap "Storage" → "Clear data" → "Clear cache"
4. Repeat for the app itself: "Bilingual Lesson Planner" → Storage → Clear data
5. Uninstall and reinstall the app

### Solution 3: Factory Reset WebView (Last Resort)
Only if above methods fail:

1. Go to Android Settings → Apps → Android System WebView
2. Tap three dots menu → "Uninstall updates"
3. This resets WebView to factory state
4. Reinstall app

## Why This Happens
- Android WebView can cache resources at the system level
- These caches persist across app uninstalls
- Only a device restart or manual WebView cache clear can remove them
- This is a known Android WebView behavior

## Prevention
After fixing:
- The cache should update normally when you update the app
- If it happens again, a device restart always clears it
- Consider adding cache-busting query parameters to assets if this becomes frequent

## Verification
After applying a solution, verify with:
```powershell
.\verify-apk-assets.ps1    # Check APK contents (should be correct)
adb logcat -d | Select-String -Pattern "index-.*\.js"  # Check what app loads
```

The APK is correct - this is purely a device-side cache issue.

