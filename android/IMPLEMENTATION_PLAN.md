# Android App Implementation Plan

## Overview

This document outlines the precise implementation phases for the Android tablet app, focusing on the **Browser** feature that allows teachers to view and navigate lesson plans for bilingual students.

## Architecture Summary

- **Pattern**: MVVM (Model-View-ViewModel)
- **UI**: Jetpack Compose with Material Design 3
- **Local DB**: Room (SQLite) - Offline-first
- **Remote DB**: Supabase (PostgreSQL) - Cloud sync
- **Sync**: Network-aware (WiFi for heavy, mobile for critical)
- **DI**: Hilt
- **Background Work**: WorkManager

## Browser Feature Scope

### Core Functionality
1. **User Selection** - Select teacher/user on app startup
2. **Week View** - Grid showing all 5 days with lesson cards
3. **Day View** - List of lessons for selected day
4. **Lesson Detail View** - Full lesson plan content with:
   - Objectives (content + language)
   - Vocabulary & cognates
   - Sentence frames
   - Materials needed
   - Instruction steps
   - Assessment
5. **Navigation** - Switch between week/day/lesson views
6. **Week Selection** - Choose which week to view
7. **Refresh** - Manual sync trigger
8. **Offline Support** - Works with cached data

### Data Requirements
- Weekly plans (metadata + full lesson_json)
- Schedule entries (teacher's schedule)
- Lesson steps (detailed step-by-step content)
- User profiles
- Sync metadata (timestamps)

---

## Implementation Phases

### Phase 0: Project Setup & Foundation
**Goal**: Create Android project and set up basic infrastructure

**Tasks**:
1. Create Android project in Android Studio
   - Package: `com.bilingual.lessonplanner`
   - Min SDK: API 26
   - Target SDK: API 35/36
   - Language: Kotlin
   - Build: Kotlin DSL

2. Configure Gradle dependencies
   - Room database
   - Jetpack Compose
   - Hilt (DI)
   - Supabase Android SDK
   - WorkManager
   - Coroutines
   - Navigation Compose
   - DataStore

3. Set up project structure
   - Create package folders (data, domain, ui, di)
   - Configure Hilt Application class
   - Set up basic theme

4. Configure Supabase
   - Add Supabase URLs and keys (build config)
   - Create Supabase client factory
   - Set up project mapping (user → project)

**Deliverables**:
- ✅ Android project created
- ✅ Dependencies configured
- ✅ Project structure in place
- ✅ Supabase connection ready

**Estimated Time**: 2-3 hours

---

### Phase 1: Data Layer - Domain Models & Repository Interface
**Goal**: Define data models and repository contracts

**Tasks**:
1. Create domain models (pure Kotlin data classes)
   - `WeeklyPlan.kt`
   - `LessonStep.kt`
   - `ScheduleEntry.kt`
   - `User.kt`

2. Create repository interface
   - `PlanRepository.kt` (interface)
   - Define all required methods (getPlans, getPlanDetail, etc.)

3. Create data mappers
   - Entity → Domain model converters
   - Domain → Entity converters

**Deliverables**:
- ✅ Domain models defined
- ✅ Repository interface defined
- ✅ Mappers implemented

**Estimated Time**: 2-3 hours

---

### Phase 2: Data Layer - Local Database (Room)
**Goal**: Set up Room database for offline storage

**Tasks**:
1. Create Room entities
   - `WeeklyPlanEntity.kt`
   - `LessonStepEntity.kt`
   - `ScheduleEntryEntity.kt`
   - `UserEntity.kt`
   - `SyncMetadataEntity.kt`

2. Create DAOs (Data Access Objects)
   - `PlanDao.kt` - CRUD operations for plans
   - `LessonStepDao.kt` - CRUD operations for steps
   - `ScheduleDao.kt` - CRUD operations for schedule
   - `UserDao.kt` - User operations
   - `SyncMetadataDao.kt` - Sync tracking

3. Create AppDatabase
   - `AppDatabase.kt` - Room database class
   - Define all DAOs
   - Set up migrations (version 1)

4. Create Local Repository
   - `LocalPlanRepository.kt` - Implements PlanRepository
   - Uses Room DAOs
   - Returns Flow for reactive updates

**Deliverables**:
- ✅ Room database set up
- ✅ All entities and DAOs created
- ✅ Local repository implemented
- ✅ Can store/retrieve data locally

**Estimated Time**: 4-5 hours

---

### Phase 3: Data Layer - Remote Database (Supabase)
**Goal**: Set up Supabase integration for cloud sync

**Tasks**:
1. Create Supabase API client
   - `SupabaseApi.kt` - Wrapper for Supabase operations
   - Methods for plans, steps, schedule, users
   - Error handling

2. Create Remote Repository
   - `RemotePlanRepository.kt` - Implements PlanRepository
   - Uses Supabase API client
   - Handles network errors

3. Implement project selection logic
   - User ID → Supabase project mapping
   - Dynamic client creation based on user

**Deliverables**:
- ✅ Supabase integration complete
- ✅ Remote repository implemented
- ✅ Can fetch data from Supabase

**Estimated Time**: 3-4 hours

---

### Phase 4: Sync Layer - Network-Aware Sync Manager
**Goal**: Implement smart sync with network awareness

**Tasks**:
1. Create NetworkAwareSyncManager
   - `NetworkAwareSyncManager.kt`
   - Detect WiFi vs Mobile/Hotspot
   - Network state monitoring (Flow)

2. Create SyncManager
   - `SyncManager.kt` - Main sync orchestration
   - Sync policies (WiFi vs Mobile)
   - Incremental sync (timestamp-based)
   - Full sync (all data)

3. Create BackgroundSyncWorker
   - `BackgroundSyncWorker.kt` - WorkManager worker
   - WiFi-only constraints
   - Periodic sync (4 hours)
   - Network change triggers

4. Implement sync strategies
   - Critical updates (always sync)
   - Full sync (WiFi only)
   - Incremental sync (timestamp-based)

**Deliverables**:
- ✅ Network-aware sync working
- ✅ Background sync scheduled
- ✅ Sync policies implemented

**Estimated Time**: 5-6 hours

---

### Phase 5: Repository Layer - Unified Repository
**Goal**: Combine local and remote repositories with sync

**Tasks**:
1. Create unified PlanRepository implementation
   - Combines LocalPlanRepository + RemotePlanRepository
   - UI always reads from local (offline-first)
   - Sync happens in background
   - Returns Flow from local DB

2. Implement sync triggers
   - App startup
   - Manual refresh
   - WiFi connected
   - Background worker

3. Add caching logic
   - Cache invalidation
   - Stale data detection
   - Smart refresh

**Deliverables**:
- ✅ Unified repository working
- ✅ Offline-first architecture
- ✅ Background sync operational

**Estimated Time**: 3-4 hours

---

### Phase 6: UI Layer - User Selection Screen
**Goal**: Implement user selection on app startup

**Tasks**:
1. Create UserSelectorScreen (Compose)
   - `UserSelectorScreen.kt`
   - List of users from Supabase
   - Selection UI (dropdown or list)
   - Material Design 3

2. Create UserSelectorViewModel
   - `UserSelectorViewModel.kt`
   - Load users from repository
   - Handle user selection
   - Store in DataStore

3. Implement navigation
   - UserSelector → Browser (after selection)
   - Store selected user ID

4. Set up DataStore
   - Preferences for user ID
   - Supabase project mapping

**Deliverables**:
- ✅ User selection screen working
- ✅ User preference stored
- ✅ Navigation to Browser

**Estimated Time**: 3-4 hours

---

### Phase 7: UI Layer - Browser Screen (Main Container)
**Goal**: Create main Browser screen with view mode switching

**Tasks**:
1. Create BrowserScreen (Compose)
   - `BrowserScreen.kt`
   - Top bar with view mode buttons (Week/Day/Lesson)
   - Week selector dropdown
   - Refresh button
   - Network indicator

2. Create BrowserViewModel
   - `BrowserViewModel.kt`
   - StateFlow for UI state
   - View mode management (week/day/lesson)
   - Week selection
   - Refresh logic

3. Implement view mode switching
   - Week view
   - Day view
   - Lesson view
   - Navigation between views

**Deliverables**:
- ✅ Browser screen with navigation
- ✅ View mode switching working
- ✅ Week selection working

**Estimated Time**: 4-5 hours

---

### Phase 8: UI Layer - Week View
**Goal**: Display weekly grid with lesson cards

**Tasks**:
1. Create WeekView (Compose)
   - `WeekView.kt`
   - Grid layout (5 columns for 5 days)
   - Lesson cards per day
   - Subject colors
   - Click to view lesson

2. Create PlanCard component
   - `PlanCard.kt` - Reusable lesson card
   - Shows: Subject, time, grade, WIDA objective preview
   - Visual indicators (status, etc.)

3. Implement lesson data loading
   - Load schedule entries
   - Match with plan slots
   - Display lesson metadata

4. Handle non-class periods
   - Filter out PREP, LUNCH, etc.
   - Show only active lessons

**Deliverables**:
- ✅ Week view displaying lessons
- ✅ Lesson cards clickable
- ✅ Data loading working

**Estimated Time**: 5-6 hours

---

### Phase 9: UI Layer - Day View
**Goal**: Display lessons for a single day

**Tasks**:
1. Create DayView (Compose)
   - `DayView.kt`
   - List of lessons for selected day
   - Day navigation (previous/next day)
   - Lesson cards in list format

2. Enhance PlanCard for list view
   - Horizontal layout option
   - More details visible
   - Click to view lesson detail

3. Implement day switching
   - Previous/next day buttons
   - Day labels (Monday-Friday)
   - Maintain selected lesson context

**Deliverables**:
- ✅ Day view displaying lessons
- ✅ Day navigation working
- ✅ Lesson selection working

**Estimated Time**: 3-4 hours

---

### Phase 10: UI Layer - Lesson Detail View
**Goal**: Display full lesson plan details

**Tasks**:
1. Create LessonDetailView (Compose)
   - `LessonDetailView.kt`
   - Scrollable content
   - All lesson sections:
     - Objectives (content + language)
     - Vocabulary & cognates
     - Sentence frames
     - Materials needed
     - Instruction steps
     - Assessment

2. Create detail components
   - `VocabularyDisplay.kt` - Show vocabulary/cognates
   - `SentenceFramesDisplay.kt` - Show sentence frames
   - `MaterialsDisplay.kt` - Show materials
   - `InstructionStepsDisplay.kt` - Show steps

3. Implement navigation
   - Back button
   - Previous/next lesson buttons
   - Lesson navigation within day

4. Load lesson steps
   - Fetch from repository
   - Display step-by-step content
   - Handle loading/error states

**Deliverables**:
- ✅ Lesson detail view complete
- ✅ All content sections displayed
- ✅ Navigation working

**Estimated Time**: 6-8 hours

---

### Phase 11: Integration & Polish
**Goal**: Integrate all components and polish UX

**Tasks**:
1. Connect all components
   - WeekView → DayView → LessonDetailView flow
   - Data flow through ViewModels
   - State management

2. Implement caching
   - Plan data caching
   - Lesson step caching
   - Cache invalidation

3. Add loading states
   - Loading indicators
   - Skeleton screens
   - Error handling

4. Polish UI/UX
   - Material Design 3 theming
   - Tablet-optimized layouts
   - Animations
   - Accessibility

5. Testing
   - Test offline functionality
   - Test sync on WiFi
   - Test sync on mobile
   - Test navigation flows

**Deliverables**:
- ✅ All features integrated
- ✅ UI polished
- ✅ Offline working
- ✅ Sync working

**Estimated Time**: 6-8 hours

---

### Phase 12: Optimization & Testing
**Goal**: Optimize performance and comprehensive testing

**Tasks**:
1. Performance optimization
   - Database query optimization
   - Image loading optimization
   - List virtualization
   - Memory management

2. Battery optimization
   - Background sync efficiency
   - Network request batching
   - Cache strategy refinement

3. Comprehensive testing
   - Unit tests (ViewModels, Repositories)
   - Integration tests (Database, Sync)
   - UI tests (Navigation, Interactions)
   - Manual testing on tablet

4. Bug fixes
   - Fix any issues found
   - Edge case handling
   - Error recovery

**Deliverables**:
- ✅ App optimized
- ✅ Tests written
- ✅ Bugs fixed
- ✅ Ready for production

**Estimated Time**: 8-10 hours

---

## Phase Dependencies

```
Phase 0 (Setup)
    ↓
Phase 1 (Domain Models)
    ↓
Phase 2 (Room) ──┐
    ↓            │
Phase 3 (Supabase) ──┐
    ↓                │
Phase 4 (Sync) ──────┤
    ↓                │
Phase 5 (Unified Repo) ──┐
    ↓                    │
Phase 6 (User Select) ───┤
    ↓                    │
Phase 7 (Browser Screen) ─┤
    ↓                    │
Phase 8 (Week View) ─────┤
    ↓                    │
Phase 9 (Day View) ──────┤
    ↓                    │
Phase 10 (Lesson Detail) ─┤
    ↓                    │
Phase 11 (Integration) ───┤
    ↓                    │
Phase 12 (Optimization) ──┘
```

## Total Estimated Time

- **Phase 0-5** (Data & Sync): ~20-25 hours
- **Phase 6-10** (UI): ~25-30 hours
- **Phase 11-12** (Polish): ~14-18 hours
- **Total**: ~59-73 hours (~1.5-2 weeks full-time)

## Critical Path

The critical path (must complete in order):
1. Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. Phase 6 → Phase 7 → Phase 8 → Phase 9 → Phase 10
3. Phase 11 → Phase 12

## Parallel Work Opportunities

- Phase 2 (Room) and Phase 3 (Supabase) can be done in parallel after Phase 1
- Phase 8 (WeekView), Phase 9 (DayView), Phase 10 (LessonDetail) can be done in parallel after Phase 7
- UI components can be built while data layer is being tested

## Success Criteria

### Phase 5 Complete (Data Layer)
- ✅ Can store data locally (Room)
- ✅ Can fetch data from Supabase
- ✅ Sync works (WiFi and mobile)
- ✅ Offline mode works

### Phase 10 Complete (UI Layer)
- ✅ User can select user
- ✅ User can view week grid
- ✅ User can view day list
- ✅ User can view lesson details
- ✅ Navigation works between views

### Phase 12 Complete (Production Ready)
- ✅ All features working
- ✅ Offline mode tested
- ✅ Sync tested
- ✅ Performance acceptable
- ✅ No critical bugs

---

## Next Steps

1. **Review this plan** - Confirm phases and priorities
2. **Create Android project** - In Android Studio
3. **Start Phase 0** - Set up project and dependencies
4. **Iterate through phases** - One phase at a time

---

## Notes

- Each phase builds on previous phases
- Can test incrementally (don't need to wait for all phases)
- Focus on Browser feature first (other features later)
- Keep architecture clean (follow MVVM, SOLID principles)

