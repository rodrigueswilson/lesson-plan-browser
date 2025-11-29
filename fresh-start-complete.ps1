# Complete Fresh Start Script - Full Reset
# Stops all services, cleans everything, restarts Docker/Prometheus, and starts services fresh
# Improved version with better error handling and verification

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Complete Fresh Start - Full Reset" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will:" -ForegroundColor Yellow
Write-Host "  1. Stop ALL running processes (backend, frontend, Docker)" -ForegroundColor Gray
Write-Host "  2. Clean ALL caches and temporary files" -ForegroundColor Gray
Write-Host "  3. Stop and restart Docker Desktop" -ForegroundColor Gray
Write-Host "  4. Stop and restart Prometheus containers" -ForegroundColor Gray
Write-Host "  5. Restart all services fresh with verification" -ForegroundColor Gray
Write-Host ""
$confirm = Read-Host "Continue? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 1: Stopping ALL Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to test if a port can actually be bound
function Test-PortBindable {
    param([int]$Port)
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

# Function to stop processes more aggressively
function Stop-ProcessesOnPort {
    param([int]$Port)
    $attempts = 0
    $maxAttempts = 10
    
    Write-Host "  Attempting to free port $Port..." -ForegroundColor Gray
    
    while ($attempts -lt $maxAttempts) {
        # First check if port is actually bindable (more reliable)
        if (Test-PortBindable -Port $Port) {
            Write-Host "  [OK] Port $Port is available for binding" -ForegroundColor Green
            return $true
        }
        
        $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if (-not $connections) {
            # No connections but port still not bindable - might be reserved or in TIME_WAIT
            Write-Host "  [INFO] No active connections, but port may be in TIME_WAIT state" -ForegroundColor Yellow
            Start-Sleep -Seconds 2
            $attempts++
            continue
        }
        
        $stoppedAny = $false
        foreach ($conn in $connections) {
            try {
                $procId = $conn.OwningProcess
                
                # Skip system processes (PID 0, 4, etc.)
                if ($procId -eq 0 -or $procId -eq 4) {
                    continue
                }
                
                $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
                if ($proc) {
                    # Handle Docker processes specially
                    if ($proc.ProcessName -like "*docker*" -or $proc.Path -like "*docker*") {
                        Write-Host "    Docker process detected (PID $procId), checking containers..." -ForegroundColor Gray
                        # Try to find and stop containers using the port
                        try {
                            $containers = docker ps --format "{{.ID}} {{.Ports}}" 2>&1
                            if ($LASTEXITCODE -eq 0) {
                                $containersWithPort = $containers | Where-Object { $_ -like "*8000*" }
                                if ($containersWithPort) {
                                    Write-Host "    Stopping Docker containers using port 8000..." -ForegroundColor Gray
                                    docker ps --filter "publish=8000" --format "{{.ID}}" | ForEach-Object {
                                        docker stop $_ 2>$null
                                    }
                                    Start-Sleep -Seconds 2
                                }
                            }
                        } catch {}
                        
                        # Still try to stop the process, but it might be protected
                        Write-Host "    Attempting to stop Docker process PID $procId..." -ForegroundColor Gray
                        try {
                            Stop-Process -Id $procId -Force -ErrorAction Stop
                            $stoppedAny = $true
                        } catch {
                            Write-Host "      [WARNING] Cannot stop Docker process (may be system-protected)" -ForegroundColor Yellow
                        }
                    } else {
                        Write-Host "    Stopping PID $procId ($($proc.ProcessName))..." -ForegroundColor Gray
                        Stop-Process -Id $procId -Force -ErrorAction Stop
                        $stoppedAny = $true
                    }
                }
            } catch {
                # Try using taskkill as fallback
                try {
                    $procId = $conn.OwningProcess
                    if ($procId -ne 0 -and $procId -ne 4) {
                        $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
                        if ($proc -and $proc.ProcessName -notlike "*docker*") {
                            Start-Process -FilePath "taskkill" -ArgumentList "/F", "/PID", $procId -Wait -NoNewWindow -ErrorAction SilentlyContinue
                            $stoppedAny = $true
                        }
                    }
                } catch {}
            }
        }
        
        if ($stoppedAny) {
            Start-Sleep -Seconds 2
        } else {
            # No processes stopped, wait longer
            Start-Sleep -Seconds 1
        }
        
        $attempts++
    }
    
    # Final check - test if port is actually bindable
    if (Test-PortBindable -Port $Port) {
        Write-Host "  [OK] Port $Port is now available for binding" -ForegroundColor Green
        return $true
    }
    
    # Check remaining processes (excluding system processes)
    $remaining = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -ne 0 -and $_.OwningProcess -ne 4 }
    if ($remaining) {
        Write-Host "  [WARNING] Port $Port still has processes after $maxAttempts attempts" -ForegroundColor Yellow
        $remaining | ForEach-Object {
            $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
            if ($proc) {
                $procInfo = "PID $($proc.Id) - $($proc.ProcessName)"
                # Check if it's Docker backend - might not actually block binding
                if ($proc.ProcessName -like "*docker*") {
                    Write-Host "    Remaining: $procInfo (Docker backend - may not block binding)" -ForegroundColor Yellow
                } else {
                    Write-Host "    Remaining: $procInfo" -ForegroundColor Yellow
                }
            }
        }
        return $false
    }
    
    # Port might be in TIME_WAIT state - wait a bit more
    Write-Host "  [INFO] Port may be in TIME_WAIT state, waiting..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    if (Test-PortBindable -Port $Port) {
        Write-Host "  [OK] Port $Port is now available" -ForegroundColor Green
        return $true
    }
    
    return $false
}

# Stop backend processes - more aggressive
Write-Host "Stopping backend processes..." -ForegroundColor Yellow
# Kill all Python processes that might be uvicorn
Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        if ($cmdLine -like "*uvicorn*" -or $cmdLine -like "*backend*") {
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
            Write-Host "  Stopped Python process $($_.Id)" -ForegroundColor Gray
        }
    } catch {}
}

# Stop all processes on port 8000
Write-Host "Clearing port 8000..." -ForegroundColor Yellow
Stop-ProcessesOnPort -Port 8000
Start-Sleep -Seconds 2

# Verify port is clear
$remaining = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($remaining) {
    Write-Host "[WARNING] Some processes still on port 8000, forcing stop..." -ForegroundColor Yellow
    $remaining | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 2
}

# Stop frontend processes
Write-Host "Stopping frontend processes..." -ForegroundColor Yellow
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process "Bilingual Lesson Planner" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Stop Prometheus containers and any containers using port 8000
Write-Host "Stopping Prometheus containers..." -ForegroundColor Yellow
try {
    docker-compose -f docker-compose.monitoring.yml down 2>$null
    Write-Host "[OK] Prometheus containers stopped" -ForegroundColor Green
} catch {
    Write-Host "[INFO] Prometheus containers already stopped or not running" -ForegroundColor Gray
}

# Stop any Docker containers that might be using port 8000
Write-Host "Checking for Docker containers using port 8000..." -ForegroundColor Yellow
try {
    $containers = docker ps --filter "publish=8000" --format "{{.ID}} {{.Names}}" 2>&1
    if ($LASTEXITCODE -eq 0 -and $containers) {
        Write-Host "Found containers using port 8000:" -ForegroundColor Yellow
        $containers | ForEach-Object {
            $parts = $_ -split '\s+', 2
            if ($parts.Length -ge 1) {
                Write-Host "  Stopping container: $($parts[1])" -ForegroundColor Gray
                docker stop $parts[0] 2>$null
            }
        }
        Start-Sleep -Seconds 2
    }
} catch {
    # Docker might not be running, that's OK
}

Start-Sleep -Seconds 2

# Stop Docker Desktop
Write-Host "Stopping Docker Desktop..." -ForegroundColor Yellow
$dockerProcesses = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
if ($dockerProcesses) {
    $dockerProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "Waiting for Docker Desktop to stop..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
    
    # Verify Docker stopped
    $stillRunning = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
    if ($stillRunning) {
        Write-Host "[WARNING] Docker Desktop still running, waiting longer..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
} else {
    Write-Host "[INFO] Docker Desktop not running" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 2: Cleaning ALL Caches" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Clean Python cache
Write-Host "Cleaning Python cache..." -ForegroundColor Yellow
$pycacheCount = (Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Measure-Object).Count
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Recurse -Filter "*.pyo" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "  Cleaned $pycacheCount Python cache directories" -ForegroundColor Gray

# Clean frontend cache
Write-Host "Cleaning frontend cache..." -ForegroundColor Yellow
$frontendCacheCleaned = $false
if (Test-Path "frontend\node_modules\.cache") {
    Remove-Item -Path "frontend\node_modules\.cache" -Recurse -Force -ErrorAction SilentlyContinue
    $frontendCacheCleaned = $true
}
if (Test-Path "frontend\.vite") {
    Remove-Item -Path "frontend\.vite" -Recurse -Force -ErrorAction SilentlyContinue
    $frontendCacheCleaned = $true
}
if (Test-Path "frontend\dist") {
    Remove-Item -Path "frontend\dist" -Recurse -Force -ErrorAction SilentlyContinue
    $frontendCacheCleaned = $true
}
if ($frontendCacheCleaned) {
    Write-Host "  Frontend cache cleaned" -ForegroundColor Gray
} else {
    Write-Host "  No frontend cache to clean" -ForegroundColor Gray
}

# Clean log files (optional - keep recent)
Write-Host "Cleaning old log files..." -ForegroundColor Yellow
if (Test-Path "logs") {
    $oldLogs = Get-ChildItem -Path "logs" -Filter "*.log" -ErrorAction SilentlyContinue | 
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) }
    $oldLogs | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "  Cleaned $($oldLogs.Count) old log files" -ForegroundColor Gray
}

# Clean temporary files
Write-Host "Cleaning temporary files..." -ForegroundColor Yellow
Get-ChildItem -Path $env:TEMP -Filter "*lesson*" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path "." -Filter "*.tmp" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "[OK] Cache cleaning complete" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 3: Restarting Docker & Prometheus" -ForegroundColor Cyan
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
    
    $maxAttempts = 60
    $attempt = 0
    $dockerReady = $false
    while ($attempt -lt $maxAttempts) {
        try {
            $null = docker ps 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[OK] Docker Desktop is ready!" -ForegroundColor Green
                $dockerReady = $true
                break
            }
        } catch {}
        $attempt++
        if ($attempt % 10 -eq 0) {
            Write-Host "  Still waiting... ($attempt/$maxAttempts)" -ForegroundColor Gray
        }
        Start-Sleep -Seconds 2
    }
    
    if (-not $dockerReady) {
        Write-Host "[WARNING] Docker Desktop may not be fully ready, but continuing..." -ForegroundColor Yellow
    }
} else {
    Write-Host "[WARNING] Docker Desktop executable not found, skipping..." -ForegroundColor Yellow
}

# Start Prometheus
Write-Host ""
Write-Host "Starting Prometheus monitoring stack..." -ForegroundColor Yellow
try {
    & ".\start-prometheus.ps1" -ErrorAction Stop
    Start-Sleep -Seconds 3
    
    # Verify Prometheus
    try {
        $promResponse = Invoke-WebRequest -Uri "http://localhost:9090/-/healthy" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($promResponse.Content -like "*Healthy*") {
            Write-Host "[OK] Prometheus is healthy" -ForegroundColor Green
        }
    } catch {
        Write-Host "[WARNING] Prometheus health check failed (may still be starting)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARNING] Prometheus startup had issues: $($_.Exception.Message)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Step 4: Starting Services Fresh" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verify port 8000 is free before starting backend (test actual binding)
Write-Host "Verifying port 8000 is available..." -ForegroundColor Yellow

# First test if port is actually bindable (more reliable than connection list)
$portBindable = Test-PortBindable -Port 8000

if (-not $portBindable) {
    Write-Host "[WARNING] Port 8000 cannot be bound! Checking processes..." -ForegroundColor Yellow
    $portCheck = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -ne 0 -and $_.OwningProcess -ne 4 }
    
    if ($portCheck) {
        # Show what's using the port (excluding system processes)
        Write-Host "Processes using port 8000:" -ForegroundColor Gray
        $portCheck | ForEach-Object {
            $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
            if ($proc) {
                $procInfo = "  PID $($proc.Id): $($proc.ProcessName)"
                if ($proc.ProcessName -like "*docker*") {
                    Write-Host "$procInfo (Docker backend)" -ForegroundColor Gray
                } else {
                    Write-Host "$procInfo" -ForegroundColor Gray
                }
            }
        }
    }
    
    # Try to free the port
    $portFreed = Stop-ProcessesOnPort -Port 8000
    
    if (-not $portFreed) {
        Write-Host "[WARNING] Port 8000 still has processes after cleanup attempts." -ForegroundColor Yellow
        
        # Check if it's Docker processes
        $portCheck = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -ne 0 -and $_.OwningProcess -ne 4 }
        $dockerProcs = $portCheck | ForEach-Object {
            $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
            if ($proc -and ($proc.ProcessName -like "*docker*" -or $proc.Path -like "*docker*")) {
                $proc
            }
        }
        
        if ($dockerProcs) {
            Write-Host "Docker processes detected. Checking if port is actually bindable..." -ForegroundColor Yellow
            
            # Test if port can actually be bound (Docker backend might not block it)
            if (Test-PortBindable -Port 8000) {
                Write-Host "[OK] Port 8000 is bindable despite Docker process (safe to continue)" -ForegroundColor Green
                $portFreed = $true
            } else {
                Write-Host "Port cannot be bound. Trying to restart Docker..." -ForegroundColor Yellow
                Write-Host "This will stop all Docker containers and free the port." -ForegroundColor Gray
                
                # Stop Docker Desktop
                $dockerProcesses = Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue
                if ($dockerProcesses) {
                    $dockerProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
                    Write-Host "Waiting for Docker to stop..." -ForegroundColor Gray
                    Start-Sleep -Seconds 5
                }
                
                # Check port again with actual binding test
                if (Test-PortBindable -Port 8000) {
                    Write-Host "[OK] Port 8000 is now bindable after Docker restart" -ForegroundColor Green
                    $portFreed = $true
                } else {
                    Write-Host "[ERROR] Port 8000 still cannot be bound. Manual intervention needed." -ForegroundColor Red
                    Write-Host ""
                    Write-Host "Please run this command manually:" -ForegroundColor Yellow
                    Write-Host "  .\stop-port-8000.ps1" -ForegroundColor Cyan
                    Write-Host ""
                    Write-Host "Or use Task Manager to stop the processes listed above." -ForegroundColor Yellow
                    Write-Host ""
                    $continue = Read-Host "Continue anyway? (Y/N)"
                    if ($continue -ne "Y" -and $continue -ne "y") {
                        exit 1
                    }
                }
            }
        } else {
            Write-Host "[ERROR] Cannot free port 8000 automatically." -ForegroundColor Red
            Write-Host "Please run this command manually:" -ForegroundColor Yellow
            Write-Host "  .\stop-port-8000.ps1" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Or use Task Manager to stop the processes listed above." -ForegroundColor Yellow
            Write-Host ""
            $continue = Read-Host "Continue anyway? (Y/N)"
            if ($continue -ne "Y" -and $continue -ne "y") {
                exit 1
            }
        }
    } else {
        Start-Sleep -Seconds 2
    }
} else {
    # Double-check with binding test
    if (Test-PortBindable -Port 8000) {
        Write-Host "[OK] Port 8000 is available and bindable" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Port 8000 shows as free but may not be bindable" -ForegroundColor Yellow
    }
}

# Check for Python virtual environment
Write-Host "Checking Python environment..." -ForegroundColor Yellow
$pythonCmd = "python"
if (Test-Path ".venv\Scripts\python.exe") {
    $pythonCmd = ".venv\Scripts\python.exe"
    Write-Host "[OK] Using virtual environment" -ForegroundColor Green
} else {
    Write-Host "[INFO] Using system Python" -ForegroundColor Gray
}

# Start Backend
Write-Host ""
Write-Host "Starting Backend API Server..." -ForegroundColor Yellow
$backendScript = "cd /d $PWD && $pythonCmd -m uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000"
Start-Process cmd -ArgumentList "/k", $backendScript -WindowStyle Normal

# Wait for backend to initialize with better verification
Write-Host "Waiting for backend to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Verify backend with retries
$backendReady = $false
$maxRetries = 15
for ($i = 1; $i -le $maxRetries; $i++) {
    try {
        # First check if port is listening
        $listening = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
        if ($listening) {
            # Then try actual API call
            $response = Invoke-RestMethod -Uri "http://localhost:8000/api/users" -Method Get -TimeoutSec 5 -ErrorAction Stop
            Write-Host "[OK] Backend is responding! Found $($response.Count) users" -ForegroundColor Green
            $backendReady = $true
            break
        } else {
            if ($i -lt $maxRetries) {
                Write-Host "  Backend starting... ($i/$maxRetries)" -ForegroundColor Gray
            }
        }
    } catch {
        if ($i -lt $maxRetries) {
            Write-Host "  Backend starting... ($i/$maxRetries)" -ForegroundColor Gray
        }
    }
    Start-Sleep -Seconds 2
}

if (-not $backendReady) {
    Write-Host "[ERROR] Backend failed to start after $maxRetries attempts" -ForegroundColor Red
    Write-Host "Check the backend window for errors" -ForegroundColor Yellow
    Write-Host "You may need to start it manually:" -ForegroundColor Yellow
    Write-Host "  cd d:\LP" -ForegroundColor Gray
    Write-Host "  python -m uvicorn backend.api:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Gray
} else {
    # Verify backend stability with multiple requests
    Write-Host "Verifying backend stability..." -ForegroundColor Yellow
    $successCount = 0
    for ($i = 1; $i -le 3; $i++) {
        try {
            $null = Invoke-RestMethod -Uri "http://localhost:8000/api/users" -Method Get -TimeoutSec 3 -ErrorAction Stop
            $successCount++
        } catch {
            # First request can timeout during cold start, that's OK
            if ($i -gt 1) {
                Write-Host "[WARNING] Request $i failed: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
        Start-Sleep -Seconds 1
    }
    if ($successCount -ge 2) {
        Write-Host "[OK] Backend is stable" -ForegroundColor Green
    }
}

# Start Frontend
Write-Host ""
Write-Host "Starting Frontend (Tauri)..." -ForegroundColor Yellow
if (Test-Path "frontend") {
    Start-Process cmd -ArgumentList "/k", "cd /d $PWD\frontend && npm run tauri:dev" -WindowStyle Normal
    Write-Host "[OK] Frontend starting..." -ForegroundColor Green
} else {
    Write-Host "[ERROR] Frontend directory not found!" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Complete Fresh Start Finished!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Final status check
Write-Host "Final Status Check:" -ForegroundColor White
Write-Host ""

$backendWorking = $false
$prometheusWorking = $false

# Check Backend
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/users" -Method Get -TimeoutSec 3 -ErrorAction Stop
    Write-Host "  [OK] Backend: http://localhost:8000 ($($response.Count) users)" -ForegroundColor Green
    $backendWorking = $true
} catch {
    Write-Host "  [ERROR] Backend: Not responding" -ForegroundColor Red
}

# Check Prometheus
try {
    $promResponse = Invoke-WebRequest -Uri "http://localhost:9090/-/healthy" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    Write-Host "  [OK] Prometheus: http://localhost:9090" -ForegroundColor Green
    $prometheusWorking = $true
} catch {
    Write-Host "  [WARNING] Prometheus: May not be ready yet" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Opening browser windows for debugging..." -ForegroundColor Yellow

# Open browser windows for debugging
Start-Sleep -Seconds 2

# Open Backend API Docs
if ($backendWorking) {
    Write-Host "  Opening Backend API Docs..." -ForegroundColor Gray
    Start-Process "http://localhost:8000/api/docs"
    Start-Sleep -Seconds 1
} else {
    Write-Host "  Skipping Backend API Docs (backend not ready)" -ForegroundColor Yellow
}

# Open Prometheus
if ($prometheusWorking) {
    Write-Host "  Opening Prometheus..." -ForegroundColor Gray
    Start-Process "http://localhost:9090"
    Start-Sleep -Seconds 1
    
    Write-Host "  Opening Prometheus Targets..." -ForegroundColor Gray
    Start-Sleep -Seconds 1
    Start-Process "http://localhost:9090/targets"
} else {
    Write-Host "  Skipping Prometheus (not ready yet)" -ForegroundColor Yellow
}

# Open Backend health/users endpoint for quick check
if ($backendWorking) {
    Write-Host "  Opening Backend Users API..." -ForegroundColor Gray
    Start-Sleep -Seconds 1
    Start-Process "http://localhost:8000/api/users"
}

# Wait for frontend to start, then open it
Write-Host ""
Write-Host "Waiting for frontend dev server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Try to open frontend in browser (Vite dev server runs on port 1420)
$frontendUrl = "http://localhost:1420"
$frontendWorking = $false

for ($i = 1; $i -le 10; $i++) {
    try {
        $response = Invoke-WebRequest -Uri $frontendUrl -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "  Opening Frontend App..." -ForegroundColor Gray
            Start-Process $frontendUrl
            $frontendWorking = $true
            break
        }
    } catch {
        if ($i -lt 10) {
            Write-Host "  Frontend starting... ($i/10)" -ForegroundColor Gray
            Start-Sleep -Seconds 2
        }
    }
}

if (-not $frontendWorking) {
    Write-Host "  [INFO] Frontend dev server not ready yet (Tauri app may open separately)" -ForegroundColor Yellow
    Write-Host "  Frontend URL: $frontendUrl" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Services:" -ForegroundColor White
Write-Host "  - Backend: http://localhost:8000" -ForegroundColor Gray
Write-Host "  - API Docs: http://localhost:8000/api/docs" -ForegroundColor Gray
Write-Host "  - Frontend App: http://localhost:1420" -ForegroundColor Gray
Write-Host "  - Prometheus: http://localhost:9090" -ForegroundColor Gray
Write-Host "  - Prometheus Targets: http://localhost:9090/targets" -ForegroundColor Gray
Write-Host ""
Write-Host "Browser windows opened for debugging!" -ForegroundColor Green
Write-Host "All caches cleaned, Docker restarted, services fresh!" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
