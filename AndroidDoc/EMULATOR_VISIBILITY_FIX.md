# Emulator App Visibility Issue

## Problem
App is installed and running, but user cannot see it on emulator screen.

## Diagnosis

### App Status: ✅ Running
- App is installed: `com.lessonplanner.bilingual`
- Activity is running: `MainActivity`
- Window exists: Window manager shows app window

### Network Issue: ⚠️ Detected
- Backend is running on PC: Port 8000 listening
- Network connectivity works: `curl http://10.0.2.2:8000/api/users` succeeds
- App cannot connect: "Failed to fetch" error in logs

### Logs Show:
```
[API] Android detected via UserAgent. Forcing: http://10.0.2.2:8000/api
[API] GET http://10.0.2.2:8000/api/users
[API] Request failed: TypeError: Failed to fetch
```

## Possible Causes

1. **WebView Security**: Android WebView may be blocking cleartext HTTP traffic
2. **Network Security Config**: Missing or incorrect network security configuration
3. **CORS Issues**: Backend might not allow requests from emulator
4. **App Window Hidden**: App might be behind other windows or minimized

## Solutions to Try

### 1. Check Network Security Config
Verify `network_security_config.xml` exists and allows cleartext traffic:
```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">10.0.2.2</domain>
        <domain includeSubdomains="true">localhost</domain>
    </domain-config>
</network-security-config>
```

### 2. Verify AndroidManifest.xml
Ensure `usesCleartextTraffic` is enabled:
```xml
<application
    android:usesCleartextTraffic="true"
    ...>
```

### 3. Bring App to Foreground
```powershell
adb -s emulator-5554 shell "am force-stop com.lessonplanner.bilingual"
adb -s emulator-5554 shell "am start -n com.lessonplanner.bilingual/.MainActivity"
```

### 4. Check App Drawer
The app should appear in the app drawer. Look for "Bilingual Lesson Planner" icon.

### 5. Check Recent Apps
Swipe up from bottom (or press recent apps button) to see if app is in recent apps list.

## Next Steps

1. Verify app icon appears in app drawer
2. Check if app shows error screen (blank or error message)
3. Verify network security config is correct
4. Test with backend running and accessible

---

**Status:** App is running but may be showing error screen due to network connectivity issue.

