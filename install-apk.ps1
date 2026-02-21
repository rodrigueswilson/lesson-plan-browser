<#
    install-apk.ps1
    ----------------
    Installs the Android APK on a connected tablet/device.
    
    This script:
    1. Checks for ADB availability
    2. Verifies a device is connected
    3. Finds the latest APK
    4. Installs the APK on the device
    5. (Optional) Pushes the database via ADB if -PushDb is specified
    
    Usage:
        .\install-apk.ps1 [-Target arm64|armv7|x86_64|x86] [-Release] [-ApkPath <path>] [-PushDb]
    
    Examples:
        .\install-apk.ps1                    # Install arm64 debug APK (default)
        .\install-apk.ps1 -Target arm64     # Install arm64 debug APK
        .\install-apk.ps1 -Release           # Install arm64 release APK
        .\install-apk.ps1 -ApkPath "path\to\app.apk"  # Install specific APK
        .\install-apk.ps1 -PushDb            # Install APK and push database to tablet
#>

[CmdletBinding()]
param(
    [ValidateSet("arm64", "armv7", "x86_64", "x86")]
    [string]$Target = "arm64",
    
    [switch]$Release,
    
    [string]$ApkPath,
    
    [switch]$PushDb
)

$ErrorActionPreference = "Stop"

# Get script directory (root of project)
# This script must be run from the project root directory (D:\LP)
$rootDir = $PSScriptRoot
if (-not $rootDir) {
    $rootDir = (Get-Location).Path
}
# Ensure we're in the root directory
if (-not (Test-Path (Join-Path $rootDir "lesson-plan-browser"))) {
    Write-Error "This script must be run from the project root directory (D:\LP). Current directory: $rootDir"
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Android APK Installation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check ADB availability
Write-Host "Step 1: Checking ADB availability..." -ForegroundColor Yellow
$adbCheck = Get-Command adb -ErrorAction SilentlyContinue
if (-not $adbCheck) {
    Write-Error "ADB not found in PATH. Please ensure Android SDK platform-tools are installed and in your PATH."
    exit 1
}
Write-Host "  ADB found at: $($adbCheck.Source)" -ForegroundColor Green
Write-Host ""

# Step 2: Check for connected devices
Write-Host "Step 2: Checking for connected devices..." -ForegroundColor Yellow
$devicesOutput = adb devices
$devices = $devicesOutput | Select-Object -Skip 1 | Where-Object { $_ -match '\tdevice' }

if (-not $devices) {
    Write-Host "  Warning: No devices found" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please ensure:" -ForegroundColor Yellow
    Write-Host "  1. Tablet/device is connected via USB" -ForegroundColor Gray
    Write-Host "  2. USB debugging is enabled on the device" -ForegroundColor Gray
    Write-Host "  3. Device is authorized (check device screen for prompt)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "All devices:" -ForegroundColor Yellow
    Write-Host $devicesOutput
    exit 1
}

Write-Host "  Device(s) connected:" -ForegroundColor Green
$deviceIds = @()
$devices | ForEach-Object {
    $deviceId = ($_ -split '\t')[0]
    $deviceIds += $deviceId
    Write-Host "    - $deviceId" -ForegroundColor Gray
}
Write-Host ""

# Step 3: Find APK
Write-Host "Step 3: Locating APK..." -ForegroundColor Yellow

if ($ApkPath) {
    # Use provided path
    if (-not (Test-Path $ApkPath)) {
        Write-Error "APK not found at: $ApkPath"
        exit 1
    }
    $apkFile = Get-Item $ApkPath
}
else {
    # Find APK in expected location
    # Note: New build process (npx tauri android build) outputs to D:\LP\lesson-plan-browser\frontend\...
    # This is the active project directory.
    
    $commonPaths = @(
        # New standard location (universal debug) - Active Project
        (Join-Path $rootDir "lesson-plan-browser\frontend\src-tauri\gen\android\app\build\outputs\apk\universal\debug\app-universal-debug.apk"),
        # New standard location (arm64 debug) - Active Project
        (Join-Path $rootDir "lesson-plan-browser\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-debug.apk"),
        # Fallback to root frontend paths (if built there)
        (Join-Path $rootDir "frontend\src-tauri\gen\android\app\build\outputs\apk\universal\debug\app-universal-debug.apk")
    )

    $apkPath = $null
    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            $apkPath = $path
            break
        }
    }
    
    if (-not $apkPath) {
        Write-Host "  Warning: Standard APK paths not found Checking: $commonPaths" -ForegroundColor Yellow
        Write-Host "  Searching for APK files in likely directories..." -ForegroundColor Yellow
        
        $searchDirs = @(
            (Join-Path $rootDir "lesson-plan-browser\frontend\src-tauri\gen\android"),
            (Join-Path $rootDir "frontend\src-tauri\gen\android")
        )

        $apkFiles = @()
        foreach ($dir in $searchDirs) {
            if (Test-Path $dir) {
                $found = Get-ChildItem -Path $dir -Filter "*.apk" -Recurse -ErrorAction SilentlyContinue 
                if ($found) { $apkFiles += $found }
            }
        }
        $apkFiles = $apkFiles | Sort-Object LastWriteTime -Descending
        
        if ($apkFiles) {
            $apkFile = $apkFiles[0]
            Write-Host "  Found APK: $($apkFile.FullName)" -ForegroundColor Green
        }
        else {
            Write-Error "No APK files found. Please build the APK first using: .\build-apk.ps1"
            exit 1
        }
    }
    else {
        $apkFile = Get-Item $apkPath
    }
}

$sizeMB = [math]::Round($apkFile.Length / 1MB, 2)
Write-Host "  APK found:" -ForegroundColor Green
Write-Host "    Path: $($apkFile.FullName)" -ForegroundColor Gray
Write-Host "    Size: $sizeMB MB" -ForegroundColor Gray
Write-Host "    Created: $($apkFile.LastWriteTime)" -ForegroundColor Gray
Write-Host ""

# Step 4: Install APK
Write-Host "Step 4: Installing APK..." -ForegroundColor Yellow
Write-Host "  This may take a minute..." -ForegroundColor Gray
Write-Host ""

$installOutput = adb install -r $apkFile.FullName 2>&1
$installResult = $installOutput | Out-String

Write-Host ""
if ($installResult -match 'Success') {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Installation Successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "The app has been installed/updated on your device." -ForegroundColor Cyan
    Write-Host "Look for 'Lesson Plan Browser' in your app drawer." -ForegroundColor Gray
    Write-Host ""
    
    # Step 5: Push database if -PushDb is specified
    if ($PushDb) {
        Write-Host "Step 5: Pushing database to tablet..." -ForegroundColor Yellow
        
        $PackageName = "com.lessonplanner.browser"
        $DbName = "lesson_planner.db"
        $LocalDbPath = Join-Path $rootDir "data\$DbName"
        $TempDbPath = "/data/local/tmp/$DbName"
        $TargetDbPath = "databases/$DbName"
        
        if (-not (Test-Path $LocalDbPath)) {
            Write-Host "  WARNING: Database not found at $LocalDbPath" -ForegroundColor Yellow
            Write-Host "  Run sync-database-to-tablet.ps1 first to generate the database." -ForegroundColor Gray
            Write-Host ""
        }
        else {
            $dbSize = (Get-Item $LocalDbPath).Length / 1MB
            Write-Host "  Source database: $LocalDbPath ($([math]::Round($dbSize, 2)) MB)" -ForegroundColor Gray
            
            # Force stop app first
            Write-Host "  Stopping app..." -ForegroundColor Gray
            adb shell am force-stop $PackageName 2>&1 | Out-Null
            Start-Sleep -Milliseconds 500
            
            # Push database to temp location
            Write-Host "  Uploading database..." -ForegroundColor Gray
            # adb push often writes progress output to stderr even on success. In this script we use
            # $ErrorActionPreference = "Stop", so that stderr becomes a terminating NativeCommandError.
            # Temporarily suppress PowerShell-native errors while still relying on $LASTEXITCODE.
            $oldEap = $ErrorActionPreference
            $ErrorActionPreference = "SilentlyContinue"
            try {
                $null = & adb push $LocalDbPath $TempDbPath 2>&1
            } finally {
                $ErrorActionPreference = $oldEap
            }
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  WARNING: Failed to push database to device" -ForegroundColor Yellow
            }
            else {
                # Create databases directory if it doesn't exist
                adb shell "run-as $PackageName mkdir -p databases" 2>&1 | Out-Null
                
                # Copy to app directory
                Write-Host "  Copying to app directory..." -ForegroundColor Gray
                $copyResult = adb shell "run-as $PackageName cp $TempDbPath $TargetDbPath" 2>&1
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  Database pushed successfully!" -ForegroundColor Green
                }
                else {
                    Write-Host "  WARNING: Failed to copy database (app may be release build)" -ForegroundColor Yellow
                    Write-Host "  Error: $copyResult" -ForegroundColor Gray
                }
                
                # Clean up temp file
                adb shell rm $TempDbPath 2>&1 | Out-Null
            }
            
            # Restart app
            Write-Host "  Restarting app..." -ForegroundColor Gray
            adb shell am start -n "$PackageName/.MainActivity" 2>&1 | Out-Null
            Write-Host ""
        }
    }
    else {
        Write-Host "TIP: Use -PushDb to also push the database after installation:" -ForegroundColor Gray
        Write-Host "  .\install-apk.ps1 -PushDb" -ForegroundColor Gray
        Write-Host ""
    }
}
elseif ($installResult -match 'Failure|Error|failed') {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Installation Failed" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error details:" -ForegroundColor Yellow
    Write-Host $installResult -ForegroundColor Gray
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  - Device storage full" -ForegroundColor Gray
    Write-Host "  - App signature mismatch (uninstall existing app first)" -ForegroundColor Gray
    Write-Host "  - Insufficient permissions" -ForegroundColor Gray
    Write-Host ""
    exit 1
}
else {
    Write-Host "Installation output:" -ForegroundColor Yellow
    Write-Host $installResult -ForegroundColor Gray
    Write-Host ""
}

