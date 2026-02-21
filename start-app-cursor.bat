@echo off
echo ========================================
echo Bilingual Lesson Planner - Cursor Mode
echo ========================================
echo.
echo This will start the app in a way that allows Cursor to access logs.
echo.
echo You need to run this in TWO separate Cursor terminals:
echo.
echo Terminal 1 (Backend):
echo   powershell -ExecutionPolicy Bypass -File start-backend-with-logs.ps1
echo.
echo Terminal 2 (Frontend):
echo   powershell -ExecutionPolicy Bypass -File start-frontend-with-logs.ps1
echo.
echo ========================================
echo.
echo Starting Backend in this terminal...
echo (Open another terminal for frontend)
echo.
echo ========================================
echo.

powershell -ExecutionPolicy Bypass -File start-backend-with-logs.ps1
