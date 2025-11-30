# Analysis of "Second Version" Tablet Browser

## Current State

The shared `WeekView.tsx` component (`shared/lesson-browser/src/components/WeekView.tsx`) already implements a proper week grid layout:

### Structure
- **Grid Layout**: Uses `grid-cols-[80px_repeat(5,1fr)]` to create a time column + 5 day columns
- **Time-based Rows**: Iterates over `sortedTimeSlots` (all unique time ranges across all days)
- **Day Columns**: For each time slot row, renders entries for all 5 days in parallel columns

### Data Processing
1. Loads all schedule entries via `scheduleApi.getSchedule(currentUser.id)`
2. Groups entries by day: `grouped[day] = lessonsForDay`
3. Separates non-class periods: `nonClassPeriods[day] = nonClassForDay`
4. Collects unique time slots across all days: `allTimeSlots.add(\`${start}-${end}\`)`
5. Renders rows: For each time slot → For each day → Find matching entry

### Expected Behavior
- A.M. Routine at 08:15-08:30 should appear **once per day** in the same time row
- Each day column should show its own A.M. Routine entry
- Result: One horizontal row with A.M. Routine appearing in all 5 day columns

## Issue Identified

**Problem**: A.M. Routine appears 5 times stacked vertically in a single column instead of spread across the week row.

**Possible Causes**:

1. **Data Structure Issue**: 
   - All 5 A.M. Routine entries might have the same `day_of_week` value
   - Or entries might be missing `day_of_week_of` field
   - Check: Are entries properly tagged with `monday`, `tuesday`, etc.?

2. **Time Slot Matching Issue**:
   - Entries might have slightly different time formats (e.g., "08:15" vs "8:15")
   - Or entries might be missing `start_time`/`end_time` fields
   - Check: Do all A.M. Routine entries have matching `start_time` and `end_time`?

3. **Filtering Logic Issue**:
   - Non-class periods might be filtered incorrectly
   - Check: Is `isNonClassPeriod()` correctly identifying A.M. Routine?
   - Check: Are entries marked as `is_active: false` when they should be active?

4. **Rendering Logic Issue**:
   - The `days.map()` loop might not be finding entries correctly
   - Check: Is `schedule[day]?.find()` returning the correct entry for each day?

## Next Steps

1. **Add Debug Logging**: Log the actual schedule data structure when A.M. Routine entries are loaded
2. **Verify Data**: Check that A.M. Routine entries have:
   - Different `day_of_week` values (monday, tuesday, wednesday, thursday, friday)
   - Matching `start_time` and `end_time` (e.g., "08:15" and "08:30")
   - Correct `is_active` status
3. **Compare with Desktop**: Check if desktop version handles this differently
4. **Fix Rendering**: Ensure the grid properly distributes entries across day columns

## Code Location

- **WeekView Component**: `shared/lesson-browser/src/components/WeekView.tsx`
- **Key Rendering Logic**: Lines 242-380 (time slot iteration + day column mapping)
- **Data Loading**: Lines 59-196 (schedule API call + grouping logic)

