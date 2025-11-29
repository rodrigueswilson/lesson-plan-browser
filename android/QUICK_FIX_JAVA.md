# Quick Fix: Set JAVA_HOME in Your Current Session

You're in a PowerShell session that doesn't have JAVA_HOME set. Here's how to fix it:

## Option 1: Set for Current Session (Quick Fix)

Run these commands in your PowerShell:

```powershell
cd android
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
java -version
```

Then build:
```powershell
.\gradlew.bat clean build
```

## Option 2: Use the Script

I've created a script for you. Run:

```powershell
cd android
.\SET_JAVA_HOME.ps1
.\gradlew.bat clean build
```

## Option 3: Set Permanently (Recommended)

To set JAVA_HOME permanently so you don't have to do this every time:

```powershell
[System.Environment]::SetEnvironmentVariable('JAVA_HOME', 'C:\Program Files\Android\Android Studio\jbr', 'User')
```

**Then restart your PowerShell terminal** and JAVA_HOME will be set automatically.

## Verify It's Working

After setting JAVA_HOME, verify:

```powershell
echo $env:JAVA_HOME
java -version
```

You should see:
- JAVA_HOME path displayed
- Java version 21.0.8 (or similar)

## Then Build

```powershell
.\gradlew.bat clean build
```

