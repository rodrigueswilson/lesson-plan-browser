# Android App - Final Decisions

## Summary

All critical decisions have been made based on the existing desktop app architecture and best practices.

---

## Decision 1: Authentication Strategy ✅

**Decision**: **Simple User Selection** (Option C)

**Rationale**:
- Matches current desktop app UX - no login required
- Teachers select their user from a dropdown
- Faster MVP development
- Familiar user experience
- Can upgrade to Supabase Auth later if security requirements change

**Implementation**:
- User selector screen on app startup
- Store selected user ID in DataStore (preferences)
- Use user ID to determine which Supabase project to connect to

**Future Migration Path**:
- If needed, can add Supabase Auth later
- User selection can remain as fallback or admin feature

---

## Decision 2: Supabase Project Configuration ✅

**Decision**: **Multiple Projects** (Option B)

**Rationale**:
- Matches existing desktop app setup
- Project 1: Wilson's data
- Project 2: Daniela's data
- Complete data isolation per teacher
- No Row Level Security (RLS) complexity
- Each teacher has their own Supabase project

**Implementation**:
- App maintains mapping: User ID → Supabase Project
- Configuration stored in app (build config or DataStore)
- When user selected, app connects to their specific Supabase project
- Matches backend's `SUPABASE_PROJECT` selection logic

**Configuration Structure**:
```kotlin
data class SupabaseConfig(
    val project1Url: String,
    val project1Key: String,
    val project2Url: String,
    val project2Key: String
)

// User to project mapping
val userProjectMap = mapOf(
    "wilson-user-id" to "project1",
    "daniela-user-id" to "project2"
)
```

---

## Decision 3: Minimum Android Version ✅

**Decision**: **API 26 (Android 8.0)**

**Rationale**:
- Tablet-focused application
- Supports 95%+ of Android tablets
- Full Room database support
- Full WorkManager support
- Modern Android features available
- Good performance characteristics

**Version Targets**:
- **Min SDK**: API 26 (Android 8.0)
- **Target SDK**: API 34 (Android 14)
- **Compile SDK**: API 34

**Device Support**:
- Primary: Android tablets (10" recommended)
- Secondary: Large phones (7"+) in landscape mode

---

## Decision 4: Package Name ✅

**Decision**: **`com.bilingual.lessonplanner`**

**Rationale**:
- Clean, professional package name
- Clearly identifies the app
- No `.android` suffix needed (this is the Android app)
- Matches app branding

**App ID**: `com.bilingual.lessonplanner`

---

## Decision 5: Development Environment ✅

**Decision**: **Hybrid Approach**

**Android Studio**:
- Initial project setup
- Running and debugging apps
- Emulator management
- Performance profiling
- Gradle sync troubleshooting

**VS Code/Cursor**:
- Daily code editing
- File navigation
- Git operations
- AI-assisted coding
- General development workflow

**Rationale**:
- Android Studio has best Android-specific tooling
- VS Code/Cursor better for general coding
- Can seamlessly switch between them
- Project files are compatible

---

## Additional Decisions

### Build System
**Decision**: **Gradle Kotlin DSL** (build.gradle.kts)
- Modern, type-safe
- Better IDE support
- Standard for new Android projects

### Architecture Pattern
**Decision**: **MVVM** (Model-View-ViewModel)
- Standard Android architecture
- Separation of concerns
- Testable components
- Lifecycle-aware

### UI Framework
**Decision**: **Jetpack Compose**
- Modern declarative UI
- Better performance
- Tablet-optimized layouts
- Material Design 3 support

---

## Implementation Notes

### User Selection Flow
1. App starts → Show user selector
2. User selects their name from list
3. App loads user's Supabase project config
4. Connect to appropriate Supabase project
5. Load user's data (plans, schedule, etc.)
6. Store selected user ID in preferences

### Supabase Project Selection
```kotlin
// When user selected
val userId = selectedUser.id
val project = when {
    userId == "wilson-user-id" -> "project1"
    userId == "daniela-user-id" -> "project2"
    else -> determineProjectFromUser(userId)
}

val supabase = createSupabaseClient(project)
```

### Network-Aware Sync
- **WiFi**: Full sync (all plans, all steps, historical data)
- **Mobile/Hotspot**: Critical updates only (metadata, current week)
- **Offline**: Use cached data from Room database

---

## Next Steps

With all decisions made:

1. ✅ Install Android Studio and tools
2. ✅ Create Android project with these settings:
   - Package: `com.bilingual.lessonplanner`
   - Min SDK: API 26
   - Language: Kotlin
   - Build: Gradle Kotlin DSL
3. ✅ Configure Supabase connection
4. ✅ Implement user selection screen
5. ✅ Set up project structure (see ARCHITECTURE.md)
6. ✅ Start implementing Browser feature

---

## References

- See `ARCHITECTURE.md` for complete architecture
- See `SETUP_CHECKLIST.md` for installation steps
- See `DECISIONS_AND_TOOLS.md` for tool installation

