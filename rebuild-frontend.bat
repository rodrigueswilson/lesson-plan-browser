@echo off
echo ========================================
echo Clean Rebuild of Frontend
echo ========================================
echo.

echo Step 1: Stopping all processes...
taskkill /F /IM node.exe 2>nul
taskkill /F /IM "Bilingual Lesson Planner.exe" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Step 2: Cleaning Tauri build cache...
cd /d %~dp0frontend\src-tauri
if exist target (
    echo Removing target directory...
    rmdir /s /q target
)

echo.
echo Step 3: Starting fresh build...
cd /d %~dp0frontend
npm run tauri:dev

pause
