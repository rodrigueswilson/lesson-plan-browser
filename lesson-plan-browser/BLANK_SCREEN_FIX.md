# Fixing Blank White Screen on Tablet

## Problem

The app launches but shows a **blank white screen** on the tablet.

## Root Cause

The app is trying to connect to `localhost:8000` which doesn't work on Android. The `UserSelector` component loads on mount and tries to fetch users from the API. When this fails, it can cause a blank screen.

## Solution

### Step 1: Get Your PC's IP Address

```powershell
ipconfig | Select-String -Pattern "IPv4"
```

Save the IP address (e.g., `192.168.1.100`).

### Step 2: Create .env File

Create `lesson-plan-browser/frontend/.env`:

```
VITE_API_BASE_URL=http://YOUR_PC_IP:8000/api
```

Replace `YOUR_PC_IP` with your actual IP from Step 1.

**Example:**
```
VITE_API_BASE_URL=http://192.168.1.100:8000/api
```

### Step 3: Rebuild Frontend

```powershell
cd D:\LP\lesson-plan-browser\frontend
npm run build:skip-check
```

This rebuilds the frontend with the new API URL baked in.

### Step 4: Rebuild Android APK

```powershell
npm run android:build
```

**Note:** This will be faster than the first build (uses cached Rust builds).

### Step 5: Reinstall APK

```powershell
cd D:\LP\lesson-plan-browser
.\install-android-app.ps1
```

### Step 6: Start Backend (All Interfaces)

**Important:** Backend must be running and accessible from tablet.

```powershell
cd D:\LP
.\start-backend-all-interfaces.bat
```

This binds backend to `0.0.0.0:8000` so it's accessible from the network.

**Requirements:**
- PC and tablet must be on **same WiFi network**
- Backend must be running before launching app
- Firewall must allow port 8000

### Step 7: Test App

```powershell
adb shell am start -n com.lessonplanner.browser/.MainActivity
```

The app should now:
1. Launch successfully
2. Show UserSelector (not blank screen)
3. Be able to connect to backend and load users

---

## Alternative: Check for JavaScript Errors

If the blank screen persists after fixing the API URL, check for JavaScript errors:

```powershell
adb logcat -d | Select-String -Pattern "Console|ReferenceError|TypeError|Uncaught|undefined is not" -Context 3,3
```

Common causes:
- Frontend bundle not loading
- JavaScript syntax errors
- Missing dependencies

---

## Quick Diagnostic Commands

**Check if backend is accessible:**
```powershell
curl http://localhost:8000/api/health
```

**View app logs:**
```powershell
adb logcat -d | Select-String -Pattern "lessonplanner|browser|ERROR|Exception" | Select-Object -Last 50
```

**Check if app is running:**
```powershell
adb shell dumpsys activity activities | Select-String -Pattern "lessonplanner|browser"
```

---

**Most likely fix:** Configure API URL with PC's IP address (Steps 1-7 above)

