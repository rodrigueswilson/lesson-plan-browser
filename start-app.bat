@echo off
echo ========================================
echo Bilingual Lesson Planner - Full Stack
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

echo Starting Prometheus Monitoring (if needed)...
powershell -ExecutionPolicy Bypass -File "%~dp0start-prometheus.ps1" -ErrorAction SilentlyContinue

echo Starting Backend API Server...
echo.
start "Backend API" cmd /k "cd /d %~dp0 && .venv\Scripts\python.exe -m uvicorn backend.api:app --reload --port 8000"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

echo Starting Frontend (Tauri)...
echo.
start "Frontend Tauri" cmd /k "cd /d %~dp0frontend && npm run tauri:dev"

echo.
echo ========================================
echo Both services are starting!
echo ========================================
echo.
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/api/docs
echo Frontend: Will open automatically
echo Prometheus: http://localhost:9090 (if started)
echo.
echo Terminal windows opened:
echo   1. Backend API (Python/FastAPI)
echo   2. Frontend (Tauri/React)
echo.
echo Close those windows to stop the services.
echo.
pause
