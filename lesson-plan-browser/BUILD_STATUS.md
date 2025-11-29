# Android Build Status

## Current Status

**Date:** 2025-01-27

### Environment Check ✅
- [x] Tablet connected via USB (Device ID: R52Y90L71YP)
- [x] ADB working (version 1.0.41)
- [x] Android SDK installed
- [x] Rust Android targets installed (aarch64, armv7, i686, x86_64)
- [ ] Java JDK - Not in PATH (may use Android Studio's Java)

### Next Steps

#### 1. Build Android APK

**Command:**
```powershell
cd D:\LP\lesson-plan-browser\frontend
npm run android:build
```

**Expected Time:** 10-20 minutes (first build)

**Output Location:**
- Release: `frontend\src-tauri\target\android\app\build\outputs\apk\release\app-release.apk`
- Debug: `frontend\src-tauri\target\android\app\build\outputs\apk\debug\app-debug.apk`

**Note:** If Java is not found, you may need to:
- Install Java JDK 17+ and add to PATH, OR
- Ensure Android Studio is installed (it includes Java)

#### 2. Configure Backend for Tablet Access

**Backend Script Available:** `start-backend-all-interfaces.bat`
- This binds backend to `0.0.0.0:8000` (accessible from network)
- Find your PC IP: `ipconfig` (look for IPv4 Address)

**Start Backend:**
```powershell
cd D:\LP
.\start-backend-all-interfaces.bat
```

#### 3. Update API Config for Tablet

**Option A: Environment Variable (Recommended)**

Create `.env` file in `lesson-plan-browser/frontend/`:
```
VITE_API_BASE_URL=http://YOUR_PC_IP:8000/api
```

Replace `YOUR_PC_IP` with your actual IP (e.g., `192.168.1.100`)

**Option B: Edit Config File**

Edit `lesson-plan-browser/frontend/src/lib/config.ts`:
```typescript
// Line 18-19, change from:
return 'http://localhost:8000/api';
// To:
return 'http://YOUR_PC_IP:8000/api';
```

**Then rebuild:** `npm run android:build`

#### 4. Install APK on Tablet

**Using Script:**
```powershell
cd D:\LP\lesson-plan-browser
.\install-android-app.ps1
```

**Or Manual:**
```powershell
adb install -r "frontend\src-tauri\target\android\app\build\outputs\apk\release\app-release.apk"
```

#### 5. Launch and Test

```powershell
adb shell am start -n com.lessonplanner.browser/.MainActivity
```

Or tap app icon on tablet.

---

## Important Notes

1. **Network Required:** Tablet and PC must be on same WiFi network
2. **Backend Must Run:** Start backend before testing app
3. **First Build is Slow:** 10-20 minutes - be patient
4. **Phase 9 Pending:** Full offline functionality requires standalone architecture

---

## Troubleshooting

**Java Not Found:**
- Install JDK 17+ from https://adoptium.net/
- Set `JAVA_HOME` environment variable
- Restart terminal

**Build Fails:**
- Check `ANDROID_HOME` is set
- Verify Rust targets: `rustup target list | Select-String android`
- Check Tauri CLI: `npx @tauri-apps/cli android --help`

**App Can't Connect:**
- Verify backend is running: `curl http://localhost:8000/api/health`
- Check PC IP address matches API config
- Ensure firewall allows port 8000
- Verify tablet and PC on same WiFi

---

**Ready to build? Run:** `cd D:\LP\lesson-plan-browser\frontend && npm run android:build`

