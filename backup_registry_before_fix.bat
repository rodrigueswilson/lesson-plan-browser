@echo off
echo ========================================
echo Backup Registry Keys Before Fix
echo ========================================
echo.

echo Creating backup of registry keys that will be modified...
echo.

REM Create backup directory
if not exist "registry_backups" mkdir registry_backups

REM Generate timestamp for backup filename
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set timestamp=%datetime:~0,8%_%datetime:~8,6%

REM Export registry keys
echo Exporting IIS Parameters...
reg export "HKLM\SOFTWARE\Microsoft\IIS\Parameters" "registry_backups\IIS_Parameters_%timestamp%.reg" /y

echo Exporting HTTP Parameters...
reg export "HKLM\SYSTEM\CurrentControlSet\Services\HTTP\Parameters" "registry_backups\HTTP_Parameters_%timestamp%.reg" /y

echo.
echo ========================================
echo Backup Complete!
echo ========================================
echo.
echo Backup files saved to: registry_backups\
echo   - IIS_Parameters_%timestamp%.reg
echo   - HTTP_Parameters_%timestamp%.reg
echo.
echo You can now safely run fix_localhost_registry.bat
echo.

pause
