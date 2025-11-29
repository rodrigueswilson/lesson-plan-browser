# Workaround script for Windows symlink issue
# This script handles the symlink error and continues the build manually

Write-Host "Starting Android dev build with symlink workaround..."
Write-Host ""

# Step 1: Copy library file
Write-Host "[1/3] Copying library file..."
npm run android:copy-lib
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to copy library file"
    exit 1
}

# Step 2: Try Tauri build (will fail on symlink, but that's OK)
Write-Host "[2/3] Running Tauri build (symlink error expected)..."
$tauriOutput = npm run tauri android dev 2>&1 | Out-String

# Check if it failed on symlink
if ($tauriOutput -match "symbolic link" -or $LASTEXITCODE -ne 0) {
    Write-Host "[INFO] Symlink error occurred (expected), continuing with manual build..."
    
    # Step 3: Copy library again (in case Tauri deleted it)
    Write-Host "[3/3] Ensuring library file is in place..."
    npm run android:copy-lib
    
    # Step 4: Continue with Gradle build manually
    Write-Host "[4/4] Running Gradle build..."
    Set-Location "src-tauri/gen/android"
    .\gradlew.bat assembleDebug
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "[SUCCESS] Build completed! Installing APK..."
        .\gradlew.bat installDebug
    } else {
        Write-Host "[ERROR] Gradle build failed"
        exit 1
    }
} else {
    Write-Host "[SUCCESS] Build completed successfully!"
}

