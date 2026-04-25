# Cross-Platform Technology Analysis: Windows 11 & Android 16

## Executive Summary

This document analyzes cross-platform technology options for implementing the Lesson Plan Browser module on **Windows 11 (PC)** and **Android 16 (tablet/phone)**, while maintaining compatibility with the existing codebase architecture (Tauri + React + TypeScript + FastAPI).

> **Reality check (Nov 2025):** The repository only ships a Windows Tauri desktop app (`frontend/` + `src-tauri/`). There is no React Native project, no Capacitor/mobile build, and no shared workspace structure yet. Everything below remains planning guidance.

**Current Stack**:
- **Desktop**: Tauri 2.x + React + TypeScript
- **Backend**: FastAPI (Python) over HTTP/SSE
- **Storage**: SQLite (local-first)
- **Sync**: Planned P2P + Supabase cloud backup

**Target Platforms**:
- Windows 11 (PC) - Primary development platform
- Android 16 (Tablet) - Secondary platform
- Android 16 (Samsung S24 Ultra) - Optional phone support

---

## Table of Contents

1. [Technology Options Evaluation](#technology-options-evaluation)
2. [Recommended Approach](#recommended-approach)
3. [Implementation Strategy](#implementation-strategy)
4. [Code Sharing Architecture](#code-sharing-architecture)
5. [Backend Integration](#backend-integration)
6. [Migration Path](#migration-path)
7. [Performance Considerations](#performance-considerations)
8. [Development Workflow](#development-workflow)

---

## Technology Options Evaluation

### Option 1: Tauri Mobile (Beta/Alpha) ⚠️

**Status**: Tauri Mobile is in **early development/alpha** (as of 2024-2025)

**Pros**:
- ✅ **Code reuse**: Same React + TypeScript frontend
- ✅ **Same architecture**: Tauri commands, same patterns
- ✅ **Small bundle size**: Native performance
- ✅ **Consistent API**: Same Tauri APIs across platforms
- ✅ **FastAPI backend**: Can reuse existing backend

**Cons**:
- ❌ **Not production-ready**: Still in alpha/beta
- ❌ **Limited Android support**: May have gaps
- ❌ **Uncertain timeline**: May not be stable for Android 16
- ❌ **Risk**: Early adoption risks

**Verdict**: ⚠️ **Monitor but not recommended for production yet**

**Resources**:
- Tauri Mobile GitHub: https://github.com/tauri-apps/tauri-mobile
- Status: Check latest release notes for Android support

---

### Option 2: React Native (Recommended) ✅

**Status**: **Mature and stable** (2024-2025)

**Pros**:
- ✅ **Code reuse**: React + TypeScript (similar to current frontend)
- ✅ **Windows support**: React Native for Windows (Microsoft-backed)
- ✅ **Android support**: Native Android support (mature)
- ✅ **Large ecosystem**: Extensive libraries and community
- ✅ **FastAPI integration**: Can use HTTP client to connect to FastAPI backend
- ✅ **Performance**: Native components, good performance
- ✅ **Hot reload**: Fast development iteration

**Cons**:
- ⚠️ **Different from Tauri**: Not the same framework (but similar patterns)
- ⚠️ **Bridge overhead**: JavaScript-to-native bridge (minimal impact)
- ⚠️ **Windows support**: React Native for Windows is separate from main RN

**Windows Support**:
- **React Native for Windows**: Microsoft-maintained fork
- Supports Windows 10/11
- Uses WinUI 3 (native Windows components)
- Status: Stable and actively maintained

**Android Support**:
- Native Android support (mature)
- Supports Android 16 (when released)
- Uses native Android components

**Verdict**: ✅ **RECOMMENDED** - Best balance of code reuse and platform support

**Code Sharing**:
- **Shared**: React components, TypeScript types, business logic
- **Platform-specific**: Navigation, native APIs, platform UI components

---

### Option 3: Flutter

**Status**: **Mature and stable** (2024-2025)

**Pros**:
- ✅ **Windows support**: Official Windows desktop support
- ✅ **Android support**: Native Android support (mature)
- ✅ **Performance**: Compiled to native code (excellent performance)
- ✅ **Single codebase**: One codebase for all platforms
- ✅ **FastAPI integration**: HTTP client for backend communication
- ✅ **Beautiful UI**: Material Design and Cupertino widgets

**Cons**:
- ❌ **Different language**: Dart (not TypeScript/React)
- ❌ **No code reuse**: Would need to rewrite frontend
- ❌ **Learning curve**: Team needs to learn Dart/Flutter
- ❌ **Different ecosystem**: Different libraries and patterns

**Verdict**: ❌ **NOT RECOMMENDED** - Too much code rewrite required

---

### Option 4: Capacitor (Ionic) ⚠️

**Status**: **Mature and stable** (2024-2025)

**Note**: Your `package.json` already includes Capacitor dependencies, suggesting it may have been considered.

**Pros**:
- ✅ **Web-based**: Uses web technologies (HTML/CSS/JS)
- ✅ **React support**: Can use React (your current frontend)
- ✅ **Android support**: Native Android support
- ✅ **FastAPI integration**: HTTP client for backend
- ✅ **Code reuse**: Can reuse React components directly
- ✅ **Already in project**: Capacitor dependencies present

**Cons**:
- ❌ **Windows support**: Limited (primarily web/mobile, not desktop)
- ❌ **Performance**: WebView-based (slower than native)
- ❌ **Not ideal for desktop**: Better suited for mobile/web
- ❌ **Tauri conflict**: Can't use Tauri and Capacitor together (different approaches)

**Windows Support**:
- Capacitor does NOT support Windows desktop
- Would need separate solution for Windows (keep Tauri)

**Verdict**: ⚠️ **PARTIALLY VIABLE** - Good for Android, but Windows still needs Tauri (hybrid approach)

---

### Option 5: Kotlin Multiplatform Mobile (KMM) + Compose Multiplatform

**Status**: **Mature and growing** (2024-2025)

**Pros**:
- ✅ **Windows support**: Compose Multiplatform supports Windows
- ✅ **Android support**: Native Android (Kotlin is Android's language)
- ✅ **Performance**: Native performance
- ✅ **FastAPI integration**: Kotlin HTTP client (Ktor, OkHttp)
- ✅ **Shared business logic**: Can share Kotlin code between platforms

**Cons**:
- ❌ **Different language**: Kotlin (not TypeScript/React)
- ❌ **No code reuse**: Would need to rewrite frontend
- ❌ **Learning curve**: Team needs to learn Kotlin/Compose
- ❌ **Different UI framework**: Compose (not React)

**Verdict**: ❌ **NOT RECOMMENDED** - Too much code rewrite required

---

### Option 6: Hybrid Approach A - Tauri + React Native (Recommended) ✅

**Strategy**: **Different implementations for different platforms**

- **Windows 11 (PC)**: Keep existing **Tauri + React + TypeScript**
- **Android 16 (Tablet/Phone)**: Use **React Native + TypeScript**

**Pros**:
- ✅ **Optimal for each platform**: Best tool for each platform
- ✅ **Code sharing**: Share React components, TypeScript types, business logic
- ✅ **FastAPI backend**: Both platforms connect to same FastAPI backend
- ✅ **Proven technologies**: Both Tauri and React Native are mature
- ✅ **No compromise**: Don't force one solution on both platforms
- ✅ **Native performance**: Both use native components

**Cons**:
- ⚠️ **Two codebases**: Need to maintain two frontend projects
- ⚠️ **Platform-specific code**: Some platform-specific implementations needed

**Code Sharing Strategy**:
- **Shared**: TypeScript types, business logic, API clients, utilities
- **Platform-specific**: UI components, navigation, native features

**Verdict**: ✅ **RECOMMENDED** - Best approach for native performance

---

### Option 7: Hybrid Approach B - Tauri + Capacitor (Alternative) ⚠️

**Strategy**: **Use existing Capacitor setup for Android**

- **Windows 11 (PC)**: Keep existing **Tauri + React + TypeScript**
- **Android 16 (Tablet/Phone)**: Use **Capacitor + React + TypeScript** (reuse existing frontend)

**Pros**:
- ✅ **Maximum code reuse**: Same React components for both platforms
- ✅ **Already in project**: Capacitor dependencies present
- ✅ **FastAPI backend**: Both platforms connect to same FastAPI backend
- ✅ **Single frontend codebase**: One React codebase for both platforms

**Cons**:
- ⚠️ **WebView performance**: Capacitor uses WebView (slower than native)
- ⚠️ **Limited native features**: Less access to native Android APIs
- ⚠️ **Two build systems**: Tauri (Rust) + Capacitor (native Android)
- ⚠️ **Platform-specific code**: Still need platform-specific implementations

**Code Sharing Strategy**:
- **Shared**: Entire React frontend (components, logic, types)
- **Platform-specific**: Build configuration, native plugins

**Verdict**: ⚠️ **ALTERNATIVE** - Good for rapid development, but React Native offers better performance

---

## Recommended Approach: Hybrid Strategy (Two Options)

### Option A: Tauri + React Native (Recommended for Performance) ✅

**Best for**: Maximum native performance and platform optimization

### Option B: Tauri + Capacitor (Recommended for Speed) ⚠️

**Best for**: Maximum code reuse and rapid development (if performance is acceptable)

### Architecture Overview - Option A (Tauri + React Native)

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python)                  │
│  - REST APIs                                                │
│  - SSE (Server-Sent Events)                                 │
│  - SQLite database                                          │
│  - Lesson plan processing                                   │
│  - Vocabulary management                                    │
│  - Game generation                                          │
└───────────────┬───────────────────────────────┬─────────────┘
                │                               │
                │ HTTP/SSE                      │ HTTP/SSE
                │                               │
    ┌───────────▼───────────┐      ┌───────────▼───────────┐
    │  Windows 11 (PC)      │      │  Android 16 (Tablet)  │
    │                       │      │                       │
    │  Tauri 2.x            │      │  React Native         │
    │  + React              │      │  + React              │
    │  + TypeScript         │      │  + TypeScript         │
    │                       │      │                       │
    │  Native Windows UI    │      │  Native Android UI    │
    │  SQLite (local)       │      │  SQLite (local)       │
    │  P2P Sync             │      │  P2P Sync             │
    └───────────────────────┘      └───────────────────────┘
                │                               │
                └───────────┬───────────────────┘
                            │
                    ┌───────▼────────┐
                    │  Shared Code   │
                    │  - Types       │
                    │  - API Client  │
                    │  - Business    │
                    │    Logic       │
                    │  - Utils       │
                    └────────────────┘
```

### Architecture Overview - Option B (Tauri + Capacitor)

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python)                  │
│  - REST APIs                                                │
│  - SSE (Server-Sent Events)                                 │
│  - SQLite database                                          │
│  - Lesson plan processing                                   │
│  - Vocabulary management                                    │
│  - Game generation                                          │
└───────────────┬───────────────────────────────┬─────────────┘
                │                               │
                │ HTTP/SSE                      │ HTTP/SSE
                │                               │
    ┌───────────▼───────────┐      ┌───────────▼───────────┐
    │  Windows 11 (PC)      │      │  Android 16 (Tablet)  │
    │                       │      │                       │
    │  Tauri 2.x            │      │  Capacitor            │
    │  + React              │      │  + React (SAME)       │
    │  + TypeScript         │      │  + TypeScript (SAME)  │
    │                       │      │                       │
    │  Native Windows UI    │      │  WebView (Android)    │
    │  SQLite (local)       │      │  SQLite (local)       │
    │  P2P Sync             │      │  P2P Sync             │
    └───────────────────────┘      └───────────────────────┘
                │                               │
                └───────────┬───────────────────┘
                            │
                    ┌───────▼────────┐
                    │  Shared Code   │
                    │  - ENTIRE      │
                    │    React App   │
                    │  - Components  │
                    │  - Types       │
                    │  - Logic       │
                    └────────────────┘
```

### Code Organization - Option A (Tauri + React Native)

```
project-root/
├── backend/                    # FastAPI backend (shared)
│   ├── api/
│   ├── services/
│   ├── database.py
│   └── ...
│
├── frontend/                   # Windows (Tauri)
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── services/          # API clients
│   │   ├── types/             # TypeScript types
│   │   └── ...
│   └── src-tauri/
│
├── mobile/                     # Android (React Native)
│   ├── src/
│   │   ├── components/        # React Native components
│   │   ├── services/          # API clients (shared)
│   │   ├── types/             # TypeScript types (shared)
│   │   ├── navigation/        # React Navigation
│   │   └── ...
│   └── android/
│
└── shared/                     # Shared code
    ├── types/                  # TypeScript types
    ├── api-client/             # FastAPI client
    ├── business-logic/         # Shared business logic
    └── utils/                  # Shared utilities
```

### Code Organization - Option B (Tauri + Capacitor)

```
project-root/
├── backend/                    # FastAPI backend (shared)
│   ├── api/
│   ├── services/
│   ├── database.py
│   └── ...
│
├── frontend/                   # Shared React App
│   ├── src/
│   │   ├── components/        # React components (shared)
│   │   ├── services/          # API clients (shared)
│   │   ├── types/             # TypeScript types (shared)
│   │   ├── platforms/         # Platform-specific code
│   │   │   ├── tauri/         # Tauri-specific
│   │   │   └── capacitor/     # Capacitor-specific
│   │   └── ...
│   ├── src-tauri/             # Tauri build (Windows)
│   └── capacitor.config.json  # Capacitor config (Android)
│
└── mobile/                     # Android (Capacitor)
    └── android/                # Native Android project
```

---

## Implementation Strategy

### Phase 1: Shared Code Foundation

**Goal**: Create shared codebase for types, API clients, and business logic.

**Tasks**:
- [ ] Create `shared/` directory structure
- [ ] Extract TypeScript types to `shared/types/`
- [ ] Create FastAPI client in `shared/api-client/`
- [ ] Extract business logic to `shared/business-logic/`
- [ ] Set up shared package (npm/yarn workspace or monorepo)

**Benefits**:
- Single source of truth for types
- Consistent API communication
- Shared business logic (no duplication)

### Phase 2: React Native Android App

**Goal**: Create React Native app for Android that uses shared code.

**Tasks**:
- [ ] Initialize React Native project
- [ ] Set up TypeScript
- [ ] Integrate shared code (types, API client, business logic)
- [ ] Create platform-specific UI components
- [ ] Implement navigation (React Navigation)
- [ ] Connect to FastAPI backend
- [ ] Implement local SQLite storage
- [ ] Test on Android tablet and phone

**Technology Stack**:
- **Framework**: React Native 0.74+ (latest stable)
- **Language**: TypeScript
- **Navigation**: React Navigation 6.x
- **State Management**: Zustand or Redux Toolkit
- **HTTP Client**: Axios or Fetch (for FastAPI)
- **Local Storage**: React Native SQLite (react-native-sqlite-storage or expo-sqlite)
- **UI Components**: React Native Paper or NativeBase

### Phase 3: Feature Parity

**Goal**: Implement all browser module features on both platforms.

**Tasks**:
- [ ] Schedule management (create, edit, view)
- [ ] Time-based current lesson display
- [ ] Schedule order navigation
- [ ] Multiple navigation modes
- [ ] Filtering system
- [ ] Lesson plan display
- [ ] Objectives printing (PDF on mobile)

**Platform-Specific Considerations**:
- **Windows**: Use Tauri's native file dialogs, print to DOCX
- **Android**: Use React Native file system, print to PDF or share

### Phase 4: Sync Integration

**Goal**: Implement P2P sync on both platforms.

**Tasks**:
- [ ] Implement P2P sync on Windows (Tauri)
- [ ] Implement P2P sync on Android (React Native)
- [ ] Test cross-platform sync (Windows ↔ Android)
- [ ] Implement Supabase cloud backup on both platforms

---

## Code Sharing Architecture

### Shared Types

**Location**: `shared/types/`

```typescript
// shared/types/schedule.ts
export interface ScheduleEntry {
  id: string;
  user_id: string;
  day_of_week: 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday';
  start_time: string;  // "13:06"
  end_time: string;    // "13:47"
  subject: string;
  grade: string;
  slot_number: number;
  homeroom?: string;
  is_active: boolean;
}

// shared/types/lesson-plan.ts
export interface LessonPlan {
  id: string;
  week_of: string;
  metadata: LessonPlanMetadata;
  days: Record<string, DayPlan>;
}

// shared/types/api.ts
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}
```

### Shared API Client

**Location**: `shared/api-client/`

```typescript
// shared/api-client/fastapi-client.ts
import axios from 'axios';
import type { ScheduleEntry, LessonPlan } from '../types';

export class FastAPIClient {
  private baseURL: string;
  
  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }
  
  async getCurrentLesson(userId: string): Promise<ScheduleEntry | null> {
    const response = await axios.get(`${this.baseURL}/api/schedules/${userId}/current`);
    return response.data.entry;
  }
  
  async getLessonPlan(planId: string): Promise<LessonPlan> {
    const response = await axios.get(`${this.baseURL}/api/plans/${planId}`);
    return response.data;
  }
  
  // ... more API methods
}
```

### Shared Business Logic

**Location**: `shared/business-logic/`

```typescript
// shared/business-logic/schedule-utils.ts
export function getCurrentLesson(
  entries: ScheduleEntry[],
  currentTime: Date
): ScheduleEntry | null {
  const dayOfWeek = currentTime.toLocaleDateString('en-US', { weekday: 'lowercase' });
  const timeStr = currentTime.toTimeString().slice(0, 5); // "HH:MM"
  
  return entries.find(entry => 
    entry.day_of_week === dayOfWeek &&
    entry.start_time <= timeStr &&
    entry.end_time >= timeStr
  ) || null;
}

export function getNextLesson(
  entries: ScheduleEntry[],
  currentEntry: ScheduleEntry
): ScheduleEntry | null {
  // Implementation
}
```

### Platform-Specific Implementations

**Windows (Tauri)**:
```typescript
// frontend/src/services/schedule-service.ts
import { FastAPIClient } from '../../../shared/api-client/fastapi-client';
import { invoke } from '@tauri-apps/api/core';

export class ScheduleService extends FastAPIClient {
  // Tauri-specific implementations
  async saveScheduleLocally(schedule: ScheduleEntry[]) {
    return invoke('save_schedule', { schedule });
  }
}
```

**Android (React Native)**:
```typescript
// mobile/src/services/schedule-service.ts
import { FastAPIClient } from '../../../shared/api-client/fastapi-client';
import SQLite from 'react-native-sqlite-storage';

export class ScheduleService extends FastAPIClient {
  // React Native-specific implementations
  async saveScheduleLocally(schedule: ScheduleEntry[]) {
    // Use React Native SQLite
    const db = await SQLite.openDatabase({ name: 'lesson_plans.db' });
    // Save to local database
  }
}
```

---

## Backend Integration

### FastAPI Backend (Shared)

**Both platforms connect to the same FastAPI backend**:

```python
# backend/api/schedules.py
from fastapi import APIRouter, HTTPException
from backend.database import get_db
from backend.services.schedule_service import ScheduleService

router = APIRouter(prefix="/api/schedules", tags=["schedules"])

@router.get("/{user_id}/current")
async def get_current_lesson(user_id: str):
    """Get current lesson for user based on current time."""
    service = ScheduleService()
    current_lesson = await service.get_current_lesson(user_id)
    
    if not current_lesson:
        raise HTTPException(status_code=404, detail="No current lesson")
    
    # Get lesson plan
    lesson_plan = await service.get_lesson_plan_for_entry(current_lesson.id)
    
    return {
        "entry": current_lesson,
        "lesson_plan": lesson_plan,
        "time_remaining": service.get_time_remaining(current_lesson)
    }
```

### Connection Strategy

**Windows (Tauri)**:
- FastAPI runs locally on `http://localhost:8000`
- Tauri app connects via HTTP/SSE
- Can use Tauri's HTTP client or Fetch API

**Android (React Native)**:
- **Option A**: FastAPI runs on PC, Android connects via local network (WiFi)
  - PC IP: `http://192.168.1.100:8000`
  - Requires same WiFi network
- **Option B**: FastAPI runs on cloud/server
  - Deploy FastAPI to cloud (AWS, Azure, etc.)
  - Android connects via internet
- **Option C**: FastAPI runs on Android device (future)
  - Use Termux or similar to run Python on Android
  - More complex, not recommended initially

**Recommended**: **Option A** (local network) for initial implementation, with Option B (cloud) as future enhancement.

---

## Migration Path

### Step 1: Extract Shared Code (Week 1)

1. Create `shared/` directory
2. Move TypeScript types to `shared/types/`
3. Create FastAPI client in `shared/api-client/`
4. Extract business logic to `shared/business-logic/`
5. Update Windows app to use shared code

### Step 2: Create React Native App (Week 2-3)

1. Initialize React Native project
2. Set up TypeScript and shared code integration
3. Create basic navigation structure
4. Implement schedule management UI
5. Connect to FastAPI backend (local network)

### Step 3: Implement Browser Module (Week 3-4)

1. Implement time-based current lesson display
2. Implement schedule order navigation
3. Implement filtering system
4. Implement multiple navigation modes
5. Test on Android tablet and phone

### Step 4: Feature Parity (Week 4-5)

1. Ensure all features work on both platforms
2. Platform-specific optimizations
3. UI/UX polish
4. Performance optimization

### Step 5: Sync Integration (Week 5-6)

1. Implement P2P sync on Android
2. Test cross-platform sync
3. Implement Supabase cloud backup on Android

---

## Performance Considerations

### Windows (Tauri)

**Advantages**:
- Native performance (Rust backend)
- Small bundle size
- Fast startup time
- Direct file system access

**Optimizations**:
- Use Tauri's native APIs for file operations
- Cache lesson plans locally
- Use SQLite for fast queries

### Android (React Native)

**Advantages**:
- Native components (good performance)
- Hot reload for fast development
- Large ecosystem

**Optimizations**:
- Use React Native's native modules for SQLite
- Implement proper caching
- Use FlatList for large lists
- Optimize images and assets

**Performance Targets**:
- Navigation: < 100ms
- Lesson plan load: < 500ms
- Filter application: < 200ms
- Sync: < 2s for typical week

---

## Development Workflow

### Monorepo Structure (Recommended)

```
project-root/
├── package.json              # Root package.json (workspaces)
├── pnpm-workspace.yaml       # or yarn workspaces
│
├── backend/                  # FastAPI backend
│   ├── pyproject.toml
│   └── ...
│
├── frontend/                 # Windows (Tauri)
│   ├── package.json
│   └── ...
│
├── mobile/                   # Android (React Native)
│   ├── package.json
│   └── ...
│
└── shared/                   # Shared code
    ├── package.json
    └── ...
```

### Development Setup

**Windows Development**:
```bash
# Terminal 1: FastAPI backend
cd backend
uvicorn main:app --reload

# Terminal 2: Tauri frontend
cd frontend
npm run tauri dev
```

**Android Development**:
```bash
# Terminal 1: FastAPI backend (same as Windows)
cd backend
uvicorn main:app --host 0.0.0.0 --reload  # Allow network access

# Terminal 2: React Native
cd mobile
npm start

# Terminal 3: Android emulator or device
npm run android
```

### Testing Strategy

**Shared Code**:
- Unit tests for business logic
- Type checking (TypeScript)
- API client tests (mock FastAPI)

**Platform-Specific**:
- **Windows**: Tauri integration tests, E2E tests
- **Android**: React Native component tests, E2E tests (Detox)

**Cross-Platform**:
- Test same features on both platforms
- Ensure consistent behavior
- Test sync between platforms

---

## Technology Stack Summary

### Recommended Stack

| Component | Windows 11 | Android 16 | Shared |
|-----------|-----------|------------|--------|
| **Framework** | Tauri 2.x | React Native 0.74+ | - |
| **UI** | React + TypeScript | React Native + TypeScript | React components (shared) |
| **Language** | TypeScript | TypeScript | TypeScript |
| **Backend** | FastAPI (local) | FastAPI (network) | FastAPI (Python) |
| **Database** | SQLite (local) | SQLite (local) | SQLite |
| **Sync** | P2P + Supabase | P2P + Supabase | Same protocol |
| **Navigation** | React Router | React Navigation | - |
| **State** | Zustand/Redux | Zustand/Redux | Shared stores |
| **HTTP Client** | Axios/Fetch | Axios/Fetch | Shared client |

### Key Libraries

**Shared**:
- `axios` - HTTP client
- `zod` or `yup` - Schema validation
- `date-fns` - Date utilities

**Windows (Tauri)**:
- `@tauri-apps/api` - Tauri APIs
- `react-router-dom` - Navigation
- `zustand` - State management

**Android (React Native)**:
- `react-navigation` - Navigation
- `react-native-sqlite-storage` - Local database
- `@react-native-async-storage/async-storage` - Key-value storage
- `react-native-paper` or `native-base` - UI components
- `zustand` - State management

---

## Advantages of Recommended Approach

### 1. Code Reuse
- ✅ **70-80% code reuse**: Types, API client, business logic
- ✅ **Shared components**: React components can be adapted for React Native
- ✅ **Single source of truth**: Types and business logic in one place

### 2. Platform Optimization
- ✅ **Native performance**: Each platform uses native components
- ✅ **Platform-specific features**: Can leverage platform-specific APIs
- ✅ **Best UX**: Native look and feel on each platform

### 3. Development Efficiency
- ✅ **Familiar technologies**: React + TypeScript (team already knows)
- ✅ **Fast iteration**: Hot reload on both platforms
- ✅ **Shared backend**: One FastAPI backend for both platforms

### 4. Future-Proof
- ✅ **Tauri Mobile**: Can migrate to Tauri Mobile when stable
- ✅ **Scalable**: Can add iOS support later (React Native supports iOS)
- ✅ **Flexible**: Can optimize each platform independently

---

## Implementation Timeline

### Phase 1: Foundation (2 weeks)
- Extract shared code
- Set up React Native project
- Basic navigation and UI

### Phase 2: Core Features (3 weeks)
- Schedule management
- Time-based display
- Navigation modes
- Filtering

### Phase 3: Integration (2 weeks)
- FastAPI backend integration
- Local storage
- Sync implementation

### Phase 4: Polish (1 week)
- UI/UX improvements
- Performance optimization
- Testing

**Total**: ~8 weeks for initial implementation

---

## Risks and Mitigations

### Risk 1: Code Duplication
**Mitigation**: 
- Extract shared code early
- Use monorepo with shared packages
- Regular code reviews to prevent duplication

### Risk 2: Platform-Specific Bugs
**Mitigation**:
- Comprehensive testing on both platforms
- Platform-specific test suites
- Continuous integration for both platforms

### Risk 3: Backend Connection (Android)
**Mitigation**:
- Start with local network (WiFi)
- Plan for cloud deployment (future)
- Implement robust error handling and retry logic

### Risk 4: Performance on Android
**Mitigation**:
- Use React Native best practices
- Optimize images and assets
- Implement proper caching
- Performance testing on real devices

---

## Next Steps

1. **Review and approve** this technology analysis
2. **Set up monorepo** structure with shared code
3. **Extract shared code** from existing Windows app
4. **Initialize React Native** project
5. **Create proof of concept** (basic schedule display on Android)
6. **Iterate and refine** based on testing

---

## References

- [Tauri Mobile](https://github.com/tauri-apps/tauri-mobile) - Check latest status
- [React Native](https://reactnative.dev/) - Official documentation
- [React Native for Windows](https://microsoft.github.io/react-native-windows/) - Windows support
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React Navigation](https://reactnavigation.org/) - Navigation library
- [Zustand](https://github.com/pmndrs/zustand) - State management

---

## Conclusion

### Recommended Approach: **Option A - Tauri + React Native** ✅

**For**: Maximum native performance and platform optimization

- **Windows 11**: Keep Tauri + React + TypeScript (existing)
- **Android 16**: Use React Native + TypeScript (new)
- **Shared**: Types, API client, business logic (70-80% code reuse)
- **Backend**: FastAPI (shared, local network for Android initially)

**Benefits**:
- ✅ Native performance on both platforms
- ✅ Platform-optimized UI/UX
- ✅ Familiar technologies (React + TypeScript)
- ✅ Future-proof (can migrate to Tauri Mobile when stable)
- ✅ Scalable (can add iOS later)

### Alternative Approach: **Option B - Tauri + Capacitor** ⚠️

**For**: Maximum code reuse and rapid development (if performance acceptable)

- **Windows 11**: Keep Tauri + React + TypeScript (existing)
- **Android 16**: Use Capacitor + React + TypeScript (reuse existing frontend)
- **Shared**: Entire React frontend (90%+ code reuse)
- **Backend**: FastAPI (shared, local network for Android initially)

**Benefits**:
- ✅ Maximum code reuse (same React components)
- ✅ Faster development (one frontend codebase)
- ✅ Already has Capacitor dependencies
- ⚠️ WebView performance (acceptable for most use cases)
- ⚠️ Less native Android features

### Final Recommendation

**Choose Option A (React Native)** if:
- Performance is critical
- You want native Android features
- You're willing to maintain two frontend codebases
- You want best-in-class mobile experience

**Choose Option B (Capacitor)** if:
- You want fastest development time
- Performance is acceptable (WebView is fine)
- You want maximum code reuse
- You already have Capacitor setup

**My Recommendation**: **Start with Option B (Capacitor)** for rapid prototyping, then evaluate if React Native is needed based on performance requirements.

