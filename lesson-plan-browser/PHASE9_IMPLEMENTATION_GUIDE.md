# Phase 9: Standalone Architecture Implementation Guide

## Overview

Phase 9 implements the standalone architecture required for Android tablets to work independently offline. The tablet must store lesson plans locally and sync updates from the PC.

## Current Status

✅ **Already Implemented:**
- Tauri database commands (`sql_query`, `sql_execute`) in Rust
- Database migrations (all 6 tables including lesson_steps and lesson_mode_sessions)
- `isStandaloneMode()` detection function
- `queryLocalDatabase()` and `executeLocalDatabase()` helpers
- Partial userApi.list() implementation for standalone mode

⏳ **Still Needed:**
- Complete all API endpoint routing to local database in standalone mode
- Local JSON file storage implementation
- Sync mechanism (WiFi + USB)
- Row transformation functions for all data types

---

## 9.1 Local Database Implementation

### Helper Functions Needed

Create transformation functions (similar to `rowToUser`):

```typescript
// Already exists: rowToUser()
// Need to create:

function rowToWeeklyPlan(row: Record<string, any>): WeeklyPlan {
  return {
    id: row.id,
    user_id: row.user_id,
    week_of: row.week_of,
    generated_at: row.generated_at,
    output_file: row.output_file || undefined,
    status: row.status,
    error_message: row.error_message || undefined,
  };
}

function rowToScheduleEntry(row: Record<string, any>): ScheduleEntry {
  return {
    id: row.id,
    user_id: row.user_id,
    day_of_week: row.day_of_week,
    start_time: row.start_time,
    end_time: row.end_time,
    subject: row.subject,
    homeroom: row.homeroom,
    grade: row.grade,
    slot_number: row.slot_number,
    plan_slot_group_id: row.plan_slot_group_id,
    week_of: row.week_of || undefined,
    is_active: row.is_active === 1 || row.is_active === true,
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

function rowToClassSlot(row: Record<string, any>): ClassSlot {
  const name = row.primary_teacher_name || 
    `${row.primary_teacher_first_name || ''} ${row.primary_teacher_last_name || ''}`.trim() || 
    undefined;
  
  return {
    id: row.id,
    user_id: row.user_id,
    slot_number: row.slot_number,
    subject: row.subject,
    grade: row.grade,
    homeroom: row.homeroom || undefined,
    plan_group_label: row.plan_group_label || undefined,
    proficiency_levels: row.proficiency_levels || undefined,
    primary_teacher_name: name,
    primary_teacher_first_name: row.primary_teacher_first_name || undefined,
    primary_teacher_last_name: row.primary_teacher_last_name || undefined,
    primary_teacher_file_pattern: row.primary_teacher_file_pattern || undefined,
    display_order: row.display_order || undefined,
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

function rowToLessonStep(row: Record<string, any>): LessonStep {
  return {
    id: row.id,
    lesson_plan_id: row.lesson_plan_id,
    day_of_week: row.day_of_week,
    slot_number: row.slot_number,
    step_number: row.step_number,
    step_name: row.step_name,
    duration_minutes: row.duration_minutes,
    start_time_offset: row.start_time_offset,
    content_type: row.content_type,
    display_content: row.display_content,
    hidden_content: row.hidden_content ? JSON.parse(row.hidden_content) : undefined,
    sentence_frames: row.sentence_frames ? JSON.parse(row.sentence_frames) : undefined,
    materials_needed: row.materials_needed ? JSON.parse(row.materials_needed) : undefined,
    vocabulary_cognates: row.vocabulary_cognates ? JSON.parse(row.vocabulary_cognates) : undefined,
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

function rowToLessonModeSession(row: Record<string, any>): LessonModeSession {
  return {
    id: row.id,
    user_id: row.user_id,
    lesson_plan_id: row.lesson_plan_id,
    schedule_entry_id: row.schedule_entry_id || undefined,
    day_of_week: row.day_of_week,
    slot_number: row.slot_number,
    current_step_index: row.current_step_index,
    remaining_time: row.remaining_time,
    is_running: row.is_running === 1 || row.is_running === true,
    is_paused: row.is_paused === 1 || row.is_paused === true,
    is_synced: row.is_synced === 1 || row.is_synced === true,
    timer_start_time: row.timer_start_time || undefined,
    paused_at: row.paused_at || undefined,
    adjusted_durations: row.adjusted_durations ? JSON.parse(row.adjusted_durations) : undefined,
    session_start_time: row.session_start_time,
    last_updated: row.last_updated,
    ended_at: row.ended_at || undefined,
  };
}
```

### API Endpoints to Implement

#### planApi.list() - Standalone Mode
```typescript
if (isStandaloneMode()) {
  const rows = await queryLocalDatabase<Record<string, any>>(
    `SELECT id, user_id, week_of, generated_at, output_file, status, error_message 
     FROM weekly_plans 
     WHERE user_id = ? 
     ORDER BY generated_at DESC 
     LIMIT ?`,
    [userId, limit]
  );
  return { data: rows.map(rowToWeeklyPlan) };
}
```

#### planApi.getPlanDetail() - Standalone Mode
```typescript
if (isStandaloneMode()) {
  const rows = await queryLocalDatabase<Record<string, any>>(
    `SELECT id, user_id, week_of, lesson_json, status, generated_at, output_file 
     FROM weekly_plans 
     WHERE id = ?`,
    [planId]
  );
  if (rows.length === 0) {
    throw new Error('Plan not found');
  }
  const row = rows[0];
  return {
    data: {
      id: row.id,
      user_id: row.user_id,
      week_of: row.week_of,
      lesson_json: row.lesson_json ? JSON.parse(row.lesson_json) : null,
      status: row.status,
      generated_at: row.generated_at,
      output_file: row.output_file || undefined,
    }
  };
}
```

#### scheduleApi.getSchedule() - Standalone Mode
```typescript
if (isStandaloneMode()) {
  let sql = `SELECT * FROM schedules WHERE user_id = ?`;
  const params: any[] = [userId];
  
  if (dayOfWeek) {
    sql += ` AND day_of_week = ?`;
    params.push(dayOfWeek);
  }
  if (homeroom) {
    sql += ` AND homeroom = ?`;
    params.push(homeroom);
  }
  if (grade) {
    sql += ` AND grade = ?`;
    params.push(grade);
  }
  
  const rows = await queryLocalDatabase<Record<string, any>>(sql, params);
  return rows.map(rowToScheduleEntry);
}
```

#### slotApi.list() - Standalone Mode
```typescript
if (isStandaloneMode()) {
  const rows = await queryLocalDatabase<Record<string, any>>(
    `SELECT * FROM class_slots WHERE user_id = ? ORDER BY display_order, slot_number`,
    [userId]
  );
  return { data: rows.map(rowToClassSlot) };
}
```

#### lessonApi.getLessonSteps() - Standalone Mode
```typescript
if (isStandaloneMode()) {
  const rows = await queryLocalDatabase<Record<string, any>>(
    `SELECT * FROM lesson_steps 
     WHERE lesson_plan_id = ? AND day_of_week = ? AND slot_number = ? 
     ORDER BY step_number`,
    [planId, day, slot]
  );
  return { data: rows.map(rowToLessonStep) };
}
```

#### lessonModeSessionApi.getActive() - Standalone Mode
```typescript
if (isStandaloneMode()) {
  let sql = `SELECT * FROM lesson_mode_sessions WHERE user_id = ? AND ended_at IS NULL`;
  const params: any[] = [userId];
  
  if (options?.lesson_plan_id) {
    sql += ` AND lesson_plan_id = ?`;
    params.push(options.lesson_plan_id);
  }
  if (options?.day_of_week) {
    sql += ` AND day_of_week = ?`;
    params.push(options.day_of_week);
  }
  if (options?.slot_number !== undefined) {
    sql += ` AND slot_number = ?`;
    params.push(options.slot_number);
  }
  
  sql += ` ORDER BY session_start_time DESC LIMIT 1`;
  
  const rows = await queryLocalDatabase<Record<string, any>>(sql, params);
  if (rows.length === 0) {
    return { data: null };
  }
  return { data: rowToLessonModeSession(rows[0]) };
}
```

#### lessonModeSessionApi.create() - Standalone Mode
```typescript
if (isStandaloneMode()) {
  const result = await executeLocalDatabase(
    `INSERT INTO lesson_mode_sessions 
     (user_id, lesson_plan_id, schedule_entry_id, day_of_week, slot_number, 
      current_step_index, remaining_time, is_running, is_paused, is_synced,
      timer_start_time, paused_at, adjusted_durations, session_start_time, last_updated)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    [
      sessionData.user_id,
      sessionData.lesson_plan_id,
      sessionData.schedule_entry_id || null,
      sessionData.day_of_week,
      sessionData.slot_number,
      sessionData.current_step_index || 0,
      sessionData.remaining_time || 0,
      sessionData.is_running ? 1 : 0,
      sessionData.is_paused ? 1 : 0,
      sessionData.is_synced ? 1 : 0,
      sessionData.timer_start_time || null,
      sessionData.paused_at || null,
      sessionData.adjusted_durations ? JSON.stringify(sessionData.adjusted_durations) : null,
      new Date().toISOString(),
      new Date().toISOString(),
    ]
  );
  
  // Fetch created session
  const rows = await queryLocalDatabase<Record<string, any>>(
    `SELECT * FROM lesson_mode_sessions WHERE id = ?`,
    [result.last_insert_id.toString()]
  );
  
  return { data: rowToLessonModeSession(rows[0]) };
}
```

#### lessonModeSessionApi.update() - Standalone Mode
Similar pattern - use executeLocalDatabase for UPDATE statements.

#### lessonModeSessionApi.end() - Standalone Mode
```typescript
if (isStandaloneMode()) {
  await executeLocalDatabase(
    `UPDATE lesson_mode_sessions 
     SET ended_at = ?, last_updated = ? 
     WHERE id = ?`,
    [new Date().toISOString(), new Date().toISOString(), sessionId]
  );
  return { data: { success: true, message: 'Session ended' } };
}
```

---

## 9.2 Local JSON File Storage

### Tauri File System Commands Needed

Add to Rust backend (`src-tauri/src/db_commands.rs` or new file):

```rust
#[tauri::command]
async fn read_json_file(path: String) -> Result<String, String> {
    // Read JSON file from local storage
    // Use app data directory for Android
}

#[tauri::command]
async fn write_json_file(path: String, content: String) -> Result<(), String> {
    // Write JSON file to local storage
}

#[tauri::command]
async fn list_json_files(base_path: String) -> Result<Vec<String>, String> {
    // List JSON files in directory
}

#[tauri::command]
async fn get_app_data_dir() -> Result<String, String> {
    // Get app's data directory path
}
```

### userApi.getRecentWeeks() - Standalone Mode

```typescript
if (isStandaloneMode()) {
  const tauriApi = await import('@tauri-apps/api/core');
  
  // Get app data directory
  const dataDir = await tauriApi.invoke<string>('get_app_data_dir');
  
  // List JSON files in user's directory
  const jsonFiles = await tauriApi.invoke<string[]>('list_json_files', {
    basePath: `${dataDir}/lesson-plans/${userId}`,
  });
  
  // Parse weeks from file names or contents
  const weeks = jsonFiles
    .map(file => {
      // Extract week from filename or read file content
      // Return { week_of, display, folder_name }
    })
    .filter(Boolean)
    .slice(0, limit);
  
  return { data: weeks };
}
```

---

## 9.3 Sync Mechanism

### WiFi Sync Implementation

Create sync component/service:

```typescript
async function syncFromPC(pcIpAddress: string, userId: string) {
  const syncBaseUrl = `http://${pcIpAddress}:8000/api`;
  
  try {
    // 1. Fetch plans
    const plansResponse = await fetch(`${syncBaseUrl}/users/${userId}/plans?limit=50`);
    const plans = await plansResponse.json();
    
    // 2. Save plans to local database
    for (const plan of plans) {
      await executeLocalDatabase(
        `INSERT OR REPLACE INTO weekly_plans (...) VALUES (...)`,
        [...]
      );
    }
    
    // 3. Fetch JSON files list
    const weeksResponse = await fetch(`${syncBaseUrl}/recent-weeks?user_id=${userId}`);
    const weeks = await weeksResponse.json();
    
    // 4. Download and save JSON files
    for (const week of weeks) {
      const jsonResponse = await fetch(`${syncBaseUrl}/plans/${week.plan_id}`);
      const planDetail = await jsonResponse.json();
      
      // Save JSON file locally
      await tauriApi.invoke('write_json_file', {
        path: `${dataDir}/lesson-plans/${userId}/${week.folder_name}/lesson-plan.json`,
        content: JSON.stringify(planDetail.lesson_json),
      });
    }
    
    // 5. Fetch schedules and slots
    // Similar pattern...
    
    return { success: true, plansSynced: plans.length };
  } catch (error) {
    console.error('Sync failed:', error);
    throw error;
  }
}
```

### USB Sync Implementation

Export script on PC side, import UI in app.

---

## Implementation Order

1. **Row transformation functions** - Create all helper functions
2. **Plan API endpoints** - planApi.list(), getPlanDetail()
3. **Schedule API endpoints** - scheduleApi.getSchedule()
4. **Lesson API endpoints** - getLessonSteps()
5. **Session API endpoints** - All lessonModeSessionApi methods
6. **Local JSON storage** - File system commands + getRecentWeeks()
7. **Sync mechanism** - WiFi sync first, then USB

---

## Testing Strategy

1. Test on Android emulator first
2. Verify database queries work
3. Test sync mechanism
4. Test offline operation
5. Test on real tablet

---

**Estimated Time:** 6-8 hours for full implementation

