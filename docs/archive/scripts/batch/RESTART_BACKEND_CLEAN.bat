@echo off
echo ========================================
echo Restarting Backend Server (Clean)
echo ========================================
echo.
echo This will:
echo   1. Kill all processes on port 8000
echo   2. Start a fresh backend server
echo.
pause

cd /d %~dp0

echo.
echo [1/2] Stopping processes on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Killing process %%a...
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul

echo.
echo [2/2] Starting backend server...
echo.
echo Backend will start in a new window.
echo Keep this window open!
echo.
pause

if exist ".venv\Scripts\python.exe" (
    start "Backend API" cmd /k ".venv\Scripts\python.exe -m uvicorn backend.api:app --reload --port 8000"
) else (
    start "Backend API" cmd /k "python -m uvicorn backend.api:app --reload --port 8000"
)

echo.
echo Backend server started in a new window!
echo Check the "Backend API" window for status.
echo.
pause

