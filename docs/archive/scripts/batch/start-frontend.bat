@echo off
echo ========================================
echo Starting Frontend (Tauri Desktop App)
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed!
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if frontend directory exists
if not exist "%~dp0frontend" (
    echo ERROR: frontend directory not found!
    echo Expected: %~dp0frontend
    pause
    exit /b 1
)

REM Check if package.json exists
if not exist "%~dp0frontend\package.json" (
    echo ERROR: frontend\package.json not found!
    echo Please ensure frontend directory is properly set up.
    pause
    exit /b 1
)

echo Starting Frontend (Tauri)...
echo.
echo The application window will open automatically when build completes.
echo This may take 30-60 seconds on first run.
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d %~dp0frontend
npm run tauri:dev

