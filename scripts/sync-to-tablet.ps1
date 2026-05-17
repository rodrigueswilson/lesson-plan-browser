param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$PackageName = "com.lessonplanner.browser"
$DbName = "lesson_planner.db"
$LocalDbPath = "data/$DbName"
$PythonScript = "scripts/sync_browser_plans_to_tablet_db.py"

Write-Host "Starting sync-to-tablet process..." -ForegroundColor Cyan

Write-Host "Checking for connected Android devices..."
$devices = adb devices
$deviceFound = $devices | Where-Object { $_ -match "\s+device$" }

if (-not $deviceFound) {
    Write-Error "No Android device found! Please connect your tablet via USB and enable debugging."
    exit 1
}

Write-Host "Generating SQLite database from browser plans..."
$syncArgs = @("--plan-limit", "100")
if ($Force) {
    Write-Host "Force mode enabled: Re-syncing existing plans..." -ForegroundColor Yellow
    $syncArgs += "--include-existing"
}

python $PythonScript @syncArgs
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to generate database. Python script exited with error code $LASTEXITCODE."
    exit 1
}

if (-not (Test-Path $LocalDbPath)) {
    Write-Error "Database file not found at $LocalDbPath after generation."
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

Write-Host "Force-stopping app on tablet..."
adb shell "am force-stop $PackageName" | Out-Null

$TmpName = "lp_xfer_{0}_{1}.db" -f ([int][double]::Parse((Get-Date -UFormat %s))), $PID
$TmpPath = "/data/local/tmp/$TmpName"

Write-Host "Pushing database to $TmpPath..."
adb push $LocalDbPath $TmpPath
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to push database to /data/local/tmp via ADB."
    exit 1
}

Write-Host "Staging into app internal storage via run-as..."
$StageScript = "run-as $PackageName sh -c 'mkdir -p files/transfer && cp $TmpPath files/transfer/$DbName && chmod 600 files/transfer/$DbName'"
adb shell $StageScript
if ($LASTEXITCODE -ne 0) {
    Write-Error "run-as stage failed. The app's Rust import requires the file at files/transfer/$DbName."
    adb shell "rm -f $TmpPath" | Out-Null
    exit 1
}

Write-Host "Cleaning up /data/local/tmp..."
adb shell "rm -f $TmpPath" | Out-Null

Write-Host "Verifying staged file..."
$verify = adb shell "run-as $PackageName ls -la files/transfer/$DbName" 2>&1
Write-Host "  $verify"

Write-Host "Restarting app to trigger import on next init_database..."
adb shell "am start -n $PackageName/.MainActivity" | Out-Null

Write-Host "Sync complete. The app will import the new DB on next launch." -ForegroundColor Green
Write-Host "Tail logs with:" -ForegroundColor Cyan
Write-Host '  adb logcat -d | findstr /C:"[DB]" /C:"[LP]" /C:"[Transfer]"' -ForegroundColor Cyan
