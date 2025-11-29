# PowerShell script to find your PC's IP address for Android app configuration
# Run this script to get your local IP address for configuring the mobile app

Write-Host "Finding your PC's IP address..." -ForegroundColor Cyan
Write-Host ""

# Get all network adapters with IPv4 addresses
$adapters = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { 
    $_.IPAddress -notlike "127.*" -and 
    $_.IPAddress -notlike "169.254.*" 
} | Select-Object IPAddress, InterfaceAlias

if ($adapters) {
    Write-Host "Available IP addresses:" -ForegroundColor Green
    Write-Host ""
    
    $index = 1
    $ipAddresses = @()
    
    foreach ($adapter in $adapters) {
        Write-Host "$index. $($adapter.IPAddress) - $($adapter.InterfaceAlias)" -ForegroundColor Yellow
        $ipAddresses += $adapter.IPAddress
        $index++
    }
    
    Write-Host ""
    Write-Host "Most likely IP for local network:" -ForegroundColor Green
    $primaryIP = $ipAddresses[0]
    Write-Host "  $primaryIP" -ForegroundColor White -BackgroundColor DarkGreen
    Write-Host ""
    Write-Host "To use this IP in your app:" -ForegroundColor Cyan
    Write-Host "  1. Update frontend/capacitor.config.ts:" -ForegroundColor Yellow
    Write-Host "     server: { url: 'http://$primaryIP:8000' }" -ForegroundColor White
    Write-Host ""
    Write-Host "  2. Or create frontend/.env.local with:" -ForegroundColor Yellow
    Write-Host "     VITE_API_BASE_URL=http://$primaryIP:8000/api" -ForegroundColor White
    Write-Host ""
    Write-Host "  3. Make sure your backend is running with:" -ForegroundColor Yellow
    Write-Host "     python -m uvicorn api:app --host 0.0.0.0 --port 8000" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "No network adapters found with IPv4 addresses." -ForegroundColor Red
}

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

