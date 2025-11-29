# Troubleshooting: App Not Showing on Tablet

## Quick Checks

### 1. Verify Device Connection
Run this command and check if your tablet appears:
```powershell
adb devices
```
Expected output should show:
```
List of devices attached
<device-id>    device
```

### 2. Check if App is Installed (but not visible)
```powershell
adb shell pm list packages | Select-String "lessonplanner"
```
If it shows `package:com.lessonplanner.bilingual`, the app IS installed but may not have a launcher icon.

### 3. Manual Installation Steps

#### Step A: Verify APK exists
```powershell
Test-Path "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"
```

#### Step B: Uninstall any existing version
```powershell
adb uninstall com.lessonplanner.bilingual
```

#### Step C: Install with full output
```powershell
adb install -r -d "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"
```

Watch for:
- "Success" message = installed correctly
- "INSTALL_FAILED_*" = installation error (check error code)
- "INSTALL_FAILED_INSUFFICIENT_STORAGE" = tablet storage full
- "INSTALL_FAILED_UPDATE_INCOMPATIBLE" = signature mismatch

#### Step D: Launch app directly (even if no icon)
```powershell
adb shell am start -n com.lessonplanner.bilingual/.MainActivity
```

### 4. Common Issues

#### Issue: App installed but no launcher icon
**Solution:** The app may need a launcher activity configured. Try launching directly:
```powershell
adb shell am start -n com.lessonplanner.bilingual/.MainActivity
```

#### Issue: Architecture mismatch
**Check tablet architecture:**
```powershell
adb shell getprop ro.product.cpu.abi
```
- If shows `arm64-v8a` → ARM64 APK is correct
- If shows `x86_64` → Need x86_64 APK instead

#### Issue: Unknown sources not enabled
On your tablet:
1. Settings → Security → Unknown Sources (enable)
2. Or: Settings → Apps → Special access → Install unknown apps → Select ADB source → Enable

#### Issue: USB debugging not authorized
On your tablet, when you connect USB, look for "Allow USB debugging?" prompt and tap "Allow".

### 5. Verify App After Installation

#### Check if app process can start
```powershell
adb shell am start -n com.lessonplanner.bilingual/.MainActivity
adb logcat | Select-String -Pattern "bilingual|lessonplanner|Error"
```

#### Check app info
```powershell
adb shell dumpsys package com.lessonplanner.bilingual | Select-String -Pattern "versionName|versionCode|enabled"
```

### 6. Alternative: Install via File Manager

If ADB install fails:
1. Copy APK to tablet storage:
   ```powershell
   adb push "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk" /sdcard/Download/app.apk
   ```
2. On tablet: Open File Manager → Downloads → Tap `app.apk` → Install

### 7. Check Logs for Errors

```powershell
# Clear logcat and watch for errors
adb logcat -c
adb logcat | Select-String -Pattern "Error|FATAL|AndroidRuntime"
```

Then try launching the app again.

## Next Steps

If app still doesn't appear:
1. Check AndroidManifest.xml for launcher activity configuration
2. Verify the APK is signed correctly
3. Check if the tablet has any app restrictions enabled
4. Try building a universal APK instead of arm64-specific

