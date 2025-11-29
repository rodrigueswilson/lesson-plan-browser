# Build script for physical tablet APK
# Usage: .\build-tablet.ps1 -PC_IP "192.168.1.100" [-Standalone]

param(
    [Parameter(Mandatory=$true)]
    [string]$PC_IP = "",
    
    [switch]$Standalone = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Building APK for Physical Tablet" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Validate PC IP format
if ($PC_IP -notmatch '^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$') {
    Write-Host "ERROR: Invalid IP address format: $PC_IP" -ForegroundColor Red
    Write-Host "Expected format: 192.168.1.100" -ForegroundColor Yellow
    exit 1
}

# Set environment variables
$apiUrl = "http://$PC_IP:8000/api"
$env:VITE_API_BASE_URL = $apiUrl
$env:VITE_ANDROID_API_BASE_URL = $apiUrl
Write-Host "✓ API URL configured: $apiUrl" -ForegroundColor Green

if ($Standalone) {
    $env:VITE_ENABLE_STANDALONE_DB = "true"
    Write-Host "✓ Standalone mode enabled (local database)" -ForegroundColor Green
} else {
    $env:VITE_ENABLE_STANDALONE_DB = "false"
    Write-Host "✓ WiFi-connected mode (using PC backend)" -ForegroundColor Green
}

$env:NODE_ENV = "production"
$env:TAURI_DEBUG = "false"

Write-Host ""
Write-Host "Environment variables set:" -ForegroundColor Yellow
Write-Host "  VITE_API_BASE_URL = $env:VITE_API_BASE_URL"
Write-Host "  VITE_ANDROID_API_BASE_URL = $env:VITE_ANDROID_API_BASE_URL"
Write-Host "  VITE_ENABLE_STANDALONE_DB = $env:VITE_ENABLE_STANDALONE_DB"
Write-Host "  NODE_ENV = $env:NODE_ENV"
Write-Host ""

# Change to frontend directory
Push-Location frontend

try {
    Write-Host "Step 1: Building frontend bundle..." -ForegroundColor Cyan
    npm run build:skip-check
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Frontend build failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Frontend build complete" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Step 2: Building Android APK (release mode)..." -ForegroundColor Cyan
    Write-Host "This may take several minutes..." -ForegroundColor Yellow
    npm run tauri android build -- --release
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Android build failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Android APK build complete" -ForegroundColor Green
    Write-Host ""
    
    # Find APK location
    $apkPaths = @(
        "src-tauri/gen/android/app/build/outputs/apk/universal/release/app-universal-release.apk",
        "src-tauri/gen/android/app/build/outputs/apk/arm64-v8a/release/app-arm64-v8a-release.apk",
        "src-tauri/gen/android/app/build/outputs/apk/armeabi-v7a/release/app-armeabi-v7a-release.apk"
    )
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Build Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "APK locations:" -ForegroundColor Yellow
    
    foreach ($apkPath in $apkPaths) {
        $fullPath = Join-Path (Get-Location) $apkPath
        if (Test-Path $fullPath) {
            $size = (Get-Item $fullPath).Length / 1MB
            Write-Host "  ✓ $fullPath ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
        }
    }
    
    Write-Host ""
    Write-Host "To install on tablet:" -ForegroundColor Yellow
    Write-Host "  adb install -r `"<APK_PATH>`"" -ForegroundColor White
    Write-Host ""
    
} finally {
    Pop-Location
}

