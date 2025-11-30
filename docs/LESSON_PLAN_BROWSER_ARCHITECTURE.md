# Lesson Plan Browser - Standalone Architecture

## Overview

The Android tablet app must work **completely independently** with local storage. It does NOT connect to the PC backend for daily use - it only connects temporarily during sync operations.

## Architecture Requirements

### Android Tablet App (Production)

**Local Storage:**
- **Own embedded SQLite database** - Stores lesson plans, schedules, users, slots, lesson mode sessions
- **Own JSON file storage** - Stores lesson plan JSON files locally on tablet
- **Completely offline** - Works without network connection after initial sync

**Data Access:**
- Browser reads from **local database** (not PC backend)
- Browser reads from **local JSON files** (not PC file system)
- Lesson Mode sessions stored in **local database** (not PC backend)

### Sync Mechanism (Updates from PC)

**Purpose:** Transfer new/updated lesson plans from PC to tablet's local storage

**WiFi Sync (Primary):**
1. Teacher adds/updates lesson plans on PC
2. Tablet connects to PC backend via WiFi (temporary connection for sync only)
3. Tablet app fetches new/updated data from PC backend API
4. Tablet saves data to local database and JSON files
5. After sync completes: Tablet disconnects, works offline using local data

**USB Sync (Fallback):**
1. Teacher adds/updates lesson plans on PC
2. Export database and JSON files from PC
3. Transfer files to tablet via USB (ADB or file transfer mode)
4. Import files to tablet's local storage
5. After import: Tablet works offline using local data

**Key Point:** Sync is ONE-WAY (PC → Tablet). After sync, tablet works independently.

### PC Version (Development Only)

The PC version can connect to backend for development/testing convenience, but the Android version MUST use standalone architecture.

## Implementation Requirements for Plan

The execution plan must include:

1. **Local Database Implementation (Android)** - Essential, not optional
   - Embedded SQLite via Tauri commands
   - Read lesson plans from local database
   - Store lesson mode sessions locally

2. **Local JSON File Storage (Android)** - Essential, not optional
   - Store JSON files locally on tablet
   - Read from local file system

3. **Sync Mechanism** - Essential for receiving updates from PC
   - WiFi sync: Connect to PC backend → Fetch → Save locally
   - USB sync: Transfer files → Import to local storage

4. **Mode Detection**
   - PC version: Use HTTP backend (localhost:8000) for development
   - Android version: Use local database (standalone mode)

## Data Flow

### Normal Operation (After Sync)

```
Tablet App (Offline)
  ↓ reads from
Local Database (SQLite)
  + 
Local JSON Files
  ↓ displays
Browser / Lesson Mode UI
```

### Sync Operation (Getting Updates from PC)

**WiFi Sync:**
```
PC Backend (localhost:8000)
  ↓ tablet connects via WiFi
Tablet App (Sync Mode)
  ↓ fetches new/updated data
PC Backend API
  ↓ saves to
Tablet Local Database + JSON Files
  ↓ disconnect
Tablet App (Offline Mode) - uses local data
```

**USB Sync:**
```
PC Database + JSON Files
  ↓ copy via USB
Tablet Local Storage
  ↓ import
Tablet Local Database + JSON Files
  ↓ ready
Tablet App (Offline Mode) - uses local data
```

## Critical Success Criteria

For Android version to be considered complete:

- [ ] Tablet has embedded local SQLite database
- [ ] Tablet stores JSON files locally
- [ ] App works completely offline (no network required)
- [ ] Browser reads from local database (not PC backend)
- [ ] Browser reads from local JSON files (not PC files)
- [ ] WiFi sync works: Fetch from PC → Save locally
- [ ] USB sync works: Transfer files → Import locally
- [ ] After sync, new lesson plans appear in tablet app
- [ ] Updates to existing plans appear after sync

