# W43 Manual Validation Plan

**Date:** 2025-10-19  
**Week:** 25 W43 (10/20-10/24)  
**Purpose:** Validate threshold change while creating production lesson plans  

---

## ✅ Perfect Approach

**Why this is better:**
- ✓ Real production use case
- ✓ You need to create these anyway
- ✓ Immediate practical feedback
- ✓ Validates on current week's data

---

## Files to Process & Validate

### **File 1: Davies (10_20-10_24)**
- **Input:** `25 W43\10_20-10_24 Davies Lesson Plans.docx`
- **Expected links:** ~80 links
- **Baseline:** 60% inline (from earlier data)
- **Expected improvement:** → 100% (based on simulation)

### **File 2: Lang (10_20_25-10_24_25)**
- **Input:** `25 W43\Lang Lesson Plans 10_20_25-10_24_25.docx`
- **Expected links:** ~78 links
- **Baseline:** 62% inline (from earlier data)
- **Expected improvement:** → 100% (based on simulation)

### **File 3: Savoca (10_20_25-10_25_25)**
- **Input:** `25 W43\Ms. Savoca-10_20_25-10_25_25 Lesson plans.docx`
- **Expected links:** ~19 links
- **Baseline:** 100% inline (already perfect)
- **Expected:** Stay at 100%

**Total: ~177 links to validate**

---

## Validation Process

### **Step 1: Process Files (Your Normal Workflow)**

1. Open Bilingual Weekly Plan Builder
2. Process each file one by one
3. The new threshold (0.55) will be used automatically
4. Save outputs with your normal naming

---

### **Step 2: Review Each Output**

**As you review for submission:**

1. **Open in Word** (you'll do this anyway)
2. **Check hyperlinks as you review content:**
   - Click links to verify they work
   - Note if any are in wrong cells
   - Note if any are broken
3. **Quick tally:**
   - How many links are inline vs. "Referenced Links"?
   - Any false positives (wrong cell)?
   - Any broken links?

---

### **Step 3: Quick Recording**

**Don't need detailed spreadsheet - just track:**

**For each file:**
```
File: Davies W43
Total links: ~80
Inline: ___ (count from document)
In "Referenced Links": ___ (count at end)
False positives: ___ (links in wrong cells)
Broken links: ___ (links that don't work)

Issues found:
- [List any problems]

Overall: ☐ Good ☐ Issues
```

---

## Quick Success Check

**After processing all 3 files:**

### **Must be true:**
- ☐ Most links are inline (not in "Referenced Links")
- ☐ No more than 2-3 links in obviously wrong cells
- ☐ Zero broken links
- ☐ No teacher complaints when you submit

### **Red flags:**
- ✗ Many links in wrong sections
- ✗ Broken links
- ✗ More links in "Referenced Links" than before

---

## Simplified Validation Template

### **File 1: Davies W43**

**Quick counts:**
- Total links: ___
- Inline: ___
- Referenced Links section: ___
- Inline rate: ___% (target: >60%)

**Issues:**
- False positives: ___ (which links? which cells?)
- Broken links: ___ (which links?)
- Other issues: ___

**Decision:** ☐ Looks good ☐ Has issues

---

### **File 2: Lang W43**

[Same as above]

---

### **File 3: Savoca W43**

[Same as above]

---

## Aggregate Results

**Total across all 3 files:**
- Total links: ___
- Inline: ___
- Referenced Links: ___
- Overall inline rate: ___% (target: ≥45%)

**Issues found:**
- False positives: ___
- Broken links: ___
- Other: ___

---

## Decision

### **If everything looks good:**
- ✅ Submit the lesson plans as normal
- ✅ Note: "Threshold change validated on W43"
- ✅ Proceed with deployment
- ✅ Continue monitoring next week

### **If issues found:**
- ⚠️ Document the issues
- ⚠️ Decide: Submit anyway or reprocess with old threshold?
- ⚠️ Consider reverting threshold change

---

## Practical Tips

### **While reviewing for submission:**

1. **Check content first** (your priority)
2. **Then check links** (quick pass)
3. **Don't spend too much time** - just note obvious issues
4. **Focus on:**
   - Broken links (critical)
   - Links in obviously wrong cells (false positives)
   - Overall improvement vs. last week

### **Quick link check:**

**For each section (Unit/Lesson, Objective, etc.):**
- Scan for blue underlined text (hyperlinks)
- Click 1-2 links to verify they work
- Check if they make sense in that cell
- Move on

**At the end:**
- Check "Referenced Links" section
- Count how many links are there
- Compare to previous weeks

---

## Time Estimate

**Added to your normal workflow:**
- **Davies:** +10 minutes for link checking
- **Lang:** +10 minutes for link checking
- **Savoca:** +5 minutes for link checking
- **Total:** +25 minutes on top of normal review

---

## What to Look For

### **Good signs:**
- ✓ Fewer links in "Referenced Links" section
- ✓ More links inline in cells
- ✓ Links make sense in their cells
- ✓ All links work

### **Bad signs:**
- ✗ Links in wrong sections (e.g., "Cool Down" in Assessment instead of Instruction)
- ✗ Broken links
- ✗ More links in "Referenced Links" than usual
- ✗ Duplicate links in multiple cells

---

## After Validation

### **If successful:**
1. Submit lesson plans as normal
2. Note in commit message: "Validated on W43 production files"
3. Deploy threshold change
4. Monitor next week

### **If issues:**
1. Document what you found
2. Decide if issues are acceptable
3. Consider reprocessing with old threshold (0.65)
4. Investigate before wider deployment

---

**This approach is perfect - you validate while doing real work!**

**Just process your W43 files normally, review them as you always do, and note any link issues. Much more practical than artificial validation.**
