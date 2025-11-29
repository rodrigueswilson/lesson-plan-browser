# Install Android APK Script for Lesson Plan Browser
$ErrorActionPreference = "Continue"

Write-Host "=== Lesson Plan Browser - Android App Installation Script ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check ADB connection
Write-Host "[1/4] Checking ADB device connection..." -ForegroundColor Yellow
$devices = adb devices 2>&1 | Out-String
Write-Host $devices

$deviceCount = ($devices -split "`n" | Where-Object { $_ -match "device$" }).Count - 1
if ($deviceCount -eq 0) {
    Write-Host "ERROR: No Android devices connected!" -ForegroundColor Red
    Write-Host "Please connect your tablet via USB and enable USB debugging." -ForegroundColor Yellow
    exit 1
}

Write-Host "Found $deviceCount device(s) connected" -ForegroundColor Green
Write-Host ""

# Step 2: Find APK file (try universal first, then release, then debug)
Write-Host "[2/4] Verifying APK file..." -ForegroundColor Yellow
# Tauri v2 uses gen/android instead of target/android
# Universal APK includes all architectures (recommended)
$universalApkPath = "frontend\src-tauri\gen\android\app\build\outputs\apk\universal\release\app-universal-release-unsigned.apk"
$releaseApkPath = "frontend\src-tauri\gen\android\app\build\outputs\apk\release\app-release.apk"
$debugApkPath = "frontend\src-tauri\gen\android\app\build\outputs\apk\debug\app-debug.apk"
# Also check old path structure (Tauri v1 or if gen/android doesn't exist)
$releaseApkPathOld = "frontend\src-tauri\target\android\app\build\outputs\apk\release\app-release.apk"
$debugApkPathOld = "frontend\src-tauri\target\android\app\build\outputs\apk\debug\app-debug.apk"
$apkPath = $null

if (Test-Path $universalApkPath) {
    $apkPath = $universalApkPath
    Write-Host "Found universal release APK (Tauri v2)" -ForegroundColor Green
} elseif (Test-Path $releaseApkPath) {
    $apkPath = $releaseApkPath
    Write-Host "Found release APK (Tauri v2 path)" -ForegroundColor Green
} elseif (Test-Path $debugApkPath) {
    $apkPath = $debugApkPath
    Write-Host "Found debug APK (Tauri v2 path, using debug version)" -ForegroundColor Yellow
} elseif (Test-Path $releaseApkPathOld) {
    $apkPath = $releaseApkPathOld
    Write-Host "Found release APK (alternative path)" -ForegroundColor Green
} elseif (Test-Path $debugApkPathOld) {
    $apkPath = $debugApkPathOld
    Write-Host "Found debug APK (alternative path, using debug version)" -ForegroundColor Yellow
} else {
    Write-Host "ERROR: APK not found!" -ForegroundColor Red
    Write-Host "Expected locations:" -ForegroundColor Yellow
    Write-Host "  - $releaseApkPath" -ForegroundColor Gray
    Write-Host "  - $debugApkPath" -ForegroundColor Gray
    Write-Host "  - $releaseApkPathOld" -ForegroundColor Gray
    Write-Host "  - $debugApkPathOld" -ForegroundColor Gray
    Write-Host "Please build the APK first using: .\build-android.ps1" -ForegroundColor Yellow
    exit 1
}

$apkInfo = Get-Item $apkPath
$apkSizeMB = [math]::Round($apkInfo.Length / 1MB, 2)
Write-Host "APK found: $apkSizeMB MB" -ForegroundColor Green
Write-Host "Path: $apkPath" -ForegroundColor Gray
Write-Host ""

# Step 3: Uninstall existing app (if any)
Write-Host "[3/4] Uninstalling existing app (if present)..." -ForegroundColor Yellow
$uninstallResult = adb uninstall com.lessonplanner.browser 2>&1 | Out-String
Write-Host $uninstallResult
Write-Host ""

# Step 4: Install new APK
Write-Host "[4/4] Installing new APK..." -ForegroundColor Yellow
Write-Host "This may take a minute..." -ForegroundColor Gray
$installResult = adb install -r -d $apkPath 2>&1 | Out-String
Write-Host $installResult

if ($installResult -match "Success") {
    Write-Host ""
    Write-Host "SUCCESS: App installed successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Step 5: Launch app
    Write-Host "Launching app..." -ForegroundColor Yellow
    $launchResult = adb shell am start -n com.lessonplanner.browser/.MainActivity 2>&1 | Out-String
    Write-Host $launchResult
    
    Write-Host ""
    Write-Host "App should now appear on your tablet!" -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANT: Ensure backend is running and tablet can connect to PC." -ForegroundColor Yellow
    Write-Host "  - Backend URL: http://YOUR_PC_IP:8000/api" -ForegroundColor Gray
    Write-Host "  - Tablet and PC must be on same WiFi network" -ForegroundColor Gray
} elseif ($installResult -match "INSTALL_FAILED") {
    Write-Host ""
    Write-Host "ERROR: Installation failed. Details above." -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  - Tablet storage full" -ForegroundColor Gray
    Write-Host "  - Unknown sources not enabled" -ForegroundColor Gray
    Write-Host "  - Architecture mismatch (check if tablet is ARM64)" -ForegroundColor Gray
    Write-Host "  - APK signature issue" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Try uninstalling first: adb uninstall com.lessonplanner.browser" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "Installation completed. Check output above for status." -ForegroundColor Yellow
}

