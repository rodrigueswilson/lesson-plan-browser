# Gradle Wrapper Setup

The Gradle wrapper files are missing. You need to initialize them before building.

## Option 1: Initialize Gradle Wrapper (Recommended)

If you have Gradle installed:

```powershell
cd android
gradle wrapper --gradle-version 8.5
```

This will create:
- `gradlew` (Unix/Linux/Mac)
- `gradlew.bat` (Windows)
- `gradle/wrapper/` directory with wrapper files

Then build with:
```powershell
.\gradlew.bat clean build
```

## Option 2: Use Gradle Directly

If you have Gradle installed globally, you can skip the wrapper:

```powershell
cd android
gradle clean build
```

## Option 3: Install Gradle

If you don't have Gradle installed:

1. **Using Chocolatey** (if installed):
   ```powershell
   choco install gradle
   ```

2. **Using SDKMAN** (if installed):
   ```bash
   sdk install gradle 8.5
   ```

3. **Manual Installation**:
   - Download from: https://gradle.org/releases/
   - Extract and add to PATH
   - Or use Android Studio's bundled Gradle

## Verify Installation

Check if Gradle is installed:
```powershell
gradle --version
```

## After Setup

Once the wrapper is created or Gradle is installed, build the project:

```powershell
cd android
.\gradlew.bat clean build
```

Or with direct Gradle:
```powershell
cd android
gradle clean build
```

