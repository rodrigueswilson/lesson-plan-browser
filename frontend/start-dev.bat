@echo off
echo ========================================
echo Bilingual Lesson Planner - Development
echo ========================================
echo.

REM Check if Node.js is installed
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed!
    echo Please install Node.js 18+ from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

REM Check if npm dependencies are installed
if not exist "node_modules\" (
    echo Installing npm dependencies...
    echo This will take a few minutes on first run.
    echo.
    npm install
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies!
        pause
        exit /b 1
    )
    echo.
)

REM Check if backend is running
echo Checking if backend is running...
curl -s http://localhost:8000/api/health >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Backend is not running!
    echo.
    echo Please start the backend in a separate terminal:
    echo   cd ..
    echo   python -m uvicorn backend.api:app --reload
    echo.
    echo Press any key to continue anyway (frontend will start but won't connect)
    echo Or close this window and start the backend first.
    pause
)

echo Backend is running!
echo.
echo Starting Tauri development mode...
echo.
echo NOTES:
echo - First run takes 5-10 minutes (Rust compilation)
echo - Subsequent runs are much faster
echo - Hot reload enabled for React changes
echo - Press Ctrl+C to stop
echo.

npm run tauri:dev
