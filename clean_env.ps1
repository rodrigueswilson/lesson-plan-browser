# PowerShell wrapper for clen_env.py
# Makes it easier to run the cleanup script

Write-Host "Running environment cleanup script..." -ForegroundColor Cyan
Write-Host ""

# Run the Python script
python clean_env.py

# Capture exit code
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "`nCleanup completed successfully!" -ForegroundColor Green
} else {
    Write-Host "`nCleanup completed with errors (exit code: $exitCode)" -ForegroundColor Yellow
}

exit $exitCode

