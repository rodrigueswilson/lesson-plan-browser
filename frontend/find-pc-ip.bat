@echo off
REM Batch script to find your PC's IP address for Android app configuration
REM Run this script to get your local IP address for configuring the mobile app

echo Finding your PC's IP address...
echo.

REM Get IP address using ipconfig
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set ip=%%a
    set ip=!ip: =!
    echo Found IP: !ip!
    echo.
    echo To use this IP in your app:
    echo   1. Update frontend\capacitor.config.ts:
    echo      server: { url: 'http://!ip!:8000' }
    echo.
    echo   2. Or create frontend\.env.local with:
    echo      VITE_API_BASE_URL=http://!ip!:8000/api
    echo.
    echo   3. Make sure your backend is running with:
    echo      python -m uvicorn api:app --host 0.0.0.0 --port 8000
    echo.
    goto :found
)

:found
pause

