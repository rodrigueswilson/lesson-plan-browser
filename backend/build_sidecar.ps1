# Build Python Sidecar Binary for Tauri
# This script builds a standalone executable using PyInstaller

param(
    [string]$Target = "windows",  # windows, linux, android
    [switch]$Clean = $false
)

$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = $ScriptDir
$ProjectRoot = Split-Path -Parent $BackendDir
$BinariesDir = Join-Path $ProjectRoot "frontend\src-tauri\binaries"

Write-Host "=== Python Sidecar Build Script ===" -ForegroundColor Cyan
Write-Host "Backend directory: $BackendDir"
Write-Host "Binaries directory: $BinariesDir"
Write-Host "Target: $Target"
Write-Host ""

# Check PyInstaller
Write-Host "[1/5] Checking PyInstaller..." -ForegroundColor Yellow
try {
    $pyInstallerVersion = python -c "import PyInstaller; print(PyInstaller.__version__)" 2>&1
    Write-Host "  PyInstaller version: $pyInstallerVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: PyInstaller not found. Install with: pip install pyinstaller" -ForegroundColor Red
    exit 1
}

# Clean previous builds if requested
if ($Clean) {
    Write-Host "[2/5] Cleaning previous builds..." -ForegroundColor Yellow
    if (Test-Path (Join-Path $BackendDir "build")) {
        Remove-Item -Recurse -Force (Join-Path $BackendDir "build")
        Write-Host "  Removed build directory" -ForegroundColor Green
    }
    if (Test-Path (Join-Path $BackendDir "dist")) {
        Remove-Item -Recurse -Force (Join-Path $BackendDir "dist")
        Write-Host "  Removed dist directory" -ForegroundColor Green
    }
}

# Determine output name based on target
$OutputName = switch ($Target) {
    "windows" { "python-sync-processor-x86_64-pc-windows-msvc.exe" }
    "linux" { "python-sync-processor-linux" }
    "android" { "python-sync-processor-aarch64-linux-android" }
    default { "python-sync-processor.exe" }
}

Write-Host "[3/5] Building with PyInstaller..." -ForegroundColor Yellow
Write-Host "  Spec file: python-sync-processor.spec"
Write-Host "  Output name: $OutputName"
Write-Host ""

# Change to backend directory
Push-Location $BackendDir

try {
    # Run PyInstaller
    python -m PyInstaller python-sync-processor.spec --clean --noconfirm
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ERROR: PyInstaller build failed" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  Build completed successfully" -ForegroundColor Green
} finally {
    Pop-Location
}

# Copy to binaries directory
Write-Host "[4/5] Copying binary to Tauri binaries directory..." -ForegroundColor Yellow

# Ensure binaries directory exists
if (-not (Test-Path $BinariesDir)) {
    New-Item -ItemType Directory -Path $BinariesDir -Force | Out-Null
    Write-Host "  Created binaries directory" -ForegroundColor Green
}

# Find the built executable
$BuiltExe = Join-Path $BackendDir "dist\python-sync-processor.exe"
if (-not (Test-Path $BuiltExe)) {
    # Try without .exe extension (Linux)
    $BuiltExe = Join-Path $BackendDir "dist\python-sync-processor"
    if (-not (Test-Path $BuiltExe)) {
        Write-Host "  ERROR: Built executable not found in dist/" -ForegroundColor Red
        exit 1
    }
}

$TargetPath = Join-Path $BinariesDir $OutputName

# Copy file
Copy-Item -Path $BuiltExe -Destination $TargetPath -Force
Write-Host "  Copied to: $TargetPath" -ForegroundColor Green

# Verify file exists and get size
if (Test-Path $TargetPath) {
    $FileInfo = Get-Item $TargetPath
    $SizeMB = [math]::Round($FileInfo.Length / 1MB, 2)
    Write-Host "  File size: $SizeMB MB" -ForegroundColor Green
} else {
    Write-Host "  ERROR: File copy failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[5/5] Build Summary" -ForegroundColor Cyan
Write-Host "  Binary location: $TargetPath"
Write-Host "  Target platform: $Target"
Write-Host ""
Write-Host "SUCCESS: Sidecar binary built and copied!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Restart the Tauri app to test binary detection"
Write-Host "  2. Check Rust logs for '[Sidecar] Found bundled binary' message"
Write-Host "  3. Test sync functionality with bundled binary"

