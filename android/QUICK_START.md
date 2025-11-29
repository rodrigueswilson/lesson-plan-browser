# Android App - Quick Start Guide

## Summary

I've reviewed our conversation and created the Android app architecture. Here's what's been defined:

### ✅ Completed

1. **Architecture Documentation** (`ARCHITECTURE.md`)
   - Complete technology stack
   - MVVM architecture pattern
   - Database strategy (Room + Supabase)
   - Network-aware sync strategy
   - Project structure
   - Data models

2. **Decisions & Tools Guide** (`DECISIONS_AND_TOOLS.md`)
   - Critical decisions needed
   - Required developer tools
   - VS Code/Cursor extensions
   - Installation instructions

3. **Setup Checklist** (`SETUP_CHECKLIST.md`)
   - Step-by-step setup process
   - Verification steps

---

## Critical Decisions Needed ⚠️

Before starting development, please decide:

### 1. Authentication Strategy
**Question**: How will teachers log in?

- **Option A**: Supabase Auth (email/password, OAuth) - **Recommended for production**
- **Option B**: Custom auth via FastAPI backend
- **Option C**: Simple user selection (like desktop) - **Recommended for MVP**

**My Recommendation**: Start with **Option C** (simple user selection) to match desktop app, upgrade to Option A later.

---

### 2. Supabase Project Configuration
**Question**: Single project or multiple projects?

- **Option A**: Single Supabase project with Row Level Security (RLS)
- **Option B**: Multiple projects (project1, project2) - **Matches current setup**

**My Recommendation**: **Option B** to match your current desktop app setup.

---

### 3. Package Name
**Suggestion**: `com.bilingual.lessonplanner`

Confirm or provide alternative.

---

### 4. Minimum Android Version
**Recommendation**: **API 26 (Android 8.0)**
- Supports 95%+ of tablets
- Full feature support
- Good performance

---

## Required Developer Tools

### Must Install

1. **Android Studio** (Primary tool)
   - Download: https://developer.android.com/studio
   - Includes: SDK, Emulator, Gradle, ADB
   - **Purpose**: Project setup, debugging, emulator management

2. **Android SDK** (Included with Android Studio)
   - Install API 26-34
   - Set ANDROID_HOME environment variable
   - Add platform-tools to PATH

3. **JDK 17**
   - Download: https://adoptium.net/
   - Or use Android Studio's bundled JDK

### VS Code/Cursor Extensions (Optional but Recommended)

For working in VS Code/Cursor instead of Android Studio:

1. **Kotlin Language** (`fwcd.kotlin`)
   - Syntax highlighting, IntelliSense

2. **Gradle for Java** (`vscjava.vscode-gradle`)
   - Build tasks, dependency management

3. **XML Tools** (`redhat.vscode-xml`)
   - AndroidManifest.xml support

4. **Error Lens** (`usernamehw.errorlens`)
   - Inline error highlighting

**Install Command**:
```bash
code --install-extension fwcd.kotlin
code --install-extension vscjava.vscode-gradle
code --install-extension redhat.vscode-xml
code --install-extension usernamehw.errorlens
```

---

## Recommended Workflow

### Hybrid Approach (Best of Both Worlds)

1. **Use Android Studio for**:
   - Initial project creation
   - Running/debugging apps
   - Emulator management
   - Profiling and performance analysis
   - Gradle sync issues

2. **Use VS Code/Cursor for**:
   - Daily code editing
   - Git operations
   - File navigation
   - AI-assisted coding

### Why This Works

- Android Studio has the best Android tooling
- VS Code/Cursor is better for general coding
- You can switch between them seamlessly
- Project files are compatible

---

## Architecture Highlights

### Technology Stack
- **Kotlin** - Native Android language
- **Jetpack Compose** - Modern UI framework
- **Room** - Local SQLite database
- **Supabase Android SDK** - Direct cloud access
- **WorkManager** - Background sync
- **Hilt** - Dependency injection
- **Material Design 3** - Native design system

### Key Features

1. **Offline-First**: All data stored locally, works without network
2. **Network-Aware Sync**: 
   - Heavy syncs on WiFi (all plans, all steps)
   - Critical updates on mobile (metadata, current week)
3. **Reactive UI**: StateFlow/Flow for automatic UI updates
4. **Battery Efficient**: Smart background sync scheduling

---

## Next Steps

### Immediate Actions

1. **Review Decisions** (`DECISIONS_AND_TOOLS.md`)
   - Answer the 4 critical questions above
   - Confirm package name

2. **Install Tools**
   - Android Studio
   - Android SDK
   - VS Code extensions (optional)

3. **Verify Installation**
   ```bash
   adb version          # Should show ADB version
   java -version       # Should show JDK 17+
   ```

4. **Set Up Supabase**
   - Get project URL and API keys
   - Configure RLS (if using single project)

### After Setup

1. Create Android project in Android Studio
2. Configure dependencies (Room, Compose, Hilt, Supabase)
3. Set up project structure (see ARCHITECTURE.md)
4. Start implementing Browser feature

---

## Documentation Files

- **`ARCHITECTURE.md`** - Complete architecture documentation
- **`DECISIONS_AND_TOOLS.md`** - Decisions needed and tools required
- **`SETUP_CHECKLIST.md`** - Step-by-step setup guide
- **`README.md`** - Project overview

---

## Questions?

Review the documentation files, then:
1. Make the 4 critical decisions
2. Install the required tools
3. Verify everything works
4. Start development!

The architecture is ready. Once you've made the decisions and installed the tools, we can start building! 🚀

