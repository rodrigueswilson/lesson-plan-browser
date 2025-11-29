# Rebuild Steps After Frontend Changes

## What Needs to Be Rebuilt?

### ✅ YES - Frontend Bundle
- **Reason**: We're changing TypeScript/React code in `frontend/src/`
- **Files changed**: `api.ts`, possibly `UserSelector.tsx` and other components
- **Build command**: `npm run build:skip-check` (from `frontend/` directory)
- **Output**: New JavaScript bundle in `frontend/dist/`

### ✅ YES - Android APK
- **Reason**: Frontend assets need to be copied into APK
- **Build command**: `./gradlew.bat assembleArm64Debug` (from `frontend/src-tauri/gen/android/`)
- **Output**: New APK at `app/build/outputs/apk/arm64/debug/app-arm64-debug.apk`

### ❌ NO - Rust Backend
- **Reason**: We'll use existing Tauri commands (`sql_query`, `sql_execute`)
- **No Rust code changes needed**
- **Skip**: Rust compilation (can skip with `-x rustBuildArm64Debug` flag)

### ❌ NO - Python Sidecar Binary
- **Reason**: Sidecar binary is already built and bundled
- **No Python code changes needed**
- **Skip**: Docker build and binary extraction

## Quick Rebuild Process

### Step 1: Build Frontend
```powershell
cd d:\LP\frontend
npm run build:skip-check
```

### Step 2: Copy Frontend Assets to Android
```powershell
# Remove old assets
Remove-Item "d:\LP\frontend\src-tauri\gen\android\app\src\main\assets\*.html","d:\LP\frontend\src-tauri\gen\android\app\src\main\assets\*.js","d:\LP\frontend\src-tauri\gen\android\app\src\main\assets\*.css" -ErrorAction SilentlyContinue

# Copy new assets
Copy-Item "d:\LP\frontend\dist\*" "d:\LP\frontend\src-tauri\gen\android\app\src\main\assets\" -Recurse -Force
```

### Step 3: Rebuild APK (Skip Rust Build)
```powershell
cd d:\LP\frontend\src-tauri\gen\android
.\gradlew.bat assembleArm64Debug -x rustBuildArm64Debug
```

### Step 4: Install New APK
```powershell
adb install -r "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"
```

## Estimated Time

- **Frontend build**: ~30-60 seconds
- **APK build (skipping Rust)**: ~2-5 minutes
- **Total**: ~3-6 minutes

## Why Skip Rust Build?

The `-x rustBuildArm64Debug` flag skips Rust compilation since:
1. We're only changing frontend TypeScript code
2. Existing Tauri commands are already compiled
3. Saves significant build time (~10-20 minutes)

## One-Command Rebuild Script

I can create a script that does all of this automatically:
- Build frontend
- Copy assets
- Rebuild APK (skip Rust)
- Install on device

Would you like me to create this script?

