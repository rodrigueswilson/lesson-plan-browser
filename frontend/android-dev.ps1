# PowerShell script to run Android dev with correct emulator IP
# This sets TAURI_DEV_HOST to 10.0.2.2 for Android emulator access

$env:TAURI_DEV_HOST = "10.0.2.2"
Write-Host "Starting Android dev with TAURI_DEV_HOST=$env:TAURI_DEV_HOST"
Write-Host "Note: Tauri may still try to verify the server from the host machine."
Write-Host "If it fails, the server is still accessible from the emulator at 10.0.2.2:1420"
Write-Host ""

cd $PSScriptRoot
npm run tauri android dev

