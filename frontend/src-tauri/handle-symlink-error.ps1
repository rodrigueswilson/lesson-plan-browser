# Script to handle symlink error and continue build
# This runs after Tauri fails on symlink creation

Write-Host "Symlink creation failed (expected on Windows without Developer Mode)"
Write-Host "Copying library file instead..."

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Target = "x86_64-linux-android"
$Profile = "debug"

$SourceFile = Join-Path $ScriptDir "target\$Target\$Profile\libbilingual_lesson_planner.so"
$DestDir = Join-Path $ScriptDir "gen\android\app\src\main\jniLibs\$Target"
$DestFile = Join-Path $DestDir "libbilingual_lesson_planner.so"

if (Test-Path $SourceFile) {
    if (-not (Test-Path $DestDir)) {
        New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
    }
    Copy-Item -Force $SourceFile -Destination $DestFile
    Write-Host "[OK] Library file copied successfully"
    Write-Host "You can now continue with: cd gen/android && .\gradlew assembleDebug"
} else {
    Write-Host "[ERROR] Source file not found: $SourceFile"
    exit 1
}

