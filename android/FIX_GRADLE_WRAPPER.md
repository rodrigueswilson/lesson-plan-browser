# Fix Gradle Wrapper JAR

If you're getting "Could not find or load main class org.gradle.wrapper.GradleWrapperMain", the wrapper JAR might be corrupted.

## Quick Fix

Run this in PowerShell:

```powershell
cd android
New-Item -ItemType Directory -Force -Path gradle\wrapper | Out-Null
Invoke-WebRequest -Uri "https://github.com/gradle/gradle/raw/v8.5.0/gradle/wrapper/gradle-wrapper.jar" -OutFile "gradle\wrapper\gradle-wrapper.jar"
```

Then try building again:
```powershell
.\gradlew.bat clean build
```

## Alternative: Use Android Studio

The easiest way is to use Android Studio:

1. Open Android Studio
2. File → Open → Select the `android` folder
3. Android Studio will automatically:
   - Set up the Gradle wrapper correctly
   - Download all dependencies
   - Configure everything

4. Then build: Build → Make Project (Ctrl+F9)

## Verify JAR File

Check if the JAR file exists and has a reasonable size:

```powershell
Get-Item gradle\wrapper\gradle-wrapper.jar | Select-Object Name, Length
```

The file should be around 40-60 KB. If it's 0 bytes or very small, it's corrupted.

