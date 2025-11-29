# Lesson Mode Persistence Verification Plan

## Objective
Verify that the Lesson Mode session state is correctly saved and restored across page refreshes and navigation, and that the session is only ended when explicitly requested.

## Prerequisites
- User is logged in.
- A lesson plan exists for the current day/slot.
- The backend server is running.

## Test Cases

### 1. Session Creation and State Tracking
**Steps:**
1. Navigate to the dashboard.
2. Click "Start Lesson" for a valid slot.
3. Verify that the timer starts.
4. Wait for 10 seconds.
5. Click "Next Step".
6. Pause the timer.

**Expected Result:**
- The session is created in the database (can be verified via API `GET /api/lesson-mode/session/active`).
- `current_step_index` should be 1 (0-indexed).
- `is_paused` should be true.
- `remaining_time` should be updated.

### 2. Persistence Across Refresh
**Steps:**
1. While in the state from Test Case 1 (Step 2, Paused), refresh the browser page.
2. Wait for the Lesson Mode to reload.

**Expected Result:**
- The Lesson Mode should automatically load the active session.
- The timer should be paused.
- The current step should be Step 2.
- The remaining time should be approximately what it was before refresh.
- The session ID should remain the same.

### 3. Persistence Across Navigation
**Steps:**
1. While in an active session, click the "Back" button to return to the dashboard.
2. Navigate back to the same lesson slot (Start Lesson).

**Expected Result:**
- The Lesson Mode should restore the previous session state.
- It should NOT start a new session (timer 00:00).

### 4. Explicit Session End
**Steps:**
1. In an active session, click the "Exit" button (or "Finish Lesson" if available).
2. Confirm the exit dialog if present.
3. Return to the dashboard.
4. Click "Start Lesson" for the same slot again.

**Expected Result:**
- A NEW session should be created.
- The timer should start from the beginning (Step 1, full duration).
- The previous session should be marked as ended in the database.

### 5. Timer Adjustment Persistence
**Steps:**
1. Start a session.
2. Click the timer to open the adjustment dialog.
3. Add 5 minutes to the current step.
4. Refresh the page.

**Expected Result:**
- The added time should be persisted and reflected after refresh.
- The `adjusted_durations` field in the database should contain the modification.
