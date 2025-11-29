# Unified Frontend Build Configuration

This document explains how both PC and Android builds work with the unified frontend implementation.

**Last Updated**: 2025-01-XX  
**Status**: Pre-Implementation Build Documentation

## Overview

The unified frontend is located at `lesson-plan-browser/frontend/` and is used by both PC and Android builds. The build processes are configured to work with this location without modification.

## Build Architecture

### Directory Structure

```
LP/
├── frontend/                          # PC build location
│   ├── src/
│   │   └── App.tsx                   # References unified frontend
│   ├── src-tauri/                    # Desktop Tauri config
│   └── vite.config.ts                # PC build config
│
└── lesson-plan-browser/
    ├── frontend/                      # Unified frontend (Android build location)
    │   ├── src/
    │   │   └── App.tsx               # Unified App.tsx
    │   ├── src-tauri/                # Android Tauri config
    │   └── vite.config.ts            # Tablet build config
    └── scripts/
        ├── run-with-ndk.ps1         # Android build entry
        └── build-android-offline.ps1 # Android build orchestrator
```

## PC Build Process

### Development Build

**Command**: `npm run tauri:dev`  
**Location**: `frontend/`  
**Process**:

1. **Frontend Bundle**
   - Vite dev server starts on port 1420
   - Hot module replacement enabled
   - Proxy configured for `/api` → `http://localhost:8000`

2. **Tauri Desktop**
   - Rust backend compiles
   - Desktop window opens
   - Loads frontend from dev server

**Configuration Files**:
- `frontend/vite.config.ts` - Vite configuration
- `frontend/src-tauri/tauri.conf.json` - Tauri desktop config
- `frontend/package.json` - Build scripts

### Production Build

**Command**: `npm run tauri:build`  
**Location**: `frontend/`  
**Process**:

1. **Frontend Bundle**
   ```bash
   npm run build:skip-check
   ```
   - Vite builds production bundle
   - Output: `frontend/dist/`
   - Minified and optimized

2. **Tauri Bundle**
   - Rust backend compiles (release mode)
   - Tauri bundler packages app
   - Output: `frontend/src-tauri/target/release/`
   - Creates installer (Windows: `.msi`, macOS: `.dmg`, Linux: `.AppImage`)

**Build Output**:
- Executable: `frontend/src-tauri/target/release/bilingual-lesson-planner.exe` (Windows)
- Installer: Platform-specific installer in `frontend/src-tauri/target/release/bundle/`

### PC Build with Unified Frontend

**After Unification**:

The PC build may reference the unified frontend in one of these ways:

**Option A: Import from Unified Location**
```typescript
// frontend/src/App.tsx
import App from '../../lesson-plan-browser/frontend/src/App';
export default App;
```

**Option B: Path Alias**
```typescript
// frontend/vite.config.ts
alias: {
  '@unified-app': path.resolve(__dirname, '../lesson-plan-browser/frontend/src/App.tsx')
}
```

**Option C: Wrapper**
```typescript
// frontend/src/App.tsx
export { default } from '../../lesson-plan-browser/frontend/src/App';
```

**Recommended**: Option C (re-export) - Simplest, most compatible

## Android Build Process

### Build Entry Point

**Command**: `.\scripts\run-with-ndk.ps1 -Target arm64`  
**Location**: `lesson-plan-browser/`  
**Script**: `lesson-plan-browser/scripts/run-with-ndk.ps1`

**Process**:

1. **NDK Configuration**
   - Sets up Android NDK environment
   - Configures compiler paths
   - Sets environment variables

2. **Calls Main Builder**
   - Calls `build-android-offline.ps1`
   - Passes parameters (target, DB path, etc.)

### Main Build Orchestrator

**Script**: `lesson-plan-browser/scripts/build-android-offline.ps1`

**Critical Path** (Line 35):
```powershell
$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $repoRoot "frontend"
```

**This resolves to**: `lesson-plan-browser/frontend/`

**Build Steps**:

1. **Step 1: Build Frontend Bundle**
   ```powershell
   npm run build:skip-check
   ```
   - Location: `lesson-plan-browser/frontend/`
   - Output: `lesson-plan-browser/frontend/dist/`
   - Creates production bundle

2. **Step 2: Build Rust Library**
   ```powershell
   cargo build --target aarch64-linux-android
   ```
   - Location: `lesson-plan-browser/frontend/src-tauri/`
   - Output: `lesson-plan-browser/frontend/src-tauri/target/aarch64-linux-android/debug/liblesson_plan_browser.so`
   - Compiles Rust backend for Android

3. **Step 3: Copy Native Library**
   - Source: `src-tauri/target/{target}/{profile}/lib*.so`
   - Destination: `src-tauri/gen/android/app/src/main/jniLibs/{abi}/`
   - Copies `.so` file to Android project

4. **Step 4: Copy Assets**
   - Source: `frontend/dist/*`
   - Destination: `src-tauri/gen/android/app/src/main/assets/`
   - Copies frontend bundle
   - Optionally bundles database and lesson JSON files

5. **Step 5: Create Tauri Metadata**
   - Creates `.tauri/` directory in assets
   - Copies Tauri configs
   - Sets `devUrl` to `tauri://localhost` for offline mode

6. **Step 6: Mirror Configs**
   - Copies configs to assets root
   - Ensures configs survive tooling quirks

7. **Step 7: Gradle Build**
   ```powershell
   .\gradlew.bat assembleArm64Debug
   ```
   - Location: `src-tauri/gen/android/`
   - Builds Android APK
   - Output: `src-tauri/gen/android/app/build/outputs/apk/arm64/debug/app-arm64-debug.apk`

### Android Build Parameters

**Entry Script** (`run-with-ndk.ps1`):

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `-Target` | string | `arm64` | Architecture: `arm64`, `armv7`, `x86_64`, `x86` |
| `-Release` | switch | false | Build release variant |
| `-DbPath` | string | required | Path to SQLite database |
| `-JsonSourcePath` | string | optional | Path to lesson JSON files |
| `-CacheSourcePath` | string | optional | Path to pre-generated cache |
| `-ApiUrl` | string | optional | API base URL (default: `http://10.0.2.2:8000/api`) |

**Example Command**:
```powershell
.\scripts\run-with-ndk.ps1 -Target arm64 -DbPath ..\data\lesson_planner.db -JsonSourcePath "F:\rodri\Documents\OneDrive\AS"
```

### Android Build Output

**APK Location**:
```
lesson-plan-browser/frontend/src-tauri/gen/android/app/build/outputs/apk/{target}/{profile}/app-{target}-{profile}.apk
```

**Example**:
```
app-arm64-debug.apk
```

**Installation**:
```powershell
adb install -r .\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk
```

## Vite Configuration

### PC Vite Config

**File**: `frontend/vite.config.ts`

**Key Settings**:
- **Port**: 1420
- **Proxy**: `/api` → `http://localhost:8000`
- **Shared Module Aliases**:
  - `@lesson-api`: `../shared/lesson-api/src`
  - `@lesson-browser`: `../shared/lesson-browser/src`
  - `@lesson-mode`: `../shared/lesson-mode/src`

**Build Target**: `chrome105` (Windows) or `safari13` (macOS)

### Tablet Vite Config

**File**: `lesson-plan-browser/frontend/vite.config.ts`

**Key Settings**:
- **Port**: 1420
- **Proxy**: `/api` → `http://127.0.0.1:8000`
- **Shared Module Aliases**:
  - `@lesson-api`: `../../shared/lesson-api/src` (2 levels up)
  - `@lesson-browser`: `../../shared/lesson-browser/src`
  - `@lesson-mode`: `../../shared/lesson-mode/src`
- **Android-Specific**:
  - `manualChunks: undefined` - Single bundle for Android
  - `chunkSizeWarningLimit: 1000` - Optimized for tablets

**Build Target**: `chrome105` (Android WebView)

## Tauri Configuration

### PC Tauri Config

**File**: `frontend/src-tauri/tauri.conf.json`

**Settings**:
- **Product Name**: "Bilingual Lesson Planner"
- **Identifier**: "com.lessonplanner.bilingual"
- **Before Build**: `npm run build:skip-check`
- **Frontend Dist**: `../dist`

### Android Tauri Config

**File**: `lesson-plan-browser/frontend/src-tauri/tauri.conf.json`

**Settings**:
- **Product Name**: "Lesson Plan Browser"
- **Identifier**: "com.lessonplanner.browser"
- **Before Build**: `npm run build:tauri`
- **Frontend Dist**: `../dist`

**Android-Specific Config**: `tauri.android.conf.json`
- **Dev URL**: `tauri://localhost` (offline mode)

## Build Script Dependencies

### Critical Paths

**Android Build Script** expects:
- Frontend at: `lesson-plan-browser/frontend/`
- Tauri config at: `lesson-plan-browser/frontend/src-tauri/`
- Dist output at: `lesson-plan-browser/frontend/dist/`

**Why This Works**:
- Script uses: `$frontendDir = Join-Path $repoRoot "frontend"`
- `$repoRoot` is `lesson-plan-browser/` (parent of `scripts/`)
- Resolves to: `lesson-plan-browser/frontend/`
- **No changes needed** - unified frontend is already at this location

### Path Resolution

```
run-with-ndk.ps1 (lesson-plan-browser/scripts/)
  └── Sets location to: lesson-plan-browser/
      └── Calls build-android-offline.ps1
          └── $repoRoot = lesson-plan-browser/
              └── $frontendDir = lesson-plan-browser/frontend/ ✅
```

## Environment Variables

### Build-Time Variables

| Variable | PC Usage | Android Usage | Default |
|----------|----------|--------------|---------|
| `VITE_API_BASE_URL` | Backend URL | Backend URL | `http://localhost:8000/api` |
| `VITE_ANDROID_API_BASE_URL` | N/A | Android backend URL | `http://10.0.2.2:8000/api` |
| `VITE_ENABLE_STANDALONE_DB` | N/A | Enable local DB | `false` |
| `TAURI_PLATFORM` | Platform detection | Platform detection | Auto-detected |
| `TAURI_DEBUG` | Debug mode | Debug mode | `false` |

### Android Build Variables

Set by `run-with-ndk.ps1`:
- `VITE_API_BASE_URL` = `$resolvedApiUrl` (from parameter or env)
- `VITE_ANDROID_API_BASE_URL` = `$resolvedApiUrl`
- `VITE_ENABLE_STANDALONE_DB` = `"true"`

## Build Verification

### PC Build Verification

**Checklist**:
- [ ] `npm run tauri:dev` launches app
- [ ] `npm run tauri:build` creates installer
- [ ] Built app launches and works
- [ ] No build errors or warnings
- [ ] Bundle size acceptable

### Android Build Verification

**Checklist**:
- [ ] `.\scripts\run-with-ndk.ps1` completes successfully
- [ ] APK created in expected location
- [ ] APK installs on device
- [ ] App launches on device
- [ ] No build errors or warnings
- [ ] Bundle size acceptable

## Troubleshooting

### Common Issues

**Issue**: Android build script can't find frontend
- **Cause**: Path resolution issue
- **Solution**: Verify script runs from `lesson-plan-browser/` directory
- **Check**: `$repoRoot` should be `lesson-plan-browser/`

**Issue**: Shared module imports fail
- **Cause**: Incorrect path aliases
- **Solution**: Verify vite.config.ts aliases point to correct `shared/` location
- **PC**: `../shared/` (1 level up)
- **Tablet**: `../../shared/` (2 levels up)

**Issue**: Bundle size too large
- **Cause**: PC-only components included in tablet bundle
- **Solution**: Verify lazy loading works, check tree-shaking
- **Check**: Analyze bundle contents

**Issue**: Platform detection fails
- **Cause**: Tauri internals not detected correctly
- **Solution**: Verify `__TAURI_INTERNALS__` check in platform.ts
- **Test**: Run on both platforms, check console logs

## Build Optimization

### PC Build

- **Code Splitting**: Enabled (default Vite behavior)
- **Minification**: Enabled in production
- **Source Maps**: Disabled in production

### Android Build

- **Code Splitting**: Disabled (`manualChunks: undefined`)
- **Single Bundle**: All code in one file
- **Minification**: Enabled in production
- **Source Maps**: Disabled in production

**Reason**: Android WebView handles single bundle better, avoids circular dependency issues

## Related Documents

- `docs/implementation/UNIFIED_FRONTEND_IMPLEMENTATION_GUIDE.md` - Main guide
- `lesson-plan-browser/README.md` - Tablet build instructions
- `lesson-plan-browser/scripts/build-android-offline.ps1` - Build script source
- `docs/implementation/UNIFIED_FRONTEND_DEPENDENCIES.md` - Dependency mapping

---

**Document Status**: Complete - Pre-Implementation  
**Last Updated**: 2025-01-XX  
**Maintainer**: Development Team

