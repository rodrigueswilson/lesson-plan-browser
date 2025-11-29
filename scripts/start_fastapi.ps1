# Start FastAPI Application
# Usage: .\scripts\start_fastapi.ps1

Write-Host "Starting FastAPI application..." -ForegroundColor Cyan

# Check if port 8000 is already in use
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "Port 8000 is already in use!" -ForegroundColor Yellow
    Write-Host "Please stop the existing process first, or use a different port." -ForegroundColor Yellow
    exit 1
}

# Check if uvicorn is available
$uvicorn = Get-Command uvicorn -ErrorAction SilentlyContinue
if (-not $uvicorn) {
    Write-Host "uvicorn not found. Installing..." -ForegroundColor Yellow
    pip install uvicorn[standard]
}

# Start FastAPI with uvicorn
Write-Host "`nStarting FastAPI on http://0.0.0.0:8000" -ForegroundColor Green
Write-Host "Metrics endpoint: http://localhost:8000/metrics" -ForegroundColor Green
Write-Host "API docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "`nPress Ctrl+C to stop`n" -ForegroundColor Yellow

# Start uvicorn
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000

