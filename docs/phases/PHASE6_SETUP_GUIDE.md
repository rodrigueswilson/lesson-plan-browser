# Phase 6: Android Build Setup Guide

## Current Status

### ✅ What's Ready
- Rust Android targets installed (aarch64-linux-android, etc.)
- ANDROID_HOME set: `C:\Users\rodri\AppData\Local\Android\Sdk`
- Android Studio installed
- Emulator available

### ⚠️ What's Needed

1. **NDK Installation**
   - Open Android Studio
   - Go to: Tools → SDK Manager
   - SDK Tools tab
   - Check "NDK (Side by side)" and "CMake"
   - Install (recommended: NDK 26.1.10909125 or latest)
   - After installation, set ANDROID_NDK_HOME

2. **Tauri CLI Issue**
   - Tauri CLI v1.5.4 has compilation errors
   - Options:
     a. Use Tauri v2.0 CLI (may require code changes)
     b. Use `npm run tauri` commands (if available)
     c. Fix Tauri CLI compilation (check Rust version)

3. **Emulator**
   - Start Android emulator from Android Studio
   - Or use: `emulator -avd <avd_name>`

## Step-by-Step Setup

### Step 1: Install NDK

1. Open Android Studio
2. Tools → SDK Manager
3. SDK Tools tab
4. Check:
   - ✅ NDK (Side by side)
   - ✅ CMake
5. Click Apply/OK
6. Wait for installation

### Step 2: Set Environment Variables

After NDK installation, find the NDK version and set:

```powershell
# Find NDK version
Get-ChildItem "$env:ANDROID_HOME\ndk" -Directory

# Set ANDROID_NDK_HOME (replace VERSION with actual version)
[Environment]::SetEnvironmentVariable("ANDROID_NDK_HOME", "$env:ANDROID_HOME\ndk\VERSION", "User")
```

### Step 3: Tauri CLI Options

**Option A: Use npm scripts (if available)**
```bash
cd frontend
npm run tauri android init
```

**Option B: Try Tauri v2.0 CLI**
```bash
cargo install tauri-cli --version "^2.0"
```

**Option C: Use existing Tauri in project**
The project already has Tauri dependencies, so we might be able to use:
```bash
cd frontend/src-tauri
cargo run --bin tauri android init
```

### Step 4: Start Emulator

1. Open Android Studio
2. Tools → Device Manager
3. Start your tablet emulator
4. Verify: `adb devices` should show the device

## Next Steps After Setup

1. Initialize Android project
2. Configure Python runtime bundling
3. Build APK
4. Test on emulator

## Quick Commands

```powershell
# Check NDK
Get-ChildItem "$env:ANDROID_HOME\ndk" -Directory

# Check devices
adb devices

# Start emulator (if AVD name known)
emulator -avd <avd_name>

# Initialize Android (after Tauri CLI works)
cd frontend
cargo tauri android init
```

## Notes

- Tauri v1.5.4 Android support may be limited
- If `android init` fails, consider upgrading to Tauri v2.0
- Python runtime bundling will be configured after Android project is initialized

