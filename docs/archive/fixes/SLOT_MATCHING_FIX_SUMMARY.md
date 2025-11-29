# Slot Matching Fix Summary

## Problem Identified

The browser was showing correct schedule metadata but wrong objectives because:

1. **Schedule has 6 periods, lesson plan has 5 slots**
   - Pattern occurs daily due to co-teaching scenarios
   - Example: 2nd grade 209 has ELA (slot #3) and Social S. (slot #4) that share ONE lesson plan slot (ELA/SS)

2. **Lesson plan slots lack metadata**
   - Slots don't have grade, homeroom, or time information
   - Only have `slot_number` and `subject`
   - This caused incorrect matching when slot numbers don't align

3. **Original matching prioritized slot_number incorrectly**
   - Schedule slot #2 (ELA Grade 3 T5) was matching lesson plan slot_number 2 (ELA/SS with wrong objective)
   - Should have matched lesson plan slot_number 1 (ELA with correct objective)

## Root Cause

```
Schedule Entry:
  slot_number: 2
  subject: ELA  
  grade: 3
  homeroom: T5
  time: 08:30-09:15

Lesson Plan Slots:
  [0]: slot_number: 1, subject: ELA     <- CORRECT MATCH (by subject)
  [1]: slot_number: 2, subject: ELA/SS  <- INCORRECT MATCH (by slot_number)
```

The old matcher prioritized `slot_number` first, causing misalignment.

## Solution

### 1. Updated Matching Priority (`planMatching.ts`)

**New matching order:**
1. **Subject + Grade + Homeroom + Time** (best match if all present)
2. **Subject + Grade + Homeroom** (when lesson plan lacks time)  
3. **Slot number** (only if subject is compatible or missing)
4. **Time** (last resort)

**Critical addition:** When multiple slots match, the code now prefers the most **specific** subject:
- "ELA/SS" (compound) is preferred over "ELA" (simple)
- Calculates specificity by counting subject parts (split by `/` or `\`)
- This ensures "ELA Grade 2 209" matches "ELA/SS" instead of plain "ELA"

### 2. Co-Teaching Support

Added `subjectsMatch()` helper that:
- Handles exact matches (ELA === ELA)
- Handles co-teaching (ELA/SS matches both ELA and Social Studies)
- Allows multiple schedule entries to share one lesson plan slot

### 3. Removed `usedIndices` Blocking

- Old code: prevented multiple schedule entries from using same lesson plan slot
- New code: allows sharing for co-teaching scenarios
- This is intentional and required for the 6→5 mapping pattern

### 4. Updated `LessonDetailView.tsx`

- Removed dangerous positional fallback `slots[slot - 1]`
- Added subject+grade+homeroom matching as fallback
- Prevents wrong objectives when slot numbering includes non-instructional periods

## Testing

To verify the fix:

### Test Case 1: ELA Grade 3 T5
1. Navigate to Thursday's schedule
2. Click on "ELA Grade 3 • T5 • 08:30 - 09:15"
3. **Expected:** "I will use map features to answer questions"
4. **Previously showed:** "I will preview text and cite supporting evidence" (wrong)

### Test Case 2: ELA Grade 2 209 (Co-Teaching)
1. Navigate to Thursday's schedule
2. Click on "ELA Grade 2 • 209 • 09:18 - 10:03"
3. **Expected:** "I will preview text and cite supporting evidence" (from ELA/SS slot)
4. **Previously showed:** Science objectives (wrong)

## Files Modified

- `d:/LP/frontend/src/utils/planMatching.ts`
  - Updated matching priority to favor subject over slot_number
  - Added `subjectsMatch()` for co-teaching scenarios (ELA/SS matches ELA and Social S.)
  - Added `getSubjectSpecificity()` to prefer compound subjects over simple ones
  - Removed `usedIndices` blocking to allow co-teaching slot sharing
  - Changed from `findIndex` to finding all matches and selecting most specific
  
- `d:/LP/frontend/src/components/LessonDetailView.tsx`
  - Removed positional fallback `slots[slot - 1]` 
  - Improved subject+grade+homeroom matching as fallback

## Impact

- **Fixes:** Misalignment between browser view and PDF/DOCX objectives
- **Supports:** Co-teaching scenarios (multiple schedule entries → one lesson plan slot)
- **Handles:** Non-instructional periods that offset slot numbering
- **Maintains:** Backward compatibility with existing lesson plans
