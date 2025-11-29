@echo off
echo ========================================
echo Restarting Backend with Supabase
echo ========================================
echo.
echo This will restart the backend to load Supabase settings from .env
echo.
echo Press any key to continue (or Ctrl+C to cancel)...
pause >nul

echo.
echo Stopping any existing backend processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Backend API*" 2>nul

echo.
echo Starting backend with Supabase...
echo.
start "Backend API (Supabase)" cmd /k "cd /d %~dp0 && python -m uvicorn backend.api:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo.
echo Backend should be starting...
echo Check the new terminal window for status.
echo.
echo Once backend is running, test with:
echo   python test_supabase_integration.py
echo.
pause

