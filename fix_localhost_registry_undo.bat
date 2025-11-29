@echo off
echo ========================================
echo Undo Localhost Registry Fix
echo Re-enables HTTP/2
echo ========================================
echo.

echo This script will re-enable HTTP/2 after Microsoft fixes the bug
echo.

pause

echo.
echo Removing registry keys...
echo.

REM Re-enable HTTP/2 for IIS
reg delete "HKLM\SOFTWARE\Microsoft\IIS\Parameters" /v EnableHttp2 /f 2>nul
reg delete "HKLM\SOFTWARE\Microsoft\IIS\Parameters" /v EnableHttp2OverTls /f 2>nul

REM Re-enable HTTP/2 for Windows HTTP Service
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\HTTP\Parameters" /v EnableHttp2Tls /f 2>nul
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\HTTP\Parameters" /v EnableHttp2Cleartext /f 2>nul

echo.
echo ========================================
echo Registry keys removed successfully!
echo ========================================
echo.
echo HTTP/2 has been re-enabled.
echo Restart your computer for changes to take effect.
echo.

pause
