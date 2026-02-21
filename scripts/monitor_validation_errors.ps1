# Monitor validation errors in real-time
# Usage: .\scripts\monitor_validation_errors.ps1

$logFile = "logs\backend_20251228_183327.log"

Write-Host "Monitoring for validation errors..." -ForegroundColor Cyan
Write-Host "Watching: $logFile" -ForegroundColor Gray
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Gray

Get-Content $logFile -Wait -Tail 20 | ForEach-Object {
    if ($_ -match "llm_validation_failed|llm_retry_attempt|llm_transform_success|llm_transform_failed|enum_serialization|parsed_errors") {
        Write-Host $_ -ForegroundColor Yellow
    }
    elseif ($_ -match "ERROR|WARNING.*validation|validation.*error") {
        Write-Host $_ -ForegroundColor Red
    }
}
