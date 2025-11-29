# Quick Installation Status Checker
Write-Host "=== Android App Installation Status ===" -ForegroundColor Cyan
Write-Host ""

# 1. Check device
Write-Host "1. Checking device connection..." -ForegroundColor Yellow
$devices = adb devices 2>&1
$devices | ForEach-Object { Write-Host $_ }
$deviceCount = ($devices | Select-String "device$").Count - 1
if ($deviceCount -eq 0) {
    Write-Host "   ERROR: No devices found!" -ForegroundColor Red
    exit 1
} else {
    Write-Host "   OK: $deviceCount device(s) connected" -ForegroundColor Green
}
Write-Host ""

# 2. Check if app is installed
Write-Host "2. Checking if app is installed..." -ForegroundColor Yellow
$packages = adb shell pm list packages 2>&1 | Out-String
if ($packages -match "lessonplanner|bilingual") {
    Write-Host "   SUCCESS: App IS installed" -ForegroundColor Green
    $packageName = ($packages -split "`n" | Select-String "lessonplanner|bilingual").ToString().Replace("package:","")
    Write-Host "   Package: $packageName" -ForegroundColor Gray
} else {
    Write-Host "   App is NOT installed" -ForegroundColor Red
}
Write-Host ""

# 3. Check APK file
Write-Host "3. Checking APK file..." -ForegroundColor Yellow
$apk = "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"
if (Test-Path $apk) {
    $size = [math]::Round((Get-Item $apk).Length / 1MB, 2)
    Write-Host "   OK: APK found ($size MB)" -ForegroundColor Green
} else {
    Write-Host "   ERROR: APK not found!" -ForegroundColor Red
}
Write-Host ""

# 4. Try to launch app
Write-Host "4. Attempting to launch app..." -ForegroundColor Yellow
$launch = adb shell am start -n com.lessonplanner.bilingual/.MainActivity 2>&1 | Out-String
if ($launch -match "Starting|Activity") {
    Write-Host "   SUCCESS: Launch command sent" -ForegroundColor Green
} else {
    Write-Host "   Launch result: $launch" -ForegroundColor Yellow
}
Write-Host ""

# 5. Summary
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "If app is installed but not visible:"
Write-Host "  - Try: adb shell am start -n com.lessonplanner.bilingual/.MainActivity"
Write-Host "  - Check tablet's app drawer (may need to scroll or search)"
Write-Host ""
Write-Host "If app is NOT installed:"
Write-Host "  - Run: .\install-android-app.ps1"
Write-Host "  - Or manually: adb install -r `"$apk`""

