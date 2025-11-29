# Tablet Installation & Testing Guide

## Prerequisites Checklist

Before building and installing on your tablet, verify the following:

### 1. Development Environment
- [ ] **Java JDK 17+** installed
  - Verify: `java -version`
  - Set `JAVA_HOME` environment variable
  
- [ ] **Android SDK** installed (via Android Studio or command-line tools)
  - Verify: `adb version`
  - Set `ANDROID_HOME` environment variable
  - Add to PATH: `$ANDROID_HOME/platform-tools` and `$ANDROID_HOME/tools/bin`

- [ ] **Rust Android Targets** installed
  ```powershell
  rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android
  ```
  - Verify: `rustup target list | Select-String android`

- [ ] **Node.js dependencies** installed
  ```powershell
  cd lesson-plan-browser\frontend
  npm install
  ```

### 2. Tablet Setup
- [ ] **Enable Developer Mode** on tablet
  - Go to Settings → About Tablet → Tap "Build Number" 7 times
  
- [ ] **Enable USB Debugging**
  - Settings → Developer Options → Enable "USB Debugging"
  
- [ ] **Enable "Install from Unknown Sources"**
  - Settings → Security → Allow installation from unknown sources
  
- [ ] **Connect tablet via USB** to your PC
  - Verify connection: `adb devices`
  - Should show device ID (e.g., `abc123def456    device`)

### 3. Backend Server (for testing)
- [ ] **Backend running** on `http://localhost:8000`
  - The tablet app will need to connect to your PC's backend
  - Ensure PC and tablet are on the same WiFi network

---

## Step-by-Step Installation Process

### Step 1: Verify Environment

Run these commands to verify everything is set up:

```powershell
# Navigate to project root
cd D:\LP

# Check Java
java -version

# Check Android SDK
adb version

# Check connected devices
adb devices

# Check Rust Android targets
rustup target list | Select-String android
```

### Step 2: Build Android APK

**Option A: Using Build Script (Recommended)**

```powershell
cd D:\LP\lesson-plan-browser
.\build-android.ps1
```

**Option B: Manual Build**

```powershell
cd D:\LP\lesson-plan-browser\frontend
npm run android:build
```

**Expected Output:**
- Build process takes 10-20 minutes on first build
- Subsequent builds are faster (~2-5 minutes)
- APK location: `frontend\src-tauri\target\android\app\build\outputs\apk\release\app-release.apk`

### Step 3: Install APK on Tablet

**Option A: Using Install Script**

```powershell
cd D:\LP
.\install-android-app.ps1
```

Note: Update the APK path in `install-android-app.ps1` to match the lesson-plan-browser location:
```
$apkPath = "D:\LP\lesson-plan-browser\frontend\src-tauri\target\android\app\build\outputs\apk\release\app-release.apk"
```

**Option B: Manual Installation via ADB**

```powershell
# Verify device is connected
adb devices

# Install APK
adb install -r "D:\LP\lesson-plan-browser\frontend\src-tauri\target\android\app\build\outputs\apk\release\app-release.apk"
```

**Option C: Manual Transfer**

1. Copy APK file to tablet (via USB, email, or cloud storage)
2. On tablet, navigate to APK file location
3. Tap APK file to install
4. Follow on-screen prompts

### Step 4: Configure Network Connection

**Important:** The tablet app needs to connect to your PC's backend server.

1. **Find your PC's IP address:**
   ```powershell
   ipconfig
   # Look for IPv4 address (e.g., 192.168.1.100)
   ```

2. **Update API configuration** (if needed):
   - Currently, the app is configured to use `http://localhost:8000`
   - For tablet testing, you may need to update the backend URL to your PC's IP
   - Check: `lesson-plan-browser\frontend\src\lib\config.ts`

3. **Ensure PC and tablet are on same WiFi network**

4. **Configure backend to accept connections from tablet:**
   - Backend should bind to `0.0.0.0:8000` (not just `localhost:8000`)
   - Check backend startup command or configuration

### Step 5: Launch and Test

1. **Launch app on tablet:**
   ```powershell
   adb shell am start -n com.lessonplanner.browser/.MainActivity
   ```

2. **Or manually:** Tap the "Lesson Plan Browser" icon on tablet

3. **Initial Testing:**
   - App should launch without errors
   - User selector should appear
   - Browser view should load (if backend is accessible)

---

## Testing Checklist

### Basic Functionality
- [ ] App launches without crashes
- [ ] User selector displays correctly
- [ ] Can select a user
- [ ] Week view displays (if backend connected)
- [ ] Can navigate between views
- [ ] Lesson detail view works
- [ ] Can enter Lesson Mode
- [ ] Lesson Mode timer functions
- [ ] Can exit Lesson Mode and return to browser

### Network Connection
- [ ] App connects to backend API
- [ ] Data loads from backend (users, plans, schedule)
- [ ] API requests succeed (check backend logs)
- [ ] No network errors in app logs

### Tablet-Specific
- [ ] Touch interactions work smoothly
- [ ] UI scales correctly on tablet screen
- [ ] Keyboard input works (if needed)
- [ ] App responds to tablet orientation changes (if supported)

---

## Troubleshooting

### Issue: ADB Device Not Found

**Symptoms:** `adb devices` shows no devices

**Solutions:**
1. Check USB cable (try different cable)
2. Ensure USB debugging is enabled on tablet
3. Check if tablet drivers are installed on PC
4. Try different USB port
5. Revoke USB debugging authorizations on tablet and reconnect

### Issue: Build Fails with "Android SDK not found"

**Solutions:**
1. Install Android Studio or command-line tools
2. Set `ANDROID_HOME` environment variable:
   ```powershell
   [System.Environment]::SetEnvironmentVariable('ANDROID_HOME', 'C:\Users\YourName\AppData\Local\Android\Sdk', 'User')
   ```
3. Restart terminal/IDE after setting environment variables

### Issue: Build Fails with "Java/JDK not found"

**Solutions:**
1. Install JDK 17+ from https://adoptium.net/
2. Set `JAVA_HOME` environment variable:
   ```powershell
   [System.Environment]::SetEnvironmentVariable('JAVA_HOME', 'C:\Program Files\Java\jdk-17', 'User')
   ```
3. Add to PATH: `%JAVA_HOME%\bin`
4. Restart terminal

### Issue: Build Fails with Rust Android Targets Missing

**Solution:**
```powershell
rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android
```

### Issue: APK Installation Fails

**Common Causes:**
- Previous version installed: `adb uninstall com.lessonplanner.browser`
- Architecture mismatch: Ensure APK matches tablet architecture (usually ARM64)
- Storage full on tablet
- Unknown sources not enabled

### Issue: App Crashes on Launch

**Diagnosis:**
```powershell
# View app logs
adb logcat | Select-String -Pattern "lesson|browser|tauri" -CaseSensitive:$false
```

**Common Causes:**
- Backend not accessible (app tries to connect to localhost)
- Missing permissions
- Corrupted installation: Uninstall and reinstall

### Issue: Cannot Connect to Backend API

**Symptoms:** Network errors, no data loading

**Solutions:**
1. **Check backend is running:**
   ```powershell
   curl http://localhost:8000/api/health
   ```

2. **Verify backend binds to all interfaces:**
   - Backend should listen on `0.0.0.0:8000`, not just `127.0.0.1:8000`
   - Check backend startup command

3. **Update API URL in app config:**
   - Change from `http://localhost:8000` to `http://YOUR_PC_IP:8000`
   - Edit: `lesson-plan-browser\frontend\src\lib\config.ts`

4. **Check firewall:**
   - Allow port 8000 through Windows Firewall
   - Ensure tablet can reach PC on network

5. **Verify same WiFi network:**
   - PC and tablet must be on the same local network

### Issue: Phase 9 Not Implemented (Standalone Mode)

**Current Status:** The app is configured for HTTP backend mode (PC version).

**For full tablet functionality (offline mode):**
- Phase 9 (Standalone Architecture) needs to be implemented
- This includes local database queries, JSON file storage, and sync mechanism
- See `PROJECT_STATUS.md` for details

**Workaround for Testing:**
- Keep tablet connected to same WiFi as PC
- Ensure backend is running and accessible
- App will work but requires network connection

---

## Next Steps After Successful Installation

1. **Test Core Features**
   - Follow `TESTING_CHECKLIST.md` for comprehensive testing
   - Test browser navigation
   - Test Lesson Mode functionality
   - Test timer and session management

2. **Performance Testing**
   - Check app responsiveness
   - Test with real lesson plan data
   - Monitor memory usage

3. **Phase 9 Implementation** (Required for Production)
   - Implement local database queries
   - Add local JSON file storage
   - Create sync mechanism (WiFi + USB)
   - Test offline functionality

---

## Quick Reference

### Key Commands

```powershell
# Check devices
adb devices

# Install APK
adb install -r "path\to\app-release.apk"

# Uninstall app
adb uninstall com.lessonplanner.browser

# View logs
adb logcat | Select-String -Pattern "lesson"

# Launch app
adb shell am start -n com.lessonplanner.browser/.MainActivity

# Find PC IP address
ipconfig
```

### Key File Locations

- **APK (Release):** `lesson-plan-browser\frontend\src-tauri\target\android\app\build\outputs\apk\release\app-release.apk`
- **APK (Debug):** `lesson-plan-browser\frontend\src-tauri\target\android\app\build\outputs\apk\debug\app-debug.apk`
- **Build Script:** `lesson-plan-browser\build-android.ps1`
- **Install Script:** `install-android-app.ps1` (needs path update)

### Package Identifier

- **App ID:** `com.lessonplanner.browser`
- **Main Activity:** `com.lessonplanner.browser.MainActivity`

---

## Notes

- First build takes 10-20 minutes (compiles Rust for Android)
- Subsequent builds are faster (~2-5 minutes)
- Use debug APK for faster testing: `npm run android:dev`
- Tablet must be on same WiFi network as PC for backend access
- Phase 9 (Standalone) is required for full offline tablet functionality

---

**Last Updated:** 2025-01-27

