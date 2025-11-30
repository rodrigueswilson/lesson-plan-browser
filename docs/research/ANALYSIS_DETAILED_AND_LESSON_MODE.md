# Analysis: Detailed View and Lesson Mode

## Overview

This document analyzes two key components:
1. **LessonDetailView** - The detailed lesson plan view (read-only, comprehensive)
2. **LessonMode** - The interactive lesson execution view (timer-based, step-by-step)

Both components are part of the shared `lesson-browser` and `lesson-mode` packages and are used by both desktop and tablet frontends.

---

## 1. LessonDetailView Component

### Location
`shared/lesson-browser/src/components/LessonDetailView.tsx`

### Purpose
Displays comprehensive lesson plan information in a read-only, two-column layout. This is the "preview" view that shows all lesson details before entering interactive lesson mode.

### Key Features

#### Data Loading
- **Plan Resolution**: Finds lesson plan for the current week (`weekOf`)
- **Slot Matching**: Uses complex slot resolution logic:
  - Priority 1: `slot` prop (from plan matching)
  - Priority 2: `planSlotIndex` prop
  - Priority 3: `scheduleEntry.slot_number` (fallback)
- **Lesson Steps**: Loads lesson steps to extract vocabulary and sentence frames
- **Vocabulary Extraction**: Parses vocabulary from:
  - `slotData.vocabulary_cognates` (preferred)
  - Lesson steps `display_content` (fallback parsing)
- **Sentence Frames**: Extracts from:
  - `slotData.sentence_frames` (preferred)
  - Lesson steps with `content_type === 'sentence_frames'`

#### Layout Structure
```
┌─────────────────────────────────────────┐
│ Header (Subject, Grade, Time, Group)    │
│ [Enter Lesson Mode] [Back]              │
├─────────────────────────────────────────┤
│ [Previous] [Next]  Day • Date • Time   │
├─────────────────────────────────────────┤
│ Left Column          │ Right Column     │
│ • Unit/Lesson        │ • Tailored Inst  │
│ • Objectives         │ • Sentence Frames│
│ • Anticipatory Set   │ • Misconceptions │
│ • Vocabulary         │ • Homework       │
│ • Assessment         │                  │
└─────────────────────────────────────────┘
```

#### Left Column Sections
1. **Unit/Lesson**: Shows `slotData.unit_lesson`
2. **Objectives**: Displays nested objectives:
   - Content Objective
   - Student Goal
   - WIDA Objective
3. **Anticipatory Set**: Shows original content + bilingual bridge
4. **Vocabulary/Cognates**: 
   - Lists English → Portuguese pairs
   - Cognate badges (COGNATE / NON-COGNATE)
   - Extracted from slotData or lesson steps
5. **Assessment**: Primary assessment + bilingual check

#### Right Column Sections
1. **Tailored Instruction**: Complex nested structure:
   - Original Content
   - Co-Teaching Model (with rationale, WIDA context, implementation notes, phase plan)
   - ELL Support (strategy cards with proficiency levels)
   - Special Needs Support
   - Materials
2. **Sentence Frames**: Grouped by proficiency levels:
   - Levels 1-2
   - Levels 3-4
   - Levels 5-6
   - Vocabulary words highlighted in frames
3. **Misconceptions**: 
   - Original content
   - Linguistic note (pattern, note, prevention tip)
   - Fallback for old structure
4. **Homework**: Original content + family connection

#### Navigation
- **Previous/Next Lesson**: Navigate between lessons in the same day
- **Enter Lesson Mode**: Transitions to interactive `LessonMode` component
- **Back**: Returns to week/day view

#### Data Resolution Logic
The component uses sophisticated slot matching to ensure correct content is displayed:

```typescript
// Priority order:
1. slot prop (from plan matching) → most authoritative
2. planSlotIndex → fallback if slot number doesn't match
3. scheduleEntry.slot_number → last resort
4. Subject/Grade/Homeroom matching → final fallback
```

**Critical Issue**: The component merges `initialSlotData` (from plan matching) with fresh database data to ensure vocabulary/frames are preserved even if slot numbers don't match exactly.

---

## 2. LessonMode Component

### Location
`shared/lesson-mode/src/components/LessonMode.tsx`

### Purpose
Interactive, timer-based lesson execution view. Provides step-by-step guidance with automatic timing, session persistence, and live mode synchronization.

### Key Features

#### Three-Column Layout
```
┌─────────────────────────────────────────────────────────┐
│ Header: Lesson Mode • Subject • Grade • Live/Preview    │
│ [Exit Lesson Mode]                                       │
├──────────┬──────────────┬──────────────────────────────┤
│ Timeline │ Instructions │ Resources                     │
│ Sidebar  │ Panel        │ Area                          │
│ (1/5)    │ (1/6)        │ (remaining)                  │
│          │              │                               │
│ • Prev   │ Current Step │ • Objective                  │
│ • Current│ Instructions │ • Vocabulary                  │
│ • Upcom. │              │ • Sentence Frames             │
│          │ [Prev][Next] │ • Lesson Card                │
│ Timer    │              │ • Lesson Plan                │
│ Controls │              │                               │
└──────────┴──────────────┴──────────────────────────────┘
```

#### Timeline Sidebar (`TimelineSidebar.tsx`)
- **Width**: 1/5 of screen (collapsible to 48px)
- **Sections**:
  - Previous Steps (scrollable, clickable to return)
  - Current Step (highlighted, with timer)
  - Upcoming Steps (preview)
- **Timer Display**: Shows remaining time, play/pause/reset controls
- **Step Filtering**: Hides resource steps (vocabulary, sentence frames) from timeline
- **Navigation**: Click any step to jump to it

#### Instructions Panel (`CurrentStepInstructions.tsx`)
- **Width**: 1/6 of screen (200-300px, collapsible)
- **Content**: Current step's `display_content`
- **Navigation**: Previous/Next buttons, "Go to Beginning" button
- **Step Counter**: Shows "X / Total" steps

#### Resources Area (`ResourceDisplayArea.tsx`)
- **Toolbar**: Tabs for different resource types
- **Resource Types**:
  1. **Objective**: Extracted from lesson plan (student goal/WIDA objective)
  2. **Vocabulary**: From lesson steps (with cognate badges)
  3. **Sentence Frames**: Grouped by proficiency levels
  4. **Lesson Card**: Current step content with vocabulary highlighting
  5. **Lesson Plan**: Full lesson plan detail view

#### Timer System (`useLessonTimer` hook)
- **Auto-Advance**: Automatically moves to next step when timer completes
- **Live Mode**: Syncs with schedule if within 30 minutes of lesson start
- **Session Persistence**: Saves state to backend every 30 seconds
- **Timer Adjustments**: 
  - Add/Subtract time
  - Skip to step
  - Recalculate remaining step durations
- **Rate Limiting**: Handles 429 errors gracefully with cooldown

#### Session Management
- **Auto-Save**: Debounced saves (max once per 30 seconds)
- **State Restoration**: Loads active session on mount
- **Session End**: Properly ends session on exit
- **Rate Limit Handling**: Pauses saves for 65 seconds after rate limit

#### Live Mode Detection
```typescript
// Checks if current time is within 30 minutes before lesson start
// or during lesson time
const isLiveMode = now >= (startTime - 30min) && now <= endTime
```

When in Live Mode:
- Timer syncs with actual lesson schedule
- Shows "Live Mode - Synced with schedule" indicator
- Auto-advance respects real-time constraints

#### Step Loading
1. Try to load existing steps from API
2. If none exist, generate steps automatically
3. Initialize adjusted steps array (for timer recalculation)
4. Handle errors gracefully (phase_plan missing, etc.)

#### Timer Adjustment Dialog
- Allows adding/subtracting time from current step
- Recalculates remaining step durations proportionally
- Supports skipping to specific steps
- Updates both `steps` and `adjustedSteps` arrays

---

## 3. Component Integration

### Flow: Week View → Detail View → Lesson Mode

```
WeekView (Week Grid)
  ↓ [Click Lesson Card]
LessonDetailView (Read-only Preview)
  ↓ [Click "Enter Lesson Mode"]
LessonMode (Interactive Timer)
  ↓ [Click "Exit Lesson Mode"]
LessonDetailView (or WeekView)
```

### Data Flow

1. **WeekView** → Passes `scheduleEntry`, `day`, `slot`, `planSlotIndex`, `initialSlotData`
2. **LessonDetailView** → Uses slot data to display content, can transition to LessonMode
3. **LessonMode** → Receives `scheduleEntry`, `planId`, `day`, `slot` and resolves plan context

### Shared Dependencies
- **API Client**: Both use `@lesson-api` for data fetching
- **Store**: Both use `useStore()` for current user
- **UI Components**: Both use `@lesson-ui` components
- **Utilities**: Both use vocabulary highlighting, plan matching utilities

---

## 4. Key Differences: Detail View vs. Lesson Mode

| Feature | LessonDetailView | LessonMode |
|---------|-----------------|------------|
| **Purpose** | Preview/Review | Execution |
| **Interactivity** | Read-only | Interactive (timer, steps) |
| **Layout** | 2-column grid | 3-column layout |
| **Navigation** | Previous/Next lesson | Previous/Next step |
| **Timer** | None | Full timer system |
| **Session** | None | Persistent session |
| **Live Mode** | No | Yes (syncs with schedule) |
| **Step Focus** | Shows all content | Shows current step only |
| **Resource Access** | All visible | Tabbed resource panel |

---

## 5. Potential Issues & Improvements

### LessonDetailView Issues

1. **Slot Resolution Complexity**: The slot matching logic is complex and may fail if:
   - Plan slot numbers don't match schedule slot numbers
   - Multiple slots have same subject/grade
   - Plan data structure changes

2. **Vocabulary Extraction**: Falls back to parsing `display_content` which is fragile

3. **Missing Error States**: Some sections don't show clear messages when data is missing

### LessonMode Issues

1. **Rate Limiting**: Session saves can hit rate limits (handled but may cause data loss)

2. **Step Generation**: Auto-generation may fail if phase_plan is missing

3. **Live Mode Timing**: 30-minute window may not be configurable

4. **Session Restoration**: May not restore all state correctly if session is stale

### Suggested Improvements

1. **Better Error Handling**: Show user-friendly messages for all error states
2. **Offline Support**: Cache lesson data for offline access
3. **Configurable Live Mode**: Allow users to set custom live mode window
4. **Better Slot Matching**: Improve plan-to-schedule matching algorithm
5. **Vocabulary Caching**: Cache parsed vocabulary to avoid re-parsing
6. **Session Conflict Resolution**: Handle multiple devices accessing same session

---

## 6. Component Dependencies

### LessonDetailView Dependencies
- `@lesson-api`: `lessonApi`, `planApi`, `ScheduleEntry`, `LessonPlanDetail`
- `@lesson-ui`: `Button`, `Card`
- `@lesson-mode/utils`: Vocabulary highlighting utilities
- `useStore`: Current user state

### LessonMode Dependencies
- `@lesson-api`: All API clients, types
- `@lesson-ui`: `Button`, `Card`
- `useLessonTimer`: Timer hook
- `recalculateStepDurations`: Timer adjustment utility
- `resolvePlanIdFromScheduleEntry`: Plan resolution utility
- Sub-components: `TimelineSidebar`, `CurrentStepInstructions`, `ResourceDisplayArea`, `TimerAdjustmentDialog`

---

## 7. Tablet-Specific Considerations

Both components should work identically on tablet and desktop, but:

1. **Touch Interactions**: Ensure buttons are large enough for touch
2. **Collapsible Panels**: Important for smaller screens
3. **Scroll Areas**: Ensure all sections are scrollable
4. **Timer Visibility**: Timer should be prominent on tablet
5. **Resource Switching**: Tab navigation should be touch-friendly

---

## Summary

- **LessonDetailView**: Comprehensive read-only preview with two-column layout showing all lesson details
- **LessonMode**: Interactive three-column execution view with timer, step navigation, and resource access
- Both components share data loading logic but serve different purposes
- Integration is smooth: Detail View → Lesson Mode → Detail View
- Main challenges: Slot resolution, rate limiting, session persistence

