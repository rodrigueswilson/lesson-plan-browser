@echo off
echo ========================================
echo Schedule API Test Runner
echo ========================================
echo.

REM Activate virtual environment
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo WARNING: No virtual environment found, using system Python
)

echo.
echo Checking if backend server is running...
python -c "import requests; r = requests.get('http://localhost:8000/health'); exit(0 if r.status_code == 200 else 1)" 2>nul
if %errorlevel% equ 0 (
    echo Backend server is already running!
    echo.
) else (
    echo Backend server is not running.
    echo.
    echo Starting backend server in a new window...
    start "Backend Server" cmd /k "cd /d %~dp0 && if exist .venv\Scripts\activate.bat (call .venv\Scripts\activate.bat) else if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat) && python -m uvicorn backend.api:app --reload --port 8000"
    
    echo Waiting for server to start...
    timeout /t 8 /nobreak >nul
    
    REM Check again
    python -c "import requests; r = requests.get('http://localhost:8000/health'); exit(0 if r.status_code == 200 else 1)" 2>nul
    if %errorlevel% neq 0 (
        echo ERROR: Backend server failed to start!
        echo Please check the server window for errors.
        pause
        exit /b 1
    )
    echo Backend server is ready!
    echo.
)

echo ========================================
echo Running Schedule API Tests
echo ========================================
echo.

python test_schedule_api.py

echo.
echo ========================================
echo Test completed!
echo ========================================
echo.
pause

