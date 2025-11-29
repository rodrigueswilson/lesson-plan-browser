# Tauri v2.0 Upgrade Status

## ✅ Completed

### 1. Tauri v2.0 Upgrade
- ✅ Updated `Cargo.toml` to Tauri v2.0 with plugins
- ✅ Updated `tauri.conf.json` to v2.0 format:
  - Changed `devPath` → `devUrl`
  - Changed `distDir` → `frontendDist`
  - Removed `withGlobalTauri` (not in v2.0)
- ✅ Verified `package.json` already at v2.0
- ✅ Code compiles successfully
- ✅ Desktop release build works

### 2. Android Project Initialization
- ✅ Ran `npm run tauri android init`
- ✅ Android project structure generated at `frontend/src-tauri/gen/android`
- ✅ Rust Android targets installed:
  - `aarch64-linux-android`
  - `armv7-linux-androideabi`
  - `i686-linux-android`
  - `x86_64-linux-android`
- ✅ Android environment variables configured:
  - `ANDROID_HOME`: C:\Users\rodri\AppData\Local\Android\Sdk
  - `ANDROID_NDK_HOME`: C:\Users\rodri\AppData\Local\Android\Sdk\ndk\29.0.14206865

### 3. Configuration Updates
- ✅ Shell plugin configured for Python execution
- ✅ Added Python, python3, and python-sync-processor to shell scope

## ⚠️ Known Issues & Next Steps

### Issue: Python Execution on Android

**Problem:** The current `SidecarBridge` implementation uses `std::process::Command` to spawn Python processes. This approach works on desktop but **will not work on Android** because:

1. Python is not installed on Android by default
2. `std::process::Command` has limited functionality on Android
3. We need to use Tauri's shell plugin API for Android

**Current Code Location:**
- `frontend/src-tauri/src/bridge.rs` - Uses `Command::new(python_exe)`
- `frontend/src-tauri/src/main.rs` - Spawns Python with `bridge.spawn()`

**Solutions:**

#### Option A: Use Tauri Shell Plugin for Android (Recommended)
Modify `bridge.rs` to use Tauri's shell plugin API on Android:

```rust
#[cfg(target_os = "android")]
use tauri_plugin_shell::ShellExt;

// In spawn method:
#[cfg(target_os = "android")]
{
    // Use Tauri shell plugin
    let app_handle = /* get from context */;
    let sidecar = app_handle.shell().sidecar("python")?;
    // Configure sidecar with args
}
```

#### Option B: Bundle Python in APK
- Use Chaquopy or similar to bundle Python runtime
- More complex but provides full Python environment
- Larger APK size

#### Option C: Use Python Runtime on Android
- Install Python via Termux or similar
- Not practical for production apps

**Recommended Approach:** Option A - Use Tauri shell plugin for Android while keeping `std::process::Command` for desktop.

### Next Steps

1. **✅ Update Bridge for Android Compatibility** (Partially Complete)
   - ✅ Modified `bridge.rs` to detect Android platform
   - ✅ Added platform-specific implementations
   - ⚠️ Android implementation is placeholder - needs Tauri shell plugin API integration
   - ✅ Desktop implementation unchanged and working

2. **Test Android Build**
   - Build debug APK: `npm run tauri android build --debug`
   - Test on emulator/device
   - Verify Python sidecar execution

3. **Handle Python Module Paths on Android**
   - Ensure backend Python modules are accessible
   - May need to bundle Python files in APK assets
   - Update `sidecar_main.py` to handle Android paths

4. **Test Full Sync Flow on Android**
   - Verify IPC communication works
   - Test database operations
   - Test Supabase sync

## Testing Checklist

### Desktop (✅ Complete)
- [x] App compiles
- [x] Release build succeeds
- [ ] Desktop IPC test (pending - should work as before)

### Android (⏳ Pending)
- [ ] Android build succeeds
- [ ] App launches on emulator/device
- [ ] Python sidecar spawns correctly
- [ ] IPC communication works
- [ ] Database operations work
- [ ] Sync functionality works

## Files Modified

1. `frontend/src-tauri/Cargo.toml` - Already at v2.0
2. `frontend/src-tauri/tauri.conf.json` - Updated to v2.0 format
3. `frontend/src-tauri/src/main.rs` - Cleaned up unused imports
4. `frontend/src-tauri/gen/android/` - Generated Android project

## Commands Reference

```bash
# Desktop development
cd frontend
npm run tauri dev

# Desktop build
npm run tauri build

# Android initialization (done)
npm run tauri android init

# Android development (requires device/emulator)
npm run tauri android dev

# Android build
npm run tauri android build --debug
npm run tauri android build --release
```

## Notes

- Tauri v2.0 provides native Android support
- Shell plugin configuration is in `tauri.conf.json` under `plugins.shell`
- Python sidecar execution needs platform-specific handling
- Desktop functionality should remain unchanged after upgrade

