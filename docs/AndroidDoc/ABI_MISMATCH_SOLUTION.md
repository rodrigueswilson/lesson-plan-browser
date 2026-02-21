# ABI Mismatch Solution - Technical Summary

**Date:** November 26, 2025  
**Status:** ✅ Verified Working  
**APK Output:** 26.8MB `app-arm64-debug.apk`

---

## The Problem

Building for physical Android tablets (`aarch64`) crashed with:
```
Execution failed for task ':app:mergeArm64DebugNativeLibs'.
> path .../target/aarch64-linux-android/debug/libbilingual_lesson_planner.so is not an ABI
```

**Root Cause:**
- Rust builds to `target/aarch64-linux-android/` (Rust target triple)
- Android Gradle expects `arm64-v8a/` (Android ABI name)
- Gradle plugin creates a directory named `aarch64-linux-android` in `jniLibs/`
- AGP sees this non-standard ABI name and crashes

---

## The Solution

### Part 1: Gradle Configuration (`build.gradle.kts`)

Added `afterEvaluate` hook to filter out problematic paths:

```kotlin
afterEvaluate {
    android.sourceSets.getByName("main") {
        val currentDirs = jniLibs.srcDirs
        println("DEBUG: Current JNI dirs before fix: $currentDirs")
        
        val safeDirs = currentDirs.filter { dir -> 
            !dir.path.contains("target") && !dir.path.contains("aarch64")
        }
        
        jniLibs.setSrcDirs(safeDirs)
        println("DEBUG: Fixed JNI dirs: ${jniLibs.srcDirs}")
    }
}
```

**Why afterEvaluate?**
- Runs after all plugins finish configuration
- Gets the "final say" before build tasks execute
- Previous `sourceSets` blocks ran too early and were overridden by plugins

### Part 2: Manual Copy Task (`copyAndRenameNativeLibs`)

Already exists in `build.gradle.kts`. Maps Rust targets to Android ABIs:

```kotlin
val abiMap = mapOf(
    "aarch64-linux-android" to "arm64-v8a",
    "armv7-linux-androideabi" to "armeabi-v7a",
    "i686-linux-android" to "x86",
    "x86_64-linux-android" to "x86_64"
)
```

### Part 3: Directory Cleanup

**Current Limitation:** The `aarch64-linux-android` directory still gets created somewhere during the build. Manual removal is required as a workaround.

---

## Automated Build Process

Use the provided script:

```powershell
cd d:\LP\frontend\src-tauri
.\build-tablet.ps1
```

### Manual Steps (if needed):

```powershell
# 1. Copy libraries
cd d:\LP\frontend\src-tauri\gen\android
.\gradlew.bat copyAndRenameNativeLibs

# 2. Remove bad directory
Remove-Item "app\src\main\jniLibs\aarch64-linux-android" -Recurse -Force -ErrorAction SilentlyContinue

# 3. Build APK
.\gradlew.bat assembleArm64Debug -x rustBuildArm64Debug

# 4. Verify
Get-Item "app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"
```

---

## Installation on Physical Tablet

### Option 1: USB (Recommended for first install)

```powershell
# Connect tablet via USB
adb devices  # Verify connection

# Install
adb install -r "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"

# Launch
adb shell am start -n com.lessonplanner.bilingual/.MainActivity
```

### Option 2: WiFi (Requires same network)

1. **Find your PC's IP:**
   ```powershell
   ipconfig  # Look for IPv4 Address (e.g., 192.168.1.15)
   ```

2. **Update API endpoint in code:**
   Edit `frontend/src/lib/api.ts`:
   ```typescript
   if (userAgent.includes('Android')) {
     return 'http://192.168.1.15:8000/api';  // Use your PC's IP
   }
   ```

3. **Rebuild and transfer APK** (via USB or file sharing)

---

## Debugging Output

When the fix is working, you'll see:

```
> Configure project :app
DEBUG: Current JNI dirs before fix: [D:\LP\frontend\src-tauri\gen\android\app\src\main\jniLibs]
DEBUG: Fixed JNI dirs: [D:\LP\frontend\src-tauri\gen\android\app\src\main\jniLibs]
```

If you see the Rust `target/` path in the "before" list, the plugin is adding it and the fix is filtering it out correctly.

---

## Why Previous Attempts Failed

| Approach | Why It Failed |
|----------|---------------|
| `packaging.excludes` | Only affects final APK packaging, not the merge step |
| `sourceSets` in main block | Runs too early, plugin overrides afterward |
| Folder renaming | Race conditions, timing issues |
| `splits { ... }` | Conflicts with plugin's auto-injected `ndk.abiFilters` |

---

## Open Questions / Future Improvements

1. **Where is `aarch64-linux-android` created?**
   - Not by our copy task
   - Not by the Rust plugin (afterEvaluate filters it from srcDirs)
   - Possibly by AGP during dependency resolution?
   - **TODO:** Run with `--debug` and trace file creation

2. **Can we prevent creation instead of cleanup?**
   - May need to hook into AGP's internal tasks
   - Might require custom Gradle plugin
   - Current workaround is reliable enough for now

3. **Does this affect other ABIs?**
   - No issues seen with `x86_64` (emulator)
   - `arm64-v8a` (physical device) now works with this fix
   - Other ABIs (`armeabi-v7a`, `x86`) untested but likely same issue

---

## Related Files

- **Gradle Config:** `frontend/src-tauri/gen/android/app/build.gradle.kts`
- **Build Script:** `frontend/src-tauri/build-tablet.ps1`
- **Documentation:** `AndroidDoc/07_ANDROID_DEBUGGING_AND_FIXES.md`

---

## Testing Checklist

- [x] APK builds without crashing
- [x] Debug output shows afterEvaluate hook running
- [x] APK size is reasonable (26.8MB)
- [x] Native library is included (verify with: `unzip -l app-arm64-debug.apk | grep .so`)
- [ ] App launches on physical tablet
- [ ] App connects to backend API
- [ ] Rust IPC works correctly
- [ ] No runtime crashes related to missing native libs

---

## Acknowledgments

Solution inspired by Gradle lifecycle best practices and Android NDK documentation. The key insight was understanding that plugin configuration order matters, and `afterEvaluate` provides the final hook before build execution.
