@echo off
echo ========================================
echo Complete Fresh Start - Backend + Frontend
echo ========================================
echo.
echo This will:
echo   1. Kill all backend processes on port 8000
echo   2. Kill all Node.js/frontend processes
echo   3. Start a fresh backend server
echo   4. Start a fresh frontend dev server
echo   5. Open Chrome with DevTools
echo.
pause

cd /d %~dp0

echo.
echo [1/3] Stopping all backend processes on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo   Killing backend process %%a...
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo [2/3] Stopping all frontend processes...
taskkill /F /IM node.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo   Killed Node.js processes
) else (
    echo   No Node.js processes found
)

timeout /t 2 /nobreak >nul

echo.
echo [3/3] Starting services...
echo.

REM Start Backend
echo Starting Backend API Server...
if exist ".venv\Scripts\python.exe" (
    start "Backend API" cmd /k ".venv\Scripts\python.exe -m uvicorn backend.api:app --reload --port 8000"
) else (
    start "Backend API" cmd /k "python -m uvicorn backend.api:app --reload --port 8000"
)

REM Wait for backend to initialize
echo Waiting for backend to initialize (8 seconds)...
timeout /t 8 /nobreak >nul

REM Start Frontend
echo Starting Frontend Dev Server...
cd /d %~dp0frontend
start "Frontend Dev Server" cmd /k "npm run dev"

REM Wait for frontend to start
echo Waiting for frontend to start (5 seconds)...
timeout /t 5 /nobreak >nul

REM Open Chrome with DevTools
echo Opening Chrome browser with DevTools...
start chrome.exe --new-window --auto-open-devtools-for-tabs "http://localhost:1420" 2>nul
if %errorlevel% neq 0 (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --new-window --auto-open-devtools-for-tabs "http://localhost:1420" 2>nul
)

cd /d %~dp0

echo.
echo ========================================
echo Fresh Start Complete!
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/api/docs
echo Frontend: http://localhost:1420
echo.
echo Terminal windows opened:
echo   1. Backend API (port 8000)
echo   2. Frontend Dev Server (port 1420)
echo.
echo Chrome browser opened with DevTools console.
echo Check the console for any errors!
echo.
pause

