# Fresh FastAPI Restart Script
# Kills Python processes, cleans cache, and starts FastAPI fresh

Write-Host "`n=== Fresh FastAPI Restart ===" -ForegroundColor Cyan

# Step 1: Kill Python processes
Write-Host "`n[1/4] Killing Python processes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*uvicorn*"} | ForEach-Object {
    Write-Host "  Killing: $($_.ProcessName) (PID: $($_.Id))" -ForegroundColor Gray
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2

# Step 2: Clear port 8000
Write-Host "`n[2/4] Clearing port 8000..." -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($port8000) {
    $port8000 | ForEach-Object {
        Write-Host "  Killing process on port 8000: PID $_" -ForegroundColor Gray
        Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep -Seconds 2

# Step 3: Clean cache
Write-Host "`n[3/4] Cleaning Python cache..." -ForegroundColor Yellow
$cacheDirs = Get-ChildItem -Path $PSScriptRoot\.. -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
$cacheFiles = Get-ChildItem -Path $PSScriptRoot\.. -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue
$total = $cacheDirs.Count + $cacheFiles.Count
if ($total -gt 0) {
    $cacheDirs | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    $cacheFiles | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "  Cleaned $total cache items" -ForegroundColor Green
} else {
    Write-Host "  No cache files found" -ForegroundColor Gray
}

# Step 4: Start FastAPI
Write-Host "`n[4/4] Starting FastAPI..." -ForegroundColor Yellow
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

# Activate virtual environment
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & ".venv\Scripts\Activate.ps1"
}

Write-Host "`nStarting FastAPI on http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Yellow

# Start uvicorn
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000

