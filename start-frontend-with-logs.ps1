# Start Frontend with Log Capture for Cursor
# This script runs the frontend in the current terminal with log capture
# Usage: Run this script in a Cursor terminal (in a separate terminal from backend)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Frontend (Tauri) (With Logs)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create logs directory if it doesn't exist
$logsDir = "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}

# Generate timestamp for log file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$frontendLog = "$logsDir\frontend_$timestamp.log"

Write-Host "Log file: $frontendLog" -ForegroundColor Yellow
Write-Host ""

# Check if Node.js is installed
$nodeCheck = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCheck) {
    Write-Host "ERROR: Node.js is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Node.js 18+ from https://nodejs.org/" -ForegroundColor Yellow
    pause
    exit 1
}

# Check if frontend directory exists
if (-not (Test-Path "frontend")) {
    Write-Host "ERROR: frontend directory not found!" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "Starting frontend..." -ForegroundColor Cyan
Write-Host "Output will be displayed here AND saved to: $frontendLog" -ForegroundColor Gray
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Get absolute path to log file before changing directory
$logPath = Join-Path (Get-Location).Path $frontendLog

# Change to frontend directory and start with log capture
Set-Location frontend
# Use cmd.exe so native stderr doesn't get surfaced as PowerShell NativeCommandError records.
cmd /c "npm run tauri:dev 2>&1" | Tee-Object -FilePath $logPath
