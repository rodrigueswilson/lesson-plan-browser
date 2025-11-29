# Capture error logs from Android device
Write-Host "=== Capturing Error Logs ===" -ForegroundColor Cyan

$LogFile = "d:\LP\error-logs.txt"

Write-Host "Clearing logcat..." -ForegroundColor Yellow
adb logcat -c
Start-Sleep -Seconds 1

Write-Host "Launching app..." -ForegroundColor Yellow
adb shell am start -n com.lessonplanner.bilingual/.MainActivity
Start-Sleep -Seconds 5

Write-Host "Capturing logcat output..." -ForegroundColor Yellow
adb logcat -d | Out-File -FilePath $LogFile -Encoding UTF8

Write-Host "Searching for relevant errors..." -ForegroundColor Yellow
$errorLines = Get-Content $LogFile | Select-String -Pattern "API|Error|error|ERROR|FATAL|sql_query|database|Database|standalone|Standalone|Cannot|load|users|Tauri|tauri" -Context 0,2

Write-Host "`n=== Found $($errorLines.Count) relevant log lines ===" -ForegroundColor Cyan
$errorLines | Select-Object -Last 50 | ForEach-Object {
    Write-Host $_
}

Write-Host "`n=== Full log saved to: $LogFile ===" -ForegroundColor Green
Write-Host "Review the file for complete error details." -ForegroundColor Gray

