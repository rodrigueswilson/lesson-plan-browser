# Stop FastAPI Application
# Usage: .\scripts\stop_fastapi.ps1

Write-Host "Stopping FastAPI application on port 8000..." -ForegroundColor Cyan

# Find processes using port 8000
$connections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if (-not $connections) {
    Write-Host "No process found using port 8000." -ForegroundColor Yellow
    exit 0
}

foreach ($conn in $connections) {
    $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "Found process: $($process.ProcessName) (PID: $($process.Id))" -ForegroundColor Yellow
        
        # Ask for confirmation
        $confirm = Read-Host "Stop this process? (Y/N)"
        if ($confirm -eq 'Y' -or $confirm -eq 'y') {
            Stop-Process -Id $process.Id -Force
            Write-Host "Stopped process $($process.Id)" -ForegroundColor Green
        }
    }
}

Write-Host "Done." -ForegroundColor Green

