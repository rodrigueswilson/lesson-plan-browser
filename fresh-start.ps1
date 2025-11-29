# Fresh Start Script - Complete Reset
# Stops all services, cleans up, and restarts everything

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fresh Start - Complete Reset" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will:" -ForegroundColor Yellow
Write-Host "  1. Stop all running services" -ForegroundColor Gray
Write-Host "  2. Clean temporary files and caches" -ForegroundColor Gray
Write-Host "  3. Restart everything fresh" -ForegroundColor Gray
Write-Host ""
$confirm = Read-Host "Continue? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 1: Stopping All Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Stop backend processes
Write-Host "Stopping backend processes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*" -or $_.MainWindowTitle -like "*Backend*"
} | Stop-Process -Force -ErrorAction SilentlyContinue
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object {
    try { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
}
Start-Sleep -Seconds 2

# Stop frontend processes
Write-Host "Stopping frontend processes..." -ForegroundColor Yellow
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process "Bilingual Lesson Planner" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Stop Prometheus containers
Write-Host "Stopping Prometheus containers..." -ForegroundColor Yellow
docker-compose -f docker-compose.monitoring.yml down 2>$null
Start-Sleep -Seconds 2

# Stop Docker Desktop
Write-Host "Stopping Docker Desktop..." -ForegroundColor Yellow
$dockerProcesses = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
if ($dockerProcesses) {
    $dockerProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "Waiting for Docker Desktop to stop..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 2: Cleaning Temporary Files" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Clean Python cache
Write-Host "Cleaning Python cache..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

# Clean frontend cache
Write-Host "Cleaning frontend cache..." -ForegroundColor Yellow
if (Test-Path "frontend\node_modules\.cache") {
    Remove-Item -Path "frontend\node_modules\.cache" -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path "frontend\.vite") {
    Remove-Item -Path "frontend\.vite" -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path "frontend\dist") {
    Remove-Item -Path "frontend\dist" -Recurse -Force -ErrorAction SilentlyContinue
}

# Clean temporary files
Write-Host "Cleaning temporary files..." -ForegroundColor Yellow
Get-ChildItem -Path "." -Filter "*.tmp" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 3: Starting Services Fresh" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start Docker Desktop
Write-Host "Starting Docker Desktop..." -ForegroundColor Yellow
$dockerPaths = @(
    "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe",
    "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
    "$env:LOCALAPPDATA\Programs\Docker\Docker\Docker Desktop.exe"
)

$dockerExe = $null
foreach ($path in $dockerPaths) {
    if (Test-Path $path) {
        $dockerExe = $path
        break
    }
}

if ($dockerExe) {
    Start-Process -FilePath $dockerExe -WindowStyle Hidden
    Write-Host "Waiting for Docker Desktop to be ready..." -ForegroundColor Gray
    Start-Sleep -Seconds 15
}

# Start Prometheus
Write-Host "Starting Prometheus monitoring stack..." -ForegroundColor Yellow
& ".\start-prometheus.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Prometheus startup had issues, but continuing..." -ForegroundColor Yellow
}
Start-Sleep -Seconds 3

# Start Backend
Write-Host ""
Write-Host "Starting Backend API Server..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k", "cd /d $PWD && python -m uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000" -WindowStyle Normal

# Wait for backend to initialize
Write-Host "Waiting for backend to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 8

# Start Frontend
Write-Host "Starting Frontend (Tauri)..." -ForegroundColor Yellow
Start-Process cmd -ArgumentList "/k", "cd /d $PWD\frontend && npm run tauri:dev" -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fresh Start Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services started:" -ForegroundColor White
Write-Host "  - Backend: http://localhost:8000" -ForegroundColor Gray
Write-Host "  - API Docs: http://localhost:8000/api/docs" -ForegroundColor Gray
Write-Host "  - Prometheus: http://localhost:9090" -ForegroundColor Gray
Write-Host "  - Prometheus Targets: http://localhost:9090/targets" -ForegroundColor Gray
Write-Host "  - Frontend: Will open automatically" -ForegroundColor Gray
Write-Host ""
Write-Host "Two terminal windows have opened for backend and frontend." -ForegroundColor White
Write-Host "Close those windows to stop the services." -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

