# Restart App Fresh - Kill processes, clean cache, restart
# Usage: .\scripts\restart_app_fresh.ps1

Write-Host "=== Restarting App Fresh ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Kill Python processes
Write-Host "1. Stopping Python processes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*uvicorn*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "   ✓ Python processes stopped" -ForegroundColor Green

# Step 2: Clean Python cache
Write-Host "`n2. Cleaning Python cache..." -ForegroundColor Yellow
$cacheDirs = Get-ChildItem -Path $PSScriptRoot\.. -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
if ($cacheDirs) {
    $cacheDirs | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "   ✓ Removed $($cacheDirs.Count) __pycache__ directories" -ForegroundColor Green
} else {
    Write-Host "   ✓ No cache directories found" -ForegroundColor Green
}

# Step 3: Clean .pyc files
Write-Host "`n3. Cleaning .pyc files..." -ForegroundColor Yellow
$pycFiles = Get-ChildItem -Path $PSScriptRoot\.. -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue
if ($pycFiles) {
    $pycFiles | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "   ✓ Removed $($pycFiles.Count) .pyc files" -ForegroundColor Green
} else {
    Write-Host "   ✓ No .pyc files found" -ForegroundColor Green
}

# Step 4: Wait a moment
Write-Host "`n4. Waiting for processes to fully stop..." -ForegroundColor Yellow
Start-Sleep -Seconds 2

# Step 5: Start Backend
Write-Host "`n5. Starting FastAPI Backend..." -ForegroundColor Yellow
$backendScript = @"
cd $PSScriptRoot\..
Write-Host '=== FastAPI Backend ===' -ForegroundColor Cyan
Write-Host 'Starting fresh...' -ForegroundColor Yellow
uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript -WindowStyle Normal
Write-Host "   ✓ Backend starting in new window" -ForegroundColor Green

# Step 6: Start Frontend
Write-Host "`n6. Starting Frontend..." -ForegroundColor Yellow
$frontendScript = @"
cd $PSScriptRoot\..\frontend
Write-Host '=== Frontend ===' -ForegroundColor Cyan
Write-Host 'Starting fresh...' -ForegroundColor Yellow
npm run dev
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript -WindowStyle Normal
Write-Host "   ✓ Frontend starting in new window" -ForegroundColor Green

# Step 7: Wait and check
Write-Host "`n7. Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

Write-Host "`n=== Service Status ===" -ForegroundColor Cyan
Write-Host ""

# Check Backend
Write-Host "Backend (FastAPI):" -ForegroundColor Yellow
try {
    $backend = Invoke-WebRequest -Uri http://localhost:8000/api/health -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    Write-Host "  ✓ Running! Status: $($backend.StatusCode)" -ForegroundColor Green
    Write-Host "  → http://localhost:8000" -ForegroundColor Gray
    Write-Host "  → Metrics: http://localhost:8000/metrics" -ForegroundColor Gray
} catch {
    Write-Host "  ⏳ Still starting... (check backend window)" -ForegroundColor Yellow
}

# Check Frontend
Write-Host "`nFrontend:" -ForegroundColor Yellow
try {
    $frontend = Invoke-WebRequest -Uri http://localhost:1420 -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    Write-Host "  ✓ Running! Status: $($frontend.StatusCode)" -ForegroundColor Green
    Write-Host "  → http://localhost:1420" -ForegroundColor Gray
} catch {
    try {
        $frontend2 = Invoke-WebRequest -Uri http://localhost:5173 -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        Write-Host "  ✓ Running on port 5173! Status: $($frontend2.StatusCode)" -ForegroundColor Green
        Write-Host "  → http://localhost:5173" -ForegroundColor Gray
    } catch {
        Write-Host "  ⏳ Still starting... (check frontend window)" -ForegroundColor Yellow
    }
}

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Check the two PowerShell windows that opened" -ForegroundColor White
Write-Host "2. Backend should show: 'Uvicorn running on http://0.0.0.0:8000'" -ForegroundColor White
Write-Host "3. Frontend should show: 'Local: http://localhost:XXXX/'" -ForegroundColor White
Write-Host "4. Open the frontend URL in your browser" -ForegroundColor White
Write-Host "5. Check Prometheus: http://localhost:9090/targets (should show backend as UP)" -ForegroundColor White

