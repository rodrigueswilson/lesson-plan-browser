# Extract binary from existing Docker image (for when build already completed)
# This script extracts the binary from the python-android-build image

$ErrorActionPreference = "Stop"

Write-Host "=== Extracting Binary from Existing Docker Image ===" -ForegroundColor Cyan

$ImageName = "python-android-build"
$BinariesDir = "d:\LP\frontend\src-tauri\binaries"
$BinarySourcePath = "/app/python-sync-processor"
$BinaryTargetName = "python-sync-processor-aarch64-linux-android"

# Ensure binaries directory exists
if (-not (Test-Path $BinariesDir)) {
    New-Item -ItemType Directory -Path $BinariesDir -Force | Out-Null
    Write-Host "Created binaries directory: $BinariesDir" -ForegroundColor Green
}

Write-Host "[1/3] Creating temporary container for extraction..." -ForegroundColor Yellow
# 1. Create a container instance from the image (it does not need to run)
$ContainerID = docker create $ImageName

if (-not $ContainerID) {
    Write-Error "Failed to create container from image $ImageName."
    exit 1
}

$ContainerID = $ContainerID.Trim()
Write-Host "  Container ID: $ContainerID" -ForegroundColor Green

Write-Host "[2/3] Extracting binary from container..." -ForegroundColor Yellow
$TargetPath = Join-Path $BinariesDir $BinaryTargetName

# 2. Use docker cp to copy the file directly from the container
docker cp "$($ContainerID):$($BinarySourcePath)" $TargetPath

if (-not $?) {
    Write-Error "Failed to copy binary from container."
    docker rm $ContainerID 2>$null
    exit 1
} else {
    Write-Host "  Successfully extracted binary as $BinaryTargetName" -ForegroundColor Green
}

Write-Host "[3/3] Cleaning up temporary container..." -ForegroundColor Yellow
# 3. Remove the temporary container
docker rm $ContainerID | Out-Null
Write-Host "  Container removed" -ForegroundColor Green

# Verify binary exists and get size
if (Test-Path $TargetPath) {
    $FileInfo = Get-Item $TargetPath
    $SizeMB = [math]::Round($FileInfo.Length / 1MB, 2)
    Write-Host "" -ForegroundColor Green
    Write-Host "SUCCESS: Binary extracted!" -ForegroundColor Green
    Write-Host "  Location: $TargetPath" -ForegroundColor Green
    Write-Host "  Size: $SizeMB MB" -ForegroundColor Green
} else {
    Write-Host "ERROR: Binary file not found after extraction" -ForegroundColor Red
    exit 1
}

