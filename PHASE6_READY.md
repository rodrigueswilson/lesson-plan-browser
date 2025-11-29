# Phase 6: Android Build - Ready to Start

## Prerequisites Checklist

Before starting Phase 6, verify:

- [ ] Android SDK installed (via Android Studio or standalone)
- [ ] Android NDK v26+ installed
- [ ] Rust Android targets installed (`rustup target add aarch64-linux-android`)
- [ ] Tauri CLI installed (`cargo install tauri-cli`)
- [ ] Environment variables set (ANDROID_HOME, ANDROID_NDK_HOME)
- [ ] Android device/emulator available for testing

## Phase 6 Tasks

### 6.1 Environment Setup
- Verify Android SDK/NDK
- Set environment variables
- Install Rust Android targets

### 6.2 Tauri Android Initialization
- Run `cargo tauri android init`
- If fails (Tauri v1.5 limitation), consider:
  - Upgrade to Tauri v2.0, OR
  - Manual Android project setup

### 6.3 Python Runtime Bundling
- Get Python ARM64 for Android
- Place in `frontend/src-tauri/resources/python/`
- Update `tauri.conf.json` to include resources
- Configure paths in code

### 6.4 Build APK
- Build debug APK: `cargo tauri android build --debug`
- Build release APK: `cargo tauri android build --target aarch64`

### 6.5 Testing
- Install on device/emulator
- Test IPC communication
- Test sync functionality
- Verify database operations

## Current Status

✅ **Phase 5**: Complete
- All bundles created
- Python runtime approach confirmed
- Code ready

⏭️ **Phase 6**: Ready to start

## Quick Start

```bash
# 1. Verify Android setup
rustup target list | grep android
echo $ANDROID_HOME

# 2. Initialize Android project
cd frontend
cargo tauri android init

# 3. Build
cargo tauri android build --debug
```

## Notes

- Tauri v1.5 Android support may be limited
- If `android init` fails, may need Tauri v2.0
- Python runtime bundling will be configured during build setup

Ready to proceed when you are!

