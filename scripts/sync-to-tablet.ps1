param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Configuration

# Configuration
$PackageName = "com.lessonplanner.browser"
$DbName = "lesson_planner.db"
$TransferDir = "/sdcard/Android/data/$PackageName/files/transfer"
$LocalDbPath = "data/$DbName"
$PythonScript = "scripts/sync_browser_plans_to_tablet_db.py"

Write-Host "Starting sync-to-tablet process..." -ForegroundColor Cyan

# 1. Check if ADB is connected
Write-Host "Checking for connected Android devices..."
$devices = adb devices
$deviceFound = $devices | Where-Object { $_ -match "\s+device$" }

if (-not $deviceFound) {
    Write-Error "No Android device found! Please connect your tablet via USB and enable debugging."
    exit 1
}

# 2. Generate the Database
Write-Host "Generating SQLite database from browser plans..."
# Use --plan-limit 100 to ensure we get all recent plans (API default is 50, but we want more)
# Lesson steps are included and fetched in parallel for better performance
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

# 3. Create Transfer Directory on Tablet
Write-Host "Ensuring transfer directory exists on tablet..."
adb shell "mkdir -p $TransferDir"

# 4. Push Database to Tablet Transfer Directory
Write-Host "Pushing database to tablet transfer directory..."
adb push $LocalDbPath "$TransferDir/$DbName"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to push database via ADB."
    exit 1
}

# 5. Copy Database to App's Database Directory
Write-Host "Copying database to app's database directory..."
Write-Host "Note: This requires the app to be debuggable"
adb shell "run-as $PackageName mkdir -p databases"
adb shell "run-as $PackageName cp $TransferDir/$DbName databases/lesson_planner.db"
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to copy database using run-as. The app may need to be restarted manually."
    Write-Host "Database is available in transfer directory: $TransferDir/$DbName"
}
else {
    Write-Host "Database copied successfully to app directory!" -ForegroundColor Green
}

# 6. Restart App to Load New Database
Write-Host "Restarting app to load new database..."
adb shell "am force-stop $PackageName"
Start-Sleep -Seconds 1
adb shell "am start -n $PackageName/.MainActivity"

Write-Host "Sync complete! The app has been restarted with the new database." -ForegroundColor Green
