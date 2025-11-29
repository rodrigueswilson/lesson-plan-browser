# Verify Slot Matching Fix

## Problem Fixed

**Issue:** "ELA Grade 2 • 209 • 09:18 - 10:03" was showing Science objectives instead of ELA/SS objectives.

**Root Cause:** When multiple lesson plan slots matched a schedule entry (both "ELA" and "ELA/SS" matched "ELA" from schedule), the code was returning the FIRST match (index 0 - "ELA") instead of the more SPECIFIC match (index 1 - "ELA/SS").

## Solution

Added **subject specificity ranking** to prefer compound subjects over simple ones:
- "ELA/SS" (specificity: 2) beats "ELA" (specificity: 1)
- "Math/Science" (specificity: 2) beats "Math" (specificity: 1)
- Etc.

## How to Verify

### Step 1: Open the app
The frontend is already running with the fix applied (auto-reloaded via HMR).

### Step 2: Test ELA Grade 2 209
1. Navigate to Thursday's schedule
2. Click on **"ELA Grade 2 • 209 • 09:18 - 10:03"**
3. **Expected objective:** "I will preview text and cite supporting evidence"
4. This should come from the ELA/SS slot, NOT the plain ELA slot or Science slot

### Step 3: Test Social S. Grade 2 209  
1. Click on **"SOCIAL S. Grade 2 • 209 • 10:06 - 10:51"** (if visible)
2. **Expected objective:** "I will preview text and cite supporting evidence" (same as ELA)
3. Both ELA and Social S. for Grade 2 209 should share the ELA/SS lesson plan slot

### Step 4: Test ELA Grade 3 T5
1. Click on **"ELA Grade 3 • T5 • 08:30 - 09:15"**
2. **Expected objective:** "I will use map features to answer questions"
3. This should come from the plain ELA slot (slot 0), not ELA/SS

## Expected Results

| Schedule Entry | Should Match | Student Goal |
|---|---|---|
| ELA Grade 3 T5 08:30-09:15 | Slot 0: ELA | "I will use map features to answer questions" |
| ELA Grade 2 209 09:18-10:03 | Slot 1: ELA/SS | "I will preview text and cite supporting evidence" |
| Social S. Grade 2 209 10:06-10:51 | Slot 1: ELA/SS | "I will preview text and cite supporting evidence" |

## Technical Details

**Before fix:**
```
Schedule: ELA Grade 2 209
Lesson slots: [0: ELA, 1: ELA/SS, 2: Science, ...]
Match process:
  - Slot 0 (ELA) matches? YES (ELA === ELA)
  - Return slot 0 ✗ WRONG
```

**After fix:**
```
Schedule: ELA Grade 2 209  
Lesson slots: [0: ELA, 1: ELA/SS, 2: Science, ...]
Match process:
  - Find ALL matches: [0, 1]
  - Slot 0 specificity: 1 (simple "ELA")
  - Slot 1 specificity: 2 (compound "ELA/SS")
  - Return slot 1 ✓ CORRECT
```
