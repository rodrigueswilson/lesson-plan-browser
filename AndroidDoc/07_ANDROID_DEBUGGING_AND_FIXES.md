# Android Debugging, Fixes & Future Guide
**Date:** November 25, 2025
**Status:** ✅ Desktop working with Tauri v2.0 + IPC. Emulator (Tablet/Phone) connected to Local Backend. ✅ Physical tablet build (frontend only) working as a remote control for the PC backend via USB ADB reverse tunnel.

## 1. Summary of Fixes (What made it work)

We resolved a persistent "Blank Screen" and "API Connection" issue. The root causes were aggressive emulator caching, stale native configuration, and proxy misconfiguration.

### A. Force API URL in `api.ts` (Tauri v2.0)
We modified `frontend/src/lib/api.ts` to bypass the Vite proxy and detect Tauri correctly, which were unreliable on both desktop and emulator.

**Working Change (Tauri v2.0):**
```typescript
// frontend/src/lib/api.ts

const getApiUrl = (): string => {
  const userAgent = navigator.userAgent || '';
  
  // Check if running in Tauri v2.0 (correct detection method)
  const isTauri = typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
  
  // FORCE Android to use the special Emulator Host IP
  if (userAgent.includes('Android')) {
    console.log('[API] Android detected. Forcing: http://10.0.2.2:8000/api');
    return 'http://10.0.2.2:8000/api';
  }
  
  // For Tauri desktop, use localhost (proxy doesn't work in Tauri)
  if (isTauri) {
    console.log('[API] Tauri detected. Using: http://localhost:8000/api');
    return 'http://localhost:8000/api';
  }
  
  // Fallback to config (for web browser with Vite proxy)
  return config.apiBaseUrl;
};

// Make API_BASE_URL a function to check at runtime
let _cachedApiUrl: string | null = null;
const getApiBaseUrl = (): string => {
  if (_cachedApiUrl === null) {
    _cachedApiUrl = getApiUrl();
  }
  return _cachedApiUrl;
};
```
> **Why:** 
> - The emulator needs `10.0.2.2` to access your computer's `localhost`
> - Tauri desktop needs direct `localhost` connection (Vite proxy doesn't work)
> - Tauri v2.0 detection: Use `__TAURI_INTERNALS__` (not `window.__TAURI__`)
> - Runtime evaluation: API URL must be determined at runtime, not module load time

### B. Tauri Configuration (`tauri.conf.json`) - v2.0
We removed `devUrl` to force the app to use **bundled assets** (production build) instead of trying to connect to a running dev server.

**Working Configuration (Tauri v2.0):**
```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build:skip-check",
    "frontendDist": "../dist"
    // NO "devUrl" - causes blank screen issues
  }
}
```

**Important:** Tauri v2.0 uses a different config format. Do NOT add `devUrl` - it will cause blank screen issues.

### C. Native Configuration Refresh
We ran `npx tauri android init`.
> **Why:** Changing `tauri.conf.json` (removing `devUrl`) does NOT automatically update the native Android project files. Running `init` forced the Android project to recognize it should look for bundled assets, not a dev server.
> **Important:** If you see a black screen after installing the app, run `npx tauri android init` again to refresh the native configuration, then rebuild and reinstall.

### D. Network Security Configuration (Required for Backend Connection)
**Problem:** Android blocks cleartext HTTP traffic by default, preventing the app from connecting to `http://10.0.2.2:8000/api`.

**Solution:** After running `npx tauri android init`, run the network security fix script:
```powershell
cd d:\LP\frontend\src-tauri
.\apply-android-network-fix.ps1
```

This script:
- Creates `network_security_config.xml` allowing cleartext traffic for `10.0.2.2`, `localhost`, and `127.0.0.1`
- Updates `AndroidManifest.xml` to enable cleartext traffic and reference the network security config

**Important:** Run this script after every `npx tauri android init` command, as it regenerates the Android project files.

**Manual Alternative:** If you prefer to apply the fix manually:
1. Create `gen/android/app/src/main/res/xml/network_security_config.xml`:
   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <network-security-config>
       <domain-config cleartextTrafficPermitted="true">
           <domain includeSubdomains="true">10.0.2.2</domain>
           <domain includeSubdomains="true">localhost</domain>
           <domain includeSubdomains="true">127.0.0.1</domain>
       </domain-config>
       <domain-config cleartextTrafficPermitted="false">
           <domain includeSubdomains="true">supabase.co</domain>
       </domain-config>
   </network-security-config>
   ```
2. Update `gen/android/app/src/main/AndroidManifest.xml`:
   - Change `android:usesCleartextTraffic="${usesCleartextTraffic}"` to `android:usesCleartextTraffic="true"`
   - Add `android:networkSecurityConfig="@xml/network_security_config"` to the `<application>` tag

### E. JNI Libraries (Manual Fix)
The build process was getting confused about where to put the Rust compiled library (`.so`).

**Workaround:**
We manually created the directory `src-tauri/gen/android/app/src/main/jniLibs/x86_64` and copied `libbilingual_lesson_planner.so` into it before running Gradle.

### F. ABI Mismatch Crash (The "afterEvaluate" Fix) ✅ **SOLVED**
**Date:** November 26, 2025

**Problem:**
When building for `aarch64` (physical tablet), Gradle crashed with:
```
path .../target/aarch64-linux-android/debug/libbilingual_lesson_planner.so is not an ABI
```

**Root Cause:**
1. The Tauri Rust plugin compiles the library to `target/aarch64-linux-android/debug/`
2. The plugin automatically registers this directory with Android's `sourceSets.main.jniLibs`
3. Android Gradle Plugin (AGP) expects only standard ABI folder names (`arm64-v8a`, `armeabi-v7a`, etc.)
4. AGP encounters the folder `aarch64-linux-android` (a Rust target name, not an Android ABI name) and crashes during the `mergeNativeLibs` task

**Why Previous Fixes Failed:**
- **`packaging.excludes`**: Only affects final APK packaging, not the merge step where crash occurs
- **`sourceSets { ... }` in main block**: Runs during configuration, but plugin overrides it afterward
- **Renaming folders**: Race conditions and timing issues
- **`splits { ... }`**: Conflicts with plugin's auto-injected `ndk.abiFilters`

**The Solution: afterEvaluate Hook**
Use Gradle's `afterEvaluate` lifecycle hook to filter out the problematic path **after** the plugin finishes configuration but **before** build tasks execute.

**Implementation:**
Add to the end of `frontend/src-tauri/gen/android/app/build.gradle.kts`:

```kotlin
// Wait for all plugins to finish configuring, then forcefully REMOVE the bad Rust path.
afterEvaluate {
    android.sourceSets.getByName("main") {
        // Get current directories (including the bad one from the plugin)
        val currentDirs = jniLibs.srcDirs
        println("DEBUG: Current JNI dirs before fix: $currentDirs")
        
        // Filter out any path that points to the Rust 'target' directory
        // This removes the 'aarch64-linux-android' folder that causes the crash
        val safeDirs = currentDirs.filter { dir -> 
            !dir.path.contains("target") && !dir.path.contains("aarch64")
        }
        
        // Reset the directories to ONLY the safe ones (which includes our src/main/jniLibs)
        jniLibs.setSrcDirs(safeDirs)
        println("DEBUG: Fixed JNI dirs: ${jniLibs.srcDirs}")
    }
}
```

**How It Works:**
1. Rust plugin adds bad path during configuration phase
2. `afterEvaluate` runs after all plugins finish configuring
3. Filter removes any directory with "target" or "aarch64" in the path
4. Gradle only sees the manually created `arm64-v8a` folder
5. Build proceeds without crash

**Expected Debug Output:**
```
DEBUG: Current JNI dirs before fix: [.../target/aarch64-linux-android/debug, .../src/main/jniLibs]
DEBUG: Fixed JNI dirs: [d:\LP\frontend\src-tauri\gen\android\app\src\main\jniLibs]
```

**Status:** ✅ **VERIFIED WORKING** - APK built successfully (26.8MB)

**Complete Working Process for aarch64 Build:**

1. **Run the copy task first:**
   ```powershell
   cd d:\LP\frontend\src-tauri\gen\android
   .\gradlew.bat copyAndRenameNativeLibs
   ```

2. **Remove the problematic directory:**
   ```powershell
   Remove-Item -Path "app\src\main\jniLibs\aarch64-linux-android" -Recurse -Force -ErrorAction SilentlyContinue
   ```

3. **Build the APK:**
   ```powershell
   .\gradlew.bat assembleArm64Debug -x rustBuildArm64Debug
   ```

4. **Verify the output:**
   ```powershell
   Get-Item "app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"
   ```

**Note:** The `aarch64-linux-android` directory still gets created somewhere in the build process. The manual removal in step 2 is currently required as a workaround until we identify the source.

**Verified Debug Output:**
```
DEBUG: Current JNI dirs before fix: [D:\LP\frontend\src-tauri\gen\android\app\src\main\jniLibs]
DEBUG: Fixed JNI dirs: [D:\LP\frontend\src-tauri\gen\android\app\src\main\jniLibs]
```

---

## Current Status (2025-11-26)

- **ABI / Native Libs (arm64-v8a):**
  - `app-arm64-debug.apk` (~26.8MB) builds successfully for `aarch64`.
  - `afterEvaluate` hook and `copyAndRenameNativeLibs` task are working; ABI mismatch crash is resolved.

- **App Install / Runtime:**
  - APK installs on the physical tablet (`R52Y90L71YP`) as `com.lessonplanner.bilingual`.
  - App launches and the Tauri WebView UI renders.

- **Backend on PC:**
  - FastAPI/Uvicorn backend is healthy at `http://localhost:8000/api/health`.
  - Python process is listening on `0.0.0.0:8000`.

- **Networking from Tablet (Remote-Control Mode):**
  - Android build currently uses **USB tunnel mode** with `http://127.0.0.1:8000/api` (tablet frontend).
  - `adb reverse tcp:8000 tcp:8000` is configured so tablet `127.0.0.1:8000` traffic reaches the **PC backend** on `localhost:8000`.
  - This "tablet frontend + PC backend" configuration is **verified working** when ADB reverse and Windows firewall rules are correctly set.

- **Standalone Backend on Tablet:**
  - Not implemented yet; will require bundling a Python sidecar for `aarch64-linux-android` and implementing the Android bridge (Phases 5–6).

## Deferred TODOs (Future Session)

- **USB / Wi‑Fi Remote-Control Hardening:**
  - Inspect Windows Defender inbound/outbound rules for `python.exe` and `adb.exe`.
  - Check any third‑party firewall / endpoint protection.
  - While the tablet is attempting `/api/users`, watch:
    - `Test-NetConnection 127.0.0.1 -Port 8000` from the PC.
    - Uvicorn access logs for `/api/users` requests and response codes.

- **True Standalone Mode (Backend on Tablet):**
  - Choose bundling strategy for the Python backend (Nuitka / PyInstaller / embedded Python) targeting `aarch64-linux-android`.
  - Build a self-contained backend sidecar binary that listens on `127.0.0.1:8000` on-device.
  - Wire the sidecar into Tauri (Android) and implement the Android branch of the Rust bridge using the Tauri shell plugin.
  - Test `/api/health` and user flows entirely on the tablet with no PC or network.

---

## 2. The Working Build Process

To deploy a new version of the frontend to the emulator, use this **exact sequence**. Do not skip steps, or caching will bite you.

### Step 0: Initialize Android Project (if needed)
**Only run this if you've regenerated the Android project or see a black screen:**
```powershell
cd d:\LP\frontend
npx tauri android init
cd src-tauri
.\apply-android-network-fix.ps1  # Apply network security fix
```

### Step 1: Build Frontend
```powershell
cd d:\LP\frontend
npm run build:skip-check
```

### Step 2: Update Android Assets (Manual Copy)
This ensures Gradle picks up the *new* frontend files.
```powershell
# Run from d:\LP root
Remove-Item "d:\LP\frontend\src-tauri\gen\android\app\src\main\assets" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path "d:\LP\frontend\src-tauri\gen\android\app\src\main\assets" -Force
Copy-Item "d:\LP\frontend\dist\*" "d:\LP\frontend\src-tauri\gen\android\app\src\main\assets\" -Recurse -Force
```

### Step 3: Build APK
```powershell
cd d:\LP\frontend\src-tauri\gen\android
.\gradlew.bat assembleX86_64Debug -x rustBuildX86_64Debug
```

### Step 4: The "Nuclear" Install (Avoids Caching)
If you just run `install -r`, the emulator often keeps using old cached HTML/JS.
```powershell
# 1. Uninstall existing app
adb -s emulator-5554 uninstall com.lessonplanner.bilingual

# 2. Install new APK
adb -s emulator-5554 install -r "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\x86_64\debug\app-x86_64-debug.apk"

# 3. Launch
adb -s emulator-5554 shell am start -n com.lessonplanner.bilingual/.MainActivity
```

---

## 3. Future Development Advice

### Working on a Real Device (WiFi)
To run this on your real tablet tomorrow:

1.  **Find your PC's IP:** Open terminal, run `ipconfig`. Look for "IPv4 Address" (e.g., `192.168.1.15`).
2.  **Edit `frontend/src/lib/api.ts`:**
    Change the hardcoded URL from `http://10.0.2.2:8000/api` to your PC's IP:
    ```typescript
    return 'http://192.168.1.15:8000/api'; // Example IP
    ```
3.  **Rebuild & Reinstall:** Follow the build process above.
4.  **Connect:** Ensure both your PC and Tablet are on the **same WiFi**.

### Working on a Real Device (USB Tunnel Mode)

If you keep the Android API URL set to:

```typescript
// frontend/src/lib/api.ts (Android branch)
return 'http://127.0.0.1:8000/api';
```

then the tablet expects a backend listening on `127.0.0.1:8000` **inside the tablet**. To make this work with the backend on the PC, you must use **ADB reverse port forwarding** (device → PC), *not* the usual `forward`:

```powershell
# From d:\LP (or any directory)

# 1. Remove any stale forwards
& "C:\Users\rodri\AppData\Local\Android\Sdk\platform-tools\adb.exe" forward --remove-all

# 2. Create reverse tunnel from tablet → PC
& "C:\Users\rodri\AppData\Local\Android\Sdk\platform-tools\adb.exe" reverse tcp:8000 tcp:8000

# 3. Verify
& "C:\Users\rodri\AppData\Local\Android\Sdk\platform-tools\adb.exe" reverse --list
```

Expected output should include something like:

```text
UsbFfs tcp:8000 tcp:8000
```

With this in place:

- Tablet app calls: `http://127.0.0.1:8000/api/...`
- ADB reverse sends that traffic to **PC** `localhost:8000`.
- Uvicorn backend on the PC handles the requests.

**Important:** Using `adb forward tcp:8000 tcp:8000` is the *wrong* direction for this scenario and will result in `TypeError: Failed to fetch` even if the backend is running.

### Windows Firewall Notes (for USB / WiFi Modes)

To avoid confusing network errors when everything else is configured correctly:

- Ensure `python.exe` (Uvicorn backend) and `adb.exe` (Android SDK platform-tools) have **Allow** rules in Windows Defender Firewall.
- Make sure those rules apply to the **Private** profile (your home WiFi), not only Public.
- If using third‑party AV/firewall, verify it is not blocking traffic on port 8000 or ADB tunnels.

### "Android Python Sidecar" Error
You will see an error: *"Android Python sidecar not yet implemented"*.

**Status:** Expected / Normal (for current development phase)

**Reason:** The app is currently a "Remote Control" for the Python backend on your PC. It does not run Python *on the device* yet.

**Technical Details:**
*   **Location:** `frontend/src-tauri/src/lib.rs` (bridge module)
*   **Current Implementation:** The Android bridge methods (`spawn()`, `send()`, `receive()`) are **stub implementations** that return errors
*   **What's Missing:** The Android bridge needs to be implemented using Tauri v2.0's shell plugin API (`tauri-plugin-shell`) to spawn the bundled Python sidecar binary
*   **Desktop Status:** ✅ Fully implemented and tested (uses `std::process::Command` to spawn Python)
*   **Desktop IPC:** ✅ Working - sync completes successfully, database operations verified
*   **Android Status:** ❌ Stub only (returns error message)

**Example of Current Stub:**
```rust
#[cfg(target_os = "android")]
pub fn spawn(&self, _python_exe: &str, _args: &[&str], _working_dir: Option<&std::path::Path>) -> Result<(), String> {
    Err("Android Python sidecar not yet implemented. Python runtime needs to be bundled in APK or use Tauri v2.0 shell plugin API.".to_string())
}
```

**Desktop Testing Results (Tauri v2.0):**
- ✅ IPC communication working
- ✅ Python sidecar spawns successfully
- ✅ Sync functionality: Pulled 17, Pushed 0
- ✅ Database operations: SQLite created, tables exist, data synced
- ✅ Supabase integration: HTTP requests successful
- See `TEST_RESULTS.md` and `DESKTOP_TESTING_COMPLETE.md` for details

**Action:** 
*   **For now:** Ignore this error. The app works because it connects to your PC's backend via the API changes above (WiFi mode).
*   **For Phase 5-6:** See `CONTEXT_VERIFICATION_AND_NEXT_STEPS.md` for implementation details and next steps.

**Related Documentation:**
*   See `CONTEXT_VERIFICATION_AND_NEXT_STEPS.md` for detailed technical implementation plan
*   See `05_BUILD_DEPLOY.md` §5.1 for Python bundling options
*   See `06_CHECKLIST.md` for Phase 5-6 checklist items

### Standalone App (Long Term)
To make the app work completely offline (without the PC), you need to complete **Phase 5** (Python Bundling) and **Phase 6** (Android Sidecar Integration):

**Phase 5: Python Bundling**
*   Bundle Python sidecar as standalone binary (Nuitka/PyInstaller/Docker)
*   Target: `aarch64-linux-android` for physical tablets
*   Place binary in `frontend/src-tauri/binaries/` with proper naming convention

**Phase 6: Android Bridge Implementation**
*   Implement Android bridge using Tauri shell plugin API
*   Update `bridge.rs` to use `tauri_plugin_shell::ShellExt` for spawning sidecar
*   Configure sidecar binary in `tauri.conf.json`
*   Test IPC communication on device

**Current Status:** Phases 0-4 complete, Phases 5-6 pending (see `06_CHECKLIST.md` for progress tracking)
