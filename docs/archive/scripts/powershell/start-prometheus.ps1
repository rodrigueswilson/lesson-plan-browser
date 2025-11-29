# Start Prometheus Monitoring Stack
# Automatically starts Docker Desktop if needed, then starts Prometheus

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Prometheus Monitoring Stack" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if Docker is running and ready
function Test-DockerRunning {
    try {
        $result = docker ps 2>&1
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        # Check if error is about Docker not running
        if ($result -match "cannot connect" -or $result -match "dockerDesktopLinuxEngine") {
            return $false
        }
        return $false
    } catch {
        return $false
    }
}

# Function to wait for Docker to be ready
function Wait-DockerReady {
    Write-Host "Waiting for Docker Desktop to be ready..." -ForegroundColor Yellow
    $maxAttempts = 60
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        if (Test-DockerRunning) {
            Write-Host "[OK] Docker Desktop is ready!" -ForegroundColor Green
            return $true
        }
        $attempt++
        Write-Host "  Attempt $attempt/$maxAttempts..." -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
    
    Write-Host "[ERROR] Docker Desktop did not start in time" -ForegroundColor Red
    return $false
}

# Check if Docker is already running
Write-Host "Checking Docker Desktop status..." -ForegroundColor Yellow
$dockerReady = Test-DockerRunning
if ($dockerReady) {
    Write-Host "[OK] Docker Desktop is running and ready" -ForegroundColor Green
} else {
    Write-Host "[INFO] Docker Desktop is not running, starting it..." -ForegroundColor Yellow
    
    # Try to find Docker Desktop executable
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
        Write-Host "Starting Docker Desktop from: $dockerExe" -ForegroundColor Yellow
        Start-Process -FilePath $dockerExe -WindowStyle Hidden
        
        # Wait for Docker to be ready
        if (-not (Wait-DockerReady)) {
            Write-Host ""
            Write-Host "[ERROR] Docker Desktop started but engine is not ready" -ForegroundColor Red
            Write-Host "Please wait for Docker Desktop to fully start (check system tray)" -ForegroundColor Yellow
            Write-Host "Then run this script again, or start Prometheus manually:" -ForegroundColor Yellow
            Write-Host "  docker-compose -f docker-compose.monitoring.yml up -d" -ForegroundColor Gray
            exit 1
        }
    } else {
        Write-Host "[ERROR] Could not find Docker Desktop executable" -ForegroundColor Red
        Write-Host "Please install Docker Desktop or start it manually." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Common locations:" -ForegroundColor Yellow
        foreach ($path in $dockerPaths) {
            Write-Host "  - $path" -ForegroundColor Gray
        }
        exit 1
    }
}

# Start Prometheus and Alertmanager
Write-Host ""
Write-Host "Starting Prometheus and Alertmanager..." -ForegroundColor Yellow
try {
    docker-compose -f docker-compose.monitoring.yml up -d
    
    Write-Host ""
    Write-Host "[OK] Prometheus stack started!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Waiting for services to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Verify Prometheus is running
    Write-Host ""
    Write-Host "Verifying services..." -ForegroundColor Yellow
    try {
        $health = Invoke-WebRequest -Uri "http://localhost:9090/-/healthy" -UseBasicParsing -TimeoutSec 5
        if ($health.Content -like "*Healthy*") {
            Write-Host "[OK] Prometheus is healthy" -ForegroundColor Green
        }
    } catch {
        Write-Host "[WARNING] Prometheus health check failed (may still be starting)" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Prometheus Monitoring Stack Started!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Prometheus UI:     http://localhost:9090" -ForegroundColor White
    Write-Host "Prometheus Targets: http://localhost:9090/targets" -ForegroundColor White
    Write-Host "Alertmanager:      http://localhost:9093" -ForegroundColor White
    Write-Host ""
    Write-Host "Note: It may take 15-30 seconds for targets to show as UP" -ForegroundColor Gray
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "[ERROR] Failed to start Prometheus stack" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Check Docker Desktop is running" -ForegroundColor Gray
    Write-Host "  2. Check logs: docker-compose -f docker-compose.monitoring.yml logs" -ForegroundColor Gray
    Write-Host "  3. Check ports 9090 and 9093 are not in use" -ForegroundColor Gray
    exit 1
}

