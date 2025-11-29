@echo off
echo ========================================
echo Restarting Backend with Enhanced Logging
echo ========================================
echo.

echo Stopping any existing backend processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Backend*" 2>nul

echo.
echo Starting backend with full error logging...
echo.
echo WATCH THIS WINDOW for error messages!
echo.

python -m uvicorn backend.api:app --reload --port 8000 --log-level debug

pause
