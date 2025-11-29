@echo off
echo ========================================
echo DEEP CLEAN AND RESTART
echo ========================================

echo [1/6] Stopping Python processes...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM uvicorn.exe /T >nul 2>&1

echo [2/6] Cleaning __pycache__...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo [3/6] Cleaning other caches...
if exist .pytest_cache rd /s /q .pytest_cache
if exist .mypy_cache rd /s /q .mypy_cache

echo [4/6] Cleaning frontend cache (node_modules/.vite)...
if exist frontend\node_modules\.vite rd /s /q frontend\node_modules\.vite

echo [5/6] Checking port 8000...
netstat -ano | findstr :8000 >nul
if %errorlevel%==0 (
    echo Port 8000 still in use. Forcing cleanup...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
)

echo [6/6] Starting backend...
cd D:\LP
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

start /B python -m uvicorn backend.api:app --reload --port 8000

echo.
echo DONE. Backend is restarting.
echo Please refresh your browser window.
echo.

