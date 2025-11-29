# Physical Tablet Build Plan

## 📋 Overview

This document outlines the plan for creating a production-ready build of the Lesson Plan Browser app for deployment on a physical Android tablet. The build will support both WiFi-connected mode (using PC backend) and standalone mode (using local SQLite database).

---

## 🎯 Objectives

1. **Create a production-ready APK** for physical tablet installation
2. **Configure network settings** for WiFi connectivity to PC backend
3. **Enable standalone mode** with local database support (optional)
4. **Optimize build** for tablet hardware (release mode, signing)
5. **Create installation guide** for deploying to physical device

---

## 📦 Current Status

### ✅ What's Already Working
- ✅ Android emulator build (`npm run android:dev`)
- ✅ Shared module integration (`@lesson-browser`, `@lesson-mode`, `@lesson-api`)
- ✅ Dual-mode API client (HTTP + local database)
- ✅ WeekView with table layout and color scheme
- ✅ All components from "second version" integrated
- ✅ Build configuration verified

### ⏳ What Needs to Be Done
- ⏳ Production build configuration
- ⏳ Network configuration for physical device
- ⏳ APK signing (optional but recommended)
- ⏳ Standalone mode testing
- ⏳ Installation and deployment guide

---

## 🔧 Phase 1: Build Configuration

### 1.1 Environment Variables Setup

**Create `.env.production` file** in `lesson-plan-browser/frontend/`:

```env
# Production build for physical tablet
VITE_API_BASE_URL=http://YOUR_PC_IP:8000/api
VITE_ANDROID_API_BASE_URL=http://YOUR_PC_IP:8000/api

# Optional: Enable standalone mode (local database)
# VITE_ENABLE_STANDALONE_DB=true

# Build mode
NODE_ENV=production
TAURI_DEBUG=false
```

**Notes:**
- Replace `YOUR_PC_IP` with the actual IP address of the PC running the backend
- The tablet and PC must be on the same WiFi network
- If standalone mode is enabled, the app will use local SQLite database instead of HTTP API

### 1.2 Tauri Configuration Updates

**Update `src-tauri/tauri.conf.json`** to include Android-specific settings:

```json
{
  "app": {
    "android": {
      "minSdkVersion": 24,
      "targetSdkVersion": 34,
      "compileSdkVersion": 34,
      "permissions": [
        "android.permission.INTERNET",
        "android.permission.ACCESS_NETWORK_STATE",
        "android.permission.READ_EXTERNAL_STORAGE",
        "android.permission.WRITE_EXTERNAL_STORAGE"
      ]
    }
  }
}
```

**Check if Android config already exists** in the generated files or needs to be added.

### 1.3 Build Script Updates

**Create `build-tablet.ps1`** script:

```powershell
# Build script for physical tablet
param(
    [string]$PC_IP = "",
    [switch]$Standalone = $false
)

Write-Host "Building APK for physical tablet..." -ForegroundColor Green

# Set environment variables
if ($PC_IP) {
    $env:VITE_API_BASE_URL = "http://$PC_IP:8000/api"
    $env:VITE_ANDROID_API_BASE_URL = "http://$PC_IP:8000/api"
    Write-Host "API URL set to: http://$PC_IP:8000/api" -ForegroundColor Yellow
} else {
    Write-Host "WARNING: PC_IP not provided. Using default or emulator IP." -ForegroundColor Yellow
}

if ($Standalone) {
    $env:VITE_ENABLE_STANDALONE_DB = "true"
    Write-Host "Standalone mode enabled (local database)" -ForegroundColor Yellow
}

$env:NODE_ENV = "production"
$env:TAURI_DEBUG = "false"

# Build
cd frontend
npm run build:skip-check
npm run tauri android build -- --release

Write-Host "Build complete! APK location: frontend/src-tauri/gen/android/app/build/outputs/apk/universal/release/" -ForegroundColor Green
```

---

## 🌐 Phase 2: Network Configuration

### 2.1 WiFi Network Setup

**Requirements:**
- PC and tablet must be on the same WiFi network
- Backend must be accessible from tablet's IP address
- Firewall must allow connections on port 8000

**Steps:**
1. Find PC's IP address:
   ```powershell
   ipconfig
   # Look for IPv4 Address under your WiFi adapter (e.g., 192.168.1.100)
   ```

2. Verify backend is accessible:
   ```powershell
   # On PC, ensure backend runs on all interfaces:
   # uvicorn main:app --host 0.0.0.0 --port 8000
   ```

3. Test connectivity from tablet:
   ```powershell
   # After installing APK, test with:
   adb shell "curl http://YOUR_PC_IP:8000/api/health"
   ```

### 2.2 API URL Configuration

**Option A: Build-time configuration (recommended)**
- Set `VITE_API_BASE_URL` in `.env.production` before building
- IP address is baked into the APK

**Option B: Runtime configuration (future enhancement)**
- Add settings screen in app to configure API URL
- Store in local storage or preferences

---

## 📱 Phase 3: Build Process

### 3.1 Pre-Build Checklist

- [ ] PC IP address identified
- [ ] Backend running and accessible on network
- [ ] WiFi network confirmed (PC and tablet connected)
- [ ] Environment variables set
- [ ] Dependencies installed (`npm install`)

### 3.2 Build Commands

**For WiFi-connected mode:**
```powershell
cd lesson-plan-browser/frontend
$env:VITE_API_BASE_URL = "http://192.168.1.100:8000/api"
$env:VITE_ANDROID_API_BASE_URL = "http://192.168.1.100:8000/api"
npm run build:skip-check
npm run tauri android build -- --release
```

**For standalone mode:**
```powershell
cd lesson-plan-browser/frontend
$env:VITE_ENABLE_STANDALONE_DB = "true"
npm run build:skip-check
npm run tauri android build -- --release
```

### 3.3 APK Location

After build, APK will be located at:
```
lesson-plan-browser/frontend/src-tauri/gen/android/app/build/outputs/apk/universal/release/app-universal-release.apk
```

Or architecture-specific:
```
lesson-plan-browser/frontend/src-tauri/gen/android/app/build/outputs/apk/arm64-v8a/release/app-arm64-v8a-release.apk
```

---

## 📲 Phase 4: Installation

### 4.1 Enable Developer Options on Tablet

1. Go to **Settings** → **About tablet**
2. Tap **Build number** 7 times
3. Go back to **Settings** → **Developer options**
4. Enable **USB debugging**

### 4.2 Install via ADB

```powershell
# Connect tablet via USB
adb devices

# Install APK
adb install -r "frontend/src-tauri/gen/android/app/build/outputs/apk/universal/release/app-universal-release.apk"

# Or install architecture-specific APK
adb install -r "frontend/src-tauri/gen/android/app/build/outputs/apk/arm64-v8a/release/app-arm64-v8a-release.apk"
```

### 4.3 Install via File Transfer

1. Copy APK to tablet (via USB, email, or cloud storage)
2. On tablet, open **Files** app
3. Navigate to APK location
4. Tap APK file
5. Allow installation from unknown sources if prompted
6. Tap **Install**

---

## 🧪 Phase 5: Testing

### 5.1 Network Connectivity Test

**Test 1: Backend connectivity**
- Open app on tablet
- Check if user list loads
- Verify API calls succeed

**Test 2: WiFi connection**
- Disconnect WiFi → App should show error or fallback
- Reconnect WiFi → App should resume working

### 5.2 Functionality Test

- [ ] User selection works
- [ ] Week view displays correctly (table layout)
- [ ] Day view displays correctly
- [ ] Lesson detail view works
- [ ] Lesson mode works
- [ ] Color scheme applies correctly
- [ ] Navigation between views works

### 5.3 Standalone Mode Test (if enabled)

- [ ] App works without WiFi
- [ ] Local database queries succeed
- [ ] Data persists between app restarts

---

## 🔐 Phase 6: APK Signing (Optional but Recommended)

### 6.1 Generate Keystore

```powershell
keytool -genkey -v -keystore lesson-plan-browser.keystore -alias lesson-plan-browser -keyalg RSA -keysize 2048 -validity 10000
```

### 6.2 Sign APK

```powershell
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 -keystore lesson-plan-browser.keystore app-universal-release.apk lesson-plan-browser
```

### 6.3 Verify Signature

```powershell
jarsigner -verify -verbose -certs app-universal-release.apk
```

---

## 📝 Phase 7: Documentation

### 7.1 Create Installation Guide

**File: `TABLET_INSTALLATION_GUIDE.md`**

Include:
- Prerequisites (PC IP, WiFi network)
- Build steps
- Installation steps
- Troubleshooting common issues
- Network configuration tips

### 7.2 Create Quick Reference

**File: `QUICK_START_TABLET.md`**

One-page quick reference for:
- Building APK
- Installing on tablet
- Verifying connectivity

---

## 🐛 Troubleshooting

### Issue: App can't connect to backend

**Solutions:**
1. Verify PC IP address is correct
2. Check backend is running: `curl http://PC_IP:8000/api/health`
3. Check firewall allows port 8000
4. Verify tablet and PC are on same WiFi network
5. Check backend is listening on `0.0.0.0`, not just `localhost`

### Issue: APK won't install

**Solutions:**
1. Enable "Install from unknown sources" in Android settings
2. Check tablet architecture matches APK (arm64-v8a vs x86_64)
3. Uninstall old version first: `adb uninstall com.lessonplanner.browser`
4. Try installing via ADB instead of file manager

### Issue: Blank screen on launch

**Solutions:**
1. Check network connectivity
2. Verify API URL is correct
3. Check browser console: `adb logcat | grep -i "lesson\|error"`
4. Verify backend is accessible from tablet's IP

---

## ✅ Success Criteria

- [ ] APK builds successfully in release mode
- [ ] APK installs on physical tablet
- [ ] App connects to PC backend via WiFi
- [ ] All views (Week, Day, Lesson Detail, Lesson Mode) work correctly
- [ ] WeekView displays with correct table layout and colors
- [ ] Navigation between views works smoothly
- [ ] Standalone mode works (if enabled)
- [ ] App persists data correctly

---

## 📅 Implementation Timeline

**Tomorrow's Session:**

1. **Morning (2-3 hours)**
   - Set up environment variables
   - Update Tauri configuration if needed
   - Create build scripts
   - Test build process

2. **Afternoon (2-3 hours)**
   - Build release APK
   - Install on physical tablet
   - Test network connectivity
   - Verify all functionality

3. **Documentation (1 hour)**
   - Create installation guide
   - Document any issues encountered
   - Update project status

---

## 📚 References

- Current build config: `lesson-plan-browser/frontend/vite.config.ts`
- Tauri config: `lesson-plan-browser/frontend/src-tauri/tauri.conf.json`
- API client: `shared/lesson-api/src/index.ts`
- Project status: `lesson-plan-browser/PROJECT_STATUS.md`

---

**Last Updated:** 2025-11-27  
**Status:** Ready for implementation tomorrow

