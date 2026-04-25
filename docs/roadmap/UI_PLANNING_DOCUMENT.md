# UI Planning Document: Lesson Plan Browser & Lesson Mode
## Cross-Platform UI Design for Windows 11 & Android 16

**Version**: 1.0  
**Date**: 2025-01-27  
**Status**: Planning Phase

---

## Executive Summary

This document provides comprehensive UI planning for two major features:
1. **Lesson Plan Browser Module** - Schedule management, navigation, and filtering (v1 Priority)
2. **Lesson Mode** - Real-time, timed step-by-step instruction guide with context-aware display

> **Reality check (Nov 2025):** The shipped UI covers only a subset of the MVP: week/day/lesson navigation and a static Lesson Mode shell (no timer sync, no approvals). There is no document management UI, filtering controls, tablet layout, or advanced timer workflow yet. Use this document as the authoritative spec for upcoming work.

**Implementation Strategy**: MVP-first approach
- **Phase 1 (v1)**: Browser Module + Simplified Lesson Mode
- **Phase 2 (v2)**: Full-featured Lesson Mode with advanced timer synchronization

Both features must work seamlessly on:
- **Windows 11 (PC)** - Tauri + React + TypeScript
- **Android 16 (Tablet/Phone)** - React Native/Capacitor + TypeScript

---

## Table of Contents

1. [MVP Strategy](#mvp-strategy)
2. [Information Architecture](#information-architecture)
3. [User Flows](#user-flows)
4. [Screen Specifications](#screen-specifications)
5. [Component Design](#component-design)
6. [Platform-Specific Considerations](#platform-specific-considerations)
7. [Data Models](#data-models)
8. [Implementation Phases](#implementation-phases)
9. [Tool Recommendations](#tool-recommendations)

---

## MVP Strategy

### Release Plan

**v1.0 (MVP) - Initial Release**
- ✅ **Browser Module** (Full implementation)
  - Current lesson display (time-based)
  - Schedule navigation
  - Filtering system
  - Lesson plan browsing and detail view
- ✅ **Simplified Lesson Mode** (Basic implementation)
  - Manual step navigation (no auto-timer)
  - Display step content (objectives, sentence frames, materials)
  - Basic timer (manual start/stop, no synchronization)
  - Context-aware content display (simplified)

**v2.0 (Full Featured) - Future Enhancement**
- ✅ **Advanced Lesson Mode**
  - Automatic timer synchronization with actual time
  - Timer reprogramming/adjustment during lesson
  - Auto-advance between steps
  - Proportional recalculation of remaining steps
  - Full timer state persistence

### Rationale

**Why MVP First?**
1. **Validate User Needs**: Test if teachers actually use Lesson Mode before building complex timer sync
2. **Faster Time to Market**: Browser Module delivers immediate value
3. **Reduce Risk**: Complex timer synchronization is high-risk; validate simpler version first
4. **Iterative Improvement**: Gather feedback on basic Lesson Mode before adding complexity

### Simplified Lesson Mode (v1) Features

**Included**:
- ✅ Step-by-step navigation (manual)
- ✅ Display current step content
- ✅ Show objectives, sentence frames, materials
- ✅ Basic timer (manual start, countdown only)
- ✅ Step progress indicator

**Deferred to v2**:
- ❌ Automatic time synchronization
- ❌ Timer adjustment/reprogramming
- ❌ Auto-advance between steps
- ❌ Proportional step recalculation
- ❌ Timer state persistence across app restarts

### Migration Path

The simplified v1 implementation uses the same data model as v2, ensuring easy upgrade:
- Same `lesson_steps` table structure
- Same component architecture
- v2 adds timer synchronization layer on top of v1 foundation

---

## Information Architecture

### Core Data Entities

```
ScheduleEntry (Database)
├── id: string
├── user_id: string
├── day_of_week: 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday'
├── start_time: string (HH:MM format, e.g., "13:06")
├── end_time: string (HH:MM format, e.g., "13:47")
├── subject: string
├── grade: string
├── slot_number: number
├── homeroom?: string
└── is_active: boolean

LessonPlan (Database)
├── id: string
├── week_of: string (MM/DD-MM/DD)
├── metadata: LessonPlanMetadata
│   ├── grade: string
│   ├── subject: string
│   ├── homeroom: string
│   └── teacher_name: string
└── days: Record<string, DayPlan>
    └── DayPlan
        ├── unit_lesson: string
        ├── objective: Objective
        ├── anticipatory_set: AnticipatorySet
        ├── tailored_instruction: TailoredInstruction
        │   ├── original_content: string
        │   ├── co_teaching_model: CoTeachingModel
        │   │   └── phase_plan: Phase[] ← TIMED STEPS FOR LESSON MODE
        │   ├── ell_support: ELLStrategy[]
        │   ├── special_needs_support: string[]
        │   └── materials: string[]
        ├── misconceptions: Misconceptions
        ├── assessment: Assessment
        └── homework: Homework

LessonStep (NEW - Database Row)
├── id: string
├── lesson_plan_id: string
├── day_of_week: string
├── slot_number: number
├── step_number: number (1, 2, 3, ...)
├── step_name: string (e.g., "Warmup", "Input", "Practice")
├── duration_minutes: number
├── start_time_offset: number (minutes from lesson start)
├── content_type: 'objective' | 'sentence_frames' | 'materials' | 'instruction' | 'assessment'
├── display_content: string (what to show on screen)
├── hidden_content: string[] (what to hide)
├── sentence_frames?: SentenceFrame[] (if content_type is 'sentence_frames')
│   ├── portuguese: string
│   └── english: string
└── materials_needed: string[]
```

### Navigation Structure

```
App Root
├── Browser Module (Schedule Management)
│   ├── Home/Dashboard
│   │   ├── Current Lesson Display (time-based)
│   │   ├── Quick Navigation (Next/Previous)
│   │   └── Week Overview
│   ├── Schedule View
│   │   ├── Weekly Calendar
│   │   ├── Day View
│   │   └── Slot Detail
│   ├── Lesson Plan Browser
│   │   ├── List View (filterable)
│   │   ├── Detail View
│   │   └── Print/Export
│   └── Filtering System
│       ├── By Subject
│       ├── By Date Range
│       ├── By User/Teacher
│       └── By Grade
│
└── Lesson Mode (NEW - Real-time Instruction)
    ├── Lesson Mode Entry
    │   ├── Select Current Lesson
    │   ├── Start Timer (sync with actual time)
    │   └── Manual Start Option
    ├── Active Lesson View
    │   ├── Timer Display (visual + countdown)
    │   ├── Current Step Display
    │   ├── Context-Aware Content
    │   │   ├── Objective Display (when needed)
    │   │   ├── Sentence Frames (large text)
    │   │   ├── Materials List
    │   │   └── Instruction Steps
    │   ├── Step Navigation
    │   └── Timer Controls
    │       ├── Pause/Resume
    │       ├── Adjust Timer (reprogram)
    │       └── Skip to Step
    └── Lesson Mode Settings
        ├── Display Preferences
        ├── Timer Alerts
        └── Content Visibility
```

---

## User Flows

### Flow 1: Browser Module - View Current Lesson

```
1. App Opens
   ↓
2. Check Current Time
   ↓
3. Query ScheduleEntry for current time slot
   ↓
4. Display Current Lesson Card
   ├── Subject, Grade, Time Range
   ├── Time Remaining (countdown)
   └── Quick Actions
       ├── View Lesson Plan
       ├── Enter Lesson Mode
       └── Navigate to Next Lesson
   ↓
5. User Clicks "View Lesson Plan"
   ↓
6. Load LessonPlan from database
   ↓
7. Display Full Lesson Plan View
   ├── All sections (Objective, Tailored Instruction, etc.)
   ├── Print/Export Options
   └── Navigation to other days/slots
```

### Flow 2: Browser Module - Filter and Navigate

```
1. User Opens Schedule View
   ↓
2. Apply Filters
   ├── Subject: "Math"
   ├── Date Range: "This Week"
   └── Grade: "5th"
   ↓
3. Display Filtered Results
   ├── List View (compact)
   └── Calendar View (visual)
   ↓
4. User Selects a Lesson
   ↓
5. Display Lesson Detail
   ├── Full Plan Content
   ├── Related Lessons
   └── Quick Actions
```

### Flow 3: Lesson Mode - Start Active Lesson (v1 MVP)

```
1. User is in Browser Module
   ↓
2. User Clicks "Enter Lesson Mode" on Current Lesson
   ↓
3. System Checks:
   ├── Is there a current lesson? (time-based)
   └── Does lesson have LessonStep data?
   ↓
4. Enter Lesson Mode View
   ├── Load LessonStep data for this lesson
   ├── Display First Step Content
   └── Show Manual Navigation Controls
   ↓
5. User Manually Starts Timer (if desired)
   ├── Click "Start Timer" button
   ├── Countdown for current step begins
   └── Visual progress bar (green → yellow → red)
   ↓
6. User Manually Navigates Steps
   ├── Click "Next Step" when ready
   ├── Timer resets for new step (if timer was running)
   └── Display updates to show new step content
```

**v2 Enhancement** (Future):
- Automatic step calculation based on actual time
- Auto-advance when timer expires
- Timer synchronization with lesson start time

### Flow 4: Lesson Mode - Adjust Timer During Lesson (v2 - Deferred)

**Status**: Deferred to v2.0

**v1 MVP Alternative**: Manual step navigation
- User clicks "Next Step" when ready
- Timer resets for new step
- No automatic recalculation needed

**v2 Full Implementation**:
```
1. User is in Active Lesson Mode
   ↓
2. Lesson is running, timer counting down
   ↓
3. Unexpected event occurs (late start, interruption, etc.)
   ↓
4. User Clicks "Adjust Timer" button
   ↓
5. Display Timer Adjustment Dialog
   ├── Current Step: "Practice" (Step 3 of 5)
   ├── Current Time Remaining: 8:32
   ├── Options:
   │   ├── Add Time (+1 min, +5 min, +10 min)
   │   ├── Subtract Time (-1 min, -5 min)
   │   ├── Reset to Original Duration
   │   └── Skip to Next Step
   └── Warning: "Adjusting will affect remaining steps"
   ↓
6. User Adjusts Timer
   ↓
7. System Recalculates:
   ├── Remaining time for current step
   ├── Remaining time for subsequent steps
   └── Total lesson time remaining
   ↓
8. Update Display
   ├── New countdown timer
   ├── Updated progress bar
   └── Notification: "Timer adjusted. Remaining steps updated."
```

### Flow 5: Lesson Mode - Context-Aware Content Display

```
1. User is in Active Lesson Mode
   ↓
2. Current Step: "Practice" (Step 3)
   ↓
3. System Checks Step Content Type
   ├── content_type: 'sentence_frames'
   ├── display_content: "Students will use sentence frames..."
   └── sentence_frames: [
       { portuguese: "Eu vou explicar...", english: "I will explain..." },
       { portuguese: "O sistema permite...", english: "The system allows..." }
   ]
   ↓
4. Display Context-Aware UI
   ├── HIDE: Objective, Materials List, Other Steps
   ├── SHOW: Sentence Frames (LARGE TEXT - 48pt+)
   │   ├── Portuguese frame (top)
   │   └── English frame (bottom)
   ├── SHOW: Current Step Name ("Practice")
   ├── SHOW: Timer (visual + countdown)
   └── SHOW: Quick Actions (Next Step, Adjust Timer)
   ↓
5. Step Completes
   ↓
6. Auto-advance to Next Step
   ↓
7. Check Next Step Content Type
   ├── content_type: 'objective'
   └── display_content: "Recall learning objective..."
   ↓
8. Update Display
   ├── SHOW: Objective (large, centered)
   ├── HIDE: Sentence Frames
   └── Update Timer for new step
```

---

## Screen Specifications

### Screen 1: Browser Module - Current Lesson Dashboard

**Purpose**: Quick access to current lesson with time-based detection

**Layout (Desktop - Windows)**:
```
┌─────────────────────────────────────────────────────────┐
│ Header: Bilingual Lesson Planner                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────────────────────────────────────────┐    │
│  │ CURRENT LESSON (Live)                          │    │
│  │                                                 │    │
│  │ 📚 Math - 5th Grade                            │    │
│  │ 🕐 1:06 PM - 1:47 PM                           │    │
│  │ ⏱️  Time Remaining: 23:45                      │    │
│  │                                                 │    │
│  │ [View Full Plan]  [Enter Lesson Mode]          │    │
│  └───────────────────────────────────────────────┘    │
│                                                         │
│  ┌──────────────────┐  ┌──────────────────┐         │
│  │ ← Previous       │  │ Next →            │         │
│  │ Math 12:20-1:00  │  │ Science 2:00-2:40 │         │
│  └──────────────────┘  └──────────────────┘         │
│                                                         │
│  ┌───────────────────────────────────────────────┐    │
│  │ Week Overview                                   │    │
│  │ Mon │ Tue │ Wed │ Thu │ Fri                    │    │
│  │  5  │  5  │  5  │  5  │  5  (lessons per day) │    │
│  └───────────────────────────────────────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Layout (Mobile - Android)**:
```
┌─────────────────────────┐
│ Lesson Planner          │
├─────────────────────────┤
│                         │
│ ┌─────────────────────┐ │
│ │ CURRENT LESSON      │ │
│ │                     │ │
│ │ 📚 Math             │ │
│ │ 5th Grade           │ │
│ │ 🕐 1:06 - 1:47 PM   │ │
│ │ ⏱️  23:45 remaining │ │
│ │                     │ │
│ │ [View Plan]         │ │
│ │ [Lesson Mode]       │ │
│ └─────────────────────┘ │
│                         │
│ ┌──────┐  ┌──────┐      │
│ │ ←    │  │  →  │      │
│ │ Prev │  │ Next│      │
│ └──────┘  └──────┘      │
│                         │
│ [Week View]             │
│                         │
└─────────────────────────┘
```

### Screen 2: Lesson Mode - Active Lesson View

**Purpose**: Real-time step-by-step instruction guide with timer

**Layout (Desktop - Windows)**:
```
┌─────────────────────────────────────────────────────────┐
│ LESSON MODE - Math, 5th Grade                            │
│ Step 3 of 5: Practice                                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │ TIMER                                            │  │
│  │                                                   │  │
│  │ ████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │  │
│  │ ████████████████ (Green → Yellow → Red)         │  │
│  │                                                   │  │
│  │ ⏱️  8:32 remaining                               │  │
│  │                                                   │  │
│  │ [Pause] [Adjust Timer] [Skip Step]               │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │ CURRENT STEP CONTENT                              │  │
│  │                                                   │  │
│  │ SENTENCE FRAMES (Large Text - 48pt)              │  │
│  │                                                   │  │
│  │ ┌─────────────────────────────────────────┐    │  │
│  │ │ Eu vou explicar como o sistema de leis  │    │  │
│  │ │ permite o crescimento do comércio.      │    │  │
│  │ └─────────────────────────────────────────┘    │  │
│  │                                                   │  │
│  │ ┌─────────────────────────────────────────┐    │  │
│  │ │ I will explain how the system of laws   │    │  │
│  │ │ allows the growth of commerce.          │    │  │
│  │ └─────────────────────────────────────────┘    │  │
│  │                                                   │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │ STEP NAVIGATION                                  │  │
│  │                                                   │  │
│  │ [1. Warmup ✓] [2. Input ✓] [3. Practice ●]      │  │
│  │ [4. Closure ○] [5. Assessment ○]                │  │
│  │                                                   │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  [Exit Lesson Mode]                                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Layout (Mobile - Android - Portrait)**:
```
┌─────────────────────┐
│ LESSON MODE         │
│ Math - 5th          │
├─────────────────────┤
│                     │
│ Step 3 of 5         │
│ Practice            │
│                     │
│ ┌─────────────────┐ │
│ │                 │ │
│ │   TIMER         │ │
│ │                 │ │
│ │ ████████░░░░░░░ │ │
│ │                 │ │
│ │   8:32          │ │
│ │                 │ │
│ └─────────────────┘ │
│                     │
│ ┌─────────────────┐ │
│ │                 │ │
│ │ SENTENCE FRAMES │ │
│ │                 │ │
│ │ Eu vou explicar │ │
│ │ como o sistema  │ │
│ │ de leis permite │ │
│ │                 │ │
│ │ ─────────────── │ │
│ │                 │ │
│ │ I will explain  │ │
│ │ how the system  │ │
│ │ of laws allows  │ │
│ │                 │ │
│ └─────────────────┘ │
│                     │
│ [Pause] [Adjust]    │
│                     │
│ [1✓] [2✓] [3●] [4○]│
│                     │
│ [Exit]              │
│                     │
└─────────────────────┘
```

**Layout (Mobile - Android - Landscape/Tablet)**:
```
┌─────────────────────────────────────────────────────┐
│ LESSON MODE - Math, 5th Grade                        │
│ Step 3 of 5: Practice                                │
├─────────────────────────────────────────────────────┤
│                                                      │
│ ┌────────────────────┐  ┌──────────────────────────┐│
│ │ TIMER              │  │ CURRENT STEP CONTENT     ││
│ │                    │  │                          ││
│ │ ████████░░░░░░░░░░ │  │ SENTENCE FRAMES         ││
│ │                    │  │                          ││
│ │ 8:32 remaining     │  │ Eu vou explicar como    ││
│ │                    │  │ o sistema de leis       ││
│ │ [Pause] [Adjust]   │  │ permite o crescimento   ││
│ │                    │  │                          ││
│ └────────────────────┘  │ I will explain how      ││
│                          │ the system of laws      ││
│ ┌────────────────────┐  │ allows the growth      ││
│ │ STEP NAVIGATION    │  │                          ││
│ │                    │  └──────────────────────────┘│
│ │ [1✓] [2✓] [3●] [4○]│                              │
│ │                    │                              │
│ └────────────────────┘                              │
│                                                      │
│ [Exit Lesson Mode]                                  │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### Screen 3: Lesson Mode - Timer Adjustment Dialog

**Purpose**: Allow teacher to reprogram timer at any step

**Layout (Both Platforms)**:
```
┌─────────────────────────────────────┐
│ Adjust Timer                        │
├─────────────────────────────────────┤
│                                     │
│ Current Step: Practice (Step 3/5)   │
│                                     │
│ Original Duration: 10:00           │
│ Current Remaining: 8:32             │
│                                     │
│ ┌─────────────────────────────┐    │
│ │ Add Time:                   │    │
│ │ [+1 min] [+5 min] [+10 min] │    │
│ └─────────────────────────────┘    │
│                                     │
│ ┌─────────────────────────────┐    │
│ │ Subtract Time:              │    │
│ │ [-1 min] [-5 min]           │    │
│ └─────────────────────────────┘    │
│                                     │
│ ┌─────────────────────────────┐    │
│ │ Other Options:              │    │
│ │ [Reset to Original]         │    │
│ │ [Skip to Next Step]         │    │
│ └─────────────────────────────┘    │
│                                     │
│ ⚠️ Warning: Adjusting will affect  │
│ remaining steps. Remaining steps    │
│ will be recalculated proportionally.│
│                                     │
│ [Cancel]  [Apply Changes]          │
│                                     │
└─────────────────────────────────────┘
```

### Screen 4: Lesson Mode - Objective Display Context

**Purpose**: Show objective when step requires it

**Layout (Desktop)**:
```
┌─────────────────────────────────────────────────────────┐
│ LESSON MODE - Math, 5th Grade                            │
│ Step 1 of 5: Warmup                                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │ TIMER                                            │  │
│  │ ████████████████████████████████████████████    │  │
│  │ ⏱️  2:15 remaining                               │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │ LEARNING OBJECTIVE                               │  │
│  │                                                   │  │
│  │ ┌─────────────────────────────────────────────┐ │  │
│  │ │ Content Objective:                          │ │  │
│  │ │ Students will be able to explain how        │ │  │
│  │ │ systems of law and banking enabled growth  │ │  │
│  │ │ in trade, wealth, and peace.                │ │  │
│  │ └─────────────────────────────────────────────┘ │  │
│  │                                                   │  │
│  │ ┌─────────────────────────────────────────────┐ │  │
│  │ │ Student Goal:                               │ │  │
│  │ │ I will explain Roman systems using         │ │  │
│  │ │ evidence and a graphic organizer.          │ │  │
│  │ └─────────────────────────────────────────────┘ │  │
│  │                                                   │  │
│  │ ┌─────────────────────────────────────────────┐ │  │
│  │ │ WIDA Language Objective:                    │ │  │
│  │ │ Students will use language to explain how   │ │  │
│  │ │ Roman law, banking, and Pax Romana enabled  │ │  │
│  │ │ economic growth (ELD-SS.6-8.Explain...)    │ │  │
│  │ └─────────────────────────────────────────────┘ │  │
│  │                                                   │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  [Next Step]                                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Component Design

### Component 1: TimerDisplay

**Purpose**: Visual timer with progress bar and countdown

**v1 MVP Props**:
```typescript
interface TimerDisplayProps {
  totalDuration: number; // seconds
  remainingTime: number; // seconds
  isRunning: boolean; // v1: manual start/stop only
  onStart: () => void;
  onStop: () => void;
  onReset: () => void;
  colorScheme: 'green' | 'yellow' | 'red'; // based on time remaining
}
```

**v2 Enhanced Props** (Future):
```typescript
interface TimerDisplayProps {
  totalDuration: number; // seconds
  remainingTime: number; // seconds
  isPaused: boolean;
  onPause: () => void;
  onResume: () => void;
  onAdjust: () => void; // v2: timer adjustment
  colorScheme: 'green' | 'yellow' | 'red';
  autoAdvance?: boolean; // v2: auto-advance to next step
}
```

**Visual States**:
- **Green** (70-100% remaining): Normal pace
- **Yellow** (30-70% remaining): Approaching deadline
- **Red** (<30% remaining): Urgent

**Progress Bar Calculation**:
```typescript
const progress = (remainingTime / totalDuration) * 100;
const colorScheme = 
  progress > 70 ? 'green' :
  progress > 30 ? 'yellow' : 'red';
```

**v1 Implementation**: Manual timer control only
**v2 Enhancement**: Add automatic synchronization and adjustment

### Component 2: StepContentDisplay

**Purpose**: Context-aware content display based on step type

**Props**:
```typescript
interface StepContentDisplayProps {
  step: LessonStep;
  displayMode: 'objective' | 'sentence_frames' | 'materials' | 'instruction';
}
```

**Display Modes**:
- **objective**: Large, centered text (36pt+)
- **sentence_frames**: Very large text (48pt+), bilingual side-by-side or stacked
- **materials**: List format, medium text (18pt)
- **instruction**: Full instruction text, scrollable

### Component 3: StepNavigation

**Purpose**: Show step progress and allow navigation

**Props**:
```typescript
interface StepNavigationProps {
  steps: LessonStep[];
  currentStepIndex: number;
  onStepSelect: (stepIndex: number) => void;
  allowSkip: boolean;
}
```

**Visual Indicators**:
- **Completed** (✓): Green checkmark
- **Current** (●): Highlighted, active
- **Upcoming** (○): Gray, inactive

### Component 4: TimerAdjustmentDialog (v2 - Deferred)

**Status**: Deferred to v2.0

**Purpose**: Allow timer reprogramming during active lesson

**v1 MVP Alternative**: Manual step navigation
- User clicks "Next Step" when ready
- Timer resets for new step
- No adjustment dialog needed

**v2 Props** (Future):
```typescript
interface TimerAdjustmentDialogProps {
  currentStep: LessonStep;
  remainingSteps: LessonStep[];
  currentRemainingTime: number;
  onAdjust: (adjustment: TimerAdjustment) => void;
  onCancel: () => void;
}

interface TimerAdjustment {
  type: 'add' | 'subtract' | 'reset' | 'skip';
  amount?: number; // minutes
  targetStep?: number; // if skipping
}
```

**v2 Recalculation Logic** (Future):
```typescript
function recalculateRemainingSteps(
  adjustedStep: LessonStep,
  remainingSteps: LessonStep[],
  adjustment: TimerAdjustment
): LessonStep[] {
  // If adding/subtracting time to current step:
  // - Adjust current step duration
  // - Proportionally adjust remaining steps OR
  // - Subtract/adjust from last step
  
  // If skipping:
  // - Mark current step as skipped
  // - Start next step timer
  
  // If resetting:
  // - Restore original durations
}
```

---

## Platform-Specific Considerations

### Windows 11 (Tauri + React)

**Advantages**:
- Larger screen real estate → Side-by-side layouts possible
- Keyboard shortcuts for timer controls
- Window management (can keep lesson mode in separate window)
- Native notifications for step transitions

**UI Patterns**:
- Desktop sidebar navigation (existing pattern)
- Modal dialogs for timer adjustment
- Keyboard shortcuts:
  - `Space`: Pause/Resume timer
  - `→`: Next step
  - `←`: Previous step
  - `A`: Adjust timer
  - `Esc`: Exit lesson mode

**Performance**:
- Use React state management (Zustand) for timer state
- Web Workers for timer calculations (avoid blocking UI)
- CSS animations for progress bar (GPU-accelerated)

### Android 16 (React Native/Capacitor)

**Advantages**:
- Touch-first interface → Large tap targets
- Portrait/landscape adaptability
- Full-screen mode for lesson mode (immersive)
- Haptic feedback for step transitions

**UI Patterns**:
- Bottom navigation (existing pattern)
- Bottom sheet for timer adjustment (Material Design)
- Swipe gestures for step navigation
- Large text sizes for readability (accessibility)

**Performance**:
- Use React Native's Animated API for timer animations
- Background timer service (if app goes to background)
- Optimize re-renders (React.memo, useMemo)

**Screen Size Adaptations**:
- **Phone (Portrait)**: Stacked layout, full-screen lesson mode
- **Tablet (Landscape)**: Side-by-side timer + content
- **Tablet (Portrait)**: Optimized for vertical reading

---

## Data Models

### New Database Schema: lesson_steps

```sql
CREATE TABLE lesson_steps (
    id TEXT PRIMARY KEY,
    lesson_plan_id TEXT NOT NULL,
    day_of_week TEXT NOT NULL, -- 'monday', 'tuesday', etc.
    slot_number INTEGER NOT NULL,
    step_number INTEGER NOT NULL, -- 1, 2, 3, ...
    step_name TEXT NOT NULL, -- 'Warmup', 'Input', etc.
    duration_minutes INTEGER NOT NULL,
    start_time_offset INTEGER NOT NULL, -- minutes from lesson start
    content_type TEXT NOT NULL, -- 'objective', 'sentence_frames', etc.
    display_content TEXT NOT NULL,
    hidden_content TEXT, -- JSON array of content to hide
    sentence_frames TEXT, -- JSON array of {portuguese, english}
    materials_needed TEXT, -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lesson_plan_id) REFERENCES lesson_plans(id),
    UNIQUE(lesson_plan_id, day_of_week, slot_number, step_number)
);
```

### TypeScript Types

```typescript
// shared/types/lesson-step.ts
export interface LessonStep {
  id: string;
  lesson_plan_id: string;
  day_of_week: 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday';
  slot_number: number;
  step_number: number;
  step_name: string;
  duration_minutes: number;
  start_time_offset: number;
  content_type: 'objective' | 'sentence_frames' | 'materials' | 'instruction' | 'assessment';
  display_content: string;
  hidden_content?: string[];
  sentence_frames?: SentenceFrame[];
  materials_needed?: string[];
  created_at: string;
  updated_at: string;
}

export interface SentenceFrame {
  portuguese: string;
  english: string;
}

export interface LessonModeState {
  currentLesson: ScheduleEntry | null;
  currentLessonPlan: LessonPlan | null;
  currentSteps: LessonStep[];
  currentStepIndex: number;
  timerState: TimerState;
  isActive: boolean;
}

export interface TimerState {
  totalDuration: number; // seconds
  remainingTime: number; // seconds
  startTime: Date | null; // when timer started
  isPaused: boolean;
  pausedAt: Date | null;
  adjustments: TimerAdjustment[];
}
```

### API Endpoints (FastAPI)

```python
# backend/api/lesson_mode.py

@router.get("/api/lesson-mode/{user_id}/current")
async def get_current_lesson_mode(user_id: str):
    """Get current lesson and steps for lesson mode."""
    # 1. Get current schedule entry (time-based)
    # 2. Get lesson plan
    # 3. Get lesson steps
    # 4. Calculate current step based on time
    pass

@router.get("/api/lesson-steps/{lesson_plan_id}/{day}/{slot}")
async def get_lesson_steps(lesson_plan_id: str, day: str, slot: int):
    """Get all steps for a specific lesson."""
    pass

@router.post("/api/lesson-mode/timer/adjust")
async def adjust_timer(adjustment: TimerAdjustmentRequest):
    """Adjust timer for current step and recalculate remaining steps."""
    pass

@router.post("/api/lesson-steps/generate")
async def generate_lesson_steps(lesson_plan_id: str, day: str, slot: int):
    """Generate lesson steps from TailoredInstruction phase_plan."""
    # Extract phases from co_teaching_model.phase_plan
    # Create LessonStep records
    # Store in database
    pass
```

---

## Implementation Phases

### Phase 1: Browser Module - Core (Week 1-2) ✅ v1 Priority

**Tasks**:
- [ ] Current lesson display component (time-based detection)
- [ ] Schedule navigation components
- [ ] Filtering system UI
- [ ] Lesson plan detail view
- [ ] Integration with existing layouts
- [ ] API endpoints for schedule and lesson plan queries

**Deliverables**:
- Browser module functional on Windows
- Basic navigation working
- Filtering system operational

### Phase 2: Browser Module - Polish (Week 2-3) ✅ v1 Priority

**Tasks**:
- [ ] Week overview calendar
- [ ] Quick navigation (previous/next lesson)
- [ ] Print/export functionality
- [ ] UI/UX refinements
- [ ] Testing and bug fixes

**Deliverables**:
- Production-ready Browser Module
- User testing complete

### Phase 3: Simplified Lesson Mode (Week 3-4) ✅ v1 MVP

**Tasks**:
- [ ] Create `lesson_steps` database table
- [ ] Create TypeScript types for LessonStep
- [ ] Implement API endpoints for lesson steps (basic CRUD)
- [ ] Create step generation logic (from phase_plan)
- [ ] TimerDisplay component (manual start/stop only)
- [ ] StepContentDisplay component
- [ ] StepNavigation component (manual navigation)
- [ ] Lesson Mode entry flow
- [ ] Context-aware content display (simplified)

**Deliverables**:
- Simplified Lesson Mode functional on Windows
- Manual step navigation working
- Basic timer (manual control only)

**Excluded from v1**:
- ❌ Automatic timer synchronization
- ❌ Timer adjustment/reprogramming
- ❌ Auto-advance between steps
- ❌ Step recalculation logic

### Phase 4: Android - Browser Module (Week 4-5) ✅ v1 Priority

**Tasks**:
- [ ] React Native/Capacitor setup
- [ ] Port Browser Module to Android
- [ ] Platform-specific optimizations
- [ ] Testing on tablet and phone

**Deliverables**:
- Browser Module functional on Android
- Cross-platform Browser Module parity

### Phase 5: Android - Simplified Lesson Mode (Week 5-6) ✅ v1 MVP

**Tasks**:
- [ ] Port Simplified Lesson Mode to Android
- [ ] Platform-specific UI adaptations
- [ ] Testing on tablet and phone

**Deliverables**:
- Simplified Lesson Mode functional on Android
- Cross-platform Lesson Mode parity (v1 MVP)

### Phase 6: v1 Release & User Validation (Week 6-7)

**Tasks**:
- [ ] End-to-end testing
- [ ] User acceptance testing
- [ ] Gather feedback on Lesson Mode usage
- [ ] Bug fixes and polish
- [ ] Documentation

**Deliverables**:
- v1.0 release ready
- User feedback collected
- Decision point: Proceed with v2 enhancements?

---

### Phase 7: Advanced Lesson Mode - Timer Synchronization (v2 - Future)

**Prerequisites**: User validation confirms Lesson Mode is valuable

**Tasks**:
- [ ] Timer synchronization logic (actual time sync)
- [ ] Auto-advance between steps
- [ ] Timer adjustment dialog
- [ ] Step recalculation logic
- [ ] Timer state persistence
- [ ] Advanced timer controls

**Deliverables**:
- Full-featured Lesson Mode
- Timer synchronization working
- Timer adjustment functional

### Phase 8: Android - Advanced Lesson Mode (v2 - Future)

**Tasks**:
- [ ] Port advanced timer features to Android
- [ ] Background timer service
- [ ] Platform-specific optimizations

**Deliverables**:
- Full-featured Lesson Mode on Android

---

## Tool Recommendations

Based on the AI recommendations and your project needs:

### 1. MockFlow (Highest Priority) ✅

**Use For**:
- Creating sitemap for Browser Module + Lesson Mode
- Mapping user flows (especially Lesson Mode flows)
- Early-stage wireframing for complex screens

**Why It Fits**:
- Supports both web (Windows) and mobile (Android) UI packs
- AI text-to-wireframe can quickly visualize your requirements
- Site mapping tools help organize the navigation structure

**Specific Use Cases**:
1. Map the complete navigation structure (Browser ↔ Lesson Mode)
2. Create wireframes for Timer Adjustment Dialog
3. Design the Context-Aware Content Display variations

### 2. UX Pilot AI (Second Priority) ✅

**Use For**:
- Generating user journey flows for Lesson Mode
- Creating screen flows for timer adjustment scenarios
- UX review of the real-time instruction flow

**Why It Fits**:
- Focuses on user experience flows (perfect for Lesson Mode)
- Can generate flows based on user research concepts
- Figma integration if you need design handoff

**Specific Use Cases**:
1. Design the "Teacher enters lesson mode" user journey
2. Map the "Timer adjustment during unexpected events" flow
3. Create the "Context-aware display transitions" flow

### 3. Google AI Studio / Gemini (Strategic Planning) ✅

**Use For**:
- Defining information architecture for LessonStep data model
- Generating content structure for different step types
- Planning the timer recalculation algorithm logic

**Why It Fits**:
- Excellent for complex reasoning and structured output
- Can help design the data model relationships
- Good for generating documentation and specifications

**Specific Use Cases**:
1. Define the LessonStep content_type enum values
2. Plan the timer adjustment recalculation algorithm
3. Generate example step content for different scenarios

### 4. Uizard (Rapid Prototyping) ⚠️

**Use For**:
- Quick visualizations of Lesson Mode screens
- Exploring different layout options for timer display
- Rapid iteration on mobile vs desktop layouts

**Why It Fits**:
- Fast text-to-UI generation
- Good for exploring visual ideas quickly
- Multi-screen support for testing variations

**Limitation**: Less useful once you have React components, better for early exploration

### Tools NOT Recommended for This Project

- **Galileo AI**: Too focused on high-fidelity design, you already have React components
- **Banani**: Consumer-focused, not suitable for complex educational/enterprise UI

---

## Next Steps

### Immediate Actions (v1 MVP)

1. **Review this document** with your team
2. **Prioritize Browser Module** - Begin Phase 1 implementation
3. **Set up MockFlow** account and create sitemap for Browser Module
4. **Begin Phase 1**: Browser Module core features
5. **Plan Simplified Lesson Mode** - Design manual navigation flow

### Future Actions (v2 Enhancement)

1. **User Validation** - Gather feedback on v1 Lesson Mode usage
2. **Use UX Pilot AI** to design advanced Lesson Mode flows (if validated)
3. **Use Google AI Studio** to refine timer synchronization algorithms
4. **Begin Phase 7**: Advanced timer features (only if user validation confirms need)

---

## Appendix: Example LessonStep Data

### Example: Step 1 - Warmup (Objective Display)

```json
{
  "id": "step_001",
  "lesson_plan_id": "plan_123",
  "day_of_week": "monday",
  "slot_number": 1,
  "step_number": 1,
  "step_name": "Warmup",
  "duration_minutes": 5,
  "start_time_offset": 0,
  "content_type": "objective",
  "display_content": "Display learning objectives to students. Review content objective, student goal, and WIDA language objective.",
  "hidden_content": ["sentence_frames", "materials", "instruction_details"],
  "materials_needed": []
}
```

### Example: Step 3 - Practice (Sentence Frames)

```json
{
  "id": "step_003",
  "lesson_plan_id": "plan_123",
  "day_of_week": "monday",
  "slot_number": 1,
  "step_number": 3,
  "step_name": "Practice",
  "duration_minutes": 10,
  "start_time_offset": 15,
  "content_type": "sentence_frames",
  "display_content": "Students will practice using sentence frames to explain Roman systems.",
  "hidden_content": ["objective", "materials", "other_steps"],
  "sentence_frames": [
    {
      "portuguese": "Eu vou explicar como o sistema de leis permite o crescimento do comércio.",
      "english": "I will explain how the system of laws allows the growth of commerce."
    },
    {
      "portuguese": "O sistema bancário facilita o comércio porque...",
      "english": "The banking system facilitates commerce because..."
    }
  ],
  "materials_needed": ["Sentence frame strips", "Bilingual vocabulary chart"]
}
```

---

**Document Status**: Updated with MVP Strategy  
**Next Review Date**: After Phase 1 completion (Browser Module)

---

## Change Log

**2025-01-27**: Initial document created
**2025-01-27**: Updated with MVP strategy - Simplified Lesson Mode for v1, advanced features deferred to v2

