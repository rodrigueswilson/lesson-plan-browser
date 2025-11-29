# Quick Docker Build Solution

The Docker approach is complex due to native module dependencies. Here's a simpler solution:

## Option 1: Manual APK Copy (Fastest)

Since the frontend builds correctly locally with the new `index-TiTynWQK.js` file:

1. **Use the existing working APK** - it contains the correct assets
2. **Force cache invalidation** by changing the version number
3. **Install fresh APK** on device

```bash
# Step 1: Update version (already done to 1.0.1)
# Step 2: Clear all device caches
adb uninstall com.lessonplanner.bilingual
adb shell pm clear com.google.android.webview

# Step 3: Restart device (physically power off/on)

# Step 4: Install APK
adb install d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk

# Step 5: Verify it loads the new file
adb logcat -d | Select-String "index-.*\.js" | Select-Object -Last 5
```

## Option 2: GitHub Actions Build

Use GitHub Actions for clean builds:

```yaml
# .github/workflows/android-build.yml
name: Android Build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
          target: aarch64-linux-android
      - name: Setup Android SDK
        run: |
          wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
          unzip commandlinetools-linux-*.zip
          mkdir -p $ANDROID_SDK_ROOT/cmdline-tools/latest
          mv cmdline-tools $ANDROID_SDK_ROOT/cmdline-tools/latest
          echo "y" | $ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager --sdk_root=$ANDROID_SDK_ROOT "platforms;android-33" "build-tools;33.0.2" "ndk;25.1.8937393"
      - name: Build frontend
        run: |
          cd frontend
          npm install
          npm run build:skip-check
      - name: Build APK
        run: |
          cd frontend/src-tauri
          cargo tauri android build
      - name: Upload APK
        uses: actions/upload-artifact@v3
        with:
          name: app-arm64-debug.apk
          path: frontend/src-tauri/gen/android/app/build/outputs/apk/arm64/debug/app-arm64-debug.apk
```

## Option 3: Alternative Build Environment

- **WSL2** (Windows Subsystem for Linux)
- **Linux VM** 
- **Cloud build service** (CircleCI, GitLab CI)

## Recommendation

Try **Option 1** first - the APK should work with the version bump. If that fails, use **Option 2** (GitHub Actions) for reliable clean builds.

The core issue is Tauri's aggressive caching on Windows. Docker works but requires significant configuration to handle cross-platform native modules.
