@echo off
echo ========================================
echo Starting Backend Server for Testing
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
echo Starting backend server on http://localhost:8000
echo API Documentation: http://localhost:8000/api/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn backend.api:app --reload --port 8000

