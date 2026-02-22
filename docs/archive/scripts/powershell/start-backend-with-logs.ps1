# Start Backend with Log Capture for Cursor
# This script runs the backend in the current terminal with log capture
# Usage: Run this script in a Cursor terminal

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Backend API Server (With Logs)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create logs directory if it doesn't exist
$logsDir = "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}

# Generate timestamp for log file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backendLog = "$logsDir\backend_$timestamp.log"

Write-Host "Log file: $backendLog" -ForegroundColor Yellow
Write-Host ""

# Check if Python is installed
$pythonCheck = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCheck) {
    Write-Host "ERROR: Python is not installed or not in PATH!" -ForegroundColor Red
    pause
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Expected: .venv\Scripts\Activate.ps1" -ForegroundColor Yellow
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
}

Write-Host ""
Write-Host "Starting backend server..." -ForegroundColor Cyan
Write-Host "Output will be displayed here AND saved to: $backendLog" -ForegroundColor Gray
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Activate virtual environment and start backend with log capture
. .venv\Scripts\Activate.ps1
# Suppress PowerShell error interpretation of INFO messages
$ErrorActionPreference = "SilentlyContinue"
python -m uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000 2>&1 | Tee-Object -FilePath $backendLog
