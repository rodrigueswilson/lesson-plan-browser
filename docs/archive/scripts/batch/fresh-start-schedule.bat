@echo off
echo ========================================
echo Fresh Start - Complete Cleanup
echo ========================================
echo.

echo Step 1: Stopping all Python/Backend processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM uvicorn.exe 2>nul
timeout /t 2 /nobreak >nul

echo Step 2: Stopping processes on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a 2>nul
)
timeout /t 2 /nobreak >nul

echo Step 3: Cleaning Python cache...
if exist backend\__pycache__ rmdir /s /q backend\__pycache__ 2>nul
if exist tools\__pycache__ rmdir /s /q tools\__pycache__ 2>nul
if exist backend\utils\__pycache__ rmdir /s /q backend\utils\__pycache__ 2>nul
if exist backend\migrations\__pycache__ rmdir /s /q backend\migrations\__pycache__ 2>nul
if exist backend\services\__pycache__ rmdir /s /q backend\services\__pycache__ 2>nul
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul
del /s /q *.pyo 2>nul

echo Step 4: Cleaning frontend cache...
if exist frontend\node_modules\.cache rmdir /s /q frontend\node_modules\.cache 2>nul
if exist frontend\.vite rmdir /s /q frontend\.vite 2>nul
if exist frontend\dist rmdir /s /q frontend\dist 2>nul

echo Step 5: Cleaning temporary files...
del /s /q *.tmp 2>nul
del /s /q wait_for_server.py 2>nul

echo.
echo ========================================
echo Cleanup Complete!
echo ========================================
echo.
echo All processes killed, caches cleaned.
echo You can now start fresh.
echo.
pause

