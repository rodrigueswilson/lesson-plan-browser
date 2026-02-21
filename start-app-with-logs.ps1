# Start App with Log Capture for Cursor
# This script runs backend and frontend in a way that allows Cursor to access logs
# Usage: Run this script in a Cursor terminal

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Bilingual Lesson Planner - With Logs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create logs directory if it doesn't exist
$logsDir = "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}

# Generate timestamp for log files
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backendLog = "$logsDir\backend_$timestamp.log"
$frontendLog = "$logsDir\frontend_$timestamp.log"

Write-Host "Log files will be saved to:" -ForegroundColor Yellow
Write-Host "  Backend:  $backendLog" -ForegroundColor Gray
Write-Host "  Frontend: $frontendLog" -ForegroundColor Gray
Write-Host ""

# Check if Python is installed
$pythonCheck = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCheck) {
    Write-Host "ERROR: Python is not installed or not in PATH!" -ForegroundColor Red
    pause
    exit 1
}

# Check if Node.js is installed
$nodeCheck = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCheck) {
    Write-Host "ERROR: Node.js is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Node.js 18+ from https://nodejs.org/" -ForegroundColor Yellow
    pause
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Expected: .venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "Please create the virtual environment first:" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor White
    Write-Host "  . .venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "  pip install -r requirements.txt" -ForegroundColor White
    pause
    exit 1
}

# Check for existing processes on port 8000
Write-Host "Checking for existing backend servers..." -ForegroundColor Yellow
$port = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($port) {
    # There can be multiple connections/listeners; stop all unique non-zero owning PIDs.
    $processIds = @($port | Select-Object -ExpandProperty OwningProcess -Unique) | Where-Object { $_ -and $_ -ne 0 }
    foreach ($processId in $processIds) {
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
    }
}

Write-Host ""
Write-Host "Starting Prometheus Monitoring (if needed)..." -ForegroundColor Yellow
if (Test-Path "start-prometheus.ps1") {
    Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-File", "start-prometheus.ps1" -WindowStyle Hidden -ErrorAction SilentlyContinue
} else {
    Write-Host "[INFO] Prometheus script not found, skipping..." -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Backend API Server..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start backend in a background job that logs to file
$backendLogPath = (Join-Path (Get-Location).Path $backendLog)
$backendJob = Start-Job -ScriptBlock {
    param($logPath, $scriptPath)
    Set-Location $scriptPath
    . .venv\Scripts\Activate.ps1
    # Use cmd.exe so native stderr doesn't get surfaced as PowerShell NativeCommandError records.
    cmd /c "python -m uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000 2>&1" | Tee-Object -FilePath $logPath
} -ArgumentList $backendLogPath, (Get-Location).Path

Write-Host "Backend started (Job ID: $($backendJob.Id))" -ForegroundColor Green
Write-Host "Logging to: $backendLog" -ForegroundColor Gray
Write-Host ""

# Wait for backend to start
Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
$backendReady = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        # Try multiple methods to check if backend is ready
        $response = $null
        try {
            # Use 127.0.0.1 to avoid IPv6 (::1) resolution issues on machines without IPv6 binding.
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        } catch {
            # If WebRequest fails, try using Test-NetConnection to check if port is open
            $tcpTest = Test-NetConnection -ComputerName 127.0.0.1 -Port 8000 -WarningAction SilentlyContinue -InformationLevel Quiet
            if ($tcpTest) {
                # Port is open, assume backend is ready even if health check failed
                $backendReady = $true
                break
            }
        }
        if ($response -and $response.StatusCode -eq 200) {
            $backendReady = $true
            break
        }
    } catch {
        # Backend not ready yet, continue waiting
    }
    if ($i -eq 0 -or ($i % 5) -eq 0) {
        Write-Host "  Still waiting... ($i/30)" -ForegroundColor Gray
    }
}

if ($backendReady) {
    Write-Host "Backend is ready!" -ForegroundColor Green
} else {
    Write-Host "Backend may still be starting... (check logs)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Frontend (Tauri)..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check for existing processes on port 1420 (Vite/Tauri dev server)
Write-Host "Checking for existing frontend dev server..." -ForegroundColor Yellow
$frontendPort = Get-NetTCPConnection -LocalPort 1420 -ErrorAction SilentlyContinue
if ($frontendPort) {
    $frontendPid = $frontendPort.OwningProcess
    $frontendProc = Get-Process -Id $frontendPid -ErrorAction SilentlyContinue
    if ($frontendProc) {
        Write-Host "Found existing frontend dev server (PID: $frontendPid) on port 1420" -ForegroundColor Yellow
        Write-Host "Stopping process $frontendPid..." -ForegroundColor Yellow
        try {
            Stop-Process -Id $frontendPid -Force -ErrorAction Stop
            Start-Sleep -Seconds 2
            Write-Host "Process stopped successfully" -ForegroundColor Green
        } catch {
            Write-Host "Warning: Could not stop frontend process: $_" -ForegroundColor Red
        }
    }
}

# Start frontend in a background job that logs to file
$frontendLogPath = (Join-Path (Get-Location).Path $frontendLog)
Write-Host "Starting frontend in the current session (so the Tauri window can open)..." -ForegroundColor Yellow
Write-Host "Logging to: $frontendLog" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Both services are running!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend: http://localhost:8000" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/api/docs" -ForegroundColor White
Write-Host "Frontend: Will open automatically" -ForegroundColor White
Write-Host ""
Write-Host "Log files:" -ForegroundColor Yellow
Write-Host "  Backend:  $backendLog" -ForegroundColor Gray
Write-Host "  Frontend: $frontendLog" -ForegroundColor Gray
Write-Host ""
Write-Host "To view logs in real-time, run:" -ForegroundColor Yellow
Write-Host "  Get-Content $backendLog -Wait -Tail 50" -ForegroundColor White
Write-Host "  Get-Content $frontendLog -Wait -Tail 50" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Function to cleanup on exit
function Cleanup {
    Write-Host ""
    Write-Host "Stopping services..." -ForegroundColor Yellow
    Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob -ErrorAction SilentlyContinue
    Write-Host "Services stopped." -ForegroundColor Green
}

# Register cleanup on script exit
Register-EngineEvent PowerShell.Exiting -Action { Cleanup } | Out-Null

try {
    $scriptPath = (Get-Location).Path
    Set-Location "$scriptPath\frontend"

    # Tauri's generate_context!() requires frontendDist to exist, even during dev.
    if (-not (Test-Path "dist")) {
        New-Item -ItemType Directory -Path "dist" | Out-Null
    }

    # Use cmd.exe so native stderr doesn't get surfaced as PowerShell NativeCommandError records.
    cmd /c "npm run tauri:dev 2>&1" | Tee-Object -FilePath $frontendLogPath
} catch {
    Write-Host "`nStopping..." -ForegroundColor Yellow
} finally {
    Cleanup
}
