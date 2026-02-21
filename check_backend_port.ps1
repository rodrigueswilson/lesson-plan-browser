# Check if backend is running on port 8000
Write-Host "Checking for backend server on port 8000..." -ForegroundColor Cyan

$port = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($port) {
    $processId = $port.OwningProcess
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    
    if ($process) {
        Write-Host "`nBackend server is already running!" -ForegroundColor Yellow
        Write-Host "Process ID: $processId" -ForegroundColor Yellow
        Write-Host "Process Name: $($process.ProcessName)" -ForegroundColor Yellow
        Write-Host "Start Time: $($process.StartTime)" -ForegroundColor Yellow
        Write-Host "`nTo stop it, run:" -ForegroundColor Cyan
        Write-Host "  Stop-Process -Id $processId" -ForegroundColor White
        Write-Host "`nOr kill all Python processes:" -ForegroundColor Cyan
        Write-Host "  Get-Process python | Stop-Process" -ForegroundColor White
    } else {
        Write-Host "Port 8000 is in use but process not found" -ForegroundColor Red
    }
} else {
    Write-Host "Port 8000 is available" -ForegroundColor Green
}

