# Android App - Bilingual Lesson Planner

Native Android tablet application for viewing and navigating bilingual lesson plans.

## Status

✅ **Phases 0-11 Complete** - Core implementation finished, ready for testing and optimization (Phase 12)

## Quick Start

### Prerequisites

1. **Install Required Tools**
   - Android Studio (latest version)
   - Android SDK (API 26+)
   - JDK 17

2. **Configure Supabase**
   - Update `SupabaseConfigProvider.getConfig()` in `data/remote/config/SupabaseConfig.kt`
   - Add your Supabase project URLs and API keys

3. **Build and Run**
   ```bash
   ./gradlew build
   ./gradlew installDebug
   ```

## Project Structure

```
android/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/bilingual/lessonplanner/
│   │   │   │   ├── data/          # Data layer (Room, Supabase, Sync)
│   │   │   │   ├── domain/        # Domain models and repository interfaces
│   │   │   │   ├── ui/            # UI layer (Compose screens)
│   │   │   │   └── di/            # Dependency injection (Hilt)
│   │   │   └── AndroidManifest.xml
│   │   ├── test/                  # Unit tests
│   │   └── androidTest/           # Instrumented tests
│   └── build.gradle.kts
├── build.gradle.kts
└── settings.gradle.kts
```

## Features Implemented

### ✅ Browser Feature (Complete)
- User Selection - Choose teacher on startup
- Week View - Grid of 5 days with lesson cards
- Day View - List of lessons for selected day
- Lesson Detail View - Full lesson plan content:
  - Objectives
  - Vocabulary & cognates
  - Sentence frames
  - Materials needed
  - Instruction steps
  - Assessment
- Navigation - Switch between views
- Refresh - Manual sync
- Offline - Works with cached data

### Sync Features
- ✅ Network-aware (WiFi vs Mobile)
- ✅ Background sync (WorkManager)
- ✅ Incremental updates
- ✅ Offline-first architecture

## Technology Stack

- **Language**: Kotlin
- **UI**: Jetpack Compose + Material Design 3
- **Architecture**: MVVM
- **Local DB**: Room (SQLite)
- **Cloud DB**: Supabase (PostgreSQL)
- **DI**: Hilt
- **Background**: WorkManager
- **State**: StateFlow/Flow
- **Storage**: DataStore

## Configuration

### Supabase Setup (Required)

**Quick Setup:**

1. Copy the example configuration file:
   ```bash
   cd android
   cp local.properties.example local.properties
   ```

2. Edit `local.properties` and add your Supabase credentials:
   ```properties
   SUPABASE_URL_PROJECT1=https://your-project1-id.supabase.co
   SUPABASE_KEY_PROJECT1=your-project1-anon-key
   SUPABASE_URL_PROJECT2=https://your-project2-id.supabase.co
   SUPABASE_KEY_PROJECT2=your-project2-anon-key
   ```

3. Rebuild the project:
   ```bash
   ./gradlew clean build
   ```

**Getting Your Credentials:**
- Go to your Supabase project dashboard
- Navigate to **Settings** → **API**
- Copy the **Project URL** and **anon/public key** for each project

**See [SUPABASE_SETUP.md](./SUPABASE_SETUP.md) for detailed instructions.**

## Testing

### Unit Tests
```bash
./gradlew test
```

### Instrumented Tests
```bash
./gradlew connectedAndroidTest
```

## Next Steps (Phase 12)

1. Configure Supabase credentials
2. Test on device/emulator
3. Fix any compilation errors
4. Add comprehensive tests
5. Performance optimization
6. Bug fixes and edge cases

## Documentation

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Complete architecture documentation
- [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) - Detailed implementation phases
- [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) - Current implementation status
- [DECISIONS.md](./DECISIONS.md) - Technical decisions

## Related Projects

- **Desktop App**: `../frontend/` - Tauri + React desktop application
- **Backend API**: `../backend/` - FastAPI backend (optional for Android)
