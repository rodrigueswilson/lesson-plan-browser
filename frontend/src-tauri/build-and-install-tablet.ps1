# Build and Install APK for Physical Tablet
# This script detects connected tablet, determines architecture, builds APK, and installs it

$ErrorActionPreference = "Stop"

Write-Host "=== Tablet Build and Install Script ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check for connected devices
Write-Host "[1/6] Checking for connected devices..." -ForegroundColor Yellow
$adbOutput = adb devices 2>&1
$devices = @()
foreach ($line in $adbOutput) {
    # Match device lines: device_id followed by whitespace and "device"
    if ($line -match '^([^\s\t]+)[\s\t]+device\s*$') {
        $devices += $matches[1]
    }
}

if ($devices.Count -eq 0) {
    Write-Host "[ERROR] No devices connected!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "  1. Connect tablet via USB" -ForegroundColor White
    Write-Host "  2. Enable USB Debugging (Settings → Developer Options)" -ForegroundColor White
    Write-Host "  3. Accept USB debugging prompt on tablet" -ForegroundColor White
    Write-Host "  4. Run: adb devices" -ForegroundColor White
    exit 1
}

$deviceId = $devices[0]
Write-Host "[OK] Found device: $deviceId" -ForegroundColor Green

# Step 2: Determine tablet architecture
Write-Host "[2/6] Determining tablet architecture..." -ForegroundColor Yellow
$abi = adb -s $deviceId shell getprop ro.product.cpu.abi
$abi = $abi.Trim()

Write-Host "  CPU ABI: $abi" -ForegroundColor Cyan

# Map ABI to build target (Gradle uses different naming)
$buildTarget = switch ($abi) {
    "arm64-v8a" { "Arm64" }  # Gradle uses "Arm64" not "aarch64"
    "armeabi-v7a" { "Armv7" }
    "x86_64" { "X86_64" }
    default { 
        Write-Host "[WARNING] Unknown ABI: $abi. Defaulting to Arm64" -ForegroundColor Yellow
        "Arm64"
    }
}

# Also need the path name (uses lowercase)
$pathTarget = switch ($abi) {
    "arm64-v8a" { "arm64" }
    "armeabi-v7a" { "armv7" }
    "x86_64" { "x86_64" }
    default { "arm64" }
}

Write-Host "[OK] Build target: $buildTarget (path: $pathTarget)" -ForegroundColor Green

# Step 3: Build APK
Write-Host "[3/6] Building APK for $buildTarget..." -ForegroundColor Yellow
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$androidDir = Join-Path $scriptDir "gen\android"

Push-Location $androidDir

try {
    $gradleTask = "assemble${buildTarget}Debug"
    # Skip all Rust builds - we'll use the already-built library or let Tauri CLI handle it
    Write-Host "  Running: .\gradlew.bat $gradleTask -x rustBuildArm64Debug -x rustBuildArmDebug -x rustBuildUniversalDebug" -ForegroundColor Cyan
    $env:CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER = "C:\Users\rodri\AppData\Local\Android\Sdk\ndk\29.0.14206865\toolchains\llvm\prebuilt\windows-x86_64\bin\aarch64-linux-android30-clang.cmd"
    & .\gradlew.bat $gradleTask "-x" "rustBuildArm64Debug" "-x" "rustBuildArmDebug" "-x" "rustBuildUniversalDebug"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Gradle build failed!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "[OK] APK built successfully" -ForegroundColor Green
} finally {
    Pop-Location
}

# Step 4: Find APK file
Write-Host "[4/6] Locating APK file..." -ForegroundColor Yellow
$apkPath = Join-Path $androidDir "app\build\outputs\apk\$pathTarget\debug\app-$pathTarget-debug.apk"

if (-not (Test-Path $apkPath)) {
    Write-Host "[ERROR] APK not found at: $apkPath" -ForegroundColor Red
    exit 1
}

$apkSize = (Get-Item $apkPath).Length / 1MB
Write-Host "[OK] APK found: $apkPath ($([math]::Round($apkSize, 2)) MB)" -ForegroundColor Green

# Step 5: Uninstall existing version (if any)
Write-Host "[5/6] Uninstalling existing version (if any)..." -ForegroundColor Yellow
adb -s $deviceId uninstall com.lessonplanner.bilingual 2>&1 | Out-Null
Write-Host "[OK] Cleaned up" -ForegroundColor Green

# Step 6: Install APK
Write-Host "[6/6] Installing APK on tablet..." -ForegroundColor Yellow
adb -s $deviceId install -r $apkPath

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Installation failed!" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] APK installed successfully" -ForegroundColor Green

# Launch app
Write-Host ""
Write-Host "Launching app..." -ForegroundColor Yellow
adb -s $deviceId shell am start -n com.lessonplanner.bilingual/.MainActivity

Write-Host ""
Write-Host "=== SUCCESS ===" -ForegroundColor Green
Write-Host ""
Write-Host "App installed and launched on tablet!" -ForegroundColor Green
Write-Host ""
Write-Host "To view logs:" -ForegroundColor Cyan
Write-Host "  adb -s $deviceId logcat | Select-String 'Bilingual|Sidecar|API|Error'" -ForegroundColor White
Write-Host ""
Write-Host "PC IP: 192.168.12.153" -ForegroundColor Yellow
Write-Host "Backend: http://192.168.12.153:8000" -ForegroundColor Yellow
Write-Host ""

