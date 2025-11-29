# Quick Start Script for PC Testing
# This script helps you start the PC version for testing

Write-Host "`n=== Lesson Plan Browser - PC Testing Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "frontend\package.json")) {
    Write-Host "Error: Must be run from lesson-plan-browser directory" -ForegroundColor Red
    Write-Host "Please run: cd lesson-plan-browser" -ForegroundColor Yellow
    exit 1
}

# Check Node.js
Write-Host "Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "  ✓ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Node.js not found. Please install Node.js 18+" -ForegroundColor Red
    exit 1
}

# Check backend
Write-Host "`nChecking backend connection..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "  ✓ Backend is running on http://localhost:8000" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Backend not running on http://localhost:8000" -ForegroundColor Red
    Write-Host "    Please start the backend first:" -ForegroundColor Yellow
    Write-Host "      cd <main-project-root>" -ForegroundColor Yellow
    Write-Host "      python -m uvicorn backend.main:app --reload" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

# Check dependencies
Write-Host "`nChecking dependencies..." -ForegroundColor Yellow
Set-Location -Path "frontend"
if (-not (Test-Path "node_modules")) {
    Write-Host "  Installing dependencies (this may take a few minutes)..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ Failed to install dependencies" -ForegroundColor Red
        Set-Location -Path ".."
        exit 1
    }
    Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ✓ Dependencies already installed" -ForegroundColor Green
}

# Start the app
Write-Host "`n=== Starting Development Server ===" -ForegroundColor Cyan
Write-Host "This will:" -ForegroundColor Yellow
Write-Host "  1. Start Vite dev server" -ForegroundColor Yellow
Write-Host "  2. Compile Rust code (first run: 5-10 minutes)" -ForegroundColor Yellow
Write-Host "  3. Launch the Tauri app window" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop the server`n" -ForegroundColor Yellow

npm run tauri:dev

Set-Location -Path ".."

