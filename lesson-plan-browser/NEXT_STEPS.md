# Next Steps: Build and Install on Tablet

## ✅ Completed Preparations

1. **Environment Verified:**
   - ✅ Tablet connected (Device ID: R52Y90L71YP)
   - ✅ ADB working
   - ✅ Android SDK installed
   - ✅ Rust Android targets installed

2. **Documentation Created:**
   - ✅ `TABLET_INSTALLATION_GUIDE.md` - Full installation guide
   - ✅ `QUICK_START_TABLET.md` - Quick reference
   - ✅ `BUILD_STATUS.md` - Build status tracker
   - ✅ `install-android-app.ps1` - Installation script

3. **Backend Configuration Ready:**
   - ✅ `start-backend-all-interfaces.bat` - Backend script for network access

---

## 🚀 Ready to Build and Install

### Step 1: Build Android APK

**Run this command:**
```powershell
cd D:\LP\lesson-plan-browser\frontend
npm run android:build
```

**Expected:**
- First build: 10-20 minutes (compiles Rust for Android)
- Output: APK in `src-tauri\target\android\app\build\outputs\apk\release\`

**If Java error occurs:**
- Install JDK 17+ from https://adoptium.net/
- OR ensure Android Studio is installed (includes Java)

### Step 2: Get Your PC's IP Address

**Find your IP:**
```powershell
ipconfig
```

Look for "IPv4 Address" (e.g., `192.168.1.100`)

**Save this IP** - you'll need it for Step 3.

### Step 3: Configure API URL for Tablet

**Option A: Environment Variable (Recommended)**

Create `.env` file in `lesson-plan-browser/frontend/`:
```
VITE_API_BASE_URL=http://YOUR_PC_IP:8000/api
```

Replace `YOUR_PC_IP` with your actual IP from Step 2.

**Then rebuild:**
```powershell
npm run android:build
```

**Option B: Edit Config File**

Edit `lesson-plan-browser/frontend/src/lib/config.ts`:
- Update the Android detection to use network IP
- See `TABLET_INSTALLATION_GUIDE.md` for details

### Step 4: Start Backend (All Interfaces)

**Start backend that listens on network:**
```powershell
cd D:\LP
.\start-backend-all-interfaces.bat
```

This binds to `0.0.0.0:8000` so tablet can connect.

### Step 5: Install APK on Tablet

**Using the script:**
```powershell
cd D:\LP\lesson-plan-browser
.\install-android-app.ps1
```

**Or manually:**
```powershell
adb install -r "frontend\src-tauri\target\android\app\build\outputs\apk\release\app-release.apk"
```

### Step 6: Launch App

```powershell
adb shell am start -n com.lessonplanner.browser/.MainActivity
```

Or tap the app icon on tablet.

### Step 7: Test

- [ ] App launches
- [ ] User selector appears
- [ ] Can connect to backend
- [ ] Week view loads
- [ ] Can navigate to lesson detail
- [ ] Can enter Lesson Mode

---

## ⚠️ Important Notes

1. **Network Required:**
   - Tablet and PC must be on **same WiFi network**
   - Backend must be running before testing

2. **First Build is Slow:**
   - 10-20 minutes for first build
   - Subsequent builds are faster

3. **Phase 9 Pending:**
   - Full offline functionality requires standalone architecture
   - Current version requires network connection to PC backend

---

## 📋 Quick Command Reference

```powershell
# Build APK
cd D:\LP\lesson-plan-browser\frontend
npm run android:build

# Get PC IP
ipconfig | Select-String -Pattern "IPv4"

# Start backend
cd D:\LP
.\start-backend-all-interfaces.bat

# Install APK
cd D:\LP\lesson-plan-browser
.\install-android-app.ps1

# Launch app
adb shell am start -n com.lessonplanner.browser/.MainActivity

# View logs
adb logcat | Select-String -Pattern "lesson|browser|tauri"
```

---

## 🐛 Troubleshooting

See `TABLET_INSTALLATION_GUIDE.md` for detailed troubleshooting.

**Quick fixes:**
- No device: Check USB cable, enable USB debugging
- Build fails: Check Java, Android SDK, Rust targets
- Can't connect: Verify same WiFi, check firewall, verify IP address

---

**Ready to start? Begin with Step 1: Build Android APK**

