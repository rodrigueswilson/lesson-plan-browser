# Install Java JDK for Android Development

Java is not currently installed. You need **Java JDK 17 or later** to build the Android app.

## Quick Install Options

### Option 1: Install via Winget (Easiest - Windows 10/11)

```powershell
winget install Microsoft.OpenJDK.17
```

After installation, **restart your PowerShell terminal** and verify:
```powershell
java -version
```

### Option 2: Install via Chocolatey (if you have it)

```powershell
choco install openjdk17
```

### Option 3: Manual Download

1. Go to: https://adoptium.net/
2. Click **Download**
3. Choose:
   - **Version**: 17 or 21 (LTS)
   - **Operating System**: Windows
   - **Architecture**: x64
   - **Package Type**: JDK
4. Download and run the installer
5. **Important**: Check "Add to PATH" during installation
6. **Restart your PowerShell terminal** after installation

### Option 4: Use Android Studio's Java (if you have Android Studio)

If you have Android Studio installed, it includes Java. Find it and set JAVA_HOME:

```powershell
# Common Android Studio Java location
$androidStudioJava = "C:\Program Files\Android\Android Studio\jbr"
if (Test-Path $androidStudioJava) {
    [System.Environment]::SetEnvironmentVariable('JAVA_HOME', $androidStudioJava, 'User')
    Write-Host "✅ Set JAVA_HOME to Android Studio's Java" -ForegroundColor Green
    Write-Host "Please restart your terminal for changes to take effect" -ForegroundColor Yellow
} else {
    Write-Host "❌ Android Studio Java not found at: $androidStudioJava" -ForegroundColor Red
}
```

## After Installing Java

### 1. Restart Your Terminal

Close and reopen PowerShell so it picks up the new PATH.

### 2. Verify Installation

```powershell
java -version
javac -version
```

You should see version 17 or higher.

### 3. Set JAVA_HOME (if not auto-set)

If JAVA_HOME is still not set after installation:

```powershell
# Find Java installation
where.exe java

# Set JAVA_HOME (replace with actual path from above)
[System.Environment]::SetEnvironmentVariable('JAVA_HOME', 'C:\Program Files\Eclipse Adoptium\jdk-17.x.x-hotspot', 'User')
```

**Restart your terminal** after setting JAVA_HOME.

### 4. Build the App

```powershell
cd android
.\gradlew.bat clean build
```

## Recommended: Use Android Studio

If you plan to develop Android apps, **Android Studio** is the easiest option:
- Includes Java JDK
- Includes Android SDK
- Includes Gradle
- Handles everything automatically

Download from: https://developer.android.com/studio

## Quick Install Script

Run this to install Java via Winget (if available):

```powershell
# Check if winget is available
if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host "Installing Java JDK 17 via Winget..." -ForegroundColor Cyan
    winget install Microsoft.OpenJDK.17
    Write-Host ""
    Write-Host "✅ Installation complete!" -ForegroundColor Green
    Write-Host "Please restart your terminal and run: java -version" -ForegroundColor Yellow
} else {
    Write-Host "Winget not available. Please install Java manually:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://adoptium.net/" -ForegroundColor Cyan
    Write-Host "2. Download JDK 17 for Windows x64" -ForegroundColor Cyan
    Write-Host "3. Run installer and check 'Add to PATH'" -ForegroundColor Cyan
}
```

