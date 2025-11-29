# Timer Auto-Advance Regression Script

Use this checklist to verify that Lesson Mode immediately begins the next step’s countdown and preserves adjusted durations.

## Setup
1. Build and install the latest tablet APK (or run the desktop app) so both client and shared modules are current.
2. Launch the app, select any user, open a weekly plan, and enter Lesson Mode for a lesson with at least four steps (warmup → closure).

## Test A – Baseline Auto-Advance
1. Start the timer on the first instructional step.
2. Do not touch any controls; let the countdown reach `00:00`.
3. **Pass criteria:** the UI flips to the next step immediately and the timer begins decrementing without tapping Play. Repeat for each subsequent step to confirm the behavior is consistent.

## Test B – After Manual Adjustment
1. While a step is running, open the Adjust dialog (or drag the progress bar) and add 2 minutes to the current step.
2. Confirm the remaining time updates and that downstream steps retain their original durations in the sidebar.
3. Let the adjusted step expire.
4. **Pass criteria:** the next step starts automatically with its original duration (not the adjusted value), and the timeline reflects recalculated totals.

## Test C – Starting Mid-Sequence
1. Manually jump to a later step using the timeline sidebar.
2. Start the timer and let it expire.
3. **Pass criteria:** the following step still auto-advances immediately and the earlier steps remain marked complete.

## Test D – Pause/Resume Edge Case
1. During any step, pause the timer for at least 5 seconds, then resume.
2. Allow the step to reach zero.
3. **Pass criteria:** the timer resumes auto-advance after the pause with no extra input.

Document any failures with the step number, expected duration, and whether the timer stopped or repeated. This script should be run on both desktop and tablet builds whenever timer logic changes.

