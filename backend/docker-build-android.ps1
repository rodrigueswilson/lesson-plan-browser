# Build Python Sidecar Binary for Android using Docker
# This script builds a cross-compiled binary for aarch64-linux-android

$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = $ScriptDir
$ProjectRoot = Split-Path -Parent $BackendDir
$BinariesDir = Join-Path $ProjectRoot "frontend\src-tauri\binaries"

Write-Host "=== Docker Android Binary Build Script ===" -ForegroundColor Cyan
Write-Host "Backend directory: $BackendDir"
Write-Host "Binaries directory: $BinariesDir"
Write-Host ""

# Ensure binaries directory exists
if (-not (Test-Path $BinariesDir)) {
    New-Item -ItemType Directory -Path $BinariesDir -Force | Out-Null
    Write-Host "Created binaries directory: $BinariesDir" -ForegroundColor Green
}

$ImageName = "python-android-build"
$ContainerName = "temp-android-build"
$OutputName = "python-sync-processor-aarch64-linux-android"

# Step 1: Build Docker image
Write-Host "[1/4] Building Docker image..." -ForegroundColor Yellow
# Build from project root so Dockerfile can access both backend/ and requirements.txt
Push-Location $ProjectRoot
try {
    docker build -f backend/Dockerfile.android -t $ImageName .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: Docker build failed" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  Docker image built successfully" -ForegroundColor Green
} finally {
    Pop-Location
}

# Step 2: Create temporary container for extraction (container doesn't need to run)
Write-Host "[2/4] Creating temporary container for extraction..." -ForegroundColor Yellow

# Get the image name you just successfully built
$BinarySourcePath = "/app/python-sync-processor"
$BinaryTargetName = $OutputName

# 1. Create a container instance from the image (it does not need to run)
$ContainerID = docker create $ImageName

if (-not $ContainerID) {
    Write-Host "  ERROR: Failed to create container from image $ImageName." -ForegroundColor Red
    exit 1
}

$ContainerID = $ContainerID.Trim()
Write-Host "  Container created: $ContainerID" -ForegroundColor Green

# Step 3: Extract binary from container
Write-Host "[3/4] Extracting binary from container..." -ForegroundColor Yellow

$TargetPath = Join-Path $BinariesDir $BinaryTargetName

# 2. Use docker cp to copy the file directly from the container
docker cp "$($ContainerID):$($BinarySourcePath)" $TargetPath

if (-not $?) {
    Write-Host "  ERROR: Failed to copy binary from container." -ForegroundColor Red
    docker rm $ContainerID 2>$null
    exit 1
} else {
    Write-Host "  Successfully extracted binary as $BinaryTargetName" -ForegroundColor Green
}

# Step 4: Cleanup and verify
Write-Host "[4/4] Cleaning up temporary container..." -ForegroundColor Yellow

# 3. Remove the temporary container
docker rm $ContainerID | Out-Null
Write-Host "  Container removed" -ForegroundColor Green

# Verify binary exists and get size
if (Test-Path $TargetPath) {
    $FileInfo = Get-Item $TargetPath
    $SizeMB = [math]::Round($FileInfo.Length / 1MB, 2)
    Write-Host "  Binary location: $TargetPath" -ForegroundColor Green
    Write-Host "  Binary size: $SizeMB MB" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Binary file not found at expected location" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "SUCCESS: Android binary built and copied!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Verify binary architecture (if possible)"
Write-Host "  2. Implement Android bridge in bridge.rs"
Write-Host "  3. Configure Tauri sidecar in tauri.conf.json"
Write-Host "  4. Build APK and test on device"

