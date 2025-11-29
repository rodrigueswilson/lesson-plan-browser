@echo off
echo ========================================
echo Starting Backend API Server
echo ========================================
echo.

REM Check if Python is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed!
    pause
    exit /b 1
)

REM Check if uvicorn is installed
python -c "import uvicorn" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing uvicorn...
    pip install uvicorn fastapi sse-starlette
    echo.
)

echo Starting Prometheus Monitoring (if needed)...
powershell -ExecutionPolicy Bypass -File "%~dp0start-prometheus.ps1" -ErrorAction SilentlyContinue

echo Starting backend server on http://0.0.0.0:8000 (accessible on your local network)
echo API Documentation: http://localhost:8000/api/docs
echo Prometheus: http://localhost:9090 (if started)
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
