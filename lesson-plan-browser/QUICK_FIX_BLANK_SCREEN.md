# Quick Fix: Blank White Screen

## Problem
App shows blank white screen on tablet.

## Cause
App is trying to connect to `localhost:8000` which doesn't exist on Android tablet. The `UserSelector` component fails to load users, causing a blank screen.

## Solution (3 Steps)

### Step 1: Create .env File with PC IP

Create `lesson-plan-browser/frontend/.env`:
```
VITE_API_BASE_URL=http://YOUR_PC_IP:8000/api
```

Replace `YOUR_PC_IP` with your PC's IP address (found via `ipconfig`).

### Step 2: Rebuild and Reinstall

```powershell
cd D:\LP\lesson-plan-browser\frontend
npm run build:skip-check
npm run android:build
```

Then install:
```powershell
cd D:\LP\lesson-plan-browser
.\install-android-app.ps1
```

### Step 3: Start Backend

```powershell
cd D:\LP
.\start-backend-all-interfaces.bat
```

**Ensure:**
- PC and tablet on same WiFi
- Backend running before launching app

---

The blank screen should be resolved after these steps!

