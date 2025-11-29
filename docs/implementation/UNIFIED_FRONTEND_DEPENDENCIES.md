# Unified Frontend Dependencies Mapping

This document maps all imports, build script references, and configuration dependencies for the unified frontend implementation.

**Last Updated**: 2025-01-XX  
**Status**: Pre-Implementation Dependency Audit

## Import Dependencies

### PC Version App.tsx Imports

**File**: `frontend/src/App.tsx`

| Import | Source | Type | Status | Notes |
|--------|--------|------|--------|-------|
| `useState, useEffect` | `react` | External | Keep | React hooks |
| `BookOpen` | `lucide-react` | External | Keep | Icon component |
| `LessonPlanBrowser, UserSelector, useStore` | `@lesson-browser` | Shared | Keep | Shared browser components |
| `SlotConfigurator` | `./components/SlotConfigurator` | Local PC-only | **Lazy load** | PC-only component |
| `BatchProcessor` | `./components/BatchProcessor` | Local PC-only | **Lazy load** | PC-only component |
| `PlanHistory` | `./components/PlanHistory` | Local PC-only | **Lazy load** | PC-only component |
| `Analytics` | `./components/Analytics` | Local PC-only | **Lazy load** | PC-only component |
| `ScheduleInput` | `./components/ScheduleInput` | Local PC-only | **Lazy load** | PC-only component |
| `LessonMode` | `@lesson-mode/components/LessonMode` | Shared | Keep | Shared lesson mode |
| `isMobile` | `./lib/platform` | Local | **Enhance** | Platform detection |
| `DesktopLayout` | `./components/layouts/DesktopLayout` | Local | **Modify** | Add nav filtering |
| `MobileLayout` | `./components/layouts/MobileLayout` | Local | Review | May be obsolete |
| `setupBackButton` | `./lib/mobile` | Local | Keep | Mobile utilities |
| `SyncTestButton` | `./components/SyncTestButton` | Local PC-only | **Lazy load** | PC-only component |

**Total Imports**: 14  
**Shared Imports**: 4  
**PC-Only Imports**: 6 (to be lazy loaded)  
**Local Utilities**: 4

### Tablet Version App.tsx Imports

**File**: `lesson-plan-browser/frontend/src/App.tsx`

| Import | Source | Type | Status | Notes |
|--------|--------|------|--------|-------|
| `useState, lazy, Suspense` | `react` | External | Keep | React hooks |
| `LessonPlanBrowser, UserSelector, useStore` | `@lesson-browser` | Shared | Keep | Shared browser components |
| `ScheduleEntry` | `@lesson-api` | Shared | Keep | API types |
| `LessonMode` | `@lesson-mode/components/LessonMode` | Shared | **Lazy load** | Already lazy loaded |

**Total Imports**: 4  
**Shared Imports**: 4  
**PC-Only Imports**: 0  
**Local Utilities**: 0

### Shared Module Dependencies

**API Client** (`shared/lesson-api/src/index.ts`):
- Already unified and platform-aware
- No changes needed
- Handles platform detection internally

**Browser Components** (`shared/lesson-browser/src/`):
- Used by both platforms
- No changes needed
- Exports: `LessonPlanBrowser`, `WeekView`, `DayView`, `LessonDetailView`, `UserSelector`, `useStore`

**Lesson Mode** (`shared/lesson-mode/src/`):
- Used by both platforms
- No changes needed
- Exports: `LessonMode` and related components

## Build Script Dependencies

### Android Build Script

**File**: `lesson-plan-browser/scripts/build-android-offline.ps1`

| Reference | Line | Type | Status | Notes |
|-----------|------|------|--------|-------|
| `$frontendDir = Join-Path $repoRoot "frontend"` | 35 | Path | **Keep unchanged** | Expects `lesson-plan-browser/frontend/` |
| `$srcTauriDir = Join-Path $frontendDir "src-tauri"` | 41 | Path | Keep | Tauri config location |
| `$distDir = Join-Path $frontendDir "dist"` | 48 | Path | Keep | Build output location |
| `npm run build:skip-check` | 337 | Command | Keep | Frontend build command |
| `cargo build --target` | 354 | Command | Keep | Rust build command |
| `Copy-Item` dist to assets | 420 | File operation | Keep | Asset bundling |
| Tauri config copy | 451-494 | File operation | Keep | Config bundling |

**Critical Path**: Line 35 expects `frontend/` relative to `lesson-plan-browser/`  
**Action**: Keep unified frontend at `lesson-plan-browser/frontend/` (no changes needed)

### Build Script Entry Point

**File**: `lesson-plan-browser/scripts/run-with-ndk.ps1`

| Reference | Line | Type | Status | Notes |
|-----------|------|------|--------|-------|
| `Set-Location 'D:\LP\lesson-plan-browser'` | 95 | Path | Keep | Sets working directory |
| `.\scripts\build-android-offline.ps1` | 96 | Script call | Keep | Calls main builder |

**Action**: No changes needed

### PC Build Dependencies

**File**: `frontend/package.json`

| Script | Command | Status | Notes |
|--------|---------|--------|-------|
| `tauri:dev` | `tauri dev` | Keep | Development build |
| `tauri:build` | `tauri build` | Keep | Production build |
| `build:skip-check` | `vite build` | Keep | Frontend bundle only |

**Action**: May need to reference unified frontend or import from it

## Vite Configuration Dependencies

### PC Vite Config

**File**: `frontend/vite.config.ts`

| Configuration | Value | Status | Notes |
|---------------|-------|--------|-------|
| `@lesson-mode` alias | `../shared/lesson-mode/src` | Keep | Shared module path |
| `@lesson-browser` alias | `../shared/lesson-browser/src` | Keep | Shared module path |
| `@lesson-api` alias | `../shared/lesson-api/src` | Keep | Shared module path |
| Server proxy | `http://localhost:8000` | Keep | Backend API |
| Port | `1420` | Keep | Dev server port |

**Action**: May need to add alias to unified frontend location if PC imports from it

### Tablet Vite Config

**File**: `lesson-plan-browser/frontend/vite.config.ts`

| Configuration | Value | Status | Notes |
|---------------|-------|--------|-------|
| `@lesson-mode` alias | `../../shared/lesson-mode/src` | **Verify** | Different path depth |
| `@lesson-browser` alias | `../../shared/lesson-browser/src` | **Verify** | Different path depth |
| `@lesson-api` alias | `../../shared/lesson-api/src` | **Verify** | Different path depth |
| Server proxy | `http://127.0.0.1:8000` | Keep | Backend API |
| Port | `1420` | Keep | Dev server port |
| `manualChunks: undefined` | Line 67 | Keep | Android-specific config |

**Action**: Verify shared module paths are correct (already configured)

## Path Alias Dependencies

### Shared Module Paths

**PC Version** (`frontend/vite.config.ts`):
- `@lesson-mode`: `../shared/lesson-mode/src` (1 level up)
- `@lesson-browser`: `../shared/lesson-browser/src` (1 level up)
- `@lesson-api`: `../shared/lesson-api/src` (1 level up)

**Tablet Version** (`lesson-plan-browser/frontend/vite.config.ts`):
- `@lesson-mode`: `../../shared/lesson-mode/src` (2 levels up)
- `@lesson-browser`: `../../shared/lesson-browser/src` (2 levels up)
- `@lesson-api`: `../../shared/lesson-api/src` (2 levels up)

**Status**: Both correctly configured for their directory depths  
**Action**: No changes needed

## Platform Detection Dependencies

### Current Implementation

**File**: `frontend/src/lib/platform.ts`

| Function | Purpose | Status | Notes |
|----------|---------|--------|-------|
| `getPlatform()` | Detect platform | **Enhance** | Verify Android Tauri detection |
| `isDesktop` | Desktop check | Keep | Uses `__TAURI_INTERNALS__` |
| `isMobile` | Mobile check | **Verify** | Should detect Android Tauri |
| `isWeb` | Web check | Keep | Fallback |

**Dependencies**:
- `window.__TAURI_INTERNALS__` - Tauri desktop
- `window.Capacitor` - Capacitor mobile (not used)
- `navigator.userAgent` - User agent check

**Action**: Verify `isMobile` correctly identifies Android Tauri

### Tablet Platform Detection

**File**: `lesson-plan-browser/frontend/src/lib/platform.ts`

**Status**: May be duplicate of PC version  
**Action**: Consolidate to use PC version or verify identical

## Component Dependencies

### Desktop Navigation

**File**: `frontend/src/components/desktop/DesktopNav.tsx`

| Dependency | Type | Status | Notes |
|------------|------|--------|-------|
| `Home, FileText, Calendar, History, BarChart3, BookOpen` | Icons (lucide-react) | Keep | Navigation icons |
| `clsx` | Utility | Keep | Class name utility |
| Nav items array | Local | **Modify** | Add filtering support |

**Action**: Add `availableNavItems` prop to filter navigation

### Desktop Layout

**File**: `frontend/src/components/layouts/DesktopLayout.tsx`

| Dependency | Type | Status | Notes |
|------------|------|--------|-------|
| `DesktopNav` | Component | Keep | Navigation component |
| `BookOpen` | Icon | Keep | Logo icon |
| `activeNavItem` | Prop | Keep | Current nav item |
| `onNavigate` | Prop | Keep | Navigation handler |

**Action**: Add `availableNavItems` prop, pass to DesktopNav

## Tauri Configuration Dependencies

### PC Tauri Config

**File**: `frontend/src-tauri/tauri.conf.json`

| Setting | Value | Status | Notes |
|---------|-------|--------|-------|
| `productName` | "Bilingual Lesson Planner" | Keep | Desktop app name |
| `identifier` | "com.lessonplanner.bilingual" | Keep | Desktop identifier |
| `beforeBuildCommand` | "npm run build:skip-check" | Keep | Build command |

**Action**: No changes needed

### Tablet Tauri Config

**File**: `lesson-plan-browser/frontend/src-tauri/tauri.conf.json`

| Setting | Value | Status | Notes |
|---------|-------|--------|-------|
| `productName` | "Lesson Plan Browser" | Keep | Tablet app name |
| `identifier` | "com.lessonplanner.browser" | Keep | Tablet identifier |
| `beforeBuildCommand` | "npm run build:tauri" | Keep | Build command |

**File**: `lesson-plan-browser/frontend/src-tauri/tauri.android.conf.json`

| Setting | Value | Status | Notes |
|---------|-------|--------|-------|
| `devUrl` | "tauri://localhost" | Keep | Offline mode URL |

**Action**: No changes needed

## Environment Variable Dependencies

### Build-Time Variables

| Variable | PC Usage | Tablet Usage | Status |
|----------|----------|--------------|--------|
| `VITE_API_BASE_URL` | Backend URL | Backend URL | Keep |
| `VITE_ANDROID_API_BASE_URL` | N/A | Backend URL (Android) | Keep |
| `VITE_ENABLE_STANDALONE_DB` | N/A | Enable local DB | Keep |
| `TAURI_PLATFORM` | Platform detection | Platform detection | Keep |
| `TAURI_DEBUG` | Debug mode | Debug mode | Keep |

**Action**: No changes needed, API client handles these

## Dependency Graph

```
Unified Frontend (lesson-plan-browser/frontend/src/App.tsx)
├── React (external)
├── Shared Modules
│   ├── @lesson-browser
│   │   ├── React
│   │   ├── Zustand
│   │   └── lucide-react
│   ├── @lesson-mode
│   │   ├── React
│   │   └── @lesson-api
│   └── @lesson-api
│       └── Tauri API
├── Platform Detection (local)
│   └── Tauri internals
├── PC-Only Components (lazy loaded)
│   ├── ScheduleInput
│   ├── Analytics
│   ├── PlanHistory
│   ├── BatchProcessor
│   ├── SlotConfigurator
│   └── SyncTestButton
└── Layout Components (local)
    ├── DesktopLayout
    └── DesktopNav
```

## Critical Dependencies

### Must Not Break

1. **Build Script Path**: `lesson-plan-browser/scripts/build-android-offline.ps1` line 35
   - **Path**: `$frontendDir = Join-Path $repoRoot "frontend"`
   - **Action**: Keep unified frontend at `lesson-plan-browser/frontend/`

2. **Shared Module Aliases**: Both vite.config.ts files
   - **Action**: Verify paths are correct (already configured)

3. **API Client**: `shared/lesson-api/src/index.ts`
   - **Status**: Already unified, no changes needed
   - **Action**: Reference as example of unified code

4. **Platform Detection**: `frontend/src/lib/platform.ts`
   - **Action**: Verify Android Tauri detection works

### Can Be Modified

1. **PC App.tsx**: Can import from unified or be replaced
2. **Navigation Components**: Can add filtering props
3. **Layout Components**: Can add conditional rendering

## Dependency Resolution Strategy

### Consolidation Opportunities

1. **Platform Detection**: Use PC version, remove tablet duplicate
2. **UI Components**: Consolidate if duplicates exist
3. **Utilities**: Review for duplicates, consolidate

### Import Strategy for Unified Frontend

**Option A: Direct Implementation**
- Unified App.tsx at `lesson-plan-browser/frontend/src/App.tsx`
- PC imports from unified location
- Requires path alias or relative import

**Option B: Wrapper Pattern**
- Unified App.tsx at `lesson-plan-browser/frontend/src/App.tsx`
- PC App.tsx becomes thin wrapper that imports unified
- Minimal changes to PC structure

**Option C: Symlink/Reference**
- Unified App.tsx at `lesson-plan-browser/frontend/src/App.tsx`
- PC App.tsx is symlink or direct reference
- Platform-dependent (may not work on Windows)

**Recommended**: Option B (Wrapper Pattern) - Most compatible, minimal changes

## Build Dependencies Summary

### Android Build Chain

```
run-with-ndk.ps1
  └── build-android-offline.ps1
      ├── npm run build:skip-check (frontend)
      ├── cargo build (Rust)
      ├── Copy dist/ to assets/
      ├── Copy .so to jniLibs/
      └── gradlew assemble (Android)
```

**All paths relative to**: `lesson-plan-browser/`  
**Frontend location**: `lesson-plan-browser/frontend/`  
**Action**: No path changes needed

### PC Build Chain

```
npm run tauri:build (frontend/)
  ├── npm run build:skip-check
  ├── cargo build (Rust)
  └── Tauri bundler
```

**Frontend location**: `frontend/` (root)  
**Action**: May need to reference unified frontend

## Next Steps

1. Verify platform detection works on both platforms
2. Test build scripts with current structure
3. Decide on import strategy (Option B recommended)
4. Create backup before modifications
5. Begin Phase 2 implementation

---

**Document Status**: Complete - Pre-Implementation  
**Last Updated**: 2025-01-XX  
**Maintainer**: Development Team

