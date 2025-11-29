@echo off
echo ========================================
echo Starting Backend (No Auto-Reload)
echo ========================================
echo.

echo This version won't restart when files change
echo.

echo Starting Prometheus Monitoring (if needed)...
powershell -ExecutionPolicy Bypass -File "%~dp0start-prometheus.ps1" -ErrorAction SilentlyContinue

python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000 --log-level debug

pause
