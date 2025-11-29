@echo off
echo ========================================
echo Windows 11 KB5066835 Localhost Fix
echo Registry Workaround (Disables HTTP/2)
echo ========================================
echo.

echo This script will disable HTTP/2 to fix localhost connections
echo broken by Windows 11 October 2025 update (KB5066835)
echo.
echo You will need to restart your computer after running this.
echo.

pause

echo.
echo Adding registry keys...
echo.

REM Disable HTTP/2 for IIS
reg add "HKLM\SOFTWARE\Microsoft\IIS\Parameters" /v EnableHttp2 /t REG_DWORD /d 0 /f
reg add "HKLM\SOFTWARE\Microsoft\IIS\Parameters" /v EnableHttp2OverTls /t REG_DWORD /d 0 /f

REM Disable HTTP/2 for Windows HTTP Service
reg add "HKLM\SYSTEM\CurrentControlSet\Services\HTTP\Parameters" /v EnableHttp2Tls /t REG_DWORD /d 0 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Services\HTTP\Parameters" /v EnableHttp2Cleartext /t REG_DWORD /d 0 /f

echo.
echo ========================================
echo Registry keys added successfully!
echo ========================================
echo.
echo IMPORTANT: You MUST restart your computer for changes to take effect.
echo.
echo After restart:
echo   - Localhost connections should work again
echo   - Backend processing should work
echo   - Tauri frontend should connect
echo.
echo To undo this fix later (after Microsoft releases a proper update):
echo   - Run: fix_localhost_registry_undo.bat
echo.

pause
