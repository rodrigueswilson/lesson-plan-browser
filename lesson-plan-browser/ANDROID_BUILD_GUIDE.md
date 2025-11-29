# Android Build Guide

## Prerequisites

### 1. Android Development Environment

#### Required Tools
- **Java JDK** (version 17 or higher)
  - Download from: https://adoptium.net/
  - Set `JAVA_HOME` environment variable

- **Android SDK**
  - Install Android Studio: https://developer.android.com/studio
  - Or install SDK command-line tools only
  - Set `ANDROID_HOME` environment variable
  - Add to PATH: `$ANDROID_HOME/platform-tools` and `$ANDROID_HOME/tools/bin`

- **Rust Android Targets**
  ```bash
  rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android
  ```

#### Verify Installation
```bash
# Check Java
java -version  # Should be 17+

# Check Android SDK
adb version

# Check Rust targets
rustup target list | grep android
```

### 2. Tauri Android Dependencies

Tauri v2 requires Android NDK. The Tauri CLI will prompt you to install it if missing.

## Build Process

### Quick Build
```bash
cd lesson-plan-browser
.\build-android.ps1
```

### Manual Build Steps

1. **Navigate to frontend directory**
   ```bash
   cd lesson-plan-browser/frontend
   ```

2. **Install dependencies (if not already done)**
   ```bash
   npm install
   ```

3. **Build Android APK**
   ```bash
   npm run android:build
   ```

   This command will:
   - Build the React frontend
   - Compile Rust code for Android
   - Generate APK file

4. **Build for Development (Debug APK)**
   ```bash
   npm run android:dev
   ```

## Output Location

After successful build:
- **Release APK**: `frontend/src-tauri/target/android/app/build/outputs/apk/release/app-release.apk`
- **Debug APK**: `frontend/src-tauri/target/android/app/build/outputs/apk/debug/app-debug.apk`

## Installation on Tablet

### Method 1: USB Connection
```bash
# Connect tablet via USB (enable USB debugging)
adb devices  # Verify device is connected

# Install APK
adb install frontend/src-tauri/target/android/app/build/outputs/apk/release/app-release.apk
```

### Method 2: Transfer APK
1. Copy APK to tablet (via USB, email, cloud storage)
2. Enable "Install from unknown sources" on tablet
3. Open APK file on tablet and install

### Method 3: Build Script with Auto-Install
```bash
# After build completes, if device is connected:
adb install -r frontend/src-tauri/target/android/app/build/outputs/apk/release/app-release.apk
```

## Troubleshooting

### Issue: "Android SDK not found"

**Solution:**
1. Install Android Studio
2. Set `ANDROID_HOME` environment variable:
   ```powershell
   # Windows PowerShell
   [System.Environment]::SetEnvironmentVariable('ANDROID_HOME', 'C:\Users\YourName\AppData\Local\Android\Sdk', 'User')
   ```
3. Restart terminal/IDE

### Issue: "Java/JDK not found"

**Solution:**
1. Install JDK 17+
2. Set `JAVA_HOME` environment variable:
   ```powershell
   [System.Environment]::SetEnvironmentVariable('JAVA_HOME', 'C:\Program Files\Java\jdk-17', 'User')
   ```
3. Add to PATH: `%JAVA_HOME%\bin`
4. Restart terminal

### Issue: "Rust Android targets not installed"

**Solution:**
```bash
rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android
```

### Issue: Build takes too long

**Solution:**
- First build always takes 10-20 minutes (compiles Rust for Android)
- Subsequent builds are faster (~2-5 minutes)
- Use `android:dev` for faster debug builds

### Issue: APK installation fails

**Solution:**
1. Check Android version (min: Android 7.0 / API 24)
2. Enable "Install from unknown sources" in tablet settings
3. Uninstall previous version first: `adb uninstall com.lessonplanner.browser`

### Issue: App crashes on launch

**Solution:**
- Check logs: `adb logcat | grep -i lesson`
- Ensure Phase 9 (standalone architecture) is implemented for full functionality
- PC version uses HTTP backend, Android needs local database (Phase 9)

## Testing on Emulator

1. **Create Android Emulator**
   - Open Android Studio → AVD Manager
   - Create new virtual device
   - Select tablet form factor (recommended: 10" tablet)
   - API Level 24+ (Android 7.0+)

2. **Start Emulator**
   ```bash
   emulator -avd YourAVDName
   ```

3. **Build and Install**
   ```bash
   npm run android:dev  # Faster for testing
   adb install frontend/src-tauri/target/android/app/build/outputs/apk/debug/app-debug.apk
   ```

## Configuration

### Android Permissions

Already configured in `tauri.conf.json`:
- `INTERNET` - For WiFi sync (future)
- `READ_EXTERNAL_STORAGE` - For local JSON files
- `WRITE_EXTERNAL_STORAGE` - For local JSON files
- `ACCESS_NETWORK_STATE` - For network detection

### SDK Versions

- **Min SDK**: 24 (Android 7.0)
- **Target SDK**: 34 (Android 14)
- **Compile SDK**: 34

## Next Steps

After successful APK build:

1. **Test on Tablet** - Install and verify app launches
2. **Phase 8** - Optimize bundle size
3. **Phase 9** - Implement standalone architecture (REQUIRED for full functionality)

**Note:** App will launch but full functionality requires Phase 9 (local database implementation).

