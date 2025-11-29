# Android Implementation - Quick Summary

## Overview

**Goal**: Build Android tablet app for viewing bilingual lesson plans (Browser feature)

**Architecture**: MVVM with Jetpack Compose, Room (local), Supabase (cloud), Network-aware sync

**Total Phases**: 12 phases, ~60-75 hours estimated

---

## Phase Breakdown

### Foundation (Phases 0-5) - Data & Sync
**Time**: ~20-25 hours

| Phase | Focus | Key Deliverables |
|-------|-------|-----------------|
| **0** | Project Setup | Android project, dependencies, structure |
| **1** | Domain Models | Data classes, repository interface |
| **2** | Room Database | Entities, DAOs, local repository |
| **3** | Supabase | API client, remote repository |
| **4** | Sync Manager | Network-aware sync, WorkManager |
| **5** | Unified Repo | Offline-first, background sync |

### UI Layer (Phases 6-10) - User Interface
**Time**: ~25-30 hours

| Phase | Focus | Key Deliverables |
|-------|-------|-----------------|
| **6** | User Selection | User selector screen, DataStore |
| **7** | Browser Screen | Main container, view mode switching |
| **8** | Week View | Grid of 5 days, lesson cards |
| **9** | Day View | List of lessons for one day |
| **10** | Lesson Detail | Full lesson plan content |

### Polish (Phases 11-12) - Integration & Testing
**Time**: ~14-18 hours

| Phase | Focus | Key Deliverables |
|-------|-------|-----------------|
| **11** | Integration | Connect all components, polish UI |
| **12** | Optimization | Performance, testing, bug fixes |

---

## Key Features to Implement

### Browser Feature
1. ✅ **User Selection** - Choose teacher on startup
2. ✅ **Week View** - Grid showing all 5 days
3. ✅ **Day View** - Lessons for selected day
4. ✅ **Lesson Detail** - Full lesson content:
   - Objectives (content + language)
   - Vocabulary & cognates
   - Sentence frames
   - Materials
   - Instruction steps
   - Assessment
5. ✅ **Navigation** - Switch between views
6. ✅ **Week Selection** - Choose which week
7. ✅ **Refresh** - Manual sync
8. ✅ **Offline** - Works with cached data

### Sync Features
- ✅ Network-aware (WiFi vs Mobile)
- ✅ Background sync (WorkManager)
- ✅ Incremental updates
- ✅ Offline-first architecture

---

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

---

## Critical Decisions Made

1. ✅ **Authentication**: Simple user selection (matches desktop)
2. ✅ **Supabase**: Multiple projects (project1, project2)
3. ✅ **Min SDK**: API 26 (Android 8.0)
4. ✅ **Target SDK**: API 35/36 (Android 15/16)
5. ✅ **Package**: `com.bilingual.lessonplanner`

---

## Implementation Order

```
Setup (Phase 0)
    ↓
Data Models (Phase 1)
    ↓
Local DB (Phase 2) ──┐
    ↓                │
Remote DB (Phase 3) ─┤
    ↓                │
Sync (Phase 4) ──────┤
    ↓                │
Unified Repo (Phase 5) ──┐
    ↓                    │
User Select (Phase 6) ───┤
    ↓                    │
Browser Screen (Phase 7) ─┤
    ↓                    │
Week View (Phase 8) ──────┤
    ↓                    │
Day View (Phase 9) ───────┤
    ↓                    │
Lesson Detail (Phase 10) ──┤
    ↓                    │
Integration (Phase 11) ────┤
    ↓                    │
Optimization (Phase 12) ───┘
```

---

## Success Milestones

### Milestone 1: Data Layer Complete (Phase 5)
- ✅ Can store data locally
- ✅ Can fetch from Supabase
- ✅ Sync works
- ✅ Offline works

### Milestone 2: UI Complete (Phase 10)
- ✅ User selection works
- ✅ All three views working
- ✅ Navigation works
- ✅ Data displays correctly

### Milestone 3: Production Ready (Phase 12)
- ✅ All features working
- ✅ Performance optimized
- ✅ Tested thoroughly
- ✅ Ready for teachers

---

## Next Action

**Start with Phase 0**: Create Android project in Android Studio

See `IMPLEMENTATION_PLAN.md` for detailed phase descriptions.

