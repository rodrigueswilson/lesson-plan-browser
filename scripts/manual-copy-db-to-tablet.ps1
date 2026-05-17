# Manual override: copy a pre-generated SQLite DB to the tablet's app
# internal storage and restart the app. The primary entry point is
# scripts/sync-to-tablet.ps1; use this script when you already have
# a built DB and want to skip the Python sync step.

$ErrorActionPreference = "Stop"

$PackageName = "com.lessonplanner.browser"
$DbName = "lesson_planner.db"
$LocalDbPath = "data/$DbName"

Write-Host "Manual Database Copy to Tablet" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $LocalDbPath)) {
    Write-Error "Source database not found at $LocalDbPath"
    exit 1
}

$devices = adb devices
$deviceFound = $devices | Where-Object { $_ -match "\s+device$" }
if (-not $deviceFound) {
    Write-Error "No Android device found!"
    exit 1
}

Write-Host "Probing run-as availability (requires debuggable APK)..."
$probeOutput = adb shell "run-as $PackageName true" 2>&1
$probeExit = $LASTEXITCODE
if ($probeExit -ne 0) {
    Write-Error @"
The installed APK is not debuggable; run-as is rejected ($probeOutput).
Build and install a debug APK before retrying:
  pwsh .\lesson-plan-browser\scripts\build-android-offline.ps1 -Target arm64
  adb install -r lesson-plan-browser\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk
"@
    exit 1
}

Write-Host "Stopping app..."
adb shell "am force-stop $PackageName" | Out-Null

$TmpName = "lp_xfer_{0}_{1}.db" -f ([int][double]::Parse((Get-Date -UFormat %s))), $PID
$TmpPath = "/data/local/tmp/$TmpName"

Write-Host "Pushing database to $TmpPath..."
adb push $LocalDbPath $TmpPath
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to push database to /data/local/tmp"
    exit 1
}

Write-Host "Staging into app internal storage via run-as..."
$StageScript = "run-as $PackageName sh -c 'mkdir -p files/transfer && cp $TmpPath files/transfer/$DbName && chmod 600 files/transfer/$DbName'"
adb shell $StageScript
if ($LASTEXITCODE -ne 0) {
    Write-Warning "run-as stage failed."
    adb shell "rm -f $TmpPath" | Out-Null
    exit 1
}

adb shell "rm -f $TmpPath" | Out-Null

$verify = adb shell "run-as $PackageName ls -la files/transfer/$DbName" 2>&1
Write-Host "Staged: $verify"

Write-Host "Restarting app..."
adb shell "am start -n $PackageName/.MainActivity" | Out-Null

Write-Host "Database staged successfully. The app will import it on next launch." -ForegroundColor Green
Write-Host "Tail logs with:" -ForegroundColor Cyan
Write-Host '  adb logcat -d | findstr /C:"[DB]" /C:"[LP]" /C:"[Transfer]"' -ForegroundColor Cyan
