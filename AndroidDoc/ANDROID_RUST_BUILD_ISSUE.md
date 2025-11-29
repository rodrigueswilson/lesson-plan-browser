# Android Rust Build - API Level and ABI Directory Issues

**Date:** November 25, 2025  
**Status:** Partially Resolved

## Issue Summary

Building the Rust library for Android ARM64 encountered two issues:
1. ✅ **API Level Mismatch** - RESOLVED
2. ❌ **ABI Directory Mismatch** - PENDING

## Issue 1: API Level Mismatch (RESOLVED)

### Problem
- Tauri was trying to use `aarch64-linux-android30-clang` 
- But `.cargo/config.toml` was configured for API 24
- NDK 29 supports API 30, so we updated the config

### Solution
Updated `frontend/src-tauri/.cargo/config.toml`:
```toml
[target.aarch64-linux-android]
linker = "C:/Users/rodri/AppData/Local/Android/Sdk/ndk/29.0.14206865/toolchains/llvm/prebuilt/windows-x86_64/bin/aarch64-linux-android30-clang.cmd"
```

**Also required:** Set environment variable before building:
```powershell
$env:CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER = "C:\Users\rodri\AppData\Local\Android\Sdk\ndk\29.0.14206865\toolchains\llvm\prebuilt\windows-x86_64\bin\aarch64-linux-android30-clang.cmd"
```

### Result
✅ Rust library compiles successfully (162MB debug build)

## Issue 2: ABI Directory Mismatch (RESOLVED)

### Problem
- Tauri Rust plugin outputs library to: `aarch64-linux-android/`
- Gradle expects: `arm64-v8a/`
- Error: `out extracted from path .../aarch64-linux-android/... is not an ABI`

### Solution
Added a Gradle task `fixAbiDirectories` in `app/build.gradle.kts` that:
1. Runs after `mergeJniLibFolders` but before `mergeNativeLibs`
2. Copies libraries from Rust target directories (`aarch64-linux-android`, etc.) to Android ABI directories (`arm64-v8a`, etc.)
3. Removes the source directories to prevent Gradle from finding them

**Implementation:**
- Task registered in `frontend/src-tauri/gen/android/app/build.gradle.kts`
- Automatically maps all Rust targets to Android ABIs:
  - `aarch64-linux-android` → `arm64-v8a`
  - `armv7-linux-androideabi` → `armeabi-v7a`
  - `i686-linux-android` → `x86`
  - `x86_64-linux-android` → `x86_64`
- Runs for all build variants (debug/release, arm64/universal)

### Result
✅ APK builds successfully with Rust library in correct ABI directory

## Files Modified

- `frontend/src-tauri/.cargo/config.toml` - Updated to API 30
- `frontend/src-tauri/fix-android-abi.ps1` - Created workaround script

## Build Command (Current)

```powershell
cd d:\LP\frontend\src-tauri
$env:CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER = "C:\Users\rodri\AppData\Local\Android\Sdk\ndk\29.0.14206865\toolchains\llvm\prebuilt\windows-x86_64\bin\aarch64-linux-android30-clang.cmd"
cd ..
npx tauri android build --target aarch64 --debug
```

## References

- NDK 29 supports API levels 21-35
- Android ABI names: `arm64-v8a` (not `aarch64-linux-android`)
- Tauri Rust plugin outputs to Rust target triple, not Android ABI name

