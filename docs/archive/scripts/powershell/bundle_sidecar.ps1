# PowerShell script to bundle Python sidecar for Android
# Usage: .\bundle_sidecar.ps1 [pyinstaller|nuitka|docker]

param(
    [Parameter(Position=0)]
    [ValidateSet('pyinstaller', 'nuitka', 'docker')]
    [string]$Bundler = 'pyinstaller'
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ScriptDir "backend"
$OutputDir = Join-Path $ScriptDir "frontend\src-tauri\binaries"

Write-Host "=== Python Sidecar Bundling ===" -ForegroundColor Cyan
Write-Host "Bundler: $Bundler" -ForegroundColor Yellow
Write-Host ""

# Create output directory
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

switch ($Bundler) {
    'pyinstaller' {
        Write-Host "Using PyInstaller..." -ForegroundColor Green
        Push-Location $BackendDir
        
        try {
            pyinstaller --onefile `
                --name python-sync-processor `
                --hidden-import=backend.ipc_database `
                --hidden-import=backend.supabase_database `
                --hidden-import=backend.schema `
                --hidden-import=backend.config `
                --hidden-import=backend.database_interface `
                --hidden-import=supabase `
                --hidden-import=postgrest `
                --hidden-import=pydantic `
                --collect-all=supabase `
                --collect-all=postgrest `
                sidecar_main.py
            
            $BinaryPath = Join-Path $BackendDir "dist\python-sync-processor.exe"
            if (Test-Path $BinaryPath) {
                $TargetName = "python-sync-processor-x86_64-pc-windows-msvc.exe"
                Copy-Item $BinaryPath (Join-Path $OutputDir $TargetName)
                Write-Host "✓ Binary created: $OutputDir\$TargetName" -ForegroundColor Green
            } else {
                Write-Host "✗ Build failed - binary not found" -ForegroundColor Red
                exit 1
            }
        } finally {
            Pop-Location
        }
    }
    
    'nuitka' {
        Write-Host "Using Nuitka..." -ForegroundColor Green
        Push-Location $BackendDir
        
        try {
            python -m nuitka `
                --standalone `
                --onefile `
                --include-module=backend `
                --include-module=backend.sidecar_main `
                --include-module=backend.ipc_database `
                --include-module=backend.supabase_database `
                --include-module=backend.schema `
                --include-module=backend.config `
                --include-module=backend.database_interface `
                --output-filename=python-sync-processor `
                --assume-yes-for-downloads `
                sidecar_main.py
            
            $BinaryPath = Join-Path $BackendDir "python-sync-processor.exe"
            if (Test-Path $BinaryPath) {
                $TargetName = "python-sync-processor-x86_64-pc-windows-msvc.exe"
                Copy-Item $BinaryPath (Join-Path $OutputDir $TargetName)
                Write-Host "✓ Binary created: $OutputDir\$TargetName" -ForegroundColor Green
            } else {
                Write-Host "✗ Build failed - binary not found" -ForegroundColor Red
                exit 1
            }
        } finally {
            Pop-Location
        }
    }
    
    'docker' {
        Write-Host "Using Docker for cross-compilation..." -ForegroundColor Green
        
        # Build Docker image
        docker build -f Dockerfile.android-python -t python-android-build .
        
        # Extract binary from container
        $ContainerId = docker create python-android-build
        docker cp "${ContainerId}:/app/python-sync-processor" "$OutputDir\python-sync-processor-aarch64-linux-android"
        docker rm $ContainerId
        
        Write-Host "✓ Binary created: $OutputDir\python-sync-processor-aarch64-linux-android" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "=== Bundle Complete ===" -ForegroundColor Cyan
Write-Host "Binary location: $OutputDir" -ForegroundColor Yellow
$Binaries = Get-ChildItem (Join-Path $OutputDir "python-sync-processor*") -ErrorAction SilentlyContinue
if ($Binaries) {
    $Binaries | Format-Table Name, Length
} else {
    Write-Host "No binaries found" -ForegroundColor Yellow
}

