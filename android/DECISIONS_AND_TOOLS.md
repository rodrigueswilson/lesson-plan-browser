# Android Development: Decisions & Tools

## Critical Decisions Needed

### 1. Authentication Strategy ⚠️ **REQUIRED**

**Question**: How will teachers authenticate in the Android app?

**Options**:
- **A) Supabase Auth** (Recommended)
  - Email/password login
  - OAuth (Google, etc.)
  - Built-in user management
  - Pros: Integrated with database, secure, scalable
  - Cons: Requires Supabase Auth setup

- **B) Custom Auth via FastAPI**
  - Use existing backend authentication
  - Pros: Consistent with desktop app
  - Cons: More complex, requires backend changes

- **C) Simple User Selection** (Like desktop app)
  - No login, just select user from list
  - Pros: Simple, matches desktop UX
  - Cons: Less secure, no multi-device sync per user

**Recommendation**: **Option A (Supabase Auth)** for production, Option C for MVP

---

### 2. Supabase Project Configuration ⚠️ **REQUIRED**

**Question**: Which Supabase project(s) will the Android app connect to?

**Current Setup**:
- Project 1: Wilson's data
- Project 2: Daniela's data

**Options**:
- **A) Single Project with RLS**
  - One Supabase project for all users
  - Row Level Security for data isolation
  - Pros: Simpler, lower cost
  - Cons: Requires RLS setup

- **B) Multiple Projects (Current)**
  - Separate projects per user/teacher
  - App determines which project to use
  - Pros: Complete isolation, matches current setup
  - Cons: More complex, higher cost

**Recommendation**: **Option B** (matches current desktop setup)

---

### 3. Minimum Android Version ⚠️ **REQUIRED**

**Question**: What's the minimum Android version to support?

**Options**:
- **Android 8.0 (API 26)** - Recommended
  - Supports 95%+ of tablets
  - Full Room/WorkManager support
  - Good performance

- **Android 7.0 (API 24)** - Broader support
  - Supports 98%+ of devices
  - Some limitations with newer features

**Recommendation**: **API 26 (Android 8.0)** for tablet-focused app

---

### 4. Development Environment ⚠️ **REQUIRED**

**Question**: Will you use Android Studio or VS Code/Cursor?

**Options**:
- **A) Android Studio** (Recommended for Android)
  - Official IDE, best Android support
  - Built-in emulator, debugging, profiling
  - Pros: Best tooling, official support
  - Cons: Heavy, separate from your current workflow

- **B) VS Code/Cursor with Extensions**
  - Use Android extensions
  - Command-line tools
  - Pros: Stay in current editor
  - Cons: Less integrated, more setup

**Recommendation**: **Android Studio** for initial setup, VS Code for editing

---

### 5. Build System

**Question**: Gradle configuration approach?

**Decision**: **Gradle Kotlin DSL** (build.gradle.kts)
- Modern, type-safe
- Better IDE support
- Standard for new projects

---

### 6. Package Name / App ID

**Question**: What should be the Android package name?

**Suggestion**: `com.bilingual.lessonplanner` or `com.bilingual.lessonplanner.android`

**Decision Needed**: Confirm package name

---

## Required Developer Tools

### Essential Tools (Must Install)

#### 1. Android Studio
- **Purpose**: Primary Android development IDE
- **Download**: https://developer.android.com/studio
- **Includes**:
  - Android SDK
  - Android Emulator
  - Gradle build system
  - Android Debug Bridge (ADB)
  - Profiling tools

**Installation Steps**:
1. Download Android Studio
2. Run installer
3. Install Android SDK (API 26-34)
4. Install Android Emulator system images
5. Configure Android SDK path

#### 2. Android SDK Command Line Tools
- **Purpose**: Command-line access to Android tools
- **Location**: Included with Android Studio
- **Path**: `$ANDROID_HOME/cmdline-tools/latest/bin`

**Environment Variables** (Add to PATH):
```bash
# Windows
ANDROID_HOME=C:\Users\YourName\AppData\Local\Android\Sdk
PATH=%PATH%;%ANDROID_HOME%\platform-tools;%ANDROID_HOME%\cmdline-tools\latest\bin

# macOS/Linux
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin
```

#### 3. Java Development Kit (JDK)
- **Purpose**: Required for Android development
- **Version**: JDK 17 (recommended) or JDK 11
- **Download**: 
  - OpenJDK: https://adoptium.net/
  - Or use Android Studio's bundled JDK

#### 4. Gradle
- **Purpose**: Build system (included with Android Studio)
- **Version**: 8.0+ (managed by Android Studio)
- **Note**: Usually auto-installed, but can install standalone

---

### VS Code / Cursor Extensions (Optional but Recommended)

#### 1. Kotlin Language Extension
- **Extension ID**: `fwcd.kotlin`
- **Purpose**: Kotlin syntax highlighting, IntelliSense
- **Install**: `code --install-extension fwcd.kotlin`

#### 2. Android iOS Emulator
- **Extension ID**: `DiemasMichiels.emulate`
- **Purpose**: Launch Android emulator from VS Code
- **Install**: `code --install-extension DiemasMichiels.emulate`

#### 3. Gradle for Java
- **Extension ID**: `vscjava.vscode-gradle`
- **Purpose**: Gradle task runner, build support
- **Install**: `code --install-extension vscjava.vscode-gradle`

#### 4. XML Tools
- **Extension ID**: `redhat.vscode-xml`
- **Purpose**: AndroidManifest.xml, layout files
- **Install**: `code --install-extension redhat.vscode-xml`

#### 5. Error Lens
- **Extension ID**: `usernamehw.errorlens`
- **Purpose**: Inline error highlighting
- **Install**: `code --install-extension usernamehw.errorlens`

---

### Command Line Tools (For VS Code/Cursor Workflow)

#### ADB (Android Debug Bridge)
- **Purpose**: Device communication, debugging
- **Location**: `$ANDROID_HOME/platform-tools/adb`
- **Usage**:
  ```bash
  adb devices              # List connected devices
  adb install app.apk      # Install APK
  adb logcat              # View device logs
  ```

#### Gradle Wrapper
- **Purpose**: Build and run tasks from command line
- **Usage**:
  ```bash
  ./gradlew build         # Build project
  ./gradlew installDebug  # Install on device
  ./gradlew test          # Run tests
  ```

---

### Recommended Additional Tools

#### 1. Android Emulator
- **Purpose**: Test on virtual devices
- **Included**: With Android Studio
- **Setup**: Create tablet emulator (10" tablet, API 26+)

#### 2. Physical Android Tablet
- **Purpose**: Real device testing
- **Requirements**: 
  - Android 8.0+
  - Enable Developer Options
  - Enable USB Debugging

#### 3. Supabase CLI (Optional)
- **Purpose**: Manage Supabase projects
- **Install**: `npm install -g supabase`
- **Usage**: Database migrations, local development

---

## Development Workflow Options

### Option 1: Android Studio (Recommended for Setup)
```
1. Create project in Android Studio
2. Set up dependencies
3. Configure build files
4. Use Android Studio for:
   - Running/debugging
   - Emulator management
   - Profiling
5. Edit code in VS Code/Cursor
```

### Option 2: VS Code/Cursor Only
```
1. Create project structure manually
2. Use Gradle from command line
3. Use ADB for device communication
4. Use VS Code extensions for:
   - Syntax highlighting
   - Code completion
   - Error checking
5. Build/run via terminal
```

**Recommendation**: **Hybrid approach**
- Use Android Studio for initial project setup
- Use VS Code/Cursor for daily coding
- Use Android Studio for debugging/profiling when needed

---

## Installation Checklist

### Step 1: Install Android Studio
- [ ] Download Android Studio
- [ ] Install with default settings
- [ ] Open Android Studio
- [ ] Install Android SDK (API 26-34)
- [ ] Install Android Emulator

### Step 2: Configure Environment
- [ ] Set ANDROID_HOME environment variable
- [ ] Add platform-tools to PATH
- [ ] Verify: `adb version` works

### Step 3: Install VS Code Extensions
- [ ] Kotlin Language Extension
- [ ] Gradle for Java
- [ ] XML Tools
- [ ] Error Lens

### Step 4: Verify Installation
- [ ] `java -version` shows JDK 17+
- [ ] `adb devices` works
- [ ] Android Studio opens without errors
- [ ] Can create new Android project

---

## Next Steps After Tools Installation

1. **Create Android Project**
   - Use Android Studio wizard
   - Select "Empty Activity" template
   - Choose Kotlin, API 26 minimum

2. **Configure Dependencies**
   - Add Room, Compose, Hilt, etc.
   - See `build.gradle.kts` in architecture

3. **Set Up Supabase**
   - Get Supabase project URL and keys
   - Configure in app

4. **Create Project Structure**
   - Follow architecture folder structure
   - Set up packages

---

## Decisions Made ✅

### 1. Authentication Strategy
**Decision**: **Option C - Simple User Selection** (Like desktop app)
- **Rationale**: 
  - Matches current desktop app UX (no login required)
  - Faster MVP development
  - Teachers already familiar with user selection pattern
  - Can upgrade to Supabase Auth later if needed
- **Implementation**: User dropdown/selector on app startup
- **Future**: Can migrate to Supabase Auth (Option A) when needed

### 2. Supabase Project Configuration
**Decision**: **Option B - Multiple Projects** (Matches current setup)
- **Rationale**:
  - Matches existing desktop app architecture
  - Project 1: Wilson's data
  - Project 2: Daniela's data
  - Complete data isolation per teacher
  - No RLS complexity needed
- **Implementation**: App determines which Supabase project based on selected user
- **Configuration**: Store project URLs/keys per user in app config

### 3. Minimum Android Version
**Decision**: **API 26 (Android 8.0)**
- **Rationale**:
  - Tablet-focused app (95%+ tablet support)
  - Full Room/WorkManager feature support
  - Good performance characteristics
  - Modern Android features available
- **Target SDK**: API 34 (Android 14)
- **Compile SDK**: API 34

### 4. Package Name
**Decision**: **`com.bilingual.lessonplanner`**
- **Rationale**: 
  - Clean, professional package name
  - Matches app purpose
  - No `.android` suffix needed (this is the Android app)

### 5. Development Environment
**Decision**: **Hybrid Approach - Android Studio + VS Code/Cursor**
- **Android Studio**: Initial setup, debugging, emulator, profiling
- **VS Code/Cursor**: Daily coding, file navigation, AI assistance
- **Rationale**: Best of both worlds - use right tool for the job

---

## Questions to Answer Before Starting

1. ✅ **Authentication**: Simple user selection (matches desktop)
2. ✅ **Supabase Project**: Multiple projects (matches current setup)
3. ✅ **Min Android Version**: API 26 (Android 8.0)
4. ✅ **Package Name**: `com.bilingual.lessonplanner`
5. ✅ **Development Tool**: Android Studio + VS Code hybrid

---

## Resources

- [Android Developer Guide](https://developer.android.com/guide)
- [Kotlin Documentation](https://kotlinlang.org/docs/home.html)
- [Jetpack Compose Tutorial](https://developer.android.com/jetpack/compose/tutorial)
- [Room Database Guide](https://developer.android.com/training/data-storage/room)
- [Supabase Android Docs](https://supabase.com/docs/reference/kotlin/introduction)

