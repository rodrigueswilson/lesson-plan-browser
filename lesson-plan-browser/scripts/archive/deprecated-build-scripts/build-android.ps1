# Build script for Android APK
# Creates an Android APK file for tablet deployment

Write-Host "Building Android version of Lesson Plan Browser..." -ForegroundColor Green

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

# Check if Android SDK is configured
Write-Host "Checking Android build environment..." -ForegroundColor Yellow

# Build Android APK
Write-Host "Building Android APK..." -ForegroundColor Yellow
Write-Host "Note: This will take several minutes on first build" -ForegroundColor Cyan

npm run android:build

if ($LASTEXITCODE -ne 0) {
    Write-Host "Android build failed!" -ForegroundColor Red
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  - Android SDK not configured" -ForegroundColor Yellow
    Write-Host "  - Rust Android targets not installed" -ForegroundColor Yellow
    Write-Host "  - Java JDK not found" -ForegroundColor Yellow
    Set-Location -Path ".."
    exit 1
}

Write-Host "Android build completed successfully!" -ForegroundColor Green
Write-Host "APK location: frontend\src-tauri\target\android\app\build\outputs\apk\release" -ForegroundColor Cyan

Set-Location -Path ".."

