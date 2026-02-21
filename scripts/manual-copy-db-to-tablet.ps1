# Manual script to copy database directly to tablet app directory
# Use this if the automatic refresh receiver doesn't work

$ErrorActionPreference = "Stop"

$PackageName = "com.bilingual.lessonplanner"
$DbName = "lesson_planner.db"
$AppDbName = "lesson_planner_db"
$TransferDir = "/sdcard/Android/data/$PackageName/files/transfer"
$LocalDbPath = "data/$DbName"

Write-Host "Manual Database Copy to Tablet" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check if source file exists
if (-not (Test-Path $LocalDbPath)) {
    Write-Error "Source database not found at $LocalDbPath"
    exit 1
}

# 2. Check if device is connected
$devices = adb devices
$deviceFound = $devices | Where-Object { $_ -match "\s+device$" }
if (-not $deviceFound) {
    Write-Error "No Android device found!"
    exit 1
}

# 3. Push to transfer directory
Write-Host "Pushing database to transfer directory..."
adb push $LocalDbPath "$TransferDir/$DbName"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to push database"
    exit 1
}

# 4. Force stop app
Write-Host "Stopping app..."
adb shell am force-stop $PackageName

# 5. Copy using run-as (requires root or debug build)
Write-Host "Copying database to app directory..."
Write-Host "Note: This requires the app to be debuggable or device to be rooted"
Write-Host ""

# Try to copy using run-as
$copyCommand = "run-as $PackageName cp $TransferDir/$DbName databases/$AppDbName"
adb shell $copyCommand

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Database copied successfully!" -ForegroundColor Green
    Write-Host "Restart the app manually to see the updated plans."
} else {
    Write-Host "Failed to copy using run-as. Trying alternative method..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Alternative: Start the app and send refresh broadcast:"
    Write-Host "  adb shell am start -n $PackageName/.MainActivity"
    Write-Host "  adb shell am broadcast -a $PackageName.REFRESH_DATABASE"
}

