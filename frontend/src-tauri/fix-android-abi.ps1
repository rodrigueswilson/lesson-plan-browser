# Fix Android ABI Directory Mismatch
# Tauri outputs to aarch64-linux-android but Gradle expects arm64-v8a

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AndroidDir = Join-Path $ScriptDir "gen\android"

Write-Host "=== Fixing Android ABI Directory ===" -ForegroundColor Cyan

# Find all libraries in wrong ABI directory
$wrongAbiPaths = @(
    "app\build\intermediates\merged_jni_libs\arm64Debug\mergeArm64DebugJniLibFolders\out\aarch64-linux-android",
    "app\build\intermediates\merged_jni_libs\universalDebug\mergeUniversalDebugJniLibFolders\out\aarch64-linux-android"
)

foreach ($wrongPath in $wrongAbiPaths) {
    $fullWrongPath = Join-Path $AndroidDir $wrongPath
    $libFile = Join-Path $fullWrongPath "libbilingual_lesson_planner.so"
    
    if (Test-Path $libFile) {
        Write-Host "Found library at: $libFile" -ForegroundColor Yellow
        
        # Determine correct ABI directory (arm64-v8a)
        $correctAbiPath = $wrongPath -replace "aarch64-linux-android", "arm64-v8a"
        $fullCorrectPath = Join-Path $AndroidDir $correctAbiPath
        
        # Create correct directory
        New-Item -ItemType Directory -Path $fullCorrectPath -Force | Out-Null
        
        # Copy library to correct location
        Copy-Item $libFile (Join-Path $fullCorrectPath "libbilingual_lesson_planner.so") -Force
        Write-Host "  Copied to: $correctAbiPath" -ForegroundColor Green
        
        # Remove wrong directory
        Remove-Item $fullWrongPath -Recurse -Force
        Write-Host "  Removed: $wrongPath" -ForegroundColor Green
    }
}

Write-Host "`n[SUCCESS] ABI directory fixed!" -ForegroundColor Green

