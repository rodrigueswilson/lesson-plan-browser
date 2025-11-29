# Quick script to set JAVA_HOME for Android Studio's Java
# Run this in your PowerShell session before building

$androidStudioJava = "C:\Program Files\Android\Android Studio\jbr"

if (Test-Path $androidStudioJava) {
    $env:JAVA_HOME = $androidStudioJava
    $env:PATH = "$androidStudioJava\bin;$env:PATH"
    
    Write-Host "✅ JAVA_HOME set to: $env:JAVA_HOME" -ForegroundColor Green
    Write-Host ""
    Write-Host "Verifying Java installation..." -ForegroundColor Cyan
    java -version
    Write-Host ""
    Write-Host "✅ Ready to build! Run: .\gradlew.bat clean build" -ForegroundColor Green
} else {
    Write-Host "❌ Android Studio Java not found at: $androidStudioJava" -ForegroundColor Red
    Write-Host "Please install Java JDK 17 or later" -ForegroundColor Yellow
}

