# Manual Validation Template

**Date:** 2025-10-19  
**Validator:** [Your name]  
**Threshold:** 0.55 (lowered from 0.65)  

---

## Files to Validate

### **File 1: W38 Lang (High Baseline)**
- **Expected baseline:** 80% inline
- **Total links:** ~46
- **Purpose:** Verify no regression on high-performing files

### **File 2: W42 Davies (Medium Baseline)**
- **Expected baseline:** 38% inline
- **Total links:** ~65
- **Purpose:** Expect moderate improvement

### **File 3: W37 Davies (Low Baseline)**
- **Expected baseline:** 24% inline
- **Total links:** ~79
- **Purpose:** Expect most improvement

**Total links to validate:** ~190

---

## Validation Process

### **For Each File:**

1. **Process the file** with your normal workflow
2. **Open output in Microsoft Word**
3. **Check EVERY hyperlink:**
   - Click to verify it works
   - Check if it's in the correct cell
   - Note if it's a false positive

4. **Record results** in spreadsheet (see below)

---

## Results Template

### **File 1: W38 Lang**

| Link# | Link Text | Expected Cell | Actual Cell | Working? | Result |
|-------|-----------|---------------|-------------|----------|--------|
| 1 | | | | ☐ Yes ☐ No | ☐ TP ☐ FP ☐ TN ☐ FN |
| 2 | | | | ☐ Yes ☐ No | ☐ TP ☐ FP ☐ TN ☐ FN |
| ... | | | | | |

**Summary:**
- Total links: ___
- True Positives (TP): ___
- False Positives (FP): ___
- True Negatives (TN): ___
- False Negatives (FN): ___
- Broken links: ___

**Rates:**
- TP rate: ___ % (target: ≥90%)
- FP rate: ___ % (target: ≤5%)
- Accuracy: ___ %

---

### **File 2: W42 Davies**

[Same template as above]

---

### **File 3: W37 Davies**

[Same template as above]

---

## Aggregate Results

**Total across all files:**
- Total links: ___
- True Positives: ___
- False Positives: ___
- True Negatives: ___
- False Negatives: ___
- Broken links: ___

**Aggregate rates:**
- TP rate: ___ % (target: ≥90%)
- FP rate: ___ % (target: ≤5%)
- Accuracy: ___ %

---

## Decision

### **Pass Criteria:**
- ☐ TP rate ≥ 90%
- ☐ FP rate ≤ 5%
- ☐ Zero broken links
- ☐ No obvious misplacements

### **Result:**
- ☐ **PASS** - Proceed with deployment
- ☐ **FAIL** - Revert threshold to 0.65

### **Notes:**
[Any observations, patterns, or issues found]

---

## Categories Explained

- **TP (True Positive):** Link is inline in the CORRECT cell ✓
- **FP (False Positive):** Link is inline in the WRONG cell ✗
- **TN (True Negative):** Link is correctly in "Referenced Links" fallback ✓
- **FN (False Negative):** Link should be inline but is in fallback ✗

---

**Save this file as:** `manual_validation_results.md`
