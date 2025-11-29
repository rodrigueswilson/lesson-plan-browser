# Unified Frontend File Inventory

This document provides a complete inventory of all files in the PC version, tablet version, and shared modules, along with their purposes and status for the unified frontend implementation.

**Last Updated**: 2025-01-XX  
**Status**: Pre-Implementation Inventory

## PC Version (`frontend/`)

### Core Application Files

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `src/App.tsx` | Main PC application with full navigation | **To be replaced** | Will import from unified frontend or be replaced |
| `src/main.tsx` | Application entry point | Keep | May need minor updates |
| `src/index.css` | Global styles | Keep | Shared styles |
| `src/vite-env.d.ts` | Vite type definitions | Keep | Standard Vite file |

### Platform Detection & Utilities

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `src/lib/platform.ts` | Platform detection utility | **Enhance** | Verify Android Tauri detection works |
| `src/lib/platform.test.ts` | Platform detection tests | Keep | Update tests after enhancement |
| `src/lib/mobile.ts` | Mobile-specific utilities (back button) | Keep | Used by unified frontend |
| `src/lib/mobile.test.ts` | Mobile utilities tests | Keep | Keep tests |
| `src/lib/utils.ts` | General utilities | Keep | Shared utilities |

### PC-Only Components

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `src/components/ScheduleInput.tsx` | Schedule grid editor | **Lazy load** | PC-only, lazy load in unified frontend |
| `src/components/Analytics.tsx` | Analytics dashboard | **Lazy load** | PC-only, lazy load in unified frontend |
| `src/components/PlanHistory.tsx` | Plan version history | **Lazy load** | PC-only, lazy load in unified frontend |
| `src/components/BatchProcessor.tsx` | Multi-day processing | **Lazy load** | PC-only, lazy load in unified frontend |
| `src/components/SlotConfigurator.tsx` | Slot configuration UI | **Lazy load** | PC-only, lazy load in unified frontend |
| `src/components/SyncTestButton.tsx` | Sync testing utility | **Lazy load** | PC-only, lazy load in unified frontend |
| `src/components/CurrentLessonCard.tsx` | Current lesson display | Review | May be shared or PC-only |
| `src/components/ScheduleCell.tsx` | Schedule cell component | Review | Used by ScheduleInput, may be shared |

### Navigation & Layout Components

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `src/components/desktop/DesktopNav.tsx` | Desktop navigation sidebar | **Modify** | Add `availableNavItems` prop for filtering |
| `src/components/layouts/DesktopLayout.tsx` | Desktop layout wrapper | **Modify** | Support conditional nav items |
| `src/components/layouts/DesktopLayout.test.tsx` | Desktop layout tests | Keep | Update tests after modification |
| `src/components/layouts/MobileLayout.tsx` | Mobile layout wrapper | **Review** | May be obsolete (tablet has no nav) |
| `src/components/layouts/MobileLayout.test.tsx` | Mobile layout tests | Review | May be obsolete |
| `src/components/mobile/MobileNav.tsx` | Mobile bottom navigation | **Archive** | Not needed for tablet (no navigation) |
| `src/components/mobile/MobileNav.test.tsx` | Mobile nav tests | Archive | Not needed |

### Shared UI Components

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `src/components/ui/Alert.tsx` | Alert component | Keep | Shared UI component |
| `src/components/ui/Button.tsx` | Button component | Keep | Shared UI component |
| `src/components/ui/Card.tsx` | Card component | Keep | Shared UI component |
| `src/components/ui/Dialog.tsx` | Dialog component | Keep | Shared UI component |
| `src/components/ui/Input.tsx` | Input component | Keep | Shared UI component |
| `src/components/ui/Label.tsx` | Label component | Keep | Shared UI component |
| `src/components/ui/Progress.tsx` | Progress component | Keep | Shared UI component |
| `src/components/ui/Select.tsx` | Select component | Keep | Shared UI component |

### Other Directories

| Directory | Purpose | Status | Notes |
|-----------|---------|--------|-------|
| `src/hooks/` | Custom React hooks | Review | Check for PC-only hooks |
| `src/store/` | State management | Review | May be shared or PC-specific |
| `src/utils/` | Utility functions | Review | Check for duplicates with shared |
| `src/test/` | Test setup | Keep | Test configuration |
| `src/components/resources/` | Resource components | Review | May be shared with tablet |

### Configuration Files

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `vite.config.ts` | Vite build configuration | **Modify** | May need to reference unified frontend |
| `package.json` | Dependencies and scripts | Keep | Verify dependencies |
| `tsconfig.json` | TypeScript configuration | Keep | Standard config |
| `tailwind.config.js` | Tailwind CSS configuration | Keep | Shared styles |

### Tauri Configuration

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `src-tauri/tauri.conf.json` | Tauri desktop configuration | Keep | Desktop-specific config |
| `src-tauri/Cargo.toml` | Rust dependencies | Keep | Desktop build |
| `src-tauri/src/` | Rust backend code | Keep | Desktop Tauri commands |

## Tablet Version (`lesson-plan-browser/frontend/`)

### Core Application Files

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `src/App.tsx` | **Main tablet application (browser only)** | **BECOMES UNIFIED** | This becomes the unified frontend |
| `src/main.tsx` | Application entry point | Keep | May need minor updates |
| `src/index.css` | Global styles | Keep | Shared styles |
| `src/vite-env.d.ts` | Vite type definitions | Keep | Standard Vite file |

### Platform Detection & Utilities

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `src/lib/platform.ts` | Platform detection utility | **Review** | May duplicate PC version, consolidate |
| `src/lib/utils.ts` | General utilities | **Review** | May duplicate PC version, consolidate |

### Components

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `src/components/ui/` | UI components | **Review** | May duplicate PC version, consolidate |
| `src/components/resources/` | Resource components | Review | May be shared |

### Other Directories

| Directory | Purpose | Status | Notes |
|-----------|---------|--------|-------|
| `src/hooks/` | Custom React hooks | Review | Check for tablet-only hooks |
| `src/store/` | State management | Review | May be shared or tablet-specific |
| `src/utils/` | Utility functions | Review | Check for duplicates |

### Configuration Files

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `vite.config.ts` | Vite build configuration | **Verify** | Ensure shared module aliases correct |
| `package.json` | Dependencies and scripts | Keep | Verify dependencies |
| `tsconfig.json` | TypeScript configuration | Keep | Standard config |
| `tailwind.config.js` | Tailwind CSS configuration | Keep | Shared styles |

### Tauri Configuration

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `src-tauri/tauri.conf.json` | Tauri Android configuration | Keep | Android-specific config |
| `src-tauri/tauri.android.conf.json` | Android-specific config | Keep | Android build config |
| `src-tauri/Cargo.toml` | Rust dependencies | Keep | Android build |
| `src-tauri/src/` | Rust backend code | Keep | Android Tauri commands |

## Shared Modules (`shared/`)

### API Client (`shared/lesson-api/`)

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `src/index.ts` | **Unified API client** | **Reference** | Already unified, handles platform differences |
| `package.json` | Package configuration | Keep | Shared module |

**Key Features:**
- Automatic platform detection (Android vs Desktop)
- URL resolution (`localhost:8000` vs `10.0.2.2:8000`)
- Local DB support for offline tablets
- Dual-mode operation (HTTP API + local SQLite)

### Browser Components (`shared/lesson-browser/`)

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `src/components/LessonPlanBrowser.tsx` | Main browser container | Keep | Used by both platforms |
| `src/components/WeekView.tsx` | Week grid layout | Keep | Used by both platforms |
| `src/components/DayView.tsx` | Day schedule view | Keep | Used by both platforms |
| `src/components/LessonDetailView.tsx` | Detailed lesson preview | Keep | Used by both platforms |
| `src/components/UserSelector.tsx` | User selection component | Keep | Used by both platforms |
| `src/components/TopNavigationBar.tsx` | Top navigation bar | Keep | Used by both platforms |
| `src/store/useStore.ts` | Zustand store | Keep | Shared state management |
| `src/utils/formatters.ts` | Formatting utilities | Keep | Shared utilities |
| `src/utils/planMatching.ts` | Plan matching logic | Keep | Shared logic |
| `src/utils/scheduleColors.ts` | Schedule color utilities | Keep | Shared utilities |
| `src/utils/scheduleEntries.ts` | Schedule entry utilities | Keep | Shared utilities |
| `src/index.ts` | Module exports | Keep | Entry point |
| `package.json` | Package configuration | Keep | Shared module |

### Lesson Mode Components (`shared/lesson-mode/`)

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `src/components/LessonMode.tsx` | Main lesson mode container | Keep | Used by both platforms |
| `src/components/TimelineSidebar.tsx` | Step timeline with timer | Keep | Used by both platforms |
| `src/components/CurrentStepInstructions.tsx` | Current step display | Keep | Used by both platforms |
| `src/components/ResourceDisplayArea.tsx` | Resource tabs | Keep | Used by both platforms |
| `src/components/TimerDisplay.tsx` | Timer controls | Keep | Used by both platforms |
| `src/components/StepNavigation.tsx` | Step navigation | Keep | Used by both platforms |
| `src/components/StepContentDisplay.tsx` | Step content | Keep | Used by both platforms |
| `src/components/ResourceToolbar.tsx` | Resource toolbar | Keep | Used by both platforms |
| `src/components/TimerAdjustmentDialog.tsx` | Timer adjustment | Keep | Used by both platforms |
| `src/components/resources/` | Resource display components | Keep | Used by both platforms |
| `src/hooks/useLessonTimer.ts` | Timer logic hook | Keep | Shared hook |
| `src/utils/` | Lesson mode utilities | Keep | Shared utilities |
| `src/index.ts` | Module exports | Keep | Entry point |
| `package.json` | Package configuration | Keep | Shared module |

## Build Scripts

### Android Build Scripts

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `lesson-plan-browser/scripts/run-with-ndk.ps1` | **Build entry point** | **Keep unchanged** | Expects `lesson-plan-browser/frontend/` |
| `lesson-plan-browser/scripts/build-android-offline.ps1` | **Main build orchestrator** | **Keep unchanged** | Uses `$frontendDir = Join-Path $repoRoot "frontend"` |
| `lesson-plan-browser/scripts/archive/deprecated-build-scripts/` | Deprecated scripts | **Document** | Index in archive, don't duplicate |

### PC Build Scripts

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `frontend/package.json` scripts | Build commands | Keep | `npm run tauri:dev`, `npm run tauri:build` |

## File Consolidation Opportunities

### Duplicate Files to Consolidate

1. **Platform Detection:**
   - `frontend/src/lib/platform.ts` (more complete)
   - `lesson-plan-browser/frontend/src/lib/platform.ts` (may be duplicate)
   - **Action**: Use PC version, remove tablet duplicate

2. **UI Components:**
   - `frontend/src/components/ui/` (complete set)
   - `lesson-plan-browser/frontend/src/components/ui/` (may be duplicate)
   - **Action**: Consolidate to shared or use PC version

3. **Utilities:**
   - `frontend/src/lib/utils.ts`
   - `lesson-plan-browser/frontend/src/lib/utils.ts`
   - **Action**: Review for duplicates, consolidate

## Files to Create

### New Files for Unified Frontend

| File | Purpose | Location |
|------|---------|----------|
| `usePlatformFeatures.ts` | Feature gating hook | `lesson-plan-browser/frontend/src/hooks/` |
| Platform detection enhancement | Enhanced platform detection | `lesson-plan-browser/frontend/src/lib/platform.ts` (or import from PC) |

## Archive Candidates

### Files to Archive After Unification

| File | Original Location | Archive Location | Reason |
|------|-------------------|------------------|--------|
| `App.tsx` (PC version) | `frontend/src/App.tsx` | `docs/archive/frontend/pc-version/App.tsx.backup` | Superseded by unified version |
| `App.tsx` (tablet version) | `lesson-plan-browser/frontend/src/App.tsx` | `docs/archive/frontend/tablet-version/App.tsx.backup` | Becomes unified version |
| `MobileNav.tsx` | `frontend/src/components/mobile/MobileNav.tsx` | `docs/archive/frontend/pc-version/components/MobileNav.tsx` | Not needed for tablet |
| `MobileNav.test.tsx` | `frontend/src/components/mobile/MobileNav.test.tsx` | `docs/archive/frontend/pc-version/components/MobileNav.test.tsx` | Not needed |
| `FRONTEND_VERSIONS_DOCUMENTATION.md` | Root level | `docs/archive/frontend/documentation/FRONTEND_VERSIONS_DOCUMENTATION.md` | Superseded by unified guide |

## Summary Statistics

- **PC Version Files**: ~50+ files
- **Tablet Version Files**: ~20+ files
- **Shared Modules**: ~30+ files
- **Files to Modify**: ~10 files
- **Files to Create**: ~2 files
- **Files to Archive**: ~5 files
- **Files to Delete**: TBD (after review)

## Next Steps

1. Complete dependency mapping (see `UNIFIED_FRONTEND_DEPENDENCIES.md`)
2. Review duplicate files for consolidation
3. Create backup of key files before modification
4. Begin Phase 2 implementation

---

**Document Status**: Complete - Pre-Implementation  
**Last Updated**: 2025-01-XX  
**Maintainer**: Development Team

