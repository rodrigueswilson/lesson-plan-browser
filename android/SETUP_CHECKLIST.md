# Android App Setup Checklist

## Pre-Development Decisions ✅

All decisions have been made! See `DECISIONS.md` for details.

### 1. Authentication Strategy ✅
- [x] **Decision**: Simple user selection (like desktop app)
- [x] Matches current desktop UX
- [x] Can upgrade to Supabase Auth later if needed

---

### 2. Supabase Configuration ✅
- [x] **Decision**: Multiple projects (project1, project2)
- [x] Matches current desktop setup
- [x] Project 1: Wilson's data
- [x] Project 2: Daniela's data

---

### 3. Package Name ✅
- [x] **Decision**: `com.bilingual.lessonplanner`
- [x] Confirmed and ready to use

---

### 4. Minimum Android Version ✅
- [x] **Decision**: API 26 (Android 8.0)
- [x] Target SDK: API 34
- [x] Compile SDK: API 34

---

## Tool Installation

### Required Tools
- [ ] **Android Studio** installed
  - Download: https://developer.android.com/studio
  - Includes: SDK, Emulator, Gradle

- [ ] **Android SDK** configured - **See ANDROID_SDK_SETUP.md for detailed instructions**
  - API 26-34 installed (install via Android Studio SDK Manager)
  - Platform tools in PATH
  - ANDROID_HOME environment variable set

- [ ] **JDK 17** installed
  - Verify: `java -version` shows 17+

- [ ] **Environment Variables** set
  ```bash
  ANDROID_HOME=<path-to-sdk>
  PATH includes: $ANDROID_HOME/platform-tools
  ```

### VS Code/Cursor Extensions (Optional)
- [x] Kotlin Language Extension (`fwcd.kotlin`) ✅ Installed
- [x] Gradle for Java (`vscjava.vscode-gradle`) ✅ Installed
- [x] XML Tools (`redhat.vscode-xml`) ✅ Installed
- [x] Error Lens (`usernamehw.errorlens`) ✅ Installed
- [x] Android iOS Emulator (`DiemasMichiels.emulate`) ✅ Installed

### Verification
- [ ] `adb version` works
- [ ] `java -version` shows JDK 17+
- [ ] Android Studio opens without errors
- [ ] Can create new Android project

---

## Supabase Setup

### Project Configuration
- [ ] Supabase project URL obtained
- [ ] Supabase API key (anon key) obtained
- [ ] Service role key (optional, for admin operations)

### Database Schema
- [ ] Schema matches desktop app structure
- [ ] Row Level Security (RLS) configured (if using single project)
- [ ] Test connection from Android app

---

## Project Initialization

### Create Project
- [ ] New Android project created in Android Studio
- [ ] Package name: `com.bilingual.lessonplanner`
- [ ] Minimum SDK: API 26
- [ ] Language: Kotlin
- [ ] Build system: Gradle Kotlin DSL

### Dependencies
- [ ] Room database added
- [ ] Jetpack Compose added
- [ ] Hilt (DI) added
- [ ] WorkManager added
- [ ] Supabase Android SDK added
- [ ] Coroutines added

### Project Structure
- [ ] Folder structure created (see ARCHITECTURE.md)
- [ ] Packages organized
- [ ] Basic MVVM structure set up

---

## Development Ready

Once all items above are checked:
- [ ] Can build project: `./gradlew build`
- [ ] Can run on emulator/device
- [ ] Can connect to Supabase
- [ ] Ready to implement Browser feature

---

## Next Steps After Setup

1. Implement data layer (Room entities, DAOs)
2. Set up Supabase connection
3. Implement sync manager
4. Create Browser UI (Compose)
5. Implement ViewModels
6. Test offline functionality
7. Test network-aware sync

---

## Notes

- Use Android Studio for initial setup and debugging
- Use VS Code/Cursor for daily coding
- Keep architecture documentation updated
- Test on real tablet device early

