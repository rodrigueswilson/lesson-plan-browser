# Metrics Verification Guide

## ✅ How to Verify Metrics Are Loading Correctly

### Quick Check List

1. **Summary Cards Display Numbers**
   - ✅ Total Plans: Shows a number (e.g., 74)
   - ✅ Avg Time Per Plan: Shows time (e.g., 7m 12s)
   - ✅ Total Tokens: Shows tokens (e.g., 4.5M)
   - ✅ Total Cost: Shows cost (e.g., $1.32)

2. **Charts Display Data**
   - ✅ Model Distribution: Pie chart shows models
   - ✅ Workflow Performance: Bar chart shows operations
   - ✅ Daily Activity: Line chart shows Plans and Cost over time

3. **Operation Breakdown Table Shows Data**
   - ✅ Table has at least one row
   - ✅ Shows Phase, Operation, Avg Time, Count, % of Total
   - ✅ Phase Summary boxes show totals

### What You're Seeing is CORRECT ✅

**If you see:**
- `process_slot` = 100% → **This is normal!** It means all operations are `process_slot`
- Only one operation type → **This is expected** if you've only processed weekly plans
- PROCESS phase highlighted → **Correct!** `process_slot` is categorized as PROCESS

### Common Questions

**Q: Why does one operation show 100%?**  
A: Because all tracked operations are of that type. This is normal if you've only used one feature.

**Q: Is the data accurate?**  
A: Yes! The metrics come directly from your performance tracking database.

**Q: Why don't I see PARSE or RENDER phases?**  
A: You'll see them when you use features that include parsing or rendering operations.

### Verification Steps

1. **Check Browser Console**
   - Open DevTools (F12)
   - Look for any errors in Console tab
   - Should see: `[API] GET /api/analytics/summary`

2. **Check Network Tab**
   - Open DevTools → Network tab
   - Refresh Analytics page
   - Look for `/api/analytics/summary` request
   - Status should be `200 OK`
   - Response should contain JSON with `total_plans`, `operation_breakdown`, etc.

3. **Visual Check**
   - Summary cards show numbers (not 0 or "Loading...")
   - Charts display (not empty)
   - Table shows operations
   - No error messages displayed

### If Metrics Are NOT Loading

**Symptoms:**
- Cards show "0" or "Loading..."
- Charts are empty
- Error message displayed
- Console shows errors

**Check:**
1. Is FastAPI backend running? (`http://localhost:8000/api/health`)
2. Are there any operations in the database?
3. Check browser console for errors
4. Check Network tab for failed requests

### Status Indicators

✅ **Loading Correctly:**
- Numbers in summary cards
- Charts display data
- Table shows operations
- No error messages

❌ **Not Loading:**
- Cards show 0 or loading spinner
- Charts empty
- Error message displayed
- Console errors

---

## Your Current Status

Based on what you're seeing:
- ✅ **Metrics ARE loading correctly**
- ✅ **Data is accurate**
- ✅ **Display is working**

The `process_slot` = 100% is **normal and expected** when that's your only operation type.

---

**Date:** 2025-11-07  
**Status:** ✅ Metrics Working Correctly

