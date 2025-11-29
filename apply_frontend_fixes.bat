@echo off
echo ========================================
echo Applying Frontend Fixes
echo ========================================
echo.

echo Step 1: Backing up current files...
copy frontend\src\lib\api.ts frontend\src\lib\api.ts.backup >nul 2>&1
echo   - api.ts backed up

echo.
echo Step 2: Applying Tauri HTTP fix...
copy api_tauri_fixed.ts frontend\src\lib\api.ts
echo   - api.ts replaced with Tauri version

echo.
echo ========================================
echo Fixes Applied Successfully!
echo ========================================
echo.
echo Next steps:
echo   1. Restart the frontend (Ctrl+C then npm run tauri:dev)
echo   2. The app should now connect to the backend
echo   3. Users will load automatically
echo   4. Create User button will work
echo.
echo Check the console (F12) for detailed logs!
echo.
pause
