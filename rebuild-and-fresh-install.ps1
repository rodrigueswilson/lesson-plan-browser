# Complete Rebuild and Fresh Install
# Rebuilds the app, clears cache, and does fresh install

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Complete Rebuild & Fresh Install" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$PackageName = "com.lessonplanner.bilingual"
$ApkPath = "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"

# Check if device is connected
Write-Host "[PRE-CHECK] Checking device connection..." -ForegroundColor Yellow
$devices = adb devices | Select-String -Pattern "device$"
if (-not $devices) {
    Write-Host "  ERROR: No Android device found. Please connect a device and enable USB debugging." -ForegroundColor Red
    exit 1
}
$DeviceId = ($devices.ToString().Split("`t")[0])
Write-Host "  ✅ Found device: $DeviceId" -ForegroundColor Green
Write-Host ""

# Step 1: Rebuild the app
Write-Host "[STEP 1/5] Rebuilding app (frontend + APK)..." -ForegroundColor Yellow
Write-Host ""
& "$PSScriptRoot\rebuild-android.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  ERROR: Rebuild failed!" -ForegroundColor Red
    exit 1
}

# Step 2: Stop app
Write-Host ""
Write-Host "[STEP 2/5] Stopping app..." -ForegroundColor Yellow
adb -s $DeviceId shell am force-stop $PackageName 2>&1 | Out-Null
Start-Sleep -Seconds 1
Write-Host "  ✅ App stopped" -ForegroundColor Green

# Step 3: Clear app data and cache
Write-Host ""
Write-Host "[STEP 3/5] Clearing app data and cache..." -ForegroundColor Yellow
$clearResult = adb -s $DeviceId shell pm clear $PackageName 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ App data and cache cleared" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Could not clear cache (app may not be installed yet)" -ForegroundColor Yellow
}

# Step 4: Uninstall old version
Write-Host ""
Write-Host "[STEP 4/5] Uninstalling old version..." -ForegroundColor Yellow
adb -s $DeviceId uninstall $PackageName 2>&1 | Out-Null
Write-Host "  ✅ Old version uninstalled (if present)" -ForegroundColor Green

# Step 5: Fresh install
Write-Host ""
Write-Host "[STEP 5/5] Installing fresh APK..." -ForegroundColor Yellow
adb -s $DeviceId install -r $ApkPath
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  ERROR: APK installation failed!" -ForegroundColor Red
    exit 1
}
Write-Host "  ✅ Fresh APK installed successfully" -ForegroundColor Green

# Launch app
Write-Host ""
Write-Host "[LAUNCH] Starting app..." -ForegroundColor Yellow
Start-Sleep -Seconds 1
adb -s $DeviceId shell am start -n ${PackageName}/.MainActivity
Write-Host "  ✅ App launched" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✅ COMPLETE! Fresh install done!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The app has been:" -ForegroundColor Cyan
Write-Host "  ✅ Rebuilt with latest code" -ForegroundColor Green
Write-Host "  ✅ Cache cleared" -ForegroundColor Green
Write-Host "  ✅ Fresh installed" -ForegroundColor Green
Write-Host "  ✅ Launched" -ForegroundColor Green
Write-Host ""
Write-Host "Test the app now!" -ForegroundColor Yellow
Write-Host ""

