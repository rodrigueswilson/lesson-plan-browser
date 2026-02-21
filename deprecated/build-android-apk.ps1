<#
    build-android-apk.ps1
    ---------------------
    Builds the native Android APK from the android/ directory.
    
    This script:
    1. Navigates to the android directory
    2. Runs Gradle to build the APK
    3. Shows the APK location and details
    
    Usage:
        .\build-android-apk.ps1 [-Release] [-Install]
    
    Examples:
        .\build-android-apk.ps1              # Build debug APK
        .\build-android-apk.ps1 -Release     # Build release APK
        .\build-android-apk.ps1 -Install     # Build and install debug APK
        .\build-android-apk.ps1 -Release -Install  # Build and install release APK
#>

[CmdletBinding()]
param(
    [switch]$Release,
    [switch]$Install
)

$ErrorActionPreference = "Stop"

# Get script directory (root of project)
$rootDir = $PSScriptRoot
if (-not $rootDir) {
    $rootDir = Get-Location
}

$androidDir = Join-Path $rootDir "android"

# Verify android directory exists
if (-not (Test-Path $androidDir)) {
    Write-Error "android directory not found at: $androidDir"
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Native Android APK Build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Build Type: $(if ($Release) { 'Release' } else { 'Debug' })" -ForegroundColor Gray
Write-Host "  Install: $(if ($Install) { 'Yes' } else { 'No' })" -ForegroundColor Gray
Write-Host "  Android Directory: $androidDir" -ForegroundColor Gray
Write-Host ""
Write-Host "Starting build process..." -ForegroundColor Yellow
Write-Host "  This may take several minutes..." -ForegroundColor Gray
Write-Host ""

# Change to android directory
Push-Location $androidDir

try {
    # Determine build task
    if ($Release) {
        $buildTask = "assembleRelease"
        $installTask = "installRelease"
    } else {
        $buildTask = "assembleDebug"
        $installTask = "installDebug"
    }
    
    # Run Gradle build
    Write-Host "Running: .\gradlew.bat $buildTask" -ForegroundColor Cyan
    & .\gradlew.bat $buildTask
    
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
    $buildType = if ($Release) { "release" } else { "debug" }
    $apkPath = Join-Path $androidDir "app\build\outputs\apk\$buildType\app-$buildType.apk"
    
    if (Test-Path $apkPath) {
        $apkInfo = Get-Item $apkPath
        $sizeMB = [math]::Round($apkInfo.Length / 1MB, 2)
        
        Write-Host "APK Details:" -ForegroundColor Cyan
        Write-Host "  Location: $apkPath" -ForegroundColor Gray
        Write-Host "  Size: $sizeMB MB" -ForegroundColor Gray
        Write-Host "  Created: $($apkInfo.LastWriteTime)" -ForegroundColor Gray
        Write-Host "  Build Type: $buildType" -ForegroundColor Gray
        Write-Host ""
        
        # Install if requested
        if ($Install) {
            Write-Host "Installing APK..." -ForegroundColor Yellow
            & .\gradlew.bat $installTask
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "========================================" -ForegroundColor Green
                Write-Host "Installation Complete!" -ForegroundColor Green
                Write-Host "========================================" -ForegroundColor Green
                Write-Host ""
                Write-Host "The app has been installed on your device." -ForegroundColor Cyan
                Write-Host "Look for 'Bilingual Lesson Planner' in your app drawer." -ForegroundColor Gray
                Write-Host ""
            } else {
                Write-Host ""
                Write-Host "Installation failed. Make sure:" -ForegroundColor Yellow
                Write-Host "  1. A device/emulator is connected" -ForegroundColor Gray
                Write-Host "  2. USB debugging is enabled" -ForegroundColor Gray
                Write-Host ""
            }
        } else {
            Write-Host "To install, run:" -ForegroundColor Yellow
            Write-Host "  .\build-android-apk.ps1 $(if ($Release) { '-Release' }) -Install" -ForegroundColor White
            Write-Host ""
            Write-Host "Or use ADB directly:" -ForegroundColor Yellow
            Write-Host "  adb install -r `"$apkPath`"" -ForegroundColor White
            Write-Host ""
        }
    } else {
        Write-Host "⚠ APK not found at expected location: $apkPath" -ForegroundColor Yellow
        Write-Host "Searching for APK files..." -ForegroundColor Yellow
        Get-ChildItem -Path (Join-Path $androidDir "app\build\outputs\apk") -Filter "*.apk" -Recurse -ErrorAction SilentlyContinue | 
            Select-Object FullName, @{Name="Size(MB)";Expression={[math]::Round($_.Length / 1MB, 2)}}, LastWriteTime | 
            Format-Table -AutoSize
    }
}
finally {
    Pop-Location
}

