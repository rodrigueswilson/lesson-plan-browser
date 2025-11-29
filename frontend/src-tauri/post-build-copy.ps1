# Post-build script to copy library file instead of using symlink
# Run this after each Rust build for Android
# This script should be run from the frontend directory

param(
    [string]$Target = "x86_64-linux-android",
    [string]$Profile = "debug"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourceFile = Join-Path $ScriptDir "target\$Target\$Profile\libbilingual_lesson_planner.so"
$DestDir = Join-Path $ScriptDir "gen\android\app\src\main\jniLibs\$Target"
$DestFile = Join-Path $DestDir "libbilingual_lesson_planner.so"

if (Test-Path $SourceFile) {
    if (-not (Test-Path $DestDir)) {
        New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
    }
    Copy-Item -Force $SourceFile -Destination $DestFile
    Write-Host "[OK] Copied library to jniLibs"
} else {
    Write-Host "[ERROR] Source file not found: $SourceFile"
    exit 1
}

