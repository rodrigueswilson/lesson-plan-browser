# W43 Validation Results - FAILED

**Date:** 2025-10-19  
**Threshold tested:** 0.55 (lowered from 0.65)  
**Result:** ❌ VALIDATION FAILED  

---

## 📊 Actual Results

**From manual inspection:**
- **4 "Referenced Links" sections found** with ~77+ links total
- Many links that should be inline are in fallback sections
- Examples of links in fallback:
  - LESSON 5, 6, 7, 8 (curriculum links)
  - Teacher Guides
  - Cool Down activities
  - Practice Problems
  - Stage activities
  - Science lesson links

**Script results were misleading:**
- Script counted 47 links in Table 1 (Davies daily plans)
- But missed 77 links in Table 9 (another teacher's daily plans)
- Script didn't detect "Referenced Links" sections properly
- Total: 181 links, but many are in fallback sections

---

## ❌ Why It Failed

### **Root Cause:**
The threshold change (0.65 → 0.55) did NOT improve placement as expected.

### **Possible reasons:**
1. **Links lack metadata** - section_hint/day_hint missing
2. **Context matching still too weak** - Even at 0.55, not matching
3. **Multiple teachers in one file** - Confusion in placement logic
4. **Curriculum links** - "LESSON X" and "Teacher Guide" not recognized

---

## 🔍 Analysis

### **Links in fallback that should be inline:**

**Curriculum links (should be in Unit/Lesson row):**
- LESSON 5: REPRESENT PRODUCTS AS AREAS
- LESSON 6: DIFFERENT SQUARE UNITS (PART 1)
- LESSON 7: DIFFERENT SQUARE UNITS (PART 2)
- LESSON 8: AREA OF A RECTANGLE WITHOUT A GRID
- 3.2.5 Teacher Guide
- 3.2.6 Teacher Guide
- 3.2.7 Teacher Guide
- 3.2.8 Teacher Guide

**Activity links (should be in Instruction/Assessment rows):**
- Capture Squares: Stage 6, 7
- Rectangle Rumble: Stage 1, 2
- Five in a Row: Addition and Subtraction: Stage 6, 7

**Assessment links (should be in Assessment/Homework rows):**
- 3.2.5 Cool Down
- 3.2.6 Cool Down
- 3.2.7 Cool Down
- 3.2.8 Cool Down
- Practice Problems
- Item UIN links

**Science links (should be in appropriate cells):**
- Lesson 2 Day 5- Elaborate and Evaluate
- Lesson 3 Day 1- Assess and Engage
- Motion and Forces Lesson 2 Test.docx
- 2nd Grade Science

---

## 📉 Comparison to Baseline

**Expected:**
- Baseline: 34.4% inline
- Target with 0.55: ≥45% inline
- Optimistic: 60-70% inline

**Actual:**
- Inline: ~47 links in one table
- Fallback: ~77+ links in 4 sections
- **Estimated inline rate: ~38%** (worse than or equal to baseline!)

---

## 🚨 Critical Issues

1. **Threshold change didn't help** - Still many links in fallback
2. **Validation script was buggy** - Gave false positive (100% inline)
3. **Multiple teachers in one file** - May have confused the logic
4. **Curriculum links not recognized** - Missing section_hint

---

## 🔄 Decision: REVERT

**Recommendation:** Revert threshold back to 0.65

**Reasons:**
1. No improvement over baseline (possibly worse)
2. Many curriculum links still in fallback
3. Threshold alone is not sufficient
4. Need to address root causes first

---

## 📝 Root Causes to Address

### **1. Missing section_hint for curriculum links**
- Parser doesn't recognize "LESSON X" rows
- Parser doesn't recognize "Teacher Guide" links
- These need special handling

### **2. Context matching too weak**
- Even at 0.55, not matching curriculum links
- Need better context extraction
- Or need structural hints instead of fuzzy matching

### **3. Multiple teachers in one file**
- 5 teachers combined in one output
- May be confusing the placement logic
- Need to test with single-teacher files

---

## 🎯 Next Steps

### **Option A: Revert and Investigate**
1. Revert threshold to 0.65
2. Investigate why curriculum links aren't matching
3. Improve parser to extract section_hint
4. Test again with better metadata

### **Option B: Try Different Approach**
1. Keep threshold at 0.55
2. Add special handling for curriculum links
3. Improve context extraction
4. Test on single-teacher files first

### **Option C: Accept Current State**
1. Keep threshold at 0.65 (baseline)
2. Document that 34-38% inline is acceptable
3. Focus on other improvements
4. Get teacher feedback on UX

---

## 📊 Detailed Link Analysis

**From the 4 "Referenced Links" sections:**

### **Section 1: Math (Davies) - ~77 links**
- Curriculum: LESSON 5-8, Teacher Guides
- Activities: Capture Squares, Rectangle Rumble, Five in a Row
- Assessment: Cool Downs, Practice Problems, Item UIDs
- Science: Lesson 2, Lesson 3, Test

### **Section 2: Math (Lang?) - ~1 link**
- 2.2.5 Cool Down

### **Section 3: Science (Piret?) - ~4 links**
- 2nd Grade Science (4 instances)

### **Section 4: Science (Savoca?) - ~4 links**
- video note taking worksheet
- Lesson 2 Day 5
- Lesson 3 Day 1
- Motion and Forces Test

**Total fallback: ~86 links**

---

## 🎓 Lessons Learned

1. **Automated validation scripts can be misleading** - Always do manual check
2. **Threshold alone is not enough** - Need better metadata and context
3. **Multi-teacher files are complex** - Test on single-teacher first
4. **Curriculum links need special handling** - Parser enhancement required
5. **Visual inspection is essential** - Scripts missed the fallback sections

---

## 💡 Recommendations

### **Immediate:**
1. ❌ **DO NOT deploy** threshold change
2. ⚠️ **Revert** to 0.65
3. 📋 **Document** findings
4. 🔍 **Investigate** root causes

### **Short-term:**
1. Improve parser to recognize curriculum links
2. Add section_hint for "LESSON X" rows
3. Test on single-teacher files
4. Improve validation scripts

### **Long-term:**
1. Get teacher feedback on UX
2. Consider alternative placement strategies
3. Improve context extraction
4. Add telemetry for better debugging

---

**Status:** ❌ Validation failed, threshold change NOT recommended for deployment
