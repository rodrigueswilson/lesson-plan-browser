# Bug Fix: Slot Order Not Consistent Between Tabs

## Problem

Slot reordering worked correctly in the "Plans" tab (SlotConfigurator) but not in the "Home" tab (BatchProcessor):

- ✅ **Plans tab:** Slots displayed in correct order (sorted by `display_order`)
- ❌ **Home tab:** Slots displayed in original order (not sorted)

**User Impact:** After reordering slots in Plans tab, the order didn't match in Home tab, causing confusion.

## Root Cause

`SlotConfigurator` was sorting slots by `display_order`:
```typescript
const sortedSlots = [...slots].sort((a, b) => {
  const orderA = a.display_order ?? a.slot_number;
  const orderB = b.display_order ?? b.slot_number;
  return orderA - orderB;
});
```

But `BatchProcessor` was using the raw `slots` array without sorting:
```typescript
{slots.map((slot) => {  // ❌ Not sorted
```

## Solution

Added the same sorting logic to `BatchProcessor`:

```typescript
// Sort slots by display_order (same as SlotConfigurator)
const sortedSlots = [...slots].sort((a, b) => {
  const orderA = a.display_order ?? a.slot_number;
  const orderB = b.display_order ?? b.slot_number;
  return orderA - orderB;
});

// Use sortedSlots instead of slots
{sortedSlots.map((slot) => {
```

## Files Changed

- `frontend/src/components/BatchProcessor.tsx`:
  - Added sorting logic (line ~198)
  - Changed `slots.map` to `sortedSlots.map` (line ~387)

## Verification

**Before Fix:**
- Plans tab: Slots in correct order ✅
- Home tab: Slots in wrong order ❌

**After Fix:**
- Plans tab: Slots in correct order ✅
- Home tab: Slots in correct order ✅

## Status

✅ **FIXED** - Both tabs now display slots in the same order

---

**Date Fixed:** 2025-11-07  
**Impact:** Medium (UX consistency issue)

