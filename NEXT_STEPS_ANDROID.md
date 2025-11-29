# Next Steps: Android Deployment

## Current Status

✅ **Desktop IPC Bridge: COMPLETE AND TESTED**
- All phases 0-4 complete
- Desktop testing successful (Pulled 17, Pushed 0)
- Ready for Android deployment

## Phase 5: Python Bundling

### Objective
Create a standalone Python executable that can run on Android devices.

### Options

#### Option A: Nuitka (Recommended for Android)
```bash
# Install Nuitka
pip install nuitka

# Build for Android (requires cross-compilation setup)
python -m nuitka \
    --standalone \
    --onefile \
    --include-module=backend \
    --include-module=backend.sidecar_main \
    --include-module=backend.ipc_database \
    --include-module=backend.supabase_database \
    --output-filename=python-sync-processor \
    backend/sidecar_main.py
```

#### Option B: PyInstaller (Easier, but larger)
```bash
pip install pyinstaller

pyinstaller --onefile \
    --name python-sync-processor \
    --hidden-import=backend.ipc_database \
    --hidden-import=backend.supabase_database \
    --hidden-import=backend.schema \
    backend/sidecar_main.py
```

#### Option C: Docker Cross-Compile (Most Reliable)
Use the Docker approach from `05_BUILD_DEPLOY.md` for consistent builds.

### Binary Placement

After building, place the binary in:
```
frontend/src-tauri/binaries/python-sync-processor-aarch64-linux-android
```

### Naming Convention
- Format: `{name}-{target-triple}`
- Example: `python-sync-processor-aarch64-linux-android`
- Tauri auto-selects based on target platform

## Phase 6: Android Build

### Prerequisites
1. Android SDK installed
2. Android NDK v26+ installed
3. Rust Android targets installed
4. Environment variables set

### Commands

```bash
# Initialize Android project (if not done)
cd frontend
cargo tauri android init

# Build debug APK
cargo tauri android build --debug

# Build release APK
cargo tauri android build --target aarch64
```

### Testing on Device

```bash
# Connect device
adb devices

# Install APK
adb install -r path/to/app.apk

# Launch app
adb shell am start -n com.lessonplanner.bilingual/.MainActivity

# View logs
adb logcat -s RustStdoutStderr:V
```

## Important Notes

### Tauri v1.5 Android Support
- Tauri v1.5 has limited Android support
- If `cargo tauri android init` fails, consider:
  1. Upgrade to Tauri v2.0 (may require code changes)
  2. Manual Android project setup

### Python Binary Size
- Standalone Python executables can be large (50-100MB+)
- Consider:
  - Using Nuitka for smaller binaries
  - Splitting functionality if needed
  - Compression options

### Testing Strategy
1. Test on Android emulator first
2. Test on physical device
3. Verify IPC communication
4. Test sync functionality
5. Test offline mode

## Estimated Timeline

- **Phase 5 (Python Bundling)**: 1-2 hours
- **Phase 6 (Android Build)**: 2-4 hours (depending on setup)
- **Testing & Debugging**: 2-4 hours

## Success Criteria

- [ ] Python binary created and placed correctly
- [ ] Android project initializes
- [ ] APK builds successfully
- [ ] App installs on device
- [ ] App launches without crash
- [ ] IPC bridge works on Android
- [ ] Sync functionality works
- [ ] Database operations work

## Ready to Proceed?

All desktop components are working. You can now proceed with:
1. Python bundling (Phase 5)
2. Android build setup (Phase 6)

Or continue testing/refining the desktop implementation first.

