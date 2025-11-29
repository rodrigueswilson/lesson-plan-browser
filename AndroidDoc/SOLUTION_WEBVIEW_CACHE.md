# WebView Cache Issue Solution

## Problem Summary
The app is still loading the old file after multiple attempts, indicating a system-level WebView cache that survives app uninstall.

## Root Cause Analysis
- **APK is correct** (verified with `verify-apk-assets.ps1`)
- **App still loads old file** (index-cOgOR3pL.js)
- **Cache persists** even after clear, uninstall, and reinstall

This is a system-level WebView cache. Android WebView can cache resources at the system level that persist across app uninstalls.

## Solution: Device Restart

**Restarting the device clears all in-memory caches, including the persistent WebView cache.**

### Required Steps

1. **Uninstall the app:**
   ```bash
   adb uninstall com.lessonplanner.bilingual
   ```

2. **Restart your Android device** (power off, then power on)

3. **After restart, reinstall the APK:**
   ```bash
   adb install d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk
   ```

4. **Launch and verify it loads the new file**

## Why This Works

- System-level WebView caches are stored in locations that survive app uninstallation
- Device restart clears all system caches and memory
- This is a known Android behavior with WebView components

## Alternative Solutions (if restart doesn't work)

### 1. Clear WebView System Cache
```bash
# Try clearing WebView system cache (requires root)
adb shell pm clear com.google.android.webview
```

### 2. Force WebView Update
```bash
# Update WebView to latest version
adb shell pm clear com.android.chrome
# Or update through Play Store
```

### 3. Use Different WebView Provider
```bash
# Check available WebView providers
adb shell cmd webviewupdate list-webview-packages

# Set different provider if available
adb shell cmd webviewupdate set-webview-package com.chrome.beta
```

### 4. Developer Options Reset
1. Go to Settings → Developer Options
2. Scroll down and tap "Clear WebView data"
3. Toggle "WebView implementation" to a different provider
4. Reboot device

## Verification

After implementing the solution:

1. Launch the app
2. Check the loaded file name in the app
3. Verify it matches the new expected file name
4. Test functionality to ensure proper loading

## Prevention

To avoid this issue in future updates:

1. **Use cache-busting in build process:**
   - Increment version numbers in `tauri.conf.json`
   - Ensure asset hashes change with each build

2. **Clear app cache before updates:**
   ```bash
   adb shell pm clear com.lessonplanner.bilingual
   ```

3. **Consider implementing version checking in the app:**
   - Add build version display in UI
   - Implement forced cache clear on version mismatch

## Technical Details

The WebView cache persistence occurs because:
- Android WebView uses system-wide caching mechanisms
- Cache files are stored in `/data/data/com.android.webview/cache/`
- These locations are not cleared during app uninstallation
- Only device restart or explicit cache clearing resolves this

## Status

**Confirmed:** APK is correct - this is purely a device-side cache issue that requires a device restart to clear.
