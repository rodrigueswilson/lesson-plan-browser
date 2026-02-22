<#
    build-apk.ps1
    -------------
    Builds the Android APK from the root directory.

    This script:
    1. Navigates to the lesson-plan-browser directory
    2. Runs the Android build script
    3. Shows the APK location and details

    Usage:
        .\build-apk.ps1 [-Target arm64|armv7|x86_64|x86] [-Release]

    Examples:
        .\build-apk.ps1                    # Build arm64 debug APK (default)
        .\build-apk.ps1 -Target arm64      # Build arm64 debug APK
        .\build-apk.ps1 -Release           # Build arm64 release APK
        .\build-apk.ps1 -Target armv7      # Build armv7 debug APK
#>

[CmdletBinding()]
param(
    [ValidateSet("arm64", "armv7", "x86_64", "x86")]
    [string]$Target = "arm64",

    [switch]$Release,

    # Optional: allow building with a specific SQLite database file (e.g. per-user tablet export)
    [string]$DbPath
)

$ErrorActionPreference = "Stop"

# Get script directory (root of project)
$rootDir = $PSScriptRoot
if (-not $rootDir) {
    $rootDir = Get-Location
}

$lessonPlanBrowserDir = Join-Path $rootDir "lesson-plan-browser"
$buildScript = Join-Path $lessonPlanBrowserDir "scripts\run-with-ndk.ps1"
$dbPath = if ($DbPath) { $DbPath } else { (Join-Path $rootDir "data\lesson_planner.db") }

# Verify directories exist
if (-not (Test-Path $lessonPlanBrowserDir)) {
    Write-Error "lesson-plan-browser directory not found at: $lessonPlanBrowserDir"
    exit 1
}

if (-not (Test-Path $buildScript)) {
    Write-Error "Build script not found at: $buildScript"
    exit 1
}

if (-not (Test-Path $dbPath)) {
    Write-Error "Database file not found at: $dbPath. Please run sync-database-to-tablet.ps1 first."
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Android APK Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Target: $Target" -ForegroundColor Gray
Write-Host "  Build Type: $(if ($Release) { 'Release' } else { 'Debug' })" -ForegroundColor Gray
Write-Host "  Root Directory: $rootDir" -ForegroundColor Gray
Write-Host "  Database: $dbPath" -ForegroundColor Gray
Write-Host "  Build Script: $buildScript" -ForegroundColor Gray
Write-Host ""
Write-Host "Starting build process..." -ForegroundColor Yellow
Write-Host "  This may take several minutes..." -ForegroundColor Gray
Write-Host ""

# Change to lesson-plan-browser directory and run build script
Push-Location $lessonPlanBrowserDir

try {
    # Run the build script with parameters
    # Pass -DbPath explicitly to ensure the correct database is bundled
    # Some tools (gradle/ndk wrappers) write progress/warnings to stderr even on success.
    # When $ErrorActionPreference = "Stop", PowerShell can treat that as a terminating error
    # (NativeCommandError) even if the process exit code is 0. Temporarily relax it and rely
    # on $LASTEXITCODE for success/failure.
    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        if ($Release) {
            & $buildScript -Target $Target -Release -DbPath $dbPath
        } else {
            & $buildScript -Target $Target -DbPath $dbPath
        }
    }
    finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Build failed with exit code: $LASTEXITCODE"
        exit $LASTEXITCODE
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Build Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""

    # Find and display APK location
    $apkPath = Join-Path $lessonPlanBrowserDir "frontend\src-tauri\gen\android\app\build\outputs\apk\$Target\debug\app-$Target-debug.apk"
    if ($Release) {
        $apkPath = Join-Path $lessonPlanBrowserDir "frontend\src-tauri\gen\android\app\build\outputs\apk\$Target\release\app-$Target-release.apk"
    }

    if (Test-Path $apkPath) {
        $apkInfo = Get-Item $apkPath
        $sizeMB = [math]::Round($apkInfo.Length / 1MB, 2)

        Write-Host "APK Details:" -ForegroundColor Cyan
        Write-Host "  Location: $apkPath" -ForegroundColor Gray
        Write-Host "  Size: $sizeMB MB" -ForegroundColor Gray
        Write-Host "  Created: $($apkInfo.LastWriteTime)" -ForegroundColor Gray
        Write-Host "  Target: $Target" -ForegroundColor Gray
        Write-Host "  Build Type: $(if ($Release) { 'Release' } else { 'Debug' })" -ForegroundColor Gray
        Write-Host ""
        Write-Host "To install, run:" -ForegroundColor Yellow
        Write-Host "  .\install-apk.ps1" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host "WARNING: APK not found at expected location: $apkPath" -ForegroundColor Yellow
        Write-Host "Searching for APK files..." -ForegroundColor Yellow
        Get-ChildItem -Path (Join-Path $lessonPlanBrowserDir "frontend\src-tauri\gen\android") -Filter "*.apk" -Recurse -ErrorAction SilentlyContinue |
            Select-Object FullName, @{Name="Size(MB)";Expression={[math]::Round($_.Length / 1MB, 2)}}, LastWriteTime |
            Format-Table -AutoSize
    }
}
finally {
    Pop-Location
}
