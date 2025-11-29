# Python Bundling Script for Android (PowerShell)
# Creates standalone executable for Tauri sidecar

Write-Host "=== Python Sidecar Bundling ===" -ForegroundColor Cyan

# Check if we're in the project root
if (-not (Test-Path "backend")) {
    Write-Host "Error: Must run from project root" -ForegroundColor Red
    exit 1
}

# Install bundling tool
Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
pip install pyinstaller

# Create output directory
$OUTPUT_DIR = "frontend/src-tauri/binaries"
if (-not (Test-Path $OUTPUT_DIR)) {
    New-Item -ItemType Directory -Path $OUTPUT_DIR -Force | Out-Null
}

# Build for Linux ARM64 (Android)
# Note: On Windows, we'll build for Windows first, then cross-compile for Android
Write-Host "Building Python executable..." -ForegroundColor Yellow

# For now, build Windows version for testing
# For Android, we'll need Docker or Linux environment
pyinstaller `
    --onefile `
    --name python-sync-processor `
    --distpath $OUTPUT_DIR `
    --workpath $env:TEMP/pyinstaller-work `
    --clean `
    --hidden-import=backend `
    --hidden-import=backend.ipc_database `
    --hidden-import=backend.supabase_database `
    --hidden-import=backend.schema `
    --hidden-import=backend.database `
    --hidden-import=supabase `
    --hidden-import=postgrest `
    --hidden-import=storage `
    --hidden-import=realtime `
    --collect-all supabase `
    --collect-all postgrest `
    backend/sidecar_main.py

# Check if build succeeded
$binaryPath = Join-Path $OUTPUT_DIR "python-sync-processor.exe"
if (Test-Path $binaryPath) {
    Write-Host "✅ Windows binary created: $binaryPath" -ForegroundColor Green
    
    # For Android, we need Linux ARM64 binary
    Write-Host "`n⚠️  Note: This is a Windows binary." -ForegroundColor Yellow
    Write-Host "For Android, you need to build Linux ARM64 binary using:" -ForegroundColor Yellow
    Write-Host "  - Docker (recommended)" -ForegroundColor Yellow
    Write-Host "  - Linux VM/WSL" -ForegroundColor Yellow
    Write-Host "  - Cross-compilation toolchain" -ForegroundColor Yellow
} else {
    Write-Host "❌ Build failed - binary not found" -ForegroundColor Red
    exit 1
}

# Clean up
if (Test-Path "$env:TEMP/pyinstaller-work") {
    Remove-Item -Recurse -Force "$env:TEMP/pyinstaller-work"
}
if (Test-Path "python-sync-processor.spec") {
    Remove-Item -Force "python-sync-processor.spec"
}

Write-Host "`n✅ Bundling complete!" -ForegroundColor Green

