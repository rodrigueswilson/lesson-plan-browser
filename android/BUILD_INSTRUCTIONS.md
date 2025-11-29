# Building the Android App

## Quick Build Commands

### Windows PowerShell:
```powershell
cd android
.\gradlew.bat clean build
```

### Windows Command Prompt:
```cmd
cd android
gradlew.bat clean build
```

### Linux/Mac:
```bash
cd android
./gradlew clean build
```

## If gradlew.bat doesn't exist

If you get an error that `gradlew.bat` is not found, you need to initialize the Gradle wrapper:

```powershell
cd android
gradle wrapper --gradle-version 8.5
```

Then try building again:
```powershell
.\gradlew.bat clean build
```

## Alternative: Use Gradle directly

If you have Gradle installed globally:

```powershell
cd android
gradle clean build
```

## Verify Supabase Configuration

After building, the app will validate your Supabase credentials on startup. Check the logs for:
- ✅ "Supabase configuration validated successfully"
- ❌ Any configuration errors

## Next Steps

1. Build the project: `.\gradlew.bat clean build`
2. Install on device/emulator: `.\gradlew.bat installDebug`
3. Run the app and check logs for configuration status

