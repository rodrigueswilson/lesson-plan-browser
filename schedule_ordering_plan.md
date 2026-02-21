
# Implementation Plan - Schedule-Based Ordering

The goal is to ensure that the Objectives and Sentence Frames PDFs list lessons in the exact order of the daily schedule, respecting day-to-day variations in class times.

## Problem
Currently, PDFs are generated with a static order because the `start_time` used for sorting is identical across all days ("most common" time), ignoring specific daily schedule variations (e.g., Friday schedule vs Monday schedule). This causes lessons to appear in the wrong order on days where the schedule shifts.

## Root Cause Analysis
1.  **Data Source**: `schedule_entries` in the database contains the correct day-specific times.
2.  **Enrichment**: `batch_processor.py` attempts to add a `day_times` map to the slot metadata.
3.  **Persistence Failure**: Investigation reveals `day_times` is missing from the final `latest_lesson.json`, suggesting it's lost during `_process_slot` or `json_merger.py`.
4.  **Sorting**: `sort_slots` relies on `start_time`. Since `start_time` is static (flattened to "most common"), sorting produces the same order every day.

## Proposed Changes

### 1. Database & Batch Processor
-   **Verify Enrichment**: Ensure `_process_slot` correctly saves `day_times` to `lesson_json["metadata"]`.
-   **Debug "Empty Schedule"**: Validate why `check_schedule_db.py` returned empty results (possible user ID mismatch or DB access issue).

### 2. JSON Merger
-   **Propagate Day Times**: Ensure `json_merger.py` correctly reads `day_times` from the input lesson's metadata and applies the *specific* day's start/end time to the slot object within that day's `slots` list.
-   **Validation**: Add debug logging to `json_merger.py` to confirm it is actually overriding `start_time` with `day_times` values.

### 3. PDF Generators
-   **Objectives Printer (`objectives_printer.py`)**:
    -   Ensure it sorts the slots *after* extracting them for a specific day.
    -   Verify `sort_slots` is called on the day-specific list where `start_time` has been corrected.
-   **Sentence Frames Generator (`sentence_frames_pdf_generator.py`)**:
    -   Apply the same sorting logic: sort slots *per day* using the day-specific `start_time`.

## Verification Plan

### Automated Test
-   Create `verify_schedule_sorting.py`:
    -   Mock `schedule_entries` with distinct times for Monday vs Friday (e.g., Slot 1 is 9:00 on Mon, 10:00 on Fri).
    -   Run `batch_processor` -> `json_merger` flow.
    -   Inspect resulting `lesson_json` to confirm Monday's slot has Monday's time and Friday's slot has Friday's time.
    -   Verify `sort_slots` produces different orders for Mon vs Fri if times overlap/shift.

### Manual Verification
-   Run batch process for the target user.
-   Inspect `latest_lesson.json` to confirm `day_times` is present (if retained) or that `days.{day}.slots` have different `start_time` values.
-   Generate PDF and visually confirm order matches the user's schedule.
