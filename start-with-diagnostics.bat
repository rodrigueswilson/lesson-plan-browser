@echo off
echo ========================================
echo Backend Diagnostics and Startup
echo ========================================
echo.

REM Step 1: Configuration check
echo [Step 1/3] Verifying configuration...
echo.
python tools\maintenance\verify_config.py
if %errorlevel% neq 0 (
    echo.
    echo Configuration check failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo.

REM Step 2: Full diagnostics
echo [Step 2/3] Running full diagnostics...
echo.
python tools\diagnostics\diagnose_crash.py
if %errorlevel% neq 0 (
    echo.
    echo Diagnostics failed! Fix the errors above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo.

REM Step 3: Start backend with visible logs
echo [Step 3/3] Starting backend with visible logs...
echo.
echo Starting Prometheus Monitoring (if needed)...
powershell -ExecutionPolicy Bypass -File "%~dp0start-prometheus.ps1" -ErrorAction SilentlyContinue
echo.
echo KEEP THIS WINDOW OPEN to see error messages!
echo.
echo Press Ctrl+C to stop the backend.
echo.
echo ========================================
echo.

python -m uvicorn backend.api:app --reload --port 8000 --log-level info

pause
