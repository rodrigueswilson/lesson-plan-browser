@echo off
echo ========================================
echo Starting Backend Server
echo ========================================
echo.
echo This will start the backend on port 8000
echo Keep this window open!
echo.
echo Press Ctrl+C to stop the server
echo.
pause

cd /d %~dp0
python -m uvicorn backend.api:app --reload --port 8000

