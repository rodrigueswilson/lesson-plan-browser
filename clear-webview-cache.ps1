# Clear WebView cache and force reload
$ErrorActionPreference = "Stop"

Write-Host "=== Clearing WebView Cache ===" -ForegroundColor Cyan
Write-Host ""

$PackageName = "com.lessonplanner.bilingual"

# Check device
$devices = adb devices | Select-String -Pattern "device$"
if (-not $devices) {
    Write-Host "ERROR: No device found" -ForegroundColor Red
    exit 1
}
$DeviceId = ($devices.ToString().Split("`t")[0])
Write-Host "Found device: $DeviceId" -ForegroundColor Green

Write-Host "`nStopping app..." -ForegroundColor Yellow
adb -s $DeviceId shell am force-stop $PackageName

Write-Host "Clearing app data (includes WebView cache)..." -ForegroundColor Yellow
adb -s $DeviceId shell pm clear $PackageName

Write-Host "Clearing WebView cache specifically..." -ForegroundColor Yellow
adb -s $DeviceId shell pm clear com.android.webview
adb -s $DeviceId shell pm clear com.google.android.webview

Write-Host "`n✅ Cache cleared!" -ForegroundColor Green
Write-Host "Reinstall the app now:" -ForegroundColor Yellow
Write-Host "  .\fresh-install.ps1" -ForegroundColor Cyan

