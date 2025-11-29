# Diagnostic script to check standalone mode errors
Write-Host "=== Standalone Mode Diagnostic ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] Clearing logcat and launching app..." -ForegroundColor Yellow
adb logcat -c
adb shell am start -n com.lessonplanner.bilingual/.MainActivity
Start-Sleep -Seconds 5

Write-Host "[2/3] Capturing logcat output..." -ForegroundColor Yellow
$logFile = "d:\LP\standalone-diagnostic.log"
adb logcat -d > $logFile
Write-Host "Logs saved to: $logFile" -ForegroundColor Green

Write-Host "[3/3] Searching for relevant errors..." -ForegroundColor Yellow
Write-Host ""

$patterns = @(
    "API",
    "Error",
    "error",
    "ERROR",
    "FATAL",
    "sql_query",
    "database",
    "Database",
    "users",
    "Users",
    "sidecar",
    "Sidecar",
    "standalone",
    "Standalone",
    "Tauri",
    "Cannot load"
)

$foundErrors = @()
Get-Content $logFile | ForEach-Object {
    $line = $_
    foreach ($pattern in $patterns) {
        if ($line -match $pattern) {
            $foundErrors += $line
            break
        }
    }
}

if ($foundErrors.Count -gt 0) {
    Write-Host "Found $($foundErrors.Count) relevant log lines:" -ForegroundColor Yellow
    Write-Host ""
    $foundErrors | Select-Object -Last 30 | ForEach-Object {
        Write-Host $_ -ForegroundColor Gray
    }
} else {
    Write-Host "No relevant errors found in logcat" -ForegroundColor Yellow
    Write-Host "Try checking the full log file: $logFile" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Diagnostic Complete ===" -ForegroundColor Cyan

