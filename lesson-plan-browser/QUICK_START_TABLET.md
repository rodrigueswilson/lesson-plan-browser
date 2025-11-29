# Quick Start: Install App on Tablet

## Prerequisites (One-Time Setup)

1. **Java JDK 17+** - Install and set `JAVA_HOME`
2. **Android SDK** - Install Android Studio or command-line tools, set `ANDROID_HOME`
3. **Rust Android Targets:**
   ```powershell
   rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android
   ```

4. **Tablet Setup:**
   - Enable Developer Mode (Settings → About → Tap Build Number 7x)
   - Enable USB Debugging (Settings → Developer Options)
   - Connect tablet via USB

## Installation Steps

### Step 1: Verify Environment
```powershell
cd D:\LP
adb devices  # Should show your tablet
java -version  # Should show Java 17+
```

### Step 2: Build APK
```powershell
cd D:\LP\lesson-plan-browser
.\build-android.ps1
```

**First build takes 10-20 minutes.** Subsequent builds are faster.

### Step 3: Install on Tablet

**Method A: ADB Install (Recommended)**
```powershell
cd D:\LP\lesson-plan-browser\frontend
$apkPath = "src-tauri\target\android\app\build\outputs\apk\release\app-release.apk"
adb install -r $apkPath
```

**Method B: Transfer APK Manually**
1. Copy APK from `src-tauri\target\android\app\build\outputs\apk\release\app-release.apk`
2. Transfer to tablet (email, USB, cloud)
3. Tap APK file on tablet to install

### Step 4: Configure Backend Connection

**Current Issue:** App uses `localhost:8000`, which won't work from tablet.

**Option 1: Use Environment Variable (Recommended for Testing)**

1. Find your PC's IP address:
   ```powershell
   ipconfig  # Look for IPv4 Address (e.g., 192.168.1.100)
   ```

2. Start backend bound to all interfaces:
   ```powershell
   cd D:\LP
   # Backend should listen on 0.0.0.0:8000 (not just localhost)
   # Check your backend startup command/script
   ```

3. Update API config for tablet testing:
   - Create `.env` file in `lesson-plan-browser/frontend/`:
     ```
     VITE_API_BASE_URL=http://YOUR_PC_IP:8000/api
     ```
   - Replace `YOUR_PC_IP` with your actual IP (e.g., `192.168.1.100`)
   - Rebuild: `npm run android:build`

**Option 2: Modify Config Temporarily**

Edit `lesson-plan-browser/frontend/src/lib/config.ts`:
```typescript
// Change line 18-19 from:
return 'http://localhost:8000/api';

// To (replace with your PC IP):
return 'http://192.168.1.100:8000/api';
```

Then rebuild: `npm run android:build`

### Step 5: Launch App

```powershell
adb shell am start -n com.lessonplanner.browser/.MainActivity
```

Or tap the app icon on tablet.

## Testing Checklist

- [ ] App launches without errors
- [ ] User selector appears
- [ ] Can connect to backend (check backend logs)
- [ ] Week view loads data
- [ ] Can navigate to lesson detail
- [ ] Can enter Lesson Mode
- [ ] Timer works in Lesson Mode
- [ ] Can exit Lesson Mode

## Troubleshooting

**No devices found:**
```powershell
adb devices  # Should show device
# If not: Check USB cable, enable USB debugging, install drivers
```

**Build fails:**
- Check `ANDROID_HOME` and `JAVA_HOME` are set
- Restart terminal after setting environment variables
- Verify Rust targets: `rustup target list | Select-String android`

**App can't connect to backend:**
- Ensure PC and tablet are on same WiFi network
- Check backend is running: `curl http://localhost:8000/api/health`
- Verify backend listens on `0.0.0.0:8000` (not just `127.0.0.1`)
- Check Windows Firewall allows port 8000
- Verify API URL in app config matches your PC IP

**View logs:**
```powershell
adb logcat | Select-String -Pattern "lesson|browser|tauri"
```

## File Locations

- **Release APK:** `lesson-plan-browser\frontend\src-tauri\target\android\app\build\outputs\apk\release\app-release.apk`
- **Debug APK:** `lesson-plan-browser\frontend\src-tauri\target\android\app\build\outputs\apk\debug\app-debug.apk`

## Important Notes

1. **First build is slow** (10-20 min) - compiles Rust for Android
2. **Network required** - Tablet must connect to PC backend (same WiFi)
3. **Phase 9 pending** - Full offline functionality requires standalone architecture implementation

---

For detailed instructions, see `TABLET_INSTALLATION_GUIDE.md`

