# Lesson Mode Improvement Plan

## 1. Current Status & Issues
- **Timer Duration**: "Vocabulary" and "Sentence Frames" steps currently have `0` duration, causing the timer to finish immediately.
- **Missing Instructions**: These steps show only the raw content (word list/grid) without the instructional script (e.g., "Teacher uses cards..."), which is buried in the JSON's `ell_support` strategies.
- **Sync Rigidity**: The current "Lesson Mode" aggressively tries to sync with the wall-clock time of the scheduled slot. This makes it difficult to:
  - Preview the lesson beforehand.
  - Review the lesson afterwards.
  - Teach the lesson if the schedule shifts (e.g., delayed start).

## 2. Proposed Feature: "Preview / Review Mode"
We need to distinguish between **Live Mode** and **Preview Mode**.

### A. Live Mode (Current Behavior)
- **Purpose**: For delivering the lesson at the scheduled time.
- **Behavior**:
  - Timer attempts to sync with `current_time` vs `slot_start_time`.
  - Auto-advances if enabled.
  - Calculates "late/early" status and compesates give more or less time to the remaining steps to help getting everything planed done.

### B. Preview / Review Mode (New)
- **Purpose**: For planning, practicing, or reviewing steps without schedule constraints.
- **Behavior**:
  - **No Wall-Clock Sync**: The timer behaves like a standard stopwatch/countdown.
  - **Manual Control**: Starts at Step 1 (or user selection), not where the wall clock says we should be.
  - **Timer**: Starts fresh for each step based on its duration.
  - **Trigger**:
    - If `current_time` is outside the `slot_start_time` - `slot_end_time` window -> Default to **Preview Mode**.
    - Or add a toggle switch: "Sync with Schedule" vs "Free Pacing".

## 3. Implementation Steps

### Phase 1: Fix Data & Content (Backend)
**File:** `backend/api.py` -> `generate_lesson_steps`

1.  **Fix Durations**:
    - Assign a default duration (e.g., `5 minutes`) to generated steps ("Vocabulary", "Sentence Frames") instead of `0`.
    - Ensure they contribute to the total lesson time.

2.  **Populate Instructions**:
    - Extract `implementation` text from `ell_support` strategies (matching IDs `cognate_awareness` and `sentence_frames`).
    - Prepend this text to the `display_content` of the respective steps.
    - This ensures the teacher sees *what to do*, not just the materials.

### Phase 2: Timer Logic Update (Frontend)
**File:** `frontend/src/hooks/useLessonTimer.ts` & `LessonMode.tsx`

1.  **Add Mode Switch**:
    - State: `isLiveMode` (boolean).
    - Logic: Initialize `true` if within 30 mins of slot time, else `false`.

2.  **Modify Sync Logic**:
    - In `useLessonTimer`, wrap the `syncWithActualTime` logic.
    - If `!isLiveMode`, disable auto-jump to step index based on time.
    - Allow the user to toggle "Sync" on/off in the UI.

3.  **UI Controls**:
    - Add a "Preview Mode" banner or toggle in the header.
    - If in Preview Mode, show "Standard Timer" instead of "Synced with actual time".

## 4. Execution Plan (Next Session)
1.  **Apply Backend Patch**: Fix `api.py` to set durations and extract instructions (as attempted previously).
2.  **Regenerate Steps**: Clear old steps for Monday Slot 1 and regenerate to verify the new data structure (5 min duration + instructions).
3.  **Frontend Update**: Modify `LessonMode.tsx` to default to "Preview Mode" if the lesson is not currently happening, solving the "0:00 / Paused" confusion when reviewing past/future lessons.
