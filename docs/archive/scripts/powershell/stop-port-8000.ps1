# Quick script to stop all processes using port 8000
# Usage: .\stop-port-8000.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Stopping Processes on Port 8000" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Find processes using port 8000 (excluding system processes)
Write-Host "Finding processes using port 8000..." -ForegroundColor Yellow
$connections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -ne 0 -and $_.OwningProcess -ne 4 }

if (-not $connections) {
    Write-Host "[OK] No processes found on port 8000 (excluding system processes)" -ForegroundColor Green
    exit 0
}

Write-Host "Found $($connections.Count) process(es) using port 8000:" -ForegroundColor Yellow
Write-Host ""

$processesToStop = @()
foreach ($conn in $connections) {
    try {
        $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  PID: $($proc.Id)" -ForegroundColor Cyan
            Write-Host "  Name: $($proc.ProcessName)" -ForegroundColor Gray
            Write-Host "  Path: $($proc.Path)" -ForegroundColor Gray
            Write-Host ""
            $processesToStop += $proc.Id
        }
    } catch {
        Write-Host "  PID: $($conn.OwningProcess) (cannot get details)" -ForegroundColor Yellow
        $processesToStop += $conn.OwningProcess
    }
}

Write-Host "Stopping processes..." -ForegroundColor Yellow
$stoppedCount = 0
$failedCount = 0

foreach ($pid in $processesToStop) {
    try {
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  Stopping PID $pid ($($proc.ProcessName))..." -ForegroundColor Gray
            
            # Handle Docker processes specially
            if ($proc.ProcessName -like "*docker*" -or $proc.Path -like "*docker*") {
                Write-Host "    Docker process detected, checking containers..." -ForegroundColor Yellow
                try {
                    # Stop containers using port 8000
                    $containers = docker ps --filter "publish=8000" --format "{{.ID}} {{.Names}}" 2>&1
                    if ($LASTEXITCODE -eq 0 -and $containers) {
                        $containers | ForEach-Object {
                            $parts = $_ -split '\s+', 2
                            if ($parts.Length -ge 1) {
                                Write-Host "      Stopping container: $($parts[1])" -ForegroundColor Gray
                                docker stop $parts[0] 2>$null
                            }
                        }
                        Start-Sleep -Seconds 2
                    }
                    
                    # Try to stop the Docker process
                    Stop-Process -Id $pid -Force -ErrorAction Stop
                    Write-Host "    [OK] Stopped Docker process" -ForegroundColor Green
                    $stoppedCount++
                } catch {
                    Write-Host "    [WARNING] Cannot stop Docker process (may require Docker Desktop restart)" -ForegroundColor Yellow
                    Write-Host "    Try stopping Docker Desktop manually from system tray" -ForegroundColor Gray
                    $failedCount++
                }
            } else {
                Stop-Process -Id $pid -Force -ErrorAction Stop
                Write-Host "    [OK] Stopped" -ForegroundColor Green
                $stoppedCount++
            }
        }
    } catch {
        Write-Host "    [ERROR] Failed to stop PID $pid: $($_.Exception.Message)" -ForegroundColor Red
        $failedCount++
        
        # Try taskkill as fallback (skip Docker processes)
        try {
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($proc -and $proc.ProcessName -notlike "*docker*") {
                Write-Host "    Trying taskkill..." -ForegroundColor Gray
                $result = Start-Process -FilePath "taskkill" -ArgumentList "/F", "/PID", $pid -Wait -NoNewWindow -PassThru -ErrorAction Stop
                if ($result.ExitCode -eq 0) {
                    Write-Host "    [OK] Stopped with taskkill" -ForegroundColor Green
                    $stoppedCount++
                    $failedCount--
                }
            }
        } catch {
            Write-Host "    [ERROR] taskkill also failed" -ForegroundColor Red
        }
    }
}

Start-Sleep -Seconds 2

# Verify port is free
Write-Host ""
Write-Host "Verifying port 8000 is free..." -ForegroundColor Yellow
$remaining = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if (-not $remaining) {
    Write-Host "[OK] Port 8000 is now free!" -ForegroundColor Green
    Write-Host "Stopped $stoppedCount process(es)" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Port 8000 still has $($remaining.Count) process(es)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Remaining processes:" -ForegroundColor Yellow
    $remaining | ForEach-Object {
        $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  PID $($proc.Id): $($proc.ProcessName)" -ForegroundColor Red
        } else {
            Write-Host "  PID $($_.OwningProcess): (unknown)" -ForegroundColor Red
        }
    }
    Write-Host ""
    Write-Host "You may need to stop these manually using Task Manager" -ForegroundColor Yellow
    Write-Host "or run this command:" -ForegroundColor Yellow
    Write-Host "  Get-NetTCPConnection -LocalPort 8000 | ForEach-Object { Stop-Process -Id `$_.OwningProcess -Force }" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

