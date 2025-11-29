# Diagnostic Script for Android App Installation
# This will write results to a file so you can see them

$logFile = "d:\LP\install-diagnosis.txt"
"=== Android App Installation Diagnosis ===" | Out-File $logFile
"" | Out-File -Append $logFile

# 1. Check ADB devices
"1. Checking ADB device connection..." | Out-File -Append $logFile
$devices = adb devices 2>&1 | Out-String
$devices | Out-File -Append $logFile
$deviceCount = ($devices -split "`n" | Where-Object { $_ -match "device$" }).Count - 1
if ($deviceCount -eq 0) {
    "   ERROR: No devices connected!" | Out-File -Append $logFile
    "   Please connect tablet via USB and enable USB debugging" | Out-File -Append $logFile
} else {
    "   OK: Found $deviceCount device(s)" | Out-File -Append $logFile
}
"" | Out-File -Append $logFile

# 2. Check tablet architecture
"2. Checking tablet architecture..." | Out-File -Append $logFile
$arch = adb shell getprop ro.product.cpu.abi 2>&1 | Out-String
$arch | Out-File -Append $logFile
"" | Out-File -Append $logFile

# 3. Check if app is installed
"3. Checking if app is installed..." | Out-File -Append $logFile
$packages = adb shell pm list packages 2>&1 | Out-String
if ($packages -match "lessonplanner|bilingual") {
    "   SUCCESS: App IS installed" | Out-File -Append $logFile
    ($packages -split "`n" | Where-Object { $_ -match "lessonplanner|bilingual" }) | Out-File -Append $logFile
} else {
    "   App is NOT installed" | Out-File -Append $logFile
}
"" | Out-File -Append $logFile

# 4. Check APK file
"4. Checking APK file..." | Out-File -Append $logFile
$apk = "d:\LP\frontend\src-tauri\gen\android\app\build\outputs\apk\arm64\debug\app-arm64-debug.apk"
if (Test-Path $apk) {
    $size = [math]::Round((Get-Item $apk).Length / 1MB, 2)
    "   APK found: $size MB" | Out-File -Append $logFile
    "   Location: $apk" | Out-File -Append $logFile
} else {
    "   ERROR: APK not found!" | Out-File -Append $logFile
}
"" | Out-File -Append $logFile

# 5. Try to install
"5. Attempting installation..." | Out-File -Append $logFile
$installOutput = adb install -r -d $apk 2>&1 | Out-String
$installOutput | Out-File -Append $logFile
"" | Out-File -Append $logFile

# 6. Try to launch
"6. Attempting to launch app..." | Out-File -Append $logFile
$launchOutput = adb shell am start -n com.lessonplanner.bilingual/.MainActivity 2>&1 | Out-String
$launchOutput | Out-File -Append $logFile
"" | Out-File -Append $logFile

# 7. Recommendations
"=== Recommendations ===" | Out-File -Append $logFile
if ($packages -match "lessonplanner") {
    "App appears to be installed. If you don't see it in launcher:" | Out-File -Append $logFile
    "  1. Try launching directly: adb shell am start -n com.lessonplanner.bilingual/.MainActivity" | Out-File -Append $logFile
    "  2. Check app drawer (may need to scroll or search)" | Out-File -Append $logFile
    "  3. Look for 'Bilingual Lesson Planner' in app list" | Out-File -Append $logFile
} else {
    "App is not installed. Installation was attempted above." | Out-File -Append $logFile
    "Check the installation output for errors." | Out-File -Append $logFile
}

Write-Host "Diagnosis complete! Results saved to: $logFile" -ForegroundColor Green
Write-Host "Opening file..." -ForegroundColor Yellow
notepad $logFile

