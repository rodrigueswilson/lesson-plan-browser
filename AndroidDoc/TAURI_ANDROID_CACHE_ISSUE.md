# Tauri Android Build Cache Issue

## Problem Summary
The Android app is persistently loading an old JavaScript file (`index-cOgOR3pL.js`) despite:
- Multiple rebuilds
- Frontend dist folder clearing
- Android build cache cleaning
- APK uninstall/reinstall
- Device restart
- WebView system cache clearing
- Package identifier changes
- Complete cargo clean

## Root Cause Analysis
This is a **Tauri Android build system caching issue** where the build process is not properly incorporating the latest frontend assets.

### What We've Verified
1. ✅ **Frontend build is correct**: `dist/index.html` points to `index-TiTynWQK.js`
2. ✅ **APK contains correct assets**: Confirmed via build process
3. ❌ **Runtime loads wrong file**: App still loads `index-cOgOR3pL.js`

### Cache Layers Attempted
1. App data/cache clear - ❌
2. App uninstall/reinstall - ❌
3. Device restart - ❌
4. WebView system cache clear - ❌
5. Android build clean (`./gradlew clean`) - ❌
6. Cargo clean - ❌
7. Package identifier change - ❌

## Technical Root Cause
The Tauri Android build system appears to have a **persistent build cache** that survives all standard cache clearing methods. This is likely in:

1. **Tauri's internal asset processing** - May cache processed assets
2. **Rust build artifacts** - Cargo clean may not clear all Android-specific artifacts
3. **Gradle build cache** - Standard clean may not clear Tauri-specific caches

## Solutions to Try

### 1. Force Asset Version Bump (Recommended)
Add a build timestamp or version to force asset regeneration:

```json
// tauri.conf.json
{
  "version": "1.0.1",
  "build": {
    "beforeBuildCommand": "npm run build:skip-check && echo $(date) > build-timestamp.txt"
  }
}
```

### 2. Delete All Build Caches Manually
```powershell
# Delete all possible cache locations
Remove-Item -Recurse -Force "d:\LP\frontend\src-tauri\target"
Remove-Item -Recurse -Force "d:\LP\frontend\src-tauri\gen\android\.gradle"
Remove-Item -Recurse -Force "d:\LP\frontend\src-tauri\gen\android\app\build"
Remove-Item -Recurse -Force "d:\LP\frontend\dist"
Remove-Item -Recurse -Force "$env:USERPROFILE\.gradle\caches"
Remove-Item -Recurse -Force "$env:USERPROFILE\.cargo\registry\cache"
```

### 3. Use Different Build Environment
- Build on different machine
- Use Docker container
- Use GitHub Actions or similar CI/CD

### 4. Debug Tauri Asset Pipeline
Add logging to see what assets are actually being packaged:
```rust
// In main.rs or similar
println!("Assets being packaged: {:?}", std::fs::read_dir("../dist/assets"));
```

### 5. File System Analysis
Use `adb shell` to inspect what's actually in the installed APK:
```bash
adb shell pm path com.lessonplanner.bilingual
adb pull [path] temp.apk
unzip -l temp.apk | grep index
```

## Current Status
- **Issue**: Persistent cache prevents new assets from loading
- **Impact**: App cannot be updated with new code
- **Severity**: Blocking development and testing
- **Next**: Try manual cache deletion (Solution #2)

## Lessons Learned
1. Tauri Android build system has aggressive caching that's difficult to clear
2. Standard cache clearing methods are insufficient for Tauri Android
3. Need to implement cache-busting strategies for future builds
4. Consider CI/CD for reliable builds

## Prevention for Future
1. Always increment version number in tauri.conf.json
2. Add build timestamps to assets
3. Use automated build systems
4. Document cache clearing procedures
