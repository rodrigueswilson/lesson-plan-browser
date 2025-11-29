# Frontend Versions Documentation

## Overview

This project has evolved through three distinct frontend implementations, each serving different purposes and platforms. This document explains each version, their relationships, and the current architecture.

---

## The Three Versions

### Version 1: Original PC Desktop Application
**Location:** `frontend/`  
**Platform:** Windows/macOS/Linux Desktop (Tauri)  
**Status:** Production (Full Application)

#### Purpose
Complete desktop application for lesson plan creation, editing, and management. This is the primary authoring tool used by teachers on their PCs.

#### Features
- **Complete UI**: Home, Lesson Plans, Schedule, Browser, History, Analytics
- **Schedule Management**: Full schedule editor with slot configuration
- **Lesson Plan Generation**: AI-powered lesson plan creation
- **Analytics Dashboard**: Usage statistics and insights
- **Plan History**: Version tracking and history
- **Batch Processing**: Multi-day lesson plan processing

#### Architecture
- **Framework**: Tauri + React + TypeScript
- **Backend Connection**: HTTP API (`http://localhost:8000`)
- **Data Storage**: Backend SQLite database (via API)
- **Build Command**: `npm run tauri:dev` (development) or `npm run tauri:build` (production)

#### Key Components
- `App.tsx` - Main application with full navigation
- `components/ScheduleInput.tsx` - Schedule grid editor
- `components/Analytics.tsx` - Analytics dashboard
- `components/PlanHistory.tsx` - Plan version history
- `components/BatchProcessor.tsx` - Multi-day processing
- `components/SlotConfigurator.tsx` - Slot configuration UI

#### Current State
✅ Fully functional and in production use  
✅ Uses shared modules (`@lesson-browser`, `@lesson-api`)  
✅ Complete feature set for lesson plan authoring

---

### Version 2: Tablet-Focused Browser-Only Application
**Location:** `lesson-plan-browser/frontend/`  
**Platform:** Android Tablet (Tauri Android)  
**Status:** Production (Browser-Only)

#### Purpose
Simplified tablet application focused solely on viewing and executing lesson plans. Designed for classroom use during instruction.

#### Features
- **Browser View Only**: Week view, Day view, Lesson detail view
- **Lesson Mode**: Interactive timer-based lesson execution
- **User Selection**: Multi-user support
- **No Editing**: Read-only access to lesson plans
- **Optimized for Touch**: Large buttons, tablet-friendly UI

#### Architecture
- **Framework**: Tauri Android + React + TypeScript
- **Backend Connection**: HTTP API (configurable via `VITE_ANDROID_API_BASE_URL`)
- **Local Database Option**: Can use local SQLite (via `VITE_ENABLE_STANDALONE_DB=true`)
- **Build Command**: `npm run android:dev` (emulator) or `npm run android:build` (APK)

#### Key Components
- `App.tsx` - Simplified entry point (browser only)
- Uses shared `LessonPlanBrowser` component
- Uses shared `WeekView`, `DayView`, `LessonDetailView`
- Uses shared `LessonMode` component

#### Current State
✅ Fully functional and optimized for tablet  
✅ Uses shared modules (`@lesson-browser`, `@lesson-mode`, `@lesson-api`)  
✅ Responsive design for tablet screens  
✅ Ready for physical tablet deployment

#### Historical Note
This was originally the "second version" that had important improvements:
- Better week grid layout (table-based)
- Improved time handling
- Complete lesson mode implementation
- Better color schemes

---

### Version 3: Shared Module (Consolidated)
**Location:** `shared/lesson-browser/` and `shared/lesson-mode/`  
**Platform:** Shared by both PC and Tablet  
**Status:** Active Development (Source of Truth)

#### Purpose
Centralized, reusable components that both PC and tablet versions consume. This is the "single source of truth" for browser and lesson mode functionality.

#### Structure

**`shared/lesson-browser/`** - Browser components:
- `LessonPlanBrowser.tsx` - Main browser container
- `WeekView.tsx` - Week grid layout (table-based)
- `DayView.tsx` - Day schedule view
- `LessonDetailView.tsx` - Detailed lesson preview
- `UserSelector.tsx` - User selection component
- `utils/` - Schedule colors, plan matching, formatters

**`shared/lesson-mode/`** - Lesson execution components:
- `LessonMode.tsx` - Main lesson mode container
- `TimelineSidebar.tsx` - Step timeline with timer
- `CurrentStepInstructions.tsx` - Current step display
- `ResourceDisplayArea.tsx` - Resource tabs (vocab, frames, etc.)
- `TimerDisplay.tsx` - Timer controls
- `hooks/useLessonTimer.ts` - Timer logic hook

**`shared/lesson-api/`** - API client:
- Dual-mode API client (HTTP + local DB)
- Platform-specific URL resolution
- All API helpers and types

#### Features
- **Table-Based Week Grid**: Proper horizontal layout for entries
- **Responsive Design**: Tablet-optimized with desktop fallbacks
- **Timer System**: Auto-advance, live mode sync, session persistence
- **Resource Display**: Vocabulary, sentence frames, lesson cards
- **Plan Matching**: Complex slot resolution logic

#### Current State
✅ Active development and maintenance  
✅ Used by both PC and tablet versions  
✅ Source of truth for browser/lesson mode features  
✅ Recently updated with tablet-responsive sizing

---

## Version Evolution Timeline

### Phase 1: Original PC Version
- **Created**: Initial desktop application
- **Purpose**: Full lesson plan authoring tool
- **Location**: `frontend/`

### Phase 2: Tablet Browser Version
- **Created**: Simplified tablet-focused browser
- **Purpose**: Classroom instruction tool
- **Location**: `lesson-plan-browser/frontend/`
- **Improvements**: Better week view, improved time handling, complete lesson mode

### Phase 3: Shared Module Consolidation
- **Created**: Extracted common components
- **Purpose**: Single source of truth for both platforms
- **Location**: `shared/lesson-browser/`, `shared/lesson-mode/`, `shared/lesson-api/`
- **Strategy**: Tablet version became reference implementation

---

## Current Architecture

### Dependency Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Shared Modules                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ @lesson-api  │  │@lesson-browser│  │ @lesson-mode │ │
│  │              │  │              │  │              │ │
│  │ • API Client │  │ • WeekView   │  │ • LessonMode │ │
│  │ • Types      │  │ • DayView    │  │ • Timer      │ │
│  │ • Helpers    │  │ • DetailView │  │ • Resources  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
         ▲                        ▲
         │                        │
         │                        │
┌────────┴────────┐    ┌─────────┴──────────┐
│  PC Version     │    │  Tablet Version    │
│  (frontend/)    │    │(lesson-plan-browser│
│                 │    │     /frontend/)    │
│ • Full App      │    │ • Browser Only     │
│ • Schedule Edit │    │ • Lesson Mode      │
│ • Analytics     │    │ • Tablet UI        │
│ • History       │    │                    │
└─────────────────┘    └────────────────────┘
```

### Build Configuration

**PC Version:**
```json
// frontend/vite.config.ts
resolve: {
  alias: {
    '@lesson-api': path.resolve(__dirname, '../../shared/lesson-api/src'),
    '@lesson-browser': path.resolve(__dirname, '../../shared/lesson-browser/src'),
    '@lesson-mode': path.resolve(__dirname, '../../shared/lesson-mode/src'),
  }
}
```

**Tablet Version:**
```json
// lesson-plan-browser/frontend/vite.config.ts
resolve: {
  alias: {
    '@lesson-api': path.resolve(__dirname, '../../../shared/lesson-api/src'),
    '@lesson-browser': path.resolve(__dirname, '../../../shared/lesson-browser/src'),
    '@lesson-mode': path.resolve(__dirname, '../../../shared/lesson-mode/src'),
  }
}
```

---

## Key Differences Summary

| Feature | PC Version | Tablet Version | Shared Module |
|---------|-----------|----------------|---------------|
| **Purpose** | Authoring | Execution | Reusable |
| **Platform** | Desktop | Android Tablet | Both |
| **UI Scope** | Full App | Browser Only | Components |
| **Editing** | ✅ Yes | ❌ No | N/A |
| **Schedule** | ✅ Editor | ❌ View Only | View Only |
| **Analytics** | ✅ Yes | ❌ No | N/A |
| **Week View** | Uses Shared | Uses Shared | Table Layout |
| **Lesson Mode** | Uses Shared | Uses Shared | Timer System |
| **API Client** | Uses Shared | Uses Shared | Dual Mode |

---

## Development Guidelines

### When to Modify Shared Modules

✅ **DO modify shared modules when:**
- Fixing bugs in browser/lesson mode
- Adding features needed by both platforms
- Improving responsive design
- Updating API client logic

❌ **DON'T modify shared modules for:**
- Platform-specific features (PC-only or tablet-only)
- UI that only one platform needs
- Backend-specific logic

### When to Modify Platform-Specific Code

✅ **PC Version (`frontend/`):**
- Schedule editing features
- Analytics dashboard
- Plan history UI
- Batch processing UI

✅ **Tablet Version (`lesson-plan-browser/frontend/`):**
- Tablet-specific build configuration
- Android-specific Tauri config
- Tablet deployment scripts

---

## Migration History

### Consolidation Process (Recent)

1. **Identified "Second Version" as Reference**
   - Tablet version had better week view implementation
   - Improved time handling and layout

2. **Extracted to Shared Modules**
   - Moved `WeekView`, `DayView`, `LessonDetailView` to `shared/lesson-browser/`
   - Moved `LessonMode` and related components to `shared/lesson-mode/`
   - Created `shared/lesson-api/` for API client

3. **Updated Both Versions**
   - PC version imports from shared modules
   - Tablet version imports from shared modules
   - Removed duplicate code

4. **Fixed Week View Layout**
   - Switched to table-based layout (from CSS Grid)
   - Fixed horizontal display of entries (A.M. Routine, etc.)
   - Improved time slot matching

5. **Added Responsive Design**
   - Tablet-optimized button sizes
   - Larger text for tablet screens
   - Touch-friendly interactions

---

## File Structure Reference

```
LP/
├── frontend/                          # Version 1: PC Desktop App
│   ├── src/
│   │   ├── components/
│   │   │   ├── ScheduleInput.tsx     # PC-only: Schedule editor
│   │   │   ├── Analytics.tsx         # PC-only: Analytics
│   │   │   └── ...                   # Other PC-specific components
│   │   ├── App.tsx                   # Full app navigation
│   │   └── main.tsx
│   └── package.json
│
├── lesson-plan-browser/
│   └── frontend/                      # Version 2: Tablet Browser
│       ├── src/
│       │   ├── App.tsx               # Browser-only entry
│       │   └── main.tsx
│       ├── src-tauri/                # Android Tauri config
│       └── package.json
│
└── shared/                            # Version 3: Shared Modules
    ├── lesson-api/                    # API Client
    │   └── src/
    │       └── index.ts
    ├── lesson-browser/                # Browser Components
    │   └── src/
    │       ├── components/
    │       │   ├── WeekView.tsx
    │       │   ├── DayView.tsx
    │       │   ├── LessonDetailView.tsx
    │       │   └── LessonPlanBrowser.tsx
    │       └── index.ts
    └── lesson-mode/                   # Lesson Mode Components
        └── src/
            ├── components/
            │   ├── LessonMode.tsx
            │   ├── TimelineSidebar.tsx
            │   └── ...
            └── index.ts
```

---

## Related Documentation

- **`lesson-plan-browser/PROJECT_STATUS.md`** - Current project status
- **`ANALYSIS_SECOND_VERSION.md`** - Analysis of tablet version
- **`ANALYSIS_DETAILED_AND_LESSON_MODE.md`** - Component analysis
- **`LESSON_PLAN_BROWSER_ARCHITECTURE.md`** - Architecture details
- **`lesson-plan-browser/RESPONSIVE_TABLET_UPDATES.md`** - Responsive design updates
- **`lesson-plan-browser/TABLET_BUILD_SUMMARY.md`** - Tablet build guide

---

## Questions & Answers

**Q: Which version should I modify for browser features?**  
A: Modify `shared/lesson-browser/` - changes will apply to both PC and tablet.

**Q: Which version should I modify for lesson mode features?**  
A: Modify `shared/lesson-mode/` - changes will apply to both PC and tablet.

**Q: Can I add PC-only features?**  
A: Yes, add them to `frontend/src/components/` - they won't affect tablet.

**Q: Can I add tablet-only features?**  
A: Yes, add them to `lesson-plan-browser/frontend/src/` - they won't affect PC.

**Q: How do I test changes to shared modules?**  
A: Test in both PC version (`npm run tauri:dev`) and tablet version (`npm run android:dev`).

**Q: What's the "second version" mentioned in conversations?**  
A: That's the tablet version (`lesson-plan-browser/frontend/`) which had better implementations that were later consolidated into shared modules.

---

**Last Updated:** 2025-11-27  
**Status:** Current Architecture Documentation

