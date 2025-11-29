$ErrorActionPreference = "Stop"

Write-Host "Extracting binary from Docker image..." -ForegroundColor Cyan

$ImageName = "python-android-build"
$BinariesDir = "d:\LP\frontend\src-tauri\binaries"
$OutputName = "python-sync-processor-aarch64-linux-android"

# Ensure binaries directory exists
if (-not (Test-Path $BinariesDir)) {
    New-Item -ItemType Directory -Path $BinariesDir -Force | Out-Null
    Write-Host "Created binaries directory: $BinariesDir" -ForegroundColor Green
}

# Create container
Write-Host "Creating container from image..." -ForegroundColor Yellow
$ContainerID = docker create $ImageName

if ($LASTEXITCODE -ne 0 -or -not $ContainerID) {
    Write-Host "ERROR: Failed to create container" -ForegroundColor Red
    exit 1
}

$ContainerID = $ContainerID.Trim()
Write-Host "Container ID: $ContainerID" -ForegroundColor Green

# Extract binary
Write-Host "Extracting binary..." -ForegroundColor Yellow
$TargetPath = Join-Path $BinariesDir $OutputName
docker cp "${ContainerID}:/app/python-sync-processor" $TargetPath

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to copy binary" -ForegroundColor Red
    docker rm $ContainerID | Out-Null
    exit 1
}

Write-Host "Binary copied successfully" -ForegroundColor Green

# Cleanup
docker rm $ContainerID | Out-Null
Write-Host "Container removed" -ForegroundColor Green

# Verify
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

