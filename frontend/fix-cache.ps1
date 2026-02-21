# Script to clear Vite cache and restart dev server
Write-Host "Clearing Vite cache..." -ForegroundColor Yellow

# Stop any running node processes
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Clear Vite cache
if (Test-Path "node_modules\.vite") {
    Remove-Item -Recurse -Force "node_modules\.vite"
    Write-Host "✓ Cleared node_modules/.vite" -ForegroundColor Green
} else {
    Write-Host "✓ No Vite cache found" -ForegroundColor Green
}

# Clear dist folder
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
    Write-Host "✓ Cleared dist folder" -ForegroundColor Green
}

Write-Host ""
Write-Host "Cache cleared! Now restart your dev server with: npm run dev" -ForegroundColor Cyan
Write-Host ""

