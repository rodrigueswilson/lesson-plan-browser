@echo off
echo ========================================
echo HARD RESET BACKEND
echo ========================================

echo [1/4] Killing ALL python processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM uvicorn.exe >nul 2>&1

echo [2/4] Checking for remaining processes on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo   Killing stubborn process %%a...
    taskkill /F /PID %%a >nul 2>&1
)

echo [3/4] Clearing pycache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo [4/4] Starting fresh backend...
if exist ".venv\Scripts\python.exe" (
    start "Backend API" cmd /k ".venv\Scripts\python.exe -m uvicorn backend.api:app --reload --port 8000"
) else (
    start "Backend API" cmd /k "python -m uvicorn backend.api:app --reload --port 8000"
)

echo.
echo DONE. Backend restarting...
pause

