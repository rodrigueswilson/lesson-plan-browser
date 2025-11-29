@echo off
echo ========================================
echo Starting Backend on All Interfaces
echo ========================================
echo.

echo This allows connections from both localhost and 127.0.0.1
echo.

echo Starting Prometheus Monitoring (if needed)...
powershell -ExecutionPolicy Bypass -File "%~dp0start-prometheus.ps1" -ErrorAction SilentlyContinue

python -m uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000 --log-level debug

pause
