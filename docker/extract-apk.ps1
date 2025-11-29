# PowerShell script to extract APK from Docker container
# Run after Docker build completes

Write-Host "📦 Extracting APK from Docker container..." -ForegroundColor Green

# Check if container exists and is running
$container = docker ps -a --filter "name=tauri-android-builder" --format "{{.Names}}"
if (-not $container) {
    Write-Host "❌ Docker container 'tauri-android-builder' not found." -ForegroundColor Red
    Write-Host "Please run the Docker build first: ./docker/build-android.sh" -ForegroundColor Yellow
    exit 1
}

# Extract APK
$apkPath = "app-arm64-debug.apk"
$containerPath = "/app/frontend/src-tauri/gen/android/app/build/outputs/apk/arm64/debug/app-arm64-debug.apk"

try {
    docker cp tauri-android-builder:$containerPath $apkPath
    Write-Host "✅ APK extracted successfully: $apkPath" -ForegroundColor Green
    
    # Show file info
    $fileInfo = Get-Item $apkPath
    Write-Host "📊 File size: $([math]::Round($fileInfo.Length / 1MB, 2)) MB" -ForegroundColor Cyan
    Write-Host "📅 Created: $($fileInfo.CreationTime)" -ForegroundColor Cyan
    
    # Offer to install
    Write-Host ""
    Write-Host "🚀 To install on device:" -ForegroundColor Yellow
    Write-Host "   adb install $apkPath" -ForegroundColor White
    
} catch {
    Write-Host "❌ Failed to extract APK: $_" -ForegroundColor Red
    Write-Host "Make sure the Docker build completed successfully." -ForegroundColor Yellow
    exit 1
}
