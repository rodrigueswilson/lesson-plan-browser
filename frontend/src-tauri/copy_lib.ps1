# PowerShell script to copy the Rust library to Android jniLibs directory
# This is a workaround for Windows systems without Developer Mode enabled
# Run this script after each build if symlink creation fails

param(
    [string]$Target = "x86_64-linux-android",
    [string]$Profile = "debug"
)

$SourceFile = "target\$Target\$Profile\libbilingual_lesson_planner.so"
$DestDir = "gen\android\app\src\main\jniLibs\$Target"
$DestFile = "$DestDir\libbilingual_lesson_planner.so"

if (Test-Path $SourceFile) {
    if (-not (Test-Path $DestDir)) {
        New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
    }
    Copy-Item -Force $SourceFile -Destination $DestFile
    Write-Host "Copied $SourceFile to $DestFile"
} else {
    Write-Host "Source file not found: $SourceFile"
    exit 1
}
