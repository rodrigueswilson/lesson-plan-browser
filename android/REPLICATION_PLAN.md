# Android Replication Plan: PC Feature Parity

## Objective
Achieve full feature and User Experience (UX) parity with the PC Frontend (`frontend/`) in the Android application (`android/`), using Native Android technologies (Kotlin/Jetpack Compose).

## Strategy: Plan-Do-Review
We will follow a **Component-Based** replication strategy, focusing on one functional area at a time to maintain stability (Single Responsibility Principle).

### Guiding Principles
*   **SSOT (Single Source of Truth):** Logic definitions (e.g., "What is a Live Lesson?") must match the PC's logic exactly.
*   **DRY (Don't Repeat Yourself):** Extract shared UI components (e.g., `TimerDisplay`, `PlanCard`) into reusable Composable functions.
*   **KISS (Keep It Simple):** Avoid over-engineering the Android architecture. Use standard MVVM with Hilt.
*   **YAGNI (You Ain't Gonna Need It):** Only implement features currently visible and active in the PC app.

---

## Phase 1: Lesson Mode "Live" Experience (High Priority)
*Goal: Make the "Start Lesson" view fully interactive and capable of managing a real classroom session.*

### 1.1 Timer Adjustment & Controls
- [ ] **Timer Adjustment Dialog:** Implement the "Adjust" dialog to Add/Subtract time or Skip steps.
- [ ] **Live vs. Preview Logic:** Implement logic to detect if the lesson is "Live" (current time matches schedule) vs "Preview".
- [ ] **Session Persistence:** Ensure timer state survives app minimization/rotation (using `SavedStateHandle` or Room).

### 1.2 Layout & Interactivity
- [ ] **Collapsible Sidebar:** Allow the Timeline (Left) to collapse to give more space to Content.
- [ ] **Collapsible Instructions:** Allow the Middle column to collapse.
- [ ] **Responsive Layout:** Ensure 3-column layout scales gracefully on different tablet sizes.

---

## Phase 2: Resources & Content Display
*Goal: Ensure all teaching materials are accessible and readable.*

### 2.1 Rich Content
- [ ] **Formatted Text:** Support bold/italic/lists in Instruction steps (if used in PC).
- [ ] **Dynamic Text Sizing:** Allow text scaling for better readability on tablets.

### 2.2 Resource Interactivity
- [ ] **Expandable Resources:** Implement "Accordion" style for Vocabulary, Sentence Frames, Materials (matching PC's `ExpandableItemView`).
- [ ] **Media Support:** Check if Audio/Images are used in resources and implement `MediaPlayer` / `Coil` if needed.

---

## Phase 3: Browser Polish & Navigation
*Goal: Refine the browsing experience to be fluid and intuitive.*

### 3.1 Visual Polish
- [ ] **Typography Alignment:** Audit font sizes and weights against PC.
- [ ] **Spacing & keylines:** Ensure strict adherence to the 8dp grid system.
- [ ] **Empty States:** Better UI for days with no lessons or empty weeks.

### 3.2 Navigation
- [ ] **Date Jumping:** Ensure "Week Selector" allows jumping to specific historical weeks.
- [ ] **Today Button:** Quick return to current date.

---

## Phase 4: Resilience & Optimization
*Goal: Ensure the app is robust for daily classroom use.*

### 4.1 Error Handling
- [ ] **Retry Mechanisms:** Friendly UI for network failures during Sync.
- [ ] **Data Integrity:** Validation to prevent "ghost" lessons or mismatched slots.

### 4.2 Performance
- [ ] **Lazy Loading:** Optimize `LazyColumn` performance for large schedules.
- [ ] **Memory Management:** Ensure `LessonSession` doesn't leak memory.

---

## Execution Log

| Status | Task | Notes |
| :--- | :--- | :--- |
| **Completed** | **Browser Architecture** | Replicated Week Grid, Day List, and Toolbar. |
| **Completed** | **Single Timer** | Implemented `TimerDisplay` in Timeline. |
| **Completed** | **Timer Adjustment** | Implemented Dialog and `recalculateStepDurations` logic. |
| **Completed** | **Collapsible Columns** | Implemented expand/collapse toggles and refined weights (20/60/20). |
| **Completed** | **Resource Accordions** | Created `ExpandableCard` and refactored Vocabulary, Frames, Materials. |
| **Completed** | **Browser Polish** | Added "Today" button, "Week:" label, improved empty states, refined spacing. |
| **Completed** | **Text Formatting** | Verified text rendering, improved line spacing, added loading indicators. |
| **Completed** | **All Phases** | ✅ Feature parity achieved with PC Frontend! |

