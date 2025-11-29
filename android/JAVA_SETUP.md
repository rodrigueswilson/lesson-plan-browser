# Java Setup for Android Development

You need Java JDK 17 or later to build the Android app.

## Check if Java is Installed

Run this command:
```powershell
java -version
```

If you see version information, Java is installed. If you get an error, you need to install Java.

## Option 1: Install Java JDK (Recommended)

### Using Chocolatey (if installed):
```powershell
choco install openjdk17
```

### Using Winget (Windows 10/11):
```powershell
winget install Microsoft.OpenJDK.17
```

### Manual Installation:
1. Download from: https://adoptium.net/ (Eclipse Temurin)
2. Choose **JDK 17** or **JDK 21** (LTS versions)
3. Download the Windows x64 installer
4. Run the installer
5. **Important**: Check "Add to PATH" during installation

## Option 2: Use Android Studio's Java

If you have Android Studio installed, it includes Java. You can use that:

1. Find Android Studio's Java location (usually):
   ```
   C:\Program Files\Android\Android Studio\jbr
   ```

2. Set JAVA_HOME temporarily:
   ```powershell
   $env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
   ```

3. Or set it permanently:
   ```powershell
   [System.Environment]::SetEnvironmentVariable('JAVA_HOME', 'C:\Program Files\Android\Android Studio\jbr', 'User')
   ```

## Set JAVA_HOME Environment Variable

After installing Java, set JAVA_HOME:

### Find Java Installation Path

If Java is installed, find its location:
```powershell
where.exe java
```

Or check common locations:
- `C:\Program Files\Java\jdk-17`
- `C:\Program Files\Eclipse Adoptium\jdk-17.x.x-hotspot`
- `C:\Program Files\Android\Android Studio\jbr`

### Set JAVA_HOME (Permanent)

**PowerShell (Current User)**:
```powershell
[System.Environment]::SetEnvironmentVariable('JAVA_HOME', 'C:\path\to\java', 'User')
```

**PowerShell (System-wide - requires admin)**:
```powershell
[System.Environment]::SetEnvironmentVariable('JAVA_HOME', 'C:\path\to\java', 'Machine')
```

**Or use GUI**:
1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Go to **Advanced** tab
3. Click **Environment Variables**
4. Under **User variables**, click **New**
5. Variable name: `JAVA_HOME`
6. Variable value: Path to your Java installation (e.g., `C:\Program Files\Java\jdk-17`)
7. Click **OK**

### Set JAVA_HOME (Temporary - Current Session Only)

```powershell
$env:JAVA_HOME = "C:\path\to\java"
```

### Add Java to PATH

Make sure Java's `bin` directory is in your PATH:

```powershell
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
```

Or permanently:
```powershell
$currentPath = [System.Environment]::GetEnvironmentVariable('Path', 'User')
[System.Environment]::SetEnvironmentVariable('Path', "$currentPath;$env:JAVA_HOME\bin", 'User')
```

## Verify Setup

After setting JAVA_HOME, verify:

```powershell
echo $env:JAVA_HOME
java -version
javac -version
```

You should see:
- JAVA_HOME path displayed
- Java version (17 or higher)
- Java compiler version

## Then Build

Once Java is set up:

```powershell
cd android
.\gradlew.bat clean build
```

## Quick Check Script

Run this to check your Java setup:

```powershell
Write-Host "Checking Java installation..." -ForegroundColor Cyan
Write-Host ""

# Check JAVA_HOME
if ($env:JAVA_HOME) {
    Write-Host "✅ JAVA_HOME is set: $env:JAVA_HOME" -ForegroundColor Green
} else {
    Write-Host "❌ JAVA_HOME is not set" -ForegroundColor Red
}

# Check java command
$javaPath = Get-Command java -ErrorAction SilentlyContinue
if ($javaPath) {
    Write-Host "✅ Java found at: $($javaPath.Source)" -ForegroundColor Green
    java -version
} else {
    Write-Host "❌ Java command not found in PATH" -ForegroundColor Red
}

# Check javac
$javacPath = Get-Command javac -ErrorAction SilentlyContinue
if ($javacPath) {
    Write-Host "✅ Java compiler found" -ForegroundColor Green
} else {
    Write-Host "⚠️  Java compiler not found (may need JDK, not just JRE)" -ForegroundColor Yellow
}
```

