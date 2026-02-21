<#
    sync-database-to-tablet.ps1
    ---------------------------
    Syncs lesson plan data to the Android tablet.
    
    This script provides two options:
    1. Sync from backend API to Supabase (then app syncs automatically)
    2. Push database directly via ADB (if app supports it)
    
    Usage:
        .\sync-database-to-tablet.ps1 [-Method supabase|adb] [-ApiUrl <url>]
    
    Examples:
        .\sync-database-to-tablet.ps1                    # Auto-detect best method
        .\sync-database-to-tablet.ps1 -Method supabase  # Sync via Supabase
        .\sync-database-to-tablet.ps1 -Method adb       # Push via ADB
#>

[CmdletBinding()]
param(
    [ValidateSet("supabase", "adb", "auto")]
    [string]$Method = "auto",
    
    [string]$ApiUrl = "http://localhost:8000/api"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Sync Database to Tablet" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if backend is running
Write-Host "Step 1: Checking backend API..." -ForegroundColor Yellow
$backendRunning = $false
try {
    $null = Invoke-WebRequest -Uri "$ApiUrl/users" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  Backend API is running at: $ApiUrl" -ForegroundColor Green
    $backendRunning = $true
    
    # Check if backend process is also using the database
    $port = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if ($port) {
        Write-Host ""
        Write-Host "  WARNING: Backend is running and may cause database lock conflicts!" -ForegroundColor Yellow
        Write-Host "  The sync script and backend both access the same SQLite database file." -ForegroundColor Gray
        Write-Host "  If Supabase sync is enabled in the frontend, this increases database activity." -ForegroundColor Gray
        Write-Host ""
        Write-Host "  If the sync script freezes, it's likely waiting for database locks." -ForegroundColor Yellow
        Write-Host "  Solutions:" -ForegroundColor Cyan
        Write-Host "    1. Stop the backend before syncing (recommended)" -ForegroundColor Gray
        Write-Host "    2. Close the frontend browser tab to reduce database activity" -ForegroundColor Gray
        Write-Host "    3. Wait for current database operations to complete" -ForegroundColor Gray
        Write-Host ""
    }
}
catch {
    Write-Host "  Backend API not accessible at: $ApiUrl" -ForegroundColor Gray
    Write-Host "  (This is fine - sync script will work, but backend must be running for API access)" -ForegroundColor Gray
    Write-Host ""
}

# Check ADB availability
Write-Host "Step 2: Checking ADB availability..." -ForegroundColor Yellow
$adbCheck = Get-Command adb -ErrorAction SilentlyContinue
if ($adbCheck) {
    Write-Host "  ADB found at: $($adbCheck.Source)" -ForegroundColor Green
    
    # Check for connected devices
    # Temporarily change error action to handle ADB daemon startup messages (which go to stderr)
    $oldErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        $devicesOutput = adb devices 2>&1
        $devices = $devicesOutput | Select-Object -Skip 1 | Where-Object { $_ -match '\tdevice' }
    }
    catch {
        # If ADB command fails completely, treat as no devices
        $devices = @()
    }
    finally {
        $ErrorActionPreference = $oldErrorAction
    }
    
    if ($devices) {
        Write-Host "  Device(s) connected:" -ForegroundColor Green
        $devices | ForEach-Object {
            $deviceId = ($_ -split '\t')[0]
            Write-Host "    - $deviceId" -ForegroundColor Gray
        }
        $adbAvailable = $true
    }
    else {
        Write-Host "  No devices connected" -ForegroundColor Yellow
        $adbAvailable = $false
    }
}
else {
    Write-Host "  ADB not found in PATH" -ForegroundColor Yellow
    $adbAvailable = $false
}
Write-Host ""

# Step 3: Updating local database from API (ALWAYS RUN)
Write-Host "Step 3: Updating local database from API..." -ForegroundColor Yellow
$syncScript = "scripts\sync_browser_plans_to_tablet_db.py"

if (Test-Path $syncScript) {
    # CRITICAL: Always include --include-existing to ensure we update stale plans
    # CRITICAL: Increase timeout to 120s to handle slow generation/fetches
    # Use -u flag for unbuffered output so progress is visible immediately
    
    if ($backendRunning) {
        Write-Host "  NOTE: Backend is running - database locks may occur." -ForegroundColor Yellow
        Write-Host "  If the script appears frozen, it's waiting for database locks to clear." -ForegroundColor Yellow
        Write-Host "  Press Ctrl+C to cancel, then stop the backend and try again." -ForegroundColor Gray
        Write-Host ""
    }
    
    Write-Host "  Running Python sync script (this may take several minutes)..." -ForegroundColor Gray
    Write-Host ""
    
    # Run Python script with unbuffered output for immediate progress visibility
    # The -u flag forces Python to use unbuffered stdout/stderr
    python -u $syncScript --api-base-url $ApiUrl --include-existing --timeout 120
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Python sync script failed."
        exit 1
    }
    Write-Host ""
    Write-Host "[OK] Local 'data/lesson_planner.db' updated." -ForegroundColor Green
    Write-Host ""
}
else {
    Write-Error "Sync script not found: $syncScript"
    exit 1
}

# Step 4: Method-specific actions
if ($Method -eq "auto") {
    if ($adbAvailable) {
        $Method = "adb"
        Write-Host "Auto-selected method: ADB (device connected)" -ForegroundColor Cyan
    }
    else {
        $Method = "supabase"
        Write-Host "Auto-selected method: Supabase (no device connected)" -ForegroundColor Cyan
    }
    Write-Host ""
}

# Method 1: Sync via Supabase
if ($Method -eq "supabase") {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Sync Complete (Local DB Updated)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Your local database is now ready to be bundled into the APK." -ForegroundColor Green
    Write-Host "Run 'build-apk.ps1' to create the new APK with this data." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Next steps for Supabase sync:" -ForegroundColor Yellow
    Write-Host "  1. Ensure your backend is pushing data to Supabase" -ForegroundColor Gray
    Write-Host "  2. Open the app on the tablet" -ForegroundColor Gray
    Write-Host "  3. The app will sync from Supabase automatically" -ForegroundColor Gray
    Write-Host ""
}

# Method 2: Push via ADB
if ($Method -eq "adb") {
    if (-not $adbAvailable) {
        Write-Error "ADB is not available or no device is connected. Cannot use ADB method."
        exit 1
    }
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Database Ready for Build" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "The local database (data/lesson_planner.db) has been updated." -ForegroundColor Green
    Write-Host ""
    Write-Host "To update your tablet, you have two options:" -ForegroundColor Yellow
    Write-Host "Option 1: Rebuild and Reinstall (Recommended)" -ForegroundColor Cyan
    Write-Host "   1. Run .\build-apk.ps1" -ForegroundColor Gray
    Write-Host "   2. Run .\install-apk.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Option 2: Direct Push (Advanced/Root only)" -ForegroundColor Cyan
    Write-Host "   Push 'data/lesson_planner.db' to /data/data/com.bilingual.lessonplanner/databases/" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "Summary" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The Android app uses Room database and syncs from Supabase." -ForegroundColor Cyan
Write-Host ""
Write-Host "To get data into the app:" -ForegroundColor Yellow
Write-Host "  1. Ensure your backend is configured to write to Supabase" -ForegroundColor Gray
Write-Host "  2. Ensure the app has Supabase credentials configured" -ForegroundColor Gray
Write-Host "  3. Launch the app - it will sync automatically on first launch" -ForegroundColor Gray
Write-Host ""
Write-Host "If sync fails, the app will show a test user with sample data." -ForegroundColor Gray
Write-Host "Check the app logs using: adb logcat" -ForegroundColor Gray
Write-Host ""
