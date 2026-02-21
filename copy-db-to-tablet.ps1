# Copy database directly to tablet app directory
# This replaces the database on the tablet with the local synced database

$ErrorActionPreference = "Stop"

$PackageName = "com.lessonplanner.browser"
$DbName = "lesson_planner.db"
$LocalDbPath = "data\$DbName"
$TempDbPath = "/data/local/tmp/$DbName"
$TargetDbPath = "databases/$DbName"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Copy Database to Tablet" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check if source file exists
if (-not (Test-Path $LocalDbPath)) {
    Write-Error "Source database not found at $LocalDbPath. Please run sync-database-to-tablet.ps1 first."
    exit 1
}

$dbSize = (Get-Item $LocalDbPath).Length / 1MB
Write-Host "Source database: $LocalDbPath ($([math]::Round($dbSize, 2)) MB)" -ForegroundColor Gray
Write-Host ""

# 2. Check if device is connected
Write-Host "Checking for connected device..." -ForegroundColor Yellow
$devicesOutput = adb devices 2>&1
$deviceFound = $devicesOutput | Select-Object -Skip 1 | Where-Object { $_ -match '\tdevice' }

if (-not $deviceFound) {
    Write-Error "No Android device found! Please connect your tablet via USB and enable USB debugging."
    exit 1
}

Write-Host "Device connected" -ForegroundColor Green
Write-Host ""

# 3. Force stop app
Write-Host "Stopping app..." -ForegroundColor Yellow
adb shell am force-stop $PackageName 2>&1 | Out-Null
Start-Sleep -Milliseconds 500

# 4. Push database to temporary location
Write-Host "Pushing database to device..." -ForegroundColor Yellow
adb push $LocalDbPath $TempDbPath
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to push database to device"
    exit 1
}

Write-Host "Database pushed to $TempDbPath" -ForegroundColor Green
Write-Host ""

# 5. Copy to app directory using run-as (requires debug build)
Write-Host "Copying database to app directory..." -ForegroundColor Yellow
Write-Host "Note: This requires the app to be a debug build" -ForegroundColor Gray
Write-Host ""

$copyResult = adb shell "run-as $PackageName cp $TempDbPath $TargetDbPath" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "Database copied successfully!" -ForegroundColor Green
} else {
    Write-Error "Failed to copy database. Error: $copyResult"
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Make sure the app is a debug build (not release)" -ForegroundColor Gray
    Write-Host "  2. Try uninstalling and reinstalling the app first" -ForegroundColor Gray
    Write-Host "  3. Check ADB logcat for more details: adb logcat" -ForegroundColor Gray
    exit 1
}

# 6. Clean up temporary file
Write-Host "Cleaning up temporary file..." -ForegroundColor Yellow
adb shell rm $TempDbPath 2>&1 | Out-Null

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Database Copy Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The database has been updated on your tablet." -ForegroundColor Cyan
Write-Host "Restart the app to see the updated data." -ForegroundColor Cyan
Write-Host ""
