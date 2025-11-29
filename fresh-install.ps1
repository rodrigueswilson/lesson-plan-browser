# Fresh Install Script - Clears cache and reinstalls app
$ErrorActionPreference = "Stop"

Write-Host "=== Fresh Install: Clear Cache & Reinstall ===" -ForegroundColor Cyan
Write-Host ""

$PackageName = "com.lessonplanner.bilingual"
$ApkPath = "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"

# Check if device is connected
Write-Host "[1/5] Checking device connection..." -ForegroundColor Yellow
$devices = adb devices | Select-String -Pattern "device$"
if (-not $devices) {
    Write-Host "  ERROR: No Android device found. Please connect a device and enable USB debugging." -ForegroundColor Red
    exit 1
}
$DeviceId = ($devices.ToString().Split("`t")[0])
Write-Host "  Found device: $DeviceId" -ForegroundColor Green

# Check if APK exists
if (-not (Test-Path $ApkPath)) {
    Write-Host ""
    Write-Host "  ERROR: APK not found at: $ApkPath" -ForegroundColor Red
    Write-Host "  Please rebuild the app first:" -ForegroundColor Yellow
    Write-Host "    .\rebuild-android.ps1" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "[2/5] Stopping app..." -ForegroundColor Yellow
adb -s $DeviceId shell am force-stop $PackageName
Start-Sleep -Seconds 1
Write-Host "  App stopped" -ForegroundColor Green

Write-Host ""
Write-Host "[3/5] Clearing app data and cache..." -ForegroundColor Yellow
adb -s $DeviceId shell pm clear $PackageName
if ($LASTEXITCODE -eq 0) {
    Write-Host "  App data and cache cleared" -ForegroundColor Green
} else {
    Write-Host "  WARNING: Failed to clear app data (app may not be installed)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[4/5] Uninstalling old version..." -ForegroundColor Yellow
adb -s $DeviceId uninstall $PackageName 2>&1 | Out-Null
Write-Host "  Old version uninstalled (if present)" -ForegroundColor Green

Write-Host ""
Write-Host "[5/5] Installing fresh APK..." -ForegroundColor Yellow
adb -s $DeviceId install -r $ApkPath
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: APK installation failed" -ForegroundColor Red
    exit 1
}
Write-Host "  Fresh APK installed successfully" -ForegroundColor Green

Write-Host ""
Write-Host "[6/6] Launching app..." -ForegroundColor Yellow
Start-Sleep -Seconds 1
adb -s $DeviceId shell am start -n ${PackageName}/.MainActivity
Write-Host "  App launched" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "SUCCESS: Fresh install complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The app has been:" -ForegroundColor Cyan
Write-Host "  ✅ Cleared of all data and cache" -ForegroundColor Green
Write-Host "  ✅ Uninstalled" -ForegroundColor Green
Write-Host "  ✅ Fresh installed" -ForegroundColor Green
Write-Host "  ✅ Launched" -ForegroundColor Green
Write-Host ""
Write-Host "Test the app now - the error should be resolved!" -ForegroundColor Yellow

