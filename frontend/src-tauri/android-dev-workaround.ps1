# android-dev-workaround.ps1
# Workaround for Windows symlink issues with Tauri Android builds
# Usage: powershell -ExecutionPolicy Bypass -File ./src-tauri/android-dev-workaround.ps1

$ErrorActionPreference = "Stop"

# Configuration
$RustTarget = "x86_64-linux-android"  # Rust target triple
$AndroidAbi = "x86_64"  # Android ABI name (without -linux-android suffix)
$Profile = "debug"  # Use debug for dev builds to enable devUrl
$AppPackage = "com.lessonplanner.bilingual"
$MainActivity = "$AppPackage/.MainActivity"

# Paths (relative to frontend root, where this script should be run from, or adjusted below)
# We assume script is run from 'frontend' directory
$SrcTauriDir = "src-tauri"
$RustTargetDir = "$SrcTauriDir\target\$RustTarget\$Profile"
$AndroidGenDir = "$SrcTauriDir\gen\android"
$JniLibsDir = "$AndroidGenDir\app\src\main\jniLibs\$AndroidAbi"
$ApkPath = "$AndroidGenDir\app\build\outputs\apk\debug\app-debug.apk"
$IntermediatesDir = "$AndroidGenDir\app\build\intermediates\merged_jni_libs"

Write-Host "Starting Android Dev Workaround..." -ForegroundColor Cyan

# 1. Aggressive Cleanup - Remove ALL jniLibs directories and intermediates
$JniLibsBaseDir = "$AndroidGenDir\app\src\main\jniLibs"
if (Test-Path $JniLibsBaseDir) {
    Write-Host "Cleaning ALL jniLibs directories: $JniLibsBaseDir"
    Remove-Item -Recurse -Force "$JniLibsBaseDir\*" -ErrorAction SilentlyContinue
}

if (Test-Path $IntermediatesDir) {
    Write-Host "Cleaning intermediates: $IntermediatesDir"
    Remove-Item -Recurse -Force $IntermediatesDir -ErrorAction SilentlyContinue
}

# Also clean the entire build directory to be safe
$BuildDir = "$AndroidGenDir\app\build"
if (Test-Path $BuildDir) {
    Write-Host "Cleaning build directory: $BuildDir"
    Remove-Item -Recurse -Force "$BuildDir\intermediates" -ErrorAction SilentlyContinue
}

# 2. Copy Library (Fix Symlink)
$SourceLib = "$RustTargetDir\libbilingual_lesson_planner.so"
$DestLib = "$JniLibsDir\libbilingual_lesson_planner.so"

if (-not (Test-Path $SourceLib)) {
    Write-Error "Source library not found at $SourceLib. Did you run 'cargo build --target $RustTarget --release'?"
}

$SourceSize = (Get-Item $SourceLib).Length
Write-Host "Source library size: $SourceSize bytes"

# Ensure the correct jniLibs directory exists
if (-not (Test-Path $JniLibsDir)) {
    New-Item -ItemType Directory -Path $JniLibsDir -Force | Out-Null
}

# Remove existing symlink/file if it exists
if (Test-Path $DestLib) {
    Remove-Item $DestLib -Force
}

Write-Host "Copying library to $DestLib..."
Copy-Item -Path $SourceLib -Destination $DestLib -Force

if (-not (Test-Path $DestLib)) {
    Write-Error "Failed to copy library!"
}

$DestSize = (Get-Item $DestLib).Length
Write-Host "Destination library size: $DestSize bytes"

if ($DestSize -ne $SourceSize) {
    Write-Error "Copy failed integrity check! Sizes do not match."
}

Write-Host "Library copied and verified." -ForegroundColor Green

# 2.5. Copy Frontend Assets
$FrontendDist = "$SrcTauriDir\..\dist"
$AndroidAssetsDir = "$AndroidGenDir\app\src\main\assets"
if (Test-Path $FrontendDist) {
    Write-Host "Copying frontend assets from $FrontendDist to $AndroidAssetsDir..." -ForegroundColor Cyan
    if (Test-Path $AndroidAssetsDir) {
        Remove-Item -Recurse -Force $AndroidAssetsDir -ErrorAction SilentlyContinue
    }
    New-Item -ItemType Directory -Path $AndroidAssetsDir -Force | Out-Null
    Copy-Item -Path "$FrontendDist\*" -Destination $AndroidAssetsDir -Recurse -Force
    Write-Host "Frontend assets copied." -ForegroundColor Green
} else {
    Write-Warning "Frontend dist folder not found at $FrontendDist. Run 'npm run build:skip-check' first."
}

# 3. Run Gradle Build directly (Bypassing Tauri CLI which creates bad symlinks)
Write-Host "Running Gradle build..." -ForegroundColor Cyan
Push-Location $AndroidGenDir
try {
    # Skip rustBuild task to avoid WebSocket/CLI connection requirements
    .\gradlew.bat assembleX86_64Debug -x rustBuildX86_64Debug
    if ($LASTEXITCODE -ne 0) {
        throw "Gradle build failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}
Write-Host "Gradle build successful." -ForegroundColor Green

# 4. Find and Install APK
Write-Host "Finding APK..." -ForegroundColor Cyan
$ApkSearchPath = "$AndroidGenDir\app\build\outputs\apk"
$FoundApk = Get-ChildItem -Path $ApkSearchPath -Recurse -Filter "*.apk" | Where-Object { $_.Name -like "*x86_64*debug*" -or $_.Name -like "*debug*" } | Select-Object -First 1

if (-not $FoundApk) {
    Write-Error "APK not found in $ApkSearchPath. Build may have failed or APK is in unexpected location."
}

$ApkPath = $FoundApk.FullName
Write-Host "Found APK: $ApkPath" -ForegroundColor Green

Write-Host "Installing APK..." -ForegroundColor Cyan
adb install -r $ApkPath

if ($LASTEXITCODE -ne 0) {
    Write-Error "ADB install failed with exit code $LASTEXITCODE"
}

Write-Host "Launching App..." -ForegroundColor Cyan
adb shell am start -n $MainActivity

if ($LASTEXITCODE -ne 0) {
    Write-Warning "ADB launch failed. Trying alternative activity path..."
    # Try with full package name
    adb shell am start -n "com.lessonplanner.bilingual/com.lessonplanner.bilingual.MainActivity"
}

Write-Host "Done! App should be running." -ForegroundColor Green
Write-Host "Make sure you have 'npm run dev' running in another terminal for the frontend." -ForegroundColor Yellow
