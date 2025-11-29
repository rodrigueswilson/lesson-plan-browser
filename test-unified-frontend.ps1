# Unified Frontend Testing Script
# This script helps verify the unified frontend implementation

Write-Host "=== Unified Frontend Testing ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: File Structure Verification
Write-Host "1. File Structure Verification" -ForegroundColor Yellow
$filesToCheck = @(
    "lesson-plan-browser\frontend\src\App.tsx",
    "lesson-plan-browser\frontend\src\hooks\usePlatformFeatures.ts",
    "lesson-plan-browser\frontend\src\lib\platform.ts",
    "frontend\src\App.tsx",
    "frontend\src\lib\platform.ts",
    "docs\archive\frontend\pc-version\App.tsx.backup",
    "docs\archive\frontend\tablet-version\App.tsx.backup"
)

$allFilesExist = $true
foreach ($file in $filesToCheck) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $file - MISSING" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if ($allFilesExist) {
    Write-Host "  → All required files exist" -ForegroundColor Green
} else {
    Write-Host "  → Some files are missing!" -ForegroundColor Red
}

Write-Host ""

# Test 2: Build Script Path Verification
Write-Host "2. Build Script Path Verification" -ForegroundColor Yellow
$buildScript = "lesson-plan-browser\scripts\build-android-offline.ps1"
if (Test-Path $buildScript) {
    $content = Get-Content $buildScript -Raw
    if ($content -match '\$frontendDir = Join-Path \$repoRoot "frontend"') {
        Write-Host "  ✓ Build script correctly references 'frontend' directory" -ForegroundColor Green
        Write-Host "  → Path resolves to: lesson-plan-browser\frontend\" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ Build script path may be incorrect" -ForegroundColor Red
    }
} else {
    Write-Host "  ✗ Build script not found" -ForegroundColor Red
}

Write-Host ""

# Test 3: Code Verification
Write-Host "3. Code Verification" -ForegroundColor Yellow

# Check platform detection
$platformFile = "lesson-plan-browser\frontend\src\lib\platform.ts"
if (Test-Path $platformFile) {
    $platformContent = Get-Content $platformFile -Raw
    if ($platformContent -match 'isAndroid.*userAgent.*includes.*Android') {
        Write-Host "  ✓ Platform detection includes Android Tauri detection" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Platform detection may be missing Android Tauri detection" -ForegroundColor Red
    }
}

# Check feature hook
$hookFile = "lesson-plan-browser\frontend\src\hooks\usePlatformFeatures.ts"
if (Test-Path $hookFile) {
    $hookContent = Get-Content $hookFile -Raw
    if ($hookContent -match 'usePlatformFeatures' -and $hookContent -match 'isTablet|isPC') {
        Write-Host "  ✓ Feature gating hook exists and has platform flags" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Feature gating hook may be incomplete" -ForegroundColor Red
    }
}

# Check unified App.tsx
$appFile = "lesson-plan-browser\frontend\src\App.tsx"
if (Test-Path $appFile) {
    $appContent = Get-Content $appFile -Raw
    if ($appContent -match 'usePlatformFeatures' -and $appContent -match 'features\.isTablet|features\.isPC') {
        Write-Host "  ✓ Unified App.tsx uses platform detection" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Unified App.tsx may not use platform detection correctly" -ForegroundColor Red
    }
    
    if ($appContent -match 'lazy.*import.*ScheduleInput|Analytics|PlanHistory') {
        Write-Host "  ✓ PC-only components are lazy loaded" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ PC-only components lazy loading needs verification" -ForegroundColor Yellow
    }
}

# Check PC App.tsx re-export
$pcAppFile = "frontend\src\App.tsx"
if (Test-Path $pcAppFile) {
    $pcAppContent = Get-Content $pcAppFile -Raw
    if ($pcAppContent -match 'export.*default.*from.*lesson-plan-browser') {
        Write-Host "  ✓ PC App.tsx correctly re-exports unified version" -ForegroundColor Green
    } else {
        Write-Host "  ✗ PC App.tsx may not correctly re-export unified version" -ForegroundColor Red
    }
}

Write-Host ""

# Test 4: Package.json Verification
Write-Host "4. Package.json Verification" -ForegroundColor Yellow
$pcPackageJson = "frontend\package.json"
$tabletPackageJson = "lesson-plan-browser\frontend\package.json"

if (Test-Path $pcPackageJson) {
    $pcPkg = Get-Content $pcPackageJson | ConvertFrom-Json
    if ($pcPkg.scripts.'tauri:dev' -or $pcPkg.scripts.'tauri:build') {
        Write-Host "  ✓ PC package.json has Tauri scripts" -ForegroundColor Green
    }
}

if (Test-Path $tabletPackageJson) {
    Write-Host "  ✓ Tablet package.json exists" -ForegroundColor Green
}

Write-Host ""

# Summary
Write-Host "=== Testing Summary ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Code Verification: COMPLETE" -ForegroundColor Green
Write-Host "Manual Testing Required:" -ForegroundColor Yellow
Write-Host "  1. PC Development Build: cd frontend; npm run tauri:dev" -ForegroundColor White
Write-Host "  2. Android APK Build: cd lesson-plan-browser; .\scripts\run-with-ndk.ps1 -Target arm64" -ForegroundColor White
Write-Host "  3. Platform Detection: Verify isDesktop/isMobile on both platforms" -ForegroundColor White
Write-Host "  4. Feature Gating: Verify PC shows all features, tablet shows only browser/lesson mode" -ForegroundColor White
Write-Host ""
Write-Host "See docs/implementation/UNIFIED_FRONTEND_TESTING_PLAN.md for detailed test procedures" -ForegroundColor Gray
Write-Host ""

