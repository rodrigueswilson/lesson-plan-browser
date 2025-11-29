# Test Results & Debugging Log

## Session: 2025-11-26 (Android USB Tunnel Fix)

### Issue
The Android app on the physical tablet was persistently connecting to `192.168.12.153:8000` and failing with "Failed to fetch", even after updating `api.ts` to use `localhost:8000` (via `adb reverse`). Logs showed the app was using an old version of the JS bundle, indicating a caching issue during the build process.

### Actions Taken
1.  **Nuclear Clean:**
    *   Deleted `gen/android` directory.
    *   Ran `npx tauri android init` to regenerate the project.
    *   Applied `apply-android-network-fix.ps1`.
2.  **Force Asset Update:**
    *   Updated `frontend/src/lib/api.ts` to force `http://localhost:8000/api` when Android is detected (ignoring other logic).
    *   Rebuilt frontend (`npm run build:skip-check`).
    *   **Manually copied** `frontend/dist/*` to `frontend/src-tauri/gen/android/app/src/main/assets` to ensure the fresh bundle is present before the Gradle build.

### Current Status (End of Day)
*   The Android project is initialized and clean.
*   The `assets` folder contains the latest build (verified).
*   **Next Step:** Build the APK using Gradle, install it, and verify if it finally picks up the `localhost` URL.

### Next Command to Run
```powershell
cd d:\LP\frontend\src-tauri\gen\android
$env:CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER = "C:\Users\rodri\AppData\Local\Android\Sdk\ndk\29.0.14206865\toolchains\llvm\prebuilt\windows-x86_64\bin\aarch64-linux-android30-clang.cmd"
.\gradlew.bat assembleArm64Debug -x rustBuildArm64Debug -x rustBuildArmDebug -x rustBuildUniversalDebug
# Then install:
# adb -s R52Y90L71YP install -r app\build\outputs\apk\arm64\debug\app-arm64-debug.apk
```

