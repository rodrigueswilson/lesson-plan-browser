<#
    update-tablet.ps1
    -----------------
    Unified script to update the tablet with the latest lesson plan data.
    
    This script streamlines the workflow by:
    1. Syncing the database from the backend API
    2. Optionally rebuilding and installing the APK (if -RebuildApk is specified)
    3. Pushing the database directly to the tablet via ADB
    4. Restarting the app
    
    Usage:
        .\update-tablet.ps1                    # Sync DB + push to tablet (fastest)
        .\update-tablet.ps1 -RebuildApk        # Full rebuild + install + push DB
        .\update-tablet.ps1 -SkipSync          # Only push existing DB to tablet
    
    Examples:
        .\update-tablet.ps1                    # Quick data update (most common)
        .\update-tablet.ps1 -RebuildApk        # After code/UI changes
        .\update-tablet.ps1 -SkipSync -Restart # Just restart app with current DB
#>

[CmdletBinding()]
param(
    [switch]$RebuildApk,
    [switch]$SkipSync,
    [switch]$Restart,
    [string]$ApiUrl = "http://localhost:8000/api"
)

$ErrorActionPreference = "Stop"

# Configuration
$PackageName = "com.lessonplanner.browser"
$DbName = "lesson_planner.db"
$LocalDbPath = "data\$DbName"
$TempDbPath = "/data/local/tmp/$DbName"
$TargetDbPath = "databases/$DbName"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Update Tablet - Unified Workflow" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Display mode
if ($RebuildApk) {
    Write-Host "Mode: Full Rebuild (sync + build APK + install + push DB)" -ForegroundColor Yellow
} elseif ($SkipSync) {
    Write-Host "Mode: Push Only (push existing DB to tablet)" -ForegroundColor Yellow
} else {
    Write-Host "Mode: Quick Update (sync from API + push DB to tablet)" -ForegroundColor Yellow
}
Write-Host ""

# Step 1: Check ADB connectivity first (fail fast)
Write-Host "Step 1: Checking ADB connectivity..." -ForegroundColor Yellow
$adbCheck = Get-Command adb -ErrorAction SilentlyContinue
if (-not $adbCheck) {
    Write-Error "ADB not found in PATH. Please ensure Android SDK platform-tools are installed."
    exit 1
}

$oldErrorAction = $ErrorActionPreference
$ErrorActionPreference = "SilentlyContinue"
try {
    $devicesOutput = adb devices 2>&1
    $devices = $devicesOutput | Select-Object -Skip 1 | Where-Object { $_ -match '\tdevice' }
}
catch {
    $devices = @()
}
finally {
    $ErrorActionPreference = $oldErrorAction
}

if (-not $devices) {
    Write-Error "No Android device connected! Please connect your tablet via USB and enable USB debugging."
    exit 1
}

$deviceId = ($devices | Select-Object -First 1) -split '\t' | Select-Object -First 1
Write-Host "  Device connected: $deviceId" -ForegroundColor Green
Write-Host ""

# Step 2: Sync database from API (unless -SkipSync)
if (-not $SkipSync) {
    Write-Host "Step 2: Syncing database from backend API..." -ForegroundColor Yellow
    $syncScript = "scripts\sync_browser_plans_to_tablet_db.py"
    
    if (-not (Test-Path $syncScript)) {
        Write-Error "Sync script not found: $syncScript"
        exit 1
    }
    
    # Check if backend is running
    $backendRunning = $false
    try {
        $null = Invoke-WebRequest -Uri "$ApiUrl/users" -Method GET -TimeoutSec 5 -ErrorAction Stop
        $backendRunning = $true
        Write-Host "  Backend API is running at: $ApiUrl" -ForegroundColor Green
    }
    catch {
        Write-Host "  Backend API not accessible at: $ApiUrl" -ForegroundColor Yellow
        Write-Host "  Will use existing local database if available." -ForegroundColor Gray
    }
    
    if ($backendRunning) {
        Write-Host "  Running sync script..." -ForegroundColor Gray
        python -u $syncScript --api-base-url $ApiUrl --include-existing --timeout 120
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Sync script failed."
            exit 1
        }
        Write-Host "  Database synced successfully." -ForegroundColor Green
    }
    Write-Host ""
} else {
    Write-Host "Step 2: Skipping sync (using existing database)" -ForegroundColor Yellow
    Write-Host ""
}

# Verify database exists
if (-not (Test-Path $LocalDbPath)) {
    Write-Error "Database not found at $LocalDbPath. Run without -SkipSync to generate it."
    exit 1
}

$dbSize = (Get-Item $LocalDbPath).Length / 1MB
Write-Host "  Local database: $LocalDbPath ($([math]::Round($dbSize, 2)) MB)" -ForegroundColor Gray
Write-Host ""

# Step 3: Rebuild APK (if -RebuildApk)
if ($RebuildApk) {
    Write-Host "Step 3: Rebuilding APK..." -ForegroundColor Yellow
    
    # Run build script
    $buildScript = ".\build-apk.ps1"
    if (-not (Test-Path $buildScript)) {
        Write-Error "Build script not found: $buildScript"
        exit 1
    }
    
    & $buildScript
    if ($LASTEXITCODE -ne 0) {
        Write-Error "APK build failed."
        exit 1
    }
    Write-Host "  APK built successfully." -ForegroundColor Green
    Write-Host ""
    
    # Run install script
    Write-Host "Step 4: Installing APK..." -ForegroundColor Yellow
    $installScript = ".\install-apk.ps1"
    if (-not (Test-Path $installScript)) {
        Write-Error "Install script not found: $installScript"
        exit 1
    }
    
    & $installScript
    if ($LASTEXITCODE -ne 0) {
        Write-Error "APK installation failed."
        exit 1
    }
    Write-Host "  APK installed successfully." -ForegroundColor Green
    Write-Host ""
    
    $stepNum = 5
} else {
    $stepNum = 3
}

# Step N: Push database to tablet via ADB
Write-Host "Step ${stepNum}: Pushing database to tablet..." -ForegroundColor Yellow

# Force stop app first
Write-Host "  Stopping app..." -ForegroundColor Gray
adb shell am force-stop $PackageName 2>&1 | Out-Null
Start-Sleep -Milliseconds 500

# Push database to temp location
Write-Host "  Uploading database..." -ForegroundColor Gray
adb push $LocalDbPath $TempDbPath
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to push database to device"
    exit 1
}

# Create databases directory if it doesn't exist
adb shell "run-as $PackageName mkdir -p databases" 2>&1 | Out-Null

# Copy to app directory
Write-Host "  Copying to app directory..." -ForegroundColor Gray
$copyResult = adb shell "run-as $PackageName cp $TempDbPath $TargetDbPath" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  WARNING: Failed to copy database using run-as." -ForegroundColor Yellow
    Write-Host "  This usually means the app is a release build (not debug)." -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Troubleshooting:" -ForegroundColor Yellow
    Write-Host "    1. Rebuild with: .\update-tablet.ps1 -RebuildApk" -ForegroundColor Gray
    Write-Host "    2. Ensure the APK is a debug build" -ForegroundColor Gray
    Write-Host "    3. Try uninstalling and reinstalling the app" -ForegroundColor Gray
    
    # Clean up temp file
    adb shell rm $TempDbPath 2>&1 | Out-Null
    exit 1
}

# Clean up temp file
adb shell rm $TempDbPath 2>&1 | Out-Null
Write-Host "  Database pushed successfully!" -ForegroundColor Green
Write-Host ""

# Step N+1: Restart app
$stepNum++
Write-Host "Step ${stepNum}: Restarting app..." -ForegroundColor Yellow
adb shell am start -n "$PackageName/.MainActivity" 2>&1 | Out-Null
Write-Host "  App started." -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Green
Write-Host "Update Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The tablet has been updated with the latest data." -ForegroundColor Cyan
Write-Host ""
Write-Host "What was done:" -ForegroundColor Yellow
if (-not $SkipSync) {
    Write-Host "  - Synced database from backend API" -ForegroundColor Gray
}
if ($RebuildApk) {
    Write-Host "  - Rebuilt and installed APK" -ForegroundColor Gray
}
Write-Host "  - Pushed database to tablet via ADB" -ForegroundColor Gray
Write-Host "  - Restarted the app" -ForegroundColor Gray
Write-Host ""
Write-Host "Quick reference:" -ForegroundColor Yellow
Write-Host "  .\update-tablet.ps1              # Quick data update (most common)" -ForegroundColor Gray
Write-Host "  .\update-tablet.ps1 -RebuildApk  # After code/UI changes" -ForegroundColor Gray
Write-Host ""
