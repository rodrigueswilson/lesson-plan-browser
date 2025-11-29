# Install Android APK Script
$ErrorActionPreference = "Continue"

Write-Host "=== Android App Installation Script ===" -ForegroundColor Cyan
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

# Step 2: Verify APK exists
Write-Host "[2/4] Verifying APK file..." -ForegroundColor Yellow
$apkPath = "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"

if (-not (Test-Path $apkPath)) {
    Write-Host "ERROR: APK not found at: $apkPath" -ForegroundColor Red
    Write-Host "Please ensure the APK was built successfully." -ForegroundColor Yellow
    exit 1
}

$apkInfo = Get-Item $apkPath
$apkSizeMB = [math]::Round($apkInfo.Length / 1MB, 2)
Write-Host "APK found: $apkSizeMB MB" -ForegroundColor Green
Write-Host "Path: $apkPath" -ForegroundColor Gray
Write-Host ""

# Step 3: Uninstall existing app (if any)
Write-Host "[3/4] Uninstalling existing app (if present)..." -ForegroundColor Yellow
$uninstallResult = adb uninstall com.lessonplanner.bilingual 2>&1 | Out-String
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
    $launchResult = adb shell am start -n com.lessonplanner.bilingual/.MainActivity 2>&1 | Out-String
    Write-Host $launchResult
    
    Write-Host ""
    Write-Host "App should now appear on your tablet!" -ForegroundColor Green
} elseif ($installResult -match "INSTALL_FAILED") {
    Write-Host ""
    Write-Host "ERROR: Installation failed. Details above." -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  - Tablet storage full"
    Write-Host "  - Unknown sources not enabled"
    Write-Host "  - Architecture mismatch (check if tablet is ARM64)"
    Write-Host "  - APK signature issue"
} else {
    Write-Host ""
    Write-Host "Installation completed. Check output above for status." -ForegroundColor Yellow
}

