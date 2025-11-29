Write-Host "Attempting to push to GitHub..."
git push -u origin master --force

if ($LASTEXITCODE -ne 0) {
    Write-Host "Push failed. Please check:" -ForegroundColor Red
    Write-Host "1. If the repo is Public, consider making it PRIVATE."
    Write-Host "2. Go to GitHub Settings -> Code security and analysis -> Disable 'Push protection'."
    Write-Host "3. Check if you have any real API keys in your code."
} else {
    Write-Host "Push SUCCESSFUL! Go to GitHub Actions to download your APK." -ForegroundColor Green
}
