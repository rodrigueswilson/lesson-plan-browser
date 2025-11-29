# Build script for PC (Windows) version
# Creates a desktop executable for Windows

Write-Host "Building PC version of Lesson Plan Browser..." -ForegroundColor Green

# Navigate to frontend directory
Set-Location -Path "frontend"

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install dependencies!" -ForegroundColor Red
        exit 1
    }
}

# Build the application
Write-Host "Building Tauri application for Windows..." -ForegroundColor Yellow
npm run tauri:build

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    Set-Location -Path ".."
    exit 1
}

Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "Output location: frontend\src-tauri\target\release" -ForegroundColor Cyan

Set-Location -Path ".."

