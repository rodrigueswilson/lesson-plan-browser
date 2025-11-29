@echo off
echo ========================================
echo Bilingual Lesson Planner - With DevTools
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

REM Check if Chrome is installed
where chrome >nul 2>&1
if %errorlevel% neq 0 (
    REM Try common Chrome installation paths
    if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
        set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
    ) else if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
        set CHROME_PATH="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ) else (
        echo WARNING: Chrome not found in PATH. Will try default location.
        set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
    )
) else (
    set CHROME_PATH=chrome
)

echo Starting Prometheus Monitoring (if needed)...
powershell -ExecutionPolicy Bypass -File "%~dp0start-prometheus.ps1" -ErrorAction SilentlyContinue

echo Starting Backend API Server...
echo.
start "Backend API" /D "%~dp0" cmd /k ".venv\Scripts\python.exe -m uvicorn backend.api:app --reload --port 8000"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

echo Starting Frontend Dev Server (Vite)...
echo.
start "Frontend Vite" /D "%~dp0frontend" cmd /k "npm run dev"

REM Wait for Vite to start
timeout /t 5 /nobreak >nul

echo Opening Chrome with DevTools...
echo.
%CHROME_PATH% --auto-open-devtools-for-tabs http://localhost:1420

echo.
echo ========================================
echo Services are starting!
echo ========================================
echo.
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/api/docs
echo Frontend: http://localhost:1420 (opening in Chrome with DevTools)
echo Prometheus: http://localhost:9090 (if started)
echo.
echo Terminal windows opened:
echo   1. Backend API (Python/FastAPI)
echo   2. Frontend (Vite Dev Server)
echo.
echo Chrome will open automatically with DevTools enabled.
echo Close those windows to stop the services.
echo.
pause

