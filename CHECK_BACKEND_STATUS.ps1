# Check Backend Status and Start if Needed

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Backend Status Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if backend is running
Write-Host "[1/3] Checking if backend is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 2
    Write-Host "✓ Backend is running!" -ForegroundColor Green
    Write-Host "  Status: $($response.StatusCode)" -ForegroundColor Gray
    $healthData = $response.Content | ConvertFrom-Json
    Write-Host "  Health: $($healthData.status)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Backend is ready. You can now test the frontend." -ForegroundColor Green
    exit 0
} catch {
    Write-Host "✗ Backend is NOT running" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Gray
    Write-Host ""
}

# Check Python installation
Write-Host "[2/3] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "  Please install Python 3.8+ from https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

# Check if uvicorn is installed
Write-Host "[3/3] Checking uvicorn installation..." -ForegroundColor Yellow
try {
    python -c "import uvicorn" 2>&1 | Out-Null
    Write-Host "✓ uvicorn is installed" -ForegroundColor Green
} catch {
    Write-Host "✗ uvicorn is not installed" -ForegroundColor Red
    Write-Host "  Installing uvicorn..." -ForegroundColor Yellow
    pip install uvicorn fastapi sse-starlette
    Write-Host ""
}

# Start backend
Write-Host ""
Write-Host "Starting backend server..." -ForegroundColor Yellow
Write-Host "  URL: http://localhost:8000" -ForegroundColor Gray
Write-Host "  API Docs: http://localhost:8000/api/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "Opening in new window. Check that window for any errors." -ForegroundColor Cyan
Write-Host ""

# Start backend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python -m uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000"

Write-Host "Waiting 5 seconds for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check again
Write-Host ""
Write-Host "Checking backend status again..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing -TimeoutSec 2
    Write-Host "✓ Backend is now running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now test the frontend at http://localhost:1420" -ForegroundColor Green
} catch {
    Write-Host "✗ Backend failed to start" -ForegroundColor Red
    Write-Host "  Check the backend window for error messages" -ForegroundColor Yellow
    Write-Host "  Common issues:" -ForegroundColor Yellow
    Write-Host "    - Missing dependencies (run: pip install -r requirements.txt)" -ForegroundColor Gray
    Write-Host "    - Database connection error" -ForegroundColor Gray
    Write-Host "    - Port 8000 already in use" -ForegroundColor Gray
    exit 1
}

