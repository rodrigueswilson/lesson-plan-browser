#!/usr/bin/env pwsh
# Build script for aarch64 (Physical Tablet) APK
# This script automates the workaround for the ABI mismatch issue

Write-Host "=== Building APK for Physical Tablet (aarch64) ===" -ForegroundColor Cyan
Write-Host ""

# Navigate to Android directory
$androidDir = "$PSScriptRoot\gen\android"
Set-Location $androidDir

# Step 1: Copy native libraries
Write-Host "[1/4] Copying native libraries..." -ForegroundColor Yellow
.\gradlew.bat copyAndRenameNativeLibs
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Copy task failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Libraries copied successfully" -ForegroundColor Green
Write-Host ""

# Step 2: Clean up problematic directory
Write-Host "[2/4] Cleaning up problematic directories..." -ForegroundColor Yellow
$badDir = "app\src\main\jniLibs\aarch64-linux-android"
if (Test-Path $badDir) {
    Remove-Item -Path $badDir -Recurse -Force
    Write-Host "✓ Removed $badDir" -ForegroundColor Green
} else {
    Write-Host "✓ Directory doesn't exist (already clean)" -ForegroundColor Green
}
Write-Host ""

# Step 3: Build APK
Write-Host "[3/4] Building APK (this may take a minute)..." -ForegroundColor Yellow
.\gradlew.bat assembleArm64Debug -x rustBuildArm64Debug
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Build failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Build completed successfully" -ForegroundColor Green
Write-Host ""

# Step 4: Verify output
Write-Host "[4/4] Verifying output..." -ForegroundColor Yellow
$apkPath = "app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"
if (Test-Path $apkPath) {
    $apkSize = (Get-Item $apkPath).Length / 1MB
    Write-Host "✓ APK created: $apkPath" -ForegroundColor Green
    Write-Host "  Size: $([math]::Round($apkSize, 2)) MB" -ForegroundColor Green
    Write-Host ""
    Write-Host "=== BUILD SUCCESSFUL ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Connect your tablet via USB or WiFi"
    Write-Host "2. Run: adb devices (to verify connection)"
    Write-Host "3. Run: adb install -r `"$apkPath`""
    Write-Host ""
} else {
    Write-Host "ERROR: APK not found at expected location" -ForegroundColor Red
    exit 1
}
