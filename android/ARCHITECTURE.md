# Android App Architecture

## Overview

Native Android tablet application for the Bilingual Weekly Plan Builder, focusing on the **Browser** feature that allows teachers to view and navigate lesson plans for their bilingual students.

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Kotlin | 1.9+ | Native Android development |
| **UI Framework** | Jetpack Compose | 1.5+ | Modern declarative UI |
| **Architecture** | MVVM | - | Separation of concerns |
| **Local Database** | Room | 2.6+ | Offline-first data storage |
| **Background Work** | WorkManager | 2.8+ | Network-aware sync scheduling |
| **Dependency Injection** | Hilt | 2.48+ | Android DI framework |
| **Networking** | Supabase Android SDK | 2.0+ | Direct cloud database access |
| **State Management** | StateFlow / Flow | - | Reactive data streams |
| **Design System** | Material Design 3 | - | Native Android design |

### Key Libraries

- **Room**: Local SQLite database with type-safe queries
- **WorkManager**: Background sync with network constraints
- **Supabase Kotlin SDK**: Direct PostgreSQL access via REST API
- **Coroutines**: Asynchronous programming
- **Hilt**: Dependency injection
- **Navigation Compose**: Screen navigation
- **DataStore**: Preferences storage

## Architecture Pattern: MVVM

```
┌─────────────────────────────────────────────────────────┐
│                    UI Layer (Compose)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Browser  │  │ WeekView  │  │LessonView│            │
│  │  Screen  │  │           │  │          │            │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘            │
└───────┼──────────────┼──────────────┼──────────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │      ViewModel Layer        │
        │  ┌──────────────────────┐  │
        │  │  BrowserViewModel    │  │
        │  │  - StateFlow<UiState>│  │
        │  │  - Business Logic    │  │
        │  └──────────┬───────────┘  │
        └─────────────┼──────────────┘
                      │
        ┌─────────────▼──────────────┐
        │     Repository Layer       │
        │  ┌──────────────────────┐  │
        │  │  PlanRepository      │  │
        │  │  (Interface)         │  │
        │  └──────────┬───────────┘  │
        └─────────────┼──────────────┘
                      │
        ┌─────────────┴──────────────┐
        │                            │
┌───────▼────────┐        ┌─────────▼────────┐
│  Local Data    │        │  Remote Data      │
│  (Room)        │        │  (Supabase)       │
│                │        │                    │
│  - Plans       │        │  - REST API       │
│  - Steps       │        │  - Realtime       │
│  - Schedule    │        │  - Auth           │
└────────────────┘        └───────────────────┘
```

## Database Architecture

### Dual Database Strategy

#### 1. Local Database (Room/SQLite)
- **Purpose**: Offline-first storage, fast local access
- **Location**: Device storage
- **Sync**: Bidirectional with Supabase
- **Tables**:
  - `weekly_plans` - Plan metadata and full lesson_json
  - `lesson_steps` - Individual lesson step details
  - `schedule_entries` - Teacher schedules
  - `users` - User profiles
  - `sync_metadata` - Track last sync timestamps

#### 2. Remote Database (Supabase PostgreSQL)
- **Purpose**: Cloud storage, multi-device sync, source of truth
- **Location**: Supabase cloud
- **Access**: Direct via Supabase Android SDK
- **Tables**: Same schema as local (mirrored)

### Sync Strategy

#### Network-Aware Sync Policies

| Data Type | WiFi | Mobile/Hotspot | Size | Priority |
|-----------|------|----------------|------|----------|
| Plan metadata | ✅ Full | ✅ Yes | ~1KB | CRITICAL |
| Current week plan | ✅ Full | ✅ Yes | ~50-200KB | HIGH |
| Historical plans | ✅ Full | ❌ No | ~200KB each | LOW |
| Single lesson step | ✅ Full | ✅ Yes | ~5-10KB | CRITICAL |
| All lesson steps | ✅ Full | ❌ No | ~500KB+ | LOW |
| Schedule updates | ✅ Full | ✅ Yes | ~10KB | HIGH |

#### Sync Triggers

1. **App Startup**: Check for critical updates (metadata only on mobile)
2. **WiFi Connected**: Trigger full background sync
3. **Manual Refresh**: User-initiated sync (respects network type)
4. **Realtime Events**: Supabase subscriptions for instant updates
5. **Background Worker**: Periodic sync every 4 hours (WiFi only)

#### Sync Flow

```
┌─────────────────────────────────────────────────┐
│            Sync Decision Tree                   │
└─────────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
    [WiFi]                 [Mobile]
        │                       │
        │                       │
┌───────▼────────┐    ┌────────▼────────┐
│ Full Sync      │    │ Incremental Sync │
│                │    │                  │
│ - All plans    │    │ - Metadata only  │
│ - All steps    │    │ - Current week   │
│ - Historical   │    │ - Critical data  │
└────────────────┘    └─────────────────┘
        │                       │
        └───────────┬───────────┘
                    │
            ┌───────▼───────┐
            │ Save to Room │
            │   Database   │
            └──────────────┘
```

## Data Models

### Core Entities

#### WeeklyPlan
```kotlin
@Entity(tableName = "weekly_plans")
data class WeeklyPlanEntity(
    @PrimaryKey val id: String,
    val user_id: String,
    val week_of: String,  // "2025-W01"
    val generated_at: String,
    val status: String,  // "pending" | "processing" | "completed" | "failed"
    val lesson_json: String?,  // Full JSON plan data
    val output_file: String?,
    val error_message: String?,
    val updated_at: Long,  // Timestamp for sync
    val synced_at: Long?  // Last successful sync
)
```

#### LessonStep
```kotlin
@Entity(tableName = "lesson_steps")
data class LessonStepEntity(
    @PrimaryKey val id: String,
    val lesson_plan_id: String,
    val day_of_week: String,  // "monday" | "tuesday" | etc.
    val slot_number: Int,
    val step_number: Int,
    val step_name: String,
    val duration_minutes: Int,
    val content_type: String,  // "objective" | "sentence_frames" | etc.
    val display_content: String,
    val hidden_content: String?,  // JSON array
    val sentence_frames: String?,  // JSON array
    val materials_needed: String?,  // JSON array
    val vocabulary_cognates: String?,  // JSON array
    val synced_at: Long?
)
```

#### ScheduleEntry
```kotlin
@Entity(tableName = "schedule_entries")
data class ScheduleEntryEntity(
    @PrimaryKey val id: String,
    val user_id: String,
    val day_of_week: String,
    val start_time: String,  // "08:15"
    val end_time: String,    // "08:30"
    val subject: String,
    val homeroom: String?,
    val grade: String?,
    val slot_number: Int,
    val plan_slot_group_id: String?,
    val is_active: Boolean,
    val synced_at: Long?
)
```

## Project Structure

```
android/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/bilingual/lessonplanner/
│   │   │   │   ├── data/
│   │   │   │   │   ├── local/
│   │   │   │   │   │   ├── database/
│   │   │   │   │   │   │   ├── AppDatabase.kt
│   │   │   │   │   │   │   ├── dao/
│   │   │   │   │   │   │   │   ├── PlanDao.kt
│   │   │   │   │   │   │   │   ├── LessonStepDao.kt
│   │   │   │   │   │   │   │   └── ScheduleDao.kt
│   │   │   │   │   │   │   └── entities/
│   │   │   │   │   │   │       ├── WeeklyPlanEntity.kt
│   │   │   │   │   │   │       ├── LessonStepEntity.kt
│   │   │   │   │   │   │       └── ScheduleEntryEntity.kt
│   │   │   │   │   │   └── repository/
│   │   │   │   │   │       └── LocalPlanRepository.kt
│   │   │   │   │   ├── remote/
│   │   │   │   │   │   ├── api/
│   │   │   │   │   │   │   └── SupabaseApi.kt
│   │   │   │   │   │   └── repository/
│   │   │   │   │   │       └── RemotePlanRepository.kt
│   │   │   │   │   └── sync/
│   │   │   │   │       ├── SyncManager.kt
│   │   │   │   │       ├── NetworkAwareSyncManager.kt
│   │   │   │   │       └── BackgroundSyncWorker.kt
│   │   │   │   ├── domain/
│   │   │   │   │   ├── model/
│   │   │   │   │   │   ├── WeeklyPlan.kt
│   │   │   │   │   │   ├── LessonStep.kt
│   │   │   │   │   │   └── ScheduleEntry.kt
│   │   │   │   │   └── repository/
│   │   │   │   │       └── PlanRepository.kt (interface)
│   │   │   │   ├── ui/
│   │   │   │   │   ├── browser/
│   │   │   │   │   │   ├── BrowserScreen.kt
│   │   │   │   │   │   ├── BrowserViewModel.kt
│   │   │   │   │   │   ├── WeekView.kt
│   │   │   │   │   │   ├── DayView.kt
│   │   │   │   │   │   └── LessonDetailView.kt
│   │   │   │   │   ├── theme/
│   │   │   │   │   │   ├── Color.kt
│   │   │   │   │   │   ├── Type.kt
│   │   │   │   │   │   └── Theme.kt
│   │   │   │   │   └── components/
│   │   │   │   │       ├── PlanCard.kt
│   │   │   │   │       ├── LessonCard.kt
│   │   │   │   │       └── NavigationBar.kt
│   │   │   │   └── di/
│   │   │   │       └── AppModule.kt
│   │   │   └── AndroidManifest.xml
│   │   └── build.gradle.kts
│   └── build.gradle.kts
├── gradle/
│   └── wrapper/
├── build.gradle.kts
├── settings.gradle.kts
└── ARCHITECTURE.md
```

## Key Design Decisions

### 1. Offline-First Architecture
- **Decision**: All data stored locally in Room
- **Rationale**: Works without network, fast access, battery efficient
- **Implementation**: UI always reads from local DB, sync happens in background

### 2. Network-Aware Sync
- **Decision**: Heavy syncs only on WiFi, critical updates on mobile
- **Rationale**: Minimize mobile data usage, respect user's data plan
- **Implementation**: WorkManager with network constraints

### 3. Direct Supabase Access
- **Decision**: Android app connects directly to Supabase (not via FastAPI)
- **Rationale**: Real-time subscriptions, lower latency, simpler architecture
- **Implementation**: Supabase Android SDK with Row Level Security

### 4. Reactive State Management
- **Decision**: StateFlow/Flow for reactive data streams
- **Rationale**: Automatic UI updates, lifecycle-aware, efficient
- **Implementation**: ViewModels expose StateFlow, UI collects

### 5. Material Design 3
- **Decision**: Use native Material Design components
- **Rationale**: Consistent Android experience, accessibility, tablet optimization
- **Implementation**: Compose Material3 library

## Security Considerations

### Authentication
- **Supabase Auth**: User authentication via Supabase
- **Row Level Security (RLS)**: Database-level access control
- **API Keys**: Store in secure storage (Android Keystore)

### Data Protection
- **Local Encryption**: Room database can be encrypted (optional)
- **Network Security**: HTTPS only, certificate pinning (optional)
- **PII Handling**: Follow Android privacy best practices

## Performance Targets

- **App Startup**: < 2 seconds to first screen
- **Data Loading**: < 500ms for cached data
- **Sync Performance**: Background sync doesn't block UI
- **Battery Impact**: Minimal background activity
- **Memory Usage**: < 200MB typical usage

## Testing Strategy

### Unit Tests
- ViewModels
- Repositories
- Use cases
- Data mappers

### Integration Tests
- Database operations
- Sync logic
- Network operations

### UI Tests
- Compose UI components
- Navigation flows
- User interactions

## Future Considerations

### iOS Support (If Needed)
- **Option 1**: Kotlin Multiplatform Mobile (KMM) for shared business logic
- **Option 2**: Separate native iOS app with shared API contracts
- **Decision**: Defer until Android app is stable

### Feature Expansion
- Lesson Mode (editing)
- Schedule management
- Analytics dashboard
- PDF export

## References

- [Android Architecture Guidelines](https://developer.android.com/topic/architecture)
- [Jetpack Compose](https://developer.android.com/jetpack/compose)
- [Room Database](https://developer.android.com/training/data-storage/room)
- [WorkManager](https://developer.android.com/topic/libraries/architecture/workmanager)
- [Supabase Android SDK](https://github.com/supabase/supabase-kt)

