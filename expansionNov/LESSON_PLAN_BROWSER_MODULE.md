# Lesson Plan Browser/Navigation Module

## Executive Summary

This document describes the architecture for a new browser/navigation module that allows teachers to navigate lesson plans in a schedule-aware, time-based manner, rather than the traditional Word document view (5 slots × 5 days).

**Key Innovation**: The browser displays the lesson plan corresponding to the current time slot in the teacher's schedule, and allows navigation through lessons in the order they occur during the day/week.

> **Reality check (Nov 2025):** Current production UI includes a `LessonPlanBrowser` with week/day/lesson toggles and a detail view (see `frontend/src/components/LessonPlanBrowser.tsx`, `WeekView.tsx`, `DayView.tsx`, `LessonDetailView.tsx`). However, it lacks:
> - automatic “current lesson” detection or time-based defaulting,
> - filtering (subject/grade/homeroom/time),
> - schedule order navigation and multi-mode view (subject/slot/browser timeline),
> - integrated schedule editing/versioning UI,
> - React Native/mobile parity.
> Treat the following sections as desired future capabilities unless explicitly marked implemented.

**Related Documents**:
- [README.md](./README.md) - Master index of all expansion documents
- [DATABASE_ARCHITECTURE_AND_SYNC.md](./DATABASE_ARCHITECTURE_AND_SYNC.md) - Database schema and sync strategy
- [ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](./ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md) - Enhanced generation features

---

## Table of Contents

1. [Requirements Analysis](#requirements-analysis)
2. [Core Concepts](#core-concepts)
3. [Data Model](#data-model)
4. [Navigation Modes](#navigation-modes)
5. [Filtering System](#filtering-system)
6. [Time-Based Display Logic](#time-based-display-logic)
7. [UI/UX Design](#uiux-design)
8. [Database Schema](#database-schema)
9. [API Design](#api-design)
10. [Implementation Phases](#implementation-phases)

---

## Requirements Analysis

### Primary Requirements

1. **Schedule-Based Navigation**
   - Navigate lessons in the order they occur in the teacher's daily schedule
   - Schedule order varies by day of week
   - Schedule order varies by user (each teacher has their own schedule)

2. **Time-Aware Default Display**
   - By default, show the lesson plan for the current time slot
   - Example: If Math 2nd grade is scheduled 1:06-1:47 PM, at 1:15 PM, show that lesson plan
   - Automatically update as time progresses (optional: auto-refresh)
   - *Current implementation*: **Not available** – user must manually pick week/day/lesson.

3. **Multiple Navigation Modes**
   - Schedule order (primary mode)
   - Day view (all lessons for a day)
   - Week view (all lessons for a week)
   - Subject view (all lessons for a subject)
   - Slot-based view (traditional 5 slots × 5 days)
   - *Current implementation*: Only week grid → day list → lesson detail views exist.

4. **Filtering Capabilities**
   - Filter by day of week
   - Filter by subject
   - Filter by grade
   - Filter by time range
   - Filter by slot number
   - Filter by week/date range
   - *Current implementation*: **No filtering UI** beyond manual week dropdown.

5. **Quick Navigation**
   - Next lesson (in schedule order)
   - Previous lesson (in schedule order)
   - Jump to current lesson
   - Jump to specific day/time
   - *Current implementation*: Manually switch tabs; no “current lesson” shortcut or quick jumps.

### Secondary Requirements

- Offline capability (local-first)
- Fast navigation (cached lesson plans)
- Integration with existing lesson plan data
- Support for "No School" days
- Handle schedule changes mid-week
- Support for substitute teachers (different schedule)

---

## Core Concepts

### Schedule vs. Slots

**Traditional View (Word Document)**:
- 5 slots (Slot 1, Slot 2, Slot 3, Slot 4, Slot 5)
- Each slot has 5 days (Monday-Friday)
- Fixed structure: `slots[slot_number][day]`

**New Browser View (Schedule-Based)**:
- Schedule entries with specific times
- Each entry: `{day, start_time, end_time, subject, grade, slot_number}`
- Dynamic order based on time
- Example schedule:
  ```
  Monday:
    8:00-8:45  → ELA 3rd grade (Slot 1)
    9:15-10:00 → Science 3rd grade (Slot 2)
    10:30-11:15 → Math 3rd grade (Slot 3)
    1:06-1:47  → Math 2nd grade (Slot 1, different class)
    2:00-2:45  → ELA 2nd grade (Slot 2)
  ```

### Time Slot Matching

**Current Time**: 1:15 PM (13:15)

**Schedule Entry**: Math 2nd grade, 1:06-1:47 PM (13:06-13:47)

**Match Logic**: `current_time >= start_time AND current_time <= end_time`

**Result**: Display Math 2nd grade lesson plan

---

## Data Model

### Schedule Entry

```typescript
interface ScheduleEntry {
  id: string;
  user_id: string;
  day_of_week: 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday';
  start_time: string;  // "13:06" (HH:MM format, 24-hour)
  end_time: string;    // "13:47"
  subject: string;     // "Math", "ELA", "Science"
  grade: string;       // "2", "3", "4"
  slot_number: number; // Links to existing slot system (1-5)
  homeroom?: string;   // "Room 101"
  is_active: boolean;  // Can disable without deleting
  created_at: timestamp;
  updated_at: timestamp;
}
```

### Schedule (Complete Week)

```typescript
interface TeacherSchedule {
  user_id: string;
  week_of: string;  // "11/18/2024" (Monday of week)
  entries: ScheduleEntry[];  // All entries for the week
  version: number;  // For tracking schedule changes
}
```

### Lesson Plan Reference

```typescript
interface LessonPlanReference {
  schedule_entry_id: string;
  plan_id: string;  // Links to weekly_plans.id
  week_of: string;
  day: string;      // "monday", "tuesday", etc.
  slot_number: number;
  subject: string;
  grade: string;
}
```

---

## Navigation Modes

### Mode 1: Schedule Order (Primary)

**Description**: Navigate lessons in the order they occur during the day/week.

**Navigation**:
- **Next**: Next lesson in schedule order (same day, or next day if last lesson)
- **Previous**: Previous lesson in schedule order
- **Current**: Jump to lesson for current time slot

**Example Flow**:
```
Monday 8:00 AM → Show ELA 3rd grade
Click "Next" → Show Science 3rd grade (9:15 AM)
Click "Next" → Show Math 3rd grade (10:30 AM)
Click "Next" → Show Math 2nd grade (1:06 PM)
Click "Next" → Show ELA 2nd grade (2:00 PM)
Click "Next" → Show Tuesday 8:00 AM lesson (wraps to next day)
```

### Mode 2: Day View

**Description**: Show all lessons for a specific day in schedule order.

**Navigation**:
- **Day Selector**: Choose Monday-Friday
- **Scroll**: Scroll through all lessons for that day
- **Jump to Time**: Click on a time slot to jump to that lesson

**Display**: List or grid of all lessons for the day with times.

### Mode 3: Week View

**Description**: Show all lessons for the week in a calendar-like view.

**Navigation**:
- **Week Selector**: Choose week
- **Day Columns**: Monday-Friday columns
- **Time Rows**: Time slots as rows
- **Click**: Click on a lesson to view it

**Display**: Calendar grid with lessons placed at their scheduled times.

### Mode 4: Subject View

**Description**: Show all lessons for a specific subject across the week.

**Navigation**:
- **Subject Filter**: Select subject (Math, ELA, Science, etc.)
- **Day Navigation**: Navigate through days
- **Next/Previous**: Next/previous lesson for that subject

**Display**: List of all lessons for the subject, grouped by day.

### Mode 5: Slot-Based View (Traditional)

**Description**: Traditional view matching Word document structure.

**Navigation**:
- **Slot Tabs**: Slot 1, Slot 2, Slot 3, Slot 4, Slot 5
- **Day Navigation**: Monday-Friday
- **Grid View**: 5 slots × 5 days grid

**Display**: Matches existing Word document structure.

---

## Filtering System

### Filter Types

1. **Day Filter**
   - Single day: Monday, Tuesday, Wednesday, Thursday, Friday
   - Multiple days: Select multiple days
   - All days: Show all

2. **Subject Filter**
   - Single subject: Math, ELA, Science, etc.
   - Multiple subjects: Select multiple
   - All subjects: Show all

3. **Grade Filter**
   - Single grade: 2, 3, 4, 5, etc.
   - Multiple grades: Select multiple
   - All grades: Show all

4. **Time Range Filter**
   - Morning: 8:00 AM - 12:00 PM
   - Afternoon: 12:00 PM - 4:00 PM
   - Custom range: Start time - End time

5. **Slot Filter**
   - Single slot: Slot 1, Slot 2, etc.
   - Multiple slots: Select multiple
   - All slots: Show all

6. **Week/Date Filter**
   - Current week
   - Previous week
   - Next week
   - Specific week: Date picker
   - Date range: Start date - End date

### Filter Combinations

Filters can be combined:
- "Show all Math lessons on Monday morning"
- "Show all 2nd grade lessons this week"
- "Show all Slot 1 lessons in the afternoon"

### Filter Persistence

- Save filter presets
- Remember last used filters
- Quick filter buttons (Today, This Week, Current Subject)

---

## Time-Based Display Logic

### Current Lesson Detection

```python
def get_current_lesson(user_id: str, current_time: datetime) -> Optional[ScheduleEntry]:
    """
    Find the lesson plan that should be displayed for the current time.
    
    Logic:
    1. Get user's schedule for current week
    2. Find entry where current_time is between start_time and end_time
    3. If multiple matches (shouldn't happen), use first match
    4. If no match, find next upcoming lesson
    """
    day_of_week = current_time.strftime('%A').lower()  # "monday"
    time_str = current_time.strftime('%H:%M')  # "13:15"
    
    # Get schedule for current week
    schedule = get_schedule_for_week(user_id, get_week_of(current_time))
    
    # Find current lesson
    for entry in schedule.entries:
        if entry.day_of_week == day_of_week:
            if entry.start_time <= time_str <= entry.end_time:
                return entry
    
    # If no current lesson, find next upcoming lesson
    return get_next_upcoming_lesson(user_id, current_time)
```

### Next/Previous Lesson Navigation

```python
def get_next_lesson_in_schedule(
    user_id: str, 
    current_entry: ScheduleEntry,
    current_week: str
) -> Optional[ScheduleEntry]:
    """
    Get next lesson in schedule order.
    
    Logic:
    1. Get all entries for current week, sorted by day and time
    2. Find current entry index
    3. Return next entry (or first entry of next week if last)
    """
    schedule = get_schedule_for_week(user_id, current_week)
    sorted_entries = sort_entries_by_schedule_order(schedule.entries)
    
    current_index = find_entry_index(sorted_entries, current_entry)
    
    if current_index < len(sorted_entries) - 1:
        return sorted_entries[current_index + 1]
    else:
        # Get first lesson of next week
        next_week = get_next_week(current_week)
        next_schedule = get_schedule_for_week(user_id, next_week)
        if next_schedule.entries:
            return sort_entries_by_schedule_order(next_schedule.entries)[0]
    
    return None
```

### Schedule Order Sorting

```python
def sort_entries_by_schedule_order(entries: List[ScheduleEntry]) -> List[ScheduleEntry]:
    """
    Sort schedule entries by day of week, then by start time.
    
    Day order: Monday, Tuesday, Wednesday, Thursday, Friday
    Time order: Chronological within each day
    """
    day_order = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4}
    
    return sorted(
        entries,
        key=lambda e: (day_order[e.day_of_week], e.start_time)
    )
```

---

## UI/UX Design

### Main Browser Interface

```
┌─────────────────────────────────────────────────────────────┐
│  Lesson Plan Browser                    [Current: 1:15 PM]  │
├─────────────────────────────────────────────────────────────┤
│  [← Previous]  [Current Lesson]  [Next →]  [Jump to...]    │
│                                                              │
│  Filters: [Day: Monday ▼] [Subject: All ▼] [Grade: All ▼]  │
│           [Time: All Day ▼] [Week: 11/18/2024 ▼]           │
│                                                              │
│  Mode: ○ Schedule Order  ○ Day View  ○ Week View           │
│        ○ Subject View    ○ Slot View                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Monday, November 18, 2024                         │    │
│  │  1:06 PM - 1:47 PM                                 │    │
│  │  Math | Grade 2 | Room 101                         │    │
│  ├────────────────────────────────────────────────────┤    │
│  │                                                    │    │
│  │  [Lesson Plan Content]                            │    │
│  │  - Student Goal: ...                              │    │
│  │  - WIDA Objective: ...                            │    │
│  │  - Anticipatory Set: ...                          │    │
│  │  - Instruction: ...                               │    │
│  │  - Assessment: ...                                │    │
│  │                                                    │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  [View Full Week] [Print Objectives] [Edit] [Share]        │
└─────────────────────────────────────────────────────────────┘
```

### Schedule Timeline View (Day Mode)

```
┌─────────────────────────────────────────────────────────────┐
│  Monday, November 18, 2024                                  │
├─────────────────────────────────────────────────────────────┤
│  8:00 AM  ──►  ELA 3rd grade          [View] [Next]        │
│  9:15 AM  ──►  Science 3rd grade      [View] [Next]        │
│  10:30 AM ──►  Math 3rd grade         [View] [Next]        │
│  12:00 PM ──►  [Lunch Break]                                │
│  1:06 PM  ──►  Math 2nd grade    ⭐ CURRENT [View] [Next]  │
│  2:00 PM  ──►  ELA 2nd grade          [View] [Next]        │
│  3:00 PM  ──►  [Planning Period]                            │
└─────────────────────────────────────────────────────────────┘
```

### Quick Navigation Panel

```
┌─────────────────────────┐
│  Quick Navigation       │
├─────────────────────────┤
│  [Jump to Current]      │
│  [Today's Schedule]     │
│  [This Week]            │
│                         │
│  Recent Lessons:        │
│  • Math 2nd (1:06 PM)   │
│  • ELA 3rd (8:00 AM)    │
│  • Science 3rd (9:15)   │
│                         │
│  Favorites:             │
│  • Math 2nd Grade       │
│  • ELA 3rd Grade        │
└─────────────────────────┘
```

---

## Database Schema

### New Table: `teacher_schedules`

```sql
CREATE TABLE teacher_schedules (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    week_of TEXT NOT NULL,  -- Monday date of week (MM/DD/YYYY)
    version INTEGER DEFAULT 1,  -- For tracking schedule changes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, week_of, version)
);

CREATE INDEX idx_teacher_schedules_user_week 
ON teacher_schedules(user_id, week_of);
```

### New Table: `schedule_entries`

```sql
CREATE TABLE schedule_entries (
    id TEXT PRIMARY KEY,
    schedule_id TEXT NOT NULL,
    day_of_week TEXT NOT NULL CHECK(day_of_week IN ('monday', 'tuesday', 'wednesday', 'thursday', 'friday')),
    start_time TEXT NOT NULL,  -- HH:MM format (24-hour)
    end_time TEXT NOT NULL,    -- HH:MM format (24-hour)
    subject TEXT NOT NULL,
    grade TEXT NOT NULL,
    slot_number INTEGER,  -- Links to existing slot system (1-5)
    homeroom TEXT,
    is_active INTEGER DEFAULT 1,  -- 1 = active, 0 = disabled
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_id) REFERENCES teacher_schedules(id) ON DELETE CASCADE
);

CREATE INDEX idx_schedule_entries_schedule 
ON schedule_entries(schedule_id);

CREATE INDEX idx_schedule_entries_day_time 
ON schedule_entries(day_of_week, start_time);

CREATE INDEX idx_schedule_entries_subject_grade 
ON schedule_entries(subject, grade);
```

### New Table: `lesson_plan_references`

```sql
CREATE TABLE lesson_plan_references (
    id TEXT PRIMARY KEY,
    schedule_entry_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,  -- Links to weekly_plans.id
    week_of TEXT NOT NULL,
    day TEXT NOT NULL,  -- "monday", "tuesday", etc.
    slot_number INTEGER,
    subject TEXT,
    grade TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_entry_id) REFERENCES schedule_entries(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES weekly_plans(id) ON DELETE CASCADE,
    UNIQUE(schedule_entry_id, plan_id, week_of, day)
);

CREATE INDEX idx_lesson_plan_refs_entry 
ON lesson_plan_references(schedule_entry_id);

CREATE INDEX idx_lesson_plan_refs_plan 
ON lesson_plan_references(plan_id);
```

---

## API Design

### Schedule Management

```python
# Get schedule for week
GET /api/schedules/{user_id}/week/{week_of}
Response: {
    "schedule_id": "...",
    "week_of": "11/18/2024",
    "entries": [...]
}

# Create/Update schedule
POST /api/schedules/{user_id}/week/{week_of}
Body: {
    "entries": [
        {
            "day_of_week": "monday",
            "start_time": "13:06",
            "end_time": "13:47",
            "subject": "Math",
            "grade": "2",
            "slot_number": 1,
            "homeroom": "Room 101"
        },
        ...
    ]
}

# Get current lesson
GET /api/schedules/{user_id}/current
Response: {
    "entry": {...},
    "lesson_plan": {...},  // Full lesson plan JSON
    "time_remaining": 32  // minutes until end
}

# Get next/previous lesson
GET /api/schedules/{user_id}/next?entry_id={entry_id}
GET /api/schedules/{user_id}/previous?entry_id={entry_id}
```

### Navigation

```python
# Navigate to specific lesson
GET /api/browser/lesson?user_id={user_id}&entry_id={entry_id}
GET /api/browser/lesson?user_id={user_id}&day={day}&time={time}

# Get lessons with filters
GET /api/browser/lessons?user_id={user_id}&day={day}&subject={subject}&grade={grade}&time_range={start}-{end}

# Get schedule timeline for day
GET /api/browser/timeline/{user_id}/day/{day}?week_of={week_of}
```

### Lesson Plan Retrieval

```python
# Get lesson plan for schedule entry
GET /api/browser/lesson-plan?entry_id={entry_id}&week_of={week_of}

# Link lesson plan to schedule entry
POST /api/browser/link-lesson-plan
Body: {
    "entry_id": "...",
    "plan_id": "...",
    "week_of": "11/18/2024",
    "day": "monday"
}
```

---

## Implementation Phases

### Phase 1: Schedule Management (Week 1)

**Goal**: Create schedule data model and basic CRUD operations.

**Tasks**:
- [ ] Create database tables (`teacher_schedules`, `schedule_entries`)
- [ ] Create schedule management API endpoints
- [ ] Create schedule editor UI (basic)
- [ ] Import schedule from existing slot data (migration)
- [ ] Test schedule creation and retrieval

**Deliverables**:
- Schedule can be created and stored
- Schedule can be retrieved by week
- Basic schedule editor works

### Phase 2: Time-Based Display (Week 1-2)

**Goal**: Implement current lesson detection and time-aware display.

**Tasks**:
- [ ] Implement `get_current_lesson()` logic
- [ ] Create API endpoint for current lesson
- [ ] Create browser UI with current lesson display
- [ ] Add auto-refresh option (optional)
- [ ] Handle edge cases (no current lesson, between lessons)

**Deliverables**:
- Browser shows current lesson by default
- Updates automatically as time progresses
- Handles "no current lesson" gracefully

### Phase 3: Schedule Order Navigation (Week 2)

**Goal**: Implement next/previous navigation in schedule order.

**Tasks**:
- [ ] Implement `get_next_lesson()` and `get_previous_lesson()` logic
- [ ] Create navigation API endpoints
- [ ] Add next/previous buttons to UI
- [ ] Handle week boundaries (wrap to next week)
- [ ] Add keyboard shortcuts (arrow keys)

**Deliverables**:
- Can navigate forward/backward through schedule
- Navigation wraps correctly at week boundaries
- Keyboard navigation works

### Phase 4: Filtering System (Week 2-3)

**Goal**: Implement comprehensive filtering.

**Tasks**:
- [ ] Create filter API endpoints
- [ ] Implement filter UI components
- [ ] Add filter persistence (save presets)
- [ ] Add quick filter buttons
- [ ] Test filter combinations

**Deliverables**:
- All filter types work
- Filters can be combined
- Filter presets can be saved

### Phase 5: Multiple Navigation Modes (Week 3-4)

**Goal**: Implement all navigation modes.

**Tasks**:
- [ ] Implement Day View
- [ ] Implement Week View (calendar)
- [ ] Implement Subject View
- [ ] Implement Slot-Based View (traditional)
- [ ] Add mode switcher UI
- [ ] Persist selected mode

**Deliverables**:
- All 5 navigation modes work
- Can switch between modes
- Mode preference is saved

### Phase 6: Lesson Plan Integration (Week 4)

**Goal**: Link schedule entries to lesson plans.

**Tasks**:
- [ ] Create `lesson_plan_references` table
- [ ] Implement lesson plan lookup logic
- [ ] Auto-link based on slot_number, day, week_of
- [ ] Manual link/unlink functionality
- [ ] Display lesson plan content in browser

**Deliverables**:
- Schedule entries link to lesson plans
- Lesson plan content displays correctly
- Can manually adjust links

### Phase 7: UI Polish and Optimization (Week 4-5)

**Goal**: Polish UI and optimize performance.

**Tasks**:
- [ ] Improve UI design and responsiveness
- [ ] Add loading states and error handling
- [ ] Optimize queries (caching, indexing)
- [ ] Add offline support (local cache)
- [ ] Performance testing

**Deliverables**:
- Polished, responsive UI
- Fast navigation (< 100ms)
- Works offline

### Phase 8: Advanced Features (Week 5+)

**Goal**: Add advanced features.

**Tasks**:
- [ ] Schedule templates (copy from previous week)
- [ ] Schedule versioning (track changes)
- [ ] Substitute teacher support (different schedule)
- [ ] Schedule import/export
- [ ] Notifications (upcoming lesson reminders)

**Deliverables**:
- Advanced features work
- Well-documented

---

## Integration with Existing System

### Linking to Existing Slot System

**Challenge**: Existing system uses `slot_number` (1-5) and `day` (monday-friday). New system uses schedule entries with specific times.

**Solution**: 
- `schedule_entries` table includes `slot_number` field
- Auto-link lesson plans: `schedule_entry.slot_number` + `day` + `week_of` → `weekly_plans`
- Maintain backward compatibility: Can still use slot-based view

### Data Migration

**From Slots to Schedule**:
```python
def migrate_slots_to_schedule(user_id: str, week_of: str):
    """
    Create initial schedule from existing slot configuration.
    
    Assumes default times:
    - Slot 1: 8:00-8:45
    - Slot 2: 9:15-10:00
    - Slot 3: 10:30-11:15
    - Slot 4: 1:06-1:47
    - Slot 5: 2:00-2:45
    """
    slots = get_user_slots(user_id)
    default_times = {
        1: ("08:00", "08:45"),
        2: ("09:15", "10:00"),
        3: ("10:30", "11:15"),
        4: ("13:06", "13:47"),
        5: ("14:00", "14:45")
    }
    
    schedule = create_schedule(user_id, week_of)
    
    for slot in slots:
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
            start_time, end_time = default_times[slot.slot_number]
            create_schedule_entry(
                schedule_id=schedule.id,
                day_of_week=day,
                start_time=start_time,
                end_time=end_time,
                subject=slot.subject,
                grade=slot.grade,
                slot_number=slot.slot_number,
                homeroom=slot.homeroom
            )
```

---

## Open Questions

1. **Schedule Changes Mid-Week**: How to handle schedule changes during the week?
   - Option A: Create new schedule version, keep old for historical reference
   - Option B: Update existing schedule, track changes in audit log
   - **Recommendation**: Option A (versioning)

2. **Multiple Classes Same Time**: What if teacher has multiple classes at the same time?
   - **Recommendation**: Don't allow overlapping times in schedule. If needed, use different schedule entries with same time but different subjects (team teaching scenario).

3. **Schedule Templates**: Should schedules be copied week-to-week?
   - **Recommendation**: Yes, provide "Copy from previous week" functionality.

4. **Substitute Teachers**: How to handle substitute with different schedule?
   - **Recommendation**: Create separate user account or schedule override for substitute period.

5. **Time Zone Handling**: How to handle time zones?
   - **Recommendation**: Use local time of device. No timezone conversion needed (per user preference).

6. **Auto-Refresh Frequency**: How often should current lesson update?
   - **Recommendation**: Every minute, or on-demand (user clicks "Refresh").

---

## Next Steps

1. **Review and approve** this architecture document
2. **Create detailed UI mockups** for each navigation mode
3. **Create API specification** document with detailed endpoints
4. **Create database migration** scripts
5. **Start Phase 1 implementation** (Schedule Management)

---

## References

- [README.md](./README.md) - Master index of all expansion documents
- [DATABASE_ARCHITECTURE_AND_SYNC.md](./DATABASE_ARCHITECTURE_AND_SYNC.md) - Database schema and sync strategy
- [ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](./ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md) - Enhanced generation features

