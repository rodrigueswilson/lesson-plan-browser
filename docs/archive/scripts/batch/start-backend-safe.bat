@echo off
echo ========================================
echo Starting Backend with Error Logging
echo ========================================
echo.

echo Starting Prometheus Monitoring (if needed)...
powershell -ExecutionPolicy Bypass -File "%~dp0start-prometheus.ps1" -ErrorAction SilentlyContinue

REM Redirect all output to a log file
python -m uvicorn backend.api:app --reload --port 8000 --log-level debug 2>&1 | tee backend_error.log

pause
