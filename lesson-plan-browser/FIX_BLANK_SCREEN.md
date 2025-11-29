# Fix: Blank White Screen on Tablet

## Problem Identified

**Symptom:** App launches but shows blank white screen

**Root Cause:** The app is trying to connect to `localhost:8000` which doesn't work on Android. The `UserSelector` component tries to fetch users on mount, fails, and this causes the blank screen.

## Quick Fix (3 Steps)

### Step 1: Get Your PC's IP Address

Run this command:
```powershell
ipconfig | Select-String -Pattern "IPv4"
```

Look for an IP address like `192.168.x.x` or `10.x.x.x`. Save this IP.

### Step 2: Create .env File

Create file: `lesson-plan-browser/frontend/.env`

With this content:
```
VITE_API_BASE_URL=http://YOUR_PC_IP:8000/api
```

Replace `YOUR_PC_IP` with the IP from Step 1.

**Example:**
```
VITE_API_BASE_URL=http://192.168.1.100:8000/api
```

### Step 3: Rebuild and Reinstall

```powershell
cd D:\LP\lesson-plan-browser\frontend
npm run build:skip-check
npm run android:build
cd ..\..
.\install-android-app.ps1
```

### Step 4: Start Backend

```powershell
cd D:\LP
.\start-backend-all-interfaces.bat
```

**Important:** 
- Backend must be running before launching app
- PC and tablet must be on same WiFi network

---

## Why This Fixes It

1. **Current Issue:** App uses `localhost:8000` which doesn't exist on Android
2. **Fix:** `.env` file sets `VITE_API_BASE_URL` to your PC's IP address
3. **Result:** App can now connect to backend running on your PC

---

## After Fix

The app should:
- ✅ Show UserSelector instead of blank screen
- ✅ Load users from backend
- ✅ Function normally

---

**Next:** Follow Steps 1-4 above to fix the blank screen!

