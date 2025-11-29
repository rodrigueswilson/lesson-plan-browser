@echo off
echo ========================================
echo Clean Frontend Restart
echo ========================================
echo.

echo Stopping all Node and Tauri processes...
taskkill /F /IM node.exe 2>nul
taskkill /F /IM "Bilingual Lesson Planner.exe" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting frontend with updated configuration...
cd /d %~dp0frontend
start "Frontend Tauri" cmd /k "npm run tauri:dev"

echo.
echo Frontend is starting...
echo The Tauri window should open in a few seconds.
echo.
pause
