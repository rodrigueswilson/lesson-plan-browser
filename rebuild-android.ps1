# Quick Rebuild Script for Android Frontend Changes
# Skips Rust build for faster iteration

$ErrorActionPreference = "Stop"

Write-Host "=== Android Quick Rebuild Script ===" -ForegroundColor Cyan
Write-Host "Rebuilds frontend and APK (skips Rust compilation)" -ForegroundColor Gray
Write-Host ""

$ProjectRoot = "d:\LP"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$DistDir = Join-Path $FrontendDir "dist"
$AssetsDir = Join-Path $ProjectRoot "frontend\src-tauri\gen\android\app\src\main\assets"
$GradleDir = Join-Path $ProjectRoot "frontend\src-tauri\gen\android"
$ApkPath = Join-Path $GradleDir "app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"

# Step 1: Build Frontend
Write-Host "[1/4] Building frontend..." -ForegroundColor Yellow
Push-Location $FrontendDir
try {
    npm run build:skip-check
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Frontend build failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "  Frontend built successfully" -ForegroundColor Green
} finally {
    Pop-Location
}

# Step 2: Copy assets to Android
Write-Host "[2/4] Copying frontend assets to Android..." -ForegroundColor Yellow
if (-not (Test-Path $DistDir)) {
    Write-Host "  ERROR: Frontend dist directory not found!" -ForegroundColor Red
    exit 1
}

# COMPLETELY remove assets directory (per AndroidDoc/07_ANDROID_DEBUGGING_AND_FIXES.md line 274)
# This ensures no old files persist
Write-Host "  Removing entire assets directory..." -ForegroundColor Gray
Remove-Item $AssetsDir -Recurse -Force -ErrorAction SilentlyContinue

# Recreate empty assets directory
Write-Host "  Creating fresh assets directory..." -ForegroundColor Gray
New-Item -ItemType Directory -Path $AssetsDir -Force | Out-Null

# Copy new frontend files (this will create assets/assets/ subdirectory automatically)
Write-Host "  Copying new frontend files..." -ForegroundColor Gray
Copy-Item "$DistDir\*" $AssetsDir -Recurse -Force
Write-Host "  Assets copied successfully" -ForegroundColor Green

# Verify the copy worked
$HtmlFile = Join-Path $AssetsDir "index.html"
if (Test-Path $HtmlFile) {
    Write-Host "  ✅ Verified: index.html exists" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  WARNING: index.html not found after copy!" -ForegroundColor Yellow
}

# Step 3: Clean Gradle cache and rebuild APK (skip Rust)
Write-Host "[3/4] Cleaning Gradle cache and rebuilding APK..." -ForegroundColor Yellow
Push-Location $GradleDir
try {
    # Stop Kotlin daemon to clear incremental compilation cache
    Write-Host "  Stopping Kotlin daemon..." -ForegroundColor Gray
    .\gradlew.bat --stop 2>&1 | Out-Null
    
    # Clean to force Gradle to pick up new assets
    Write-Host "  Cleaning Gradle build cache..." -ForegroundColor Gray
    .\gradlew.bat clean -q
    
    # Also remove APK outputs and build directories to force complete rebuild
    $APKOutputDir = "app\build\outputs\apk"
    if (Test-Path $APKOutputDir) {
        Write-Host "  Removing old APK outputs..." -ForegroundColor Gray
        Remove-Item $APKOutputDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    # Remove app build directory (keeps Gradle cache for faster rebuilds)
    if (Test-Path "app\build") {
        Write-Host "  Removing app build directory..." -ForegroundColor Gray
        Remove-Item "app\build" -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "  Building APK (skipping Rust)..." -ForegroundColor Gray
    .\gradlew.bat assembleArm64Debug -x rustBuildArm64Debug --no-build-cache
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: APK build failed" -ForegroundColor Red
        exit 1
    }
    Write-Host "  APK built successfully" -ForegroundColor Green
} finally {
    Pop-Location
}

# Step 4: Install on device
Write-Host "[4/4] Installing APK on device..." -ForegroundColor Yellow
if (-not (Test-Path $ApkPath)) {
    Write-Host "  ERROR: APK not found at: $ApkPath" -ForegroundColor Red
    exit 1
}

$installResult = adb install -r -d $ApkPath 2>&1 | Out-String
if ($installResult -match "Success") {
    Write-Host "  APK installed successfully" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Launching app..." -ForegroundColor Yellow
    adb shell am start -n com.lessonplanner.bilingual/.MainActivity | Out-Null
    Write-Host "  App launched" -ForegroundColor Green
} else {
    Write-Host "  Installation result:" -ForegroundColor Yellow
    Write-Host $installResult
}

Write-Host ""
Write-Host "=== Rebuild Complete ===" -ForegroundColor Green
Write-Host "APK location: $ApkPath" -ForegroundColor Gray
if (Test-Path $ApkPath) {
    $size = [math]::Round((Get-Item $ApkPath).Length / 1MB, 2)
    Write-Host "APK size: $size MB" -ForegroundColor Gray
}

