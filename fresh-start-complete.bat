@echo off
echo ========================================
echo Complete Fresh Start - Full Reset
echo ========================================
echo.
echo This will:
echo   1. Stop ALL running processes
echo   2. Clean ALL caches and temporary files
echo   3. Stop and restart Docker Desktop
echo   4. Stop and restart Prometheus containers
echo   5. Restart all services fresh
echo.
pause

echo.
echo ========================================
echo Step 1: Stopping ALL Services
echo ========================================
echo.

echo Stopping backend processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Backend*" 2>nul
taskkill /F /IM python.exe /FI "COMMANDLINE eq *uvicorn*" 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a 2>nul
)
timeout /t 2 /nobreak >nul

echo Stopping frontend processes...
taskkill /F /IM node.exe 2>nul
taskkill /F /IM "Bilingual Lesson Planner.exe" 2>nul
timeout /t 2 /nobreak >nul

echo Stopping Prometheus containers...
docker-compose -f docker-compose.monitoring.yml down 2>nul
timeout /t 2 /nobreak >nul

echo Stopping Docker Desktop...
taskkill /F /IM "Docker Desktop.exe" 2>nul
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Step 2: Cleaning ALL Caches
echo ========================================
echo.

echo Cleaning Python cache...
if exist backend\__pycache__ rmdir /s /q backend\__pycache__ 2>nul
if exist tools\__pycache__ rmdir /s /q tools\__pycache__ 2>nul
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul
del /s /q *.pyo 2>nul

echo Cleaning frontend cache...
if exist frontend\node_modules\.cache rmdir /s /q frontend\node_modules\.cache 2>nul
if exist frontend\.vite rmdir /s /q frontend\.vite 2>nul
if exist frontend\dist rmdir /s /q frontend\dist 2>nul

echo Cleaning temporary files...
del /s /q *.tmp 2>nul

echo.
echo ========================================
echo Step 3: Restarting Docker & Prometheus
echo ========================================
echo.

echo Starting Docker Desktop...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" 2>nul
if errorlevel 1 (
    start "" "%ProgramFiles(x86)%\Docker\Docker\Docker Desktop.exe" 2>nul
)
if errorlevel 1 (
    start "" "%LOCALAPPDATA%\Programs\Docker\Docker\Docker Desktop.exe" 2>nul
)

echo Waiting for Docker Desktop to be ready...
timeout /t 15 /nobreak >nul

echo Starting Prometheus monitoring stack...
powershell -ExecutionPolicy Bypass -File "%~dp0start-prometheus.ps1"
if errorlevel 1 (
    echo [WARNING] Prometheus startup had issues, but continuing...
)
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo Step 4: Starting Services Fresh
echo ========================================
echo.

echo Starting Backend API Server...
if exist "%~dp0.venv\Scripts\python.exe" (
    start "Backend API" cmd /k "cd /d %~dp0 && .venv\Scripts\python.exe -m uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000"
) else (
    start "Backend API" cmd /k "cd /d %~dp0 && python -m uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000"
)

REM Wait for backend to initialize
timeout /t 8 /nobreak >nul

echo Starting Frontend (Tauri)...
start "Frontend Tauri" cmd /k "cd /d %~dp0\frontend && npm run tauri:dev"

echo.
echo ========================================
echo Complete Fresh Start Finished!
echo ========================================
echo.
echo Services started:
echo   - Backend: http://localhost:8000
echo   - API Docs: http://localhost:8000/api/docs
echo   - Prometheus: http://localhost:9090
echo   - Prometheus Targets: http://localhost:9090/targets
echo   - Frontend: Will open automatically
echo.
echo All caches cleaned, Docker restarted, services fresh!
echo.
pause

