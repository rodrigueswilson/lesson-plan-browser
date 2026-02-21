# Physical Tablet Testing Guide

**Date:** November 25, 2025  
**Status:** Guide for testing on physical Android tablet

## ⚠️ IMPORTANT: Rust Library Build Required

**Current Issue:** The app requires the Rust native library (`libbilingual_lesson_planner.so`) to run. Building this requires:
- Android NDK (Native Development Kit) installed
- NDK linker configured in `.cargo/config.toml`
- Proper environment variables set

**Quick Fix for Testing:** If you see `UnsatisfiedLinkError: library "libbilingual_lesson_planner.so" not found`, you need to build the Rust library first. See "Building Rust Library" section below.

## Overview

This guide walks you through testing the Bilingual Lesson Planner app on a physical Android tablet. The app will run in **source mode** (Python from source) since we haven't built the Android binary yet.

## Prerequisites

- [ ] Physical Android tablet connected to same WiFi network as your PC
- [ ] USB debugging enabled on tablet (or wireless ADB)
- [ ] FastAPI backend running on PC
- [ ] PC and tablet on same local network

## Step 1: Find Your PC's IP Address

The tablet needs to connect to your PC's backend. Find your PC's local IP address:

### Windows (PowerShell):
```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -notlike "169.254.*"} | Select-Object IPAddress, InterfaceAlias
```

**Look for:** An IP like `192.168.1.15` or `192.168.12.153` (not `127.0.0.1` or `169.254.x.x`)

**Example output:**
```
IPAddress      InterfaceAlias
---------      --------------
192.168.12.153 Wi-Fi
```

**Note this IP address** - you'll need it in Step 3.

## Step 2: Update API URL for Physical Tablet

The current code uses `10.0.2.2` which only works for emulators. We need to update it for physical tablets.

### Update `frontend/src/lib/api.ts`:

Open `frontend/src/lib/api.ts` and find this line (around line 30):

```typescript
const getApiUrl = (): string => {
  const userAgent = navigator.userAgent || '';
  console.log('[API] Determining API URL. UserAgent:', userAgent);
  
  const isTauri = typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
  
  if (userAgent.includes('Android')) {
    // For physical tablet: use PC's LAN IP
    // For emulator: use 10.0.2.2
    // TODO: Make this configurable or auto-detect
    const pcIp = '192.168.12.153'; // REPLACE WITH YOUR PC's IP FROM STEP 1
    console.log('[API] Android detected. Using PC IP:', pcIp);
    return `http://${pcIp}:8000/api`;
  }
  
  // For Tauri desktop, use localhost
  if (isTauri) {
    console.log('[API] Tauri detected. Using: http://localhost:8000/api');
    return 'http://localhost:8000/api';
  }
  
  return config.apiBaseUrl;
};
```

**Replace `192.168.12.153` with your PC's IP from Step 1.**

**Note:** After changing the IP, you must rebuild the frontend for the change to take effect.

## Step 3: Start FastAPI Backend

Make sure the backend is running and accessible from your network:

```powershell
cd d:\LP
python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000
```

**Important:** 
- `--host 0.0.0.0` allows connections from other devices on your network
- Make sure Windows Firewall allows connections on port 8000

### Test Backend Accessibility

From another device (or your tablet's browser), try:
```
http://YOUR_PC_IP:8000/api/health
```

You should see a JSON response. If not, check Windows Firewall settings.

## Step 4: Connect Tablet via ADB

### Option A: USB Connection

1. Enable **Developer Options** on tablet:
   - Go to Settings → About Tablet
   - Tap "Build Number" 7 times
   
2. Enable **USB Debugging**:
   - Settings → Developer Options → USB Debugging (ON)

3. Connect tablet via USB

4. Verify connection:
```powershell
adb devices
```

You should see your device listed:
```
List of devices attached
ABC123XYZ    device
```

### Option B: Wireless ADB (No USB Cable)

1. Connect tablet and PC to same WiFi

2. Enable USB debugging (see Option A)

3. Connect via USB once to enable wireless:
```powershell
adb tcpip 5555
adb connect TABLET_IP:5555
```

4. Disconnect USB cable

5. Verify:
```powershell
adb devices
```

## Step 5: Build Frontend

```powershell
cd d:\LP\frontend
npm run build:skip-check
```

## Step 6: Apply Android Network Security Fix

This allows the app to make HTTP (not HTTPS) requests to your PC backend:

```powershell
cd d:\LP\frontend\src-tauri
.\apply-android-network-fix.ps1
```

This script:
- Creates `network_security_config.xml` allowing cleartext HTTP
- Updates `AndroidManifest.xml` to use it

## Step 7: Copy Frontend Assets

```powershell
Remove-Item "d:\LP\frontend\src-tauri\gen\android\app\src\main\assets" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path "d:\LP\frontend\src-tauri\gen\android\app\src\main\assets" -Force
Copy-Item "d:\LP\frontend\dist\*" "d:\LP\frontend\src-tauri\gen\android\app\src\main\assets\" -Recurse -Force
```

## Step 8: Determine Tablet Architecture

Check your tablet's CPU architecture:

```powershell
adb shell getprop ro.product.cpu.abi
```

**Common results:**
- `arm64-v8a` → Use `aarch64` target
- `armeabi-v7a` → Use `armv7` target  
- `x86_64` → Use `x86_64` target (rare for tablets)

**Most modern tablets are `arm64-v8a` (aarch64).**

## Step 9: Build APK for Your Tablet

### For ARM64 (most common):
```powershell
cd d:\LP\frontend\src-tauri\gen\android
.\gradlew.bat assembleAarch64Debug -x rustBuildAarch64Debug
```

### For x86_64 (if your tablet is x86):
```powershell
.\gradlew.bat assembleX86_64Debug -x rustBuildX86_64Debug
```

**Note:** The `-x rustBuildAarch64Debug` flag skips Rust compilation to speed up build. The app will use Python from source mode.

## Step 10: Install APK on Tablet

### Find your device ID:
```powershell
adb devices
```

### Install APK:
```powershell
# For ARM64
adb install -r "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\aarch64\debug\app-aarch64-debug.apk"

# For x86_64
adb install -r "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\x86_64\debug\app-x86_64-debug.apk"
```

### Launch App:
```powershell
adb shell am start -n com.lessonplanner.bilingual/.MainActivity
```

## Step 11: Test the App

### What to Test:

1. **App Launch**
   - [ ] App opens without crash
   - [ ] UI renders correctly
   - [ ] No blank screen

2. **Backend Connection**
   - [ ] Check browser console (if accessible) or ADB logs:
   ```powershell
   adb logcat | Select-String "API\|Sidecar\|Error"
   ```
   - [ ] Look for: `[API] Android detected. Using PC IP: ...`
   - [ ] Users should load from backend

3. **Basic Functionality**
   - [ ] Select a user
   - [ ] View class slots
   - [ ] Navigate through the app

4. **Sync Functionality** (if Python sidecar works)
   - [ ] Trigger sync
   - [ ] Check if data syncs from Supabase
   - [ ] Note: This requires Python to be installed on tablet OR Android binary

## Step 12: View Logs

Monitor app logs in real-time:

```powershell
# Filter for relevant logs
adb logcat | Select-String "Bilingual\|Sidecar\|API\|Tauri\|Error\|Exception"
```

Or view all logs:
```powershell
adb logcat
```

## Building Rust Library (Required)

The app needs the Rust native library to run. If you see `UnsatisfiedLinkError`, you need to build it.

### Option 1: Use Tauri CLI (Recommended)

The Tauri CLI should handle NDK setup automatically:

```powershell
cd d:\LP\frontend
npx tauri android build --target aarch64
```

**Note:** This requires Android NDK to be installed. If it fails, see Option 2.

### Option 2: Set Up Android NDK Manually

1. **Install Android NDK:**
   - Download Android Studio
   - Open SDK Manager → SDK Tools → Check "NDK (Side by side)"
   - Install NDK version 26.1.10909125 or later

2. **Set Environment Variables:**
   ```powershell
   # Find your Android SDK path (usually in %LOCALAPPDATA%\Android\Sdk)
   $env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
   $env:ANDROID_NDK_HOME = "$env:ANDROID_HOME\ndk\26.1.10909125"  # Adjust version
   ```

3. **Configure Cargo:**
   Create `frontend/src-tauri/.cargo/config.toml`:
   ```toml
   [target.aarch64-linux-android]
   linker = "aarch64-linux-android21-clang"
   ```

4. **Build:**
   ```powershell
   cd d:\LP\frontend\src-tauri
   cargo build --target aarch64-linux-android --lib
   ```

5. **Then build APK:**
   ```powershell
   cd d:\LP\frontend\src-tauri\gen\android
   .\gradlew.bat assembleArm64Debug
   ```

### Option 3: Skip Rust Build (Limited Testing)

For now, you can test the app's UI and API connection even if sync doesn't work:
- The app will crash when trying to use sync functionality
- But you can verify the app launches and connects to the backend
- This is useful for testing network configuration

## Troubleshooting

### App Crashes with "libbilingual_lesson_planner.so not found"

**Cause:** Rust library not built for Android.

**Solution:** Build the Rust library (see "Building Rust Library" section above).

### App Won't Install

**Error: "INSTALL_FAILED_UPDATE_INCOMPATIBLE"**
```powershell
# Uninstall existing version first
adb uninstall com.lessonplanner.bilingual
# Then install again
adb install -r "path\to\apk"
```

### "Failed to fetch" Error

1. **Check backend is running:**
   ```powershell
   # On PC, verify backend is accessible
   curl http://localhost:8000/api/health
   ```

2. **Check Windows Firewall:**
   - Windows Defender Firewall → Allow an app
   - Ensure Python/uvicorn is allowed on port 8000

3. **Verify IP address:**
   - Check `api.ts` has correct PC IP
   - Test from tablet browser: `http://YOUR_PC_IP:8000/api/health`

4. **Check network security config:**
   ```powershell
   # Re-run the fix
   cd d:\LP\frontend\src-tauri
   .\apply-android-network-fix.ps1
   ```

### Black Screen

1. **Check ADB logs:**
   ```powershell
   adb logcat | Select-String "Error\|Exception\|FATAL"
   ```

2. **Rebuild and reinstall:**
   ```powershell
   # Rebuild frontend
   cd d:\LP\frontend
   npm run build:skip-check
   
   # Copy assets
   Copy-Item "d:\LP\frontend\dist\*" "d:\LP\frontend\src-tauri\gen\android\app\src\main\assets\" -Recurse -Force
   
   # Rebuild APK
   cd d:\LP\frontend\src-tauri\gen\android
   .\gradlew.bat assembleAarch64Debug -x rustBuildAarch64Debug
   
   # Reinstall
   adb install -r "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\aarch64\debug\app-aarch64-debug.apk"
   ```

### Python Sidecar Not Working

**Expected:** The app will try to run Python from source, which requires:
- Python installed on tablet (unlikely)
- OR Android binary (not built yet)

**Current behavior:** Sync will fail with "Python not found" or similar. This is expected until we build the Android binary.

**Workaround:** The app can still use the PC backend for API calls, but sync functionality won't work without Python.

## Next Steps After Testing

Once tablet testing is successful:

1. ✅ **Validate app works on target device**
2. ✅ **Confirm network configuration**
3. ⏭️ **Build Android binary** (Phase 5 Android) for full offline capability
4. ⏭️ **Production build** (Phase 6)

## Quick Reference Commands

```powershell
# Find PC IP
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*"}

# Check ADB connection
adb devices

# Check tablet architecture
adb shell getprop ro.product.cpu.abi

# Build and install
cd d:\LP\frontend
npm run build:skip-check
cd src-tauri
.\apply-android-network-fix.ps1
Remove-Item "gen\android\app\src\main\assets" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path "gen\android\app\src\main\assets" -Force
Copy-Item "..\dist\*" "gen\android\app\src\main\assets\" -Recurse -Force
cd gen\android
.\gradlew.bat assembleAarch64Debug -x rustBuildAarch64Debug
adb install -r "app\build\outputs\apk\aarch64\debug\app-aarch64-debug.apk"

# View logs
adb logcat | Select-String "Bilingual\|Sidecar\|API\|Error"
```

---

**Last Updated:** November 25, 2025

