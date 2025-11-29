# Aggressive WebView cache clearing
$ErrorActionPreference = "Continue"  # Continue on errors to complete all steps

Write-Host "=== Aggressive WebView Cache Clear ===" -ForegroundColor Cyan
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
Write-Host ""

Write-Host "[1/6] Stopping app..." -ForegroundColor Yellow
adb -s $DeviceId shell am force-stop $PackageName
Start-Sleep -Seconds 1

Write-Host "[2/6] Clearing app data (includes WebView cache)..." -ForegroundColor Yellow
adb -s $DeviceId shell pm clear $PackageName
Start-Sleep -Seconds 1

Write-Host "[3/6] Clearing system WebView cache..." -ForegroundColor Yellow
# Try to clear system WebView (may fail without root, that's OK)
$result1 = adb -s $DeviceId shell pm clear com.android.webview 2>&1
$result2 = adb -s $DeviceId shell pm clear com.google.android.webview 2>&1
# Don't fail if these don't work (they require system permissions)
Write-Host "  (System WebView cache clear attempted - may require root)" -ForegroundColor Gray
Start-Sleep -Seconds 1

Write-Host "[4/6] Clearing app-specific WebView storage..." -ForegroundColor Yellow
# Try to remove WebView directories (may fail without root, but app data clear should handle it)
$AppDataDir = "/data/data/$PackageName"
$WebViewDirs = @(
    "$AppDataDir/app_webview",
    "$AppDataDir/cache",
    "$AppDataDir/files/cache",
    "$AppDataDir/code_cache"
)

foreach ($dir in $WebViewDirs) {
    try {
        $result = adb -s $DeviceId shell "rm -rf $dir 2>/dev/null && echo 'cleared' || echo 'not_found'" 2>&1
        if ($result -match "cleared") {
            Write-Host "  ✅ Cleared: $dir" -ForegroundColor Green
        }
    } catch {
        # Ignore errors - app data clear should handle this
    }
}

Write-Host "[5/6] Uninstalling app (removes all cached data)..." -ForegroundColor Yellow
adb -s $DeviceId uninstall $PackageName 2>&1 | Out-Null
Start-Sleep -Seconds 1

Write-Host "[6/6] Reinstalling fresh APK..." -ForegroundColor Yellow
$APKPath = "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"

if (-not (Test-Path $APKPath)) {
    Write-Host "ERROR: APK not found at: $APKPath" -ForegroundColor Red
    Write-Host "Please build the APK first." -ForegroundColor Yellow
    exit 1
}

adb -s $DeviceId install $APKPath
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Installation failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Aggressive cache clear complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Launch the app" -ForegroundColor Cyan
Write-Host "  2. Check logcat for which file it loads:" -ForegroundColor Cyan
Write-Host "     adb logcat -d | Select-String -Pattern 'index-.*\.js'" -ForegroundColor Gray
Write-Host ""
Write-Host "If it still loads the old file, try:" -ForegroundColor Yellow
Write-Host "  - Restart the device" -ForegroundColor Cyan
Write-Host "  - Clear all app data from Android Settings" -ForegroundColor Cyan

