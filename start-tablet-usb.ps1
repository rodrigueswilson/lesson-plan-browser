# Start backend and USB tunnel for tablet app
# Usage: Run from PowerShell:  cd d:\LP; .\start-tablet-usb.ps1

Write-Host "=== Starting backend and USB tunnel for tablet ===" -ForegroundColor Cyan

# 1) Activate virtual environment (if present)
$venvScript = Join-Path $PSScriptRoot ".venv\Scripts\Activate.ps1"
if (Test-Path $venvScript) {
    Write-Host "[1/4] Activating virtual environment..." -ForegroundColor Yellow
    . $venvScript
} else {
    Write-Host "[1/4] No .venv found, continuing without activating." -ForegroundColor Yellow
}

# 2) Start backend on port 8000 if not already listening
Write-Host "[2/4] Ensuring backend is listening on 0.0.0.0:8000..." -ForegroundColor Yellow
$existing = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if (-not $existing) {
    Write-Host "  No existing listener on 8000. Starting uvicorn..." -ForegroundColor Yellow
    Start-Process -FilePath "python" -ArgumentList "-m","uvicorn","backend.api:app","--host","0.0.0.0","--port","8000" -WorkingDirectory $PSScriptRoot
    Start-Sleep -Seconds 3
} else {
    Write-Host "  Backend already listening on port 8000 (PID(s): $($existing.OwningProcess -join ', '))." -ForegroundColor Green
}

# 3) Configure ADB reverse tunnel (device -> PC)
$adb = "C:\Users\rodri\AppData\Local\Android\Sdk\platform-tools\adb.exe"
if (-not (Test-Path $adb)) {
    Write-Host "[3/4] ERROR: adb.exe not found at expected path: $adb" -ForegroundColor Red
    Write-Host "        Update start-tablet-usb.ps1 with the correct adb path and retry."
    exit 1
}

Write-Host "[3/4] Setting up ADB reverse tcp:8000 -> tcp:8000..." -ForegroundColor Yellow
& $adb forward --remove-all | Out-Null
& $adb reverse tcp:8000 tcp:8000 | Out-Null

$reverseList = & $adb reverse --list
Write-Host "  ADB reverse --list:" -ForegroundColor Green
Write-Host $reverseList

# 4) Launch tablet app
Write-Host "[4/4] Launching tablet app (com.lessonplanner.bilingual)..." -ForegroundColor Yellow
& $adb shell am start -n com.lessonplanner.bilingual/.MainActivity | Out-Null

Write-Host "" 
Write-Host "=== READY ===" -ForegroundColor Cyan
Write-Host "Tablet app is running and should reach backend at http://127.0.0.1:8000/api via ADB reverse."
