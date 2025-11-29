@echo off
echo ========================================
echo Lesson Mode v2 - Fresh Start Browser Test
echo ========================================
echo.

REM Check if Python is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed!
    pause
    exit /b 1
)

REM Check if Node.js is installed
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed!
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

echo [1/4] Starting Backend API Server...
echo.
start "Backend API" cmd /k "cd /d %~dp0 && python -m uvicorn backend.api:app --reload --port 8000"

REM Wait for backend to start
echo Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

echo [2/4] Starting Frontend Dev Server (Browser Mode)...
echo.
start "Frontend Dev Server" cmd /k "cd /d %~dp0frontend && npm run dev"

REM Wait for frontend to start
echo Waiting for frontend to start...
timeout /t 5 /nobreak >nul

echo [3/4] Opening Chrome Browser...
echo.
REM Try to open Chrome with DevTools
start chrome.exe --new-window --auto-open-devtools-for-tabs "http://localhost:1420" 2>nul
if %errorlevel% neq 0 (
    REM Alternative if Chrome is not in PATH:
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --new-window --auto-open-devtools-for-tabs "http://localhost:1420"
)

echo.
echo ========================================
echo Services Started!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/api/docs
echo Frontend: http://localhost:1420 (opened in Chrome)
echo.
echo Terminal windows opened:
echo   1. Backend API (Python/FastAPI)
echo   2. Frontend Dev Server (Vite)
echo.
echo Chrome browser opened with DevTools console.
echo.
echo Check the console tab for any errors!
echo.
echo Press any key to close this window...
pause >nul

