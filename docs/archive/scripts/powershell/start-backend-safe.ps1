# Safe Backend Startup Script
# Stops existing backend processes before starting a new one

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Backend API Server (Safe Mode)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
$pythonCheck = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCheck) {
    Write-Host "ERROR: Python is not installed or not in PATH!" -ForegroundColor Red
    pause
    exit 1
}

# Check for existing processes on port 8000
Write-Host "Checking for existing backend servers..." -ForegroundColor Yellow
$port = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($port) {
    $processId = $port.OwningProcess
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    
    if ($process) {
        Write-Host "Found existing backend server (PID: $processId)" -ForegroundColor Yellow
        Write-Host "Stopping process $processId..." -ForegroundColor Yellow
        try {
            Stop-Process -Id $processId -Force -ErrorAction Stop
            Start-Sleep -Seconds 2
            Write-Host "Process stopped successfully" -ForegroundColor Green
        } catch {
            Write-Host "Warning: Could not stop process: $_" -ForegroundColor Red
        }
    }
} else {
    Write-Host "No existing server found on port 8000" -ForegroundColor Green
}

# Check for other Python processes that might be uvicorn
Write-Host "`nChecking for other uvicorn processes..." -ForegroundColor Yellow
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*backend.api*"
}

if ($pythonProcesses) {
    Write-Host "Found additional Python processes that might be backend servers" -ForegroundColor Yellow
    foreach ($proc in $pythonProcesses) {
        Write-Host "  PID: $($proc.Id) - Started: $($proc.StartTime)" -ForegroundColor Yellow
    }
    $response = Read-Host "Stop these processes? (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        foreach ($proc in $pythonProcesses) {
            try {
                Stop-Process -Id $proc.Id -Force -ErrorAction Stop
                Write-Host "Stopped process $($proc.Id)" -ForegroundColor Green
            } catch {
                Write-Host "Could not stop process $($proc.Id): $_" -ForegroundColor Red
            }
        }
        Start-Sleep -Seconds 2
    }
}

# Verify port is free
Write-Host "`nVerifying port 8000 is available..." -ForegroundColor Yellow
Start-Sleep -Seconds 1
$portCheck = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portCheck) {
    Write-Host "WARNING: Port 8000 is still in use!" -ForegroundColor Red
    Write-Host "You may need to manually stop the process or use a different port." -ForegroundColor Yellow
    pause
    exit 1
} else {
    Write-Host "Port 8000 is available" -ForegroundColor Green
}

# Check if uvicorn is installed
Write-Host "`nChecking for uvicorn..." -ForegroundColor Yellow
$uvicornCheck = python -c "import uvicorn" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing uvicorn and dependencies..." -ForegroundColor Yellow
    pip install uvicorn fastapi sse-starlette
    Write-Host ""
}

Write-Host "`nStarting backend server on http://0.0.0.0:8000" -ForegroundColor Cyan
Write-Host "API Documentation: http://localhost:8000/api/docs" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
python -m uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000

