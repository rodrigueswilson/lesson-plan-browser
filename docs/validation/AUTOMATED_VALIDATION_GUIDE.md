# Automated Validation Guide

**Script:** `tools/validate_threshold_change.py`  
**Purpose:** Automatically analyze input/output files to validate threshold change  

---

## 🚀 Quick Start

### **Step 1: Generate Your W43 Lesson Plans**

1. Open the Bilingual Weekly Plan Builder app
2. Process your 3 W43 files:
   - Davies: `10_20-10_24 Davies Lesson Plans.docx`
   - Lang: `Lang Lesson Plans 10_20_25-10_24_25.docx`
   - Savoca: `Ms. Savoca-10_20_25-10_25_25 Lesson plans.docx`
3. Note the output file names (they'll have timestamps)

---

### **Step 2: Update the Script**

**Edit `tools/validate_threshold_change.py` line ~235:**

Replace the output paths with your actual generated files:

```python
pairs = [
    {
        'name': 'Davies W43',
        'input': base_dir / '10_20-10_24 Davies Lesson Plans.docx',
        'output': base_dir / 'Wilson_Rodrigues_Weekly_W43_10-20-10-24_20251019_XXXXXX.docx'  # Your actual file
    },
    {
        'name': 'Lang W43',
        'input': base_dir / 'Lang Lesson Plans 10_20_25-10_24_25.docx',
        'output': base_dir / 'Wilson_Rodrigues_Weekly_W43_10-20-10-24_20251019_YYYYYY.docx'  # Your actual file
    },
    {
        'name': 'Savoca W43',
        'input': base_dir / 'Ms. Savoca-10_20_25-10_25_25 Lesson plans.docx',
        'output': base_dir / 'Wilson_Rodrigues_Weekly_W43_10-20-10-24_20251019_ZZZZZZ.docx'  # Your actual file
    }
]
```

---

### **Step 3: Run the Validation**

```bash
cd d:\LP
python tools/validate_threshold_change.py
```

---

## 📊 What the Script Does

### **Automatic Analysis:**

1. **Parses input files** - Extracts all hyperlinks
2. **Parses output files** - Categorizes links as inline or fallback
3. **Calculates rates:**
   - Inline rate (target: ≥45%)
   - Fallback rate
   - False positive rate (target: ≤5%)
4. **Detects issues:**
   - Broken links (critical!)
   - Potential false positives
   - Duplicate generic text
5. **Generates report** - Pass/fail decision

---

## ✅ Success Criteria

**The script checks:**
- ☐ Inline rate ≥ 45%
- ☐ FP rate ≤ 5%
- ☐ Zero broken links

**If all pass:** ✓ Safe to deploy  
**If any fail:** ✗ Review issues

---

## 📋 Example Output

```
================================================================================
AUTOMATED THRESHOLD VALIDATION
================================================================================

Validating threshold change (0.65 → 0.55)
Analyzing W43 lesson plans

================================================================================
Validating: Davies W43
================================================================================

1. Parsing input file...
   Found 80 hyperlinks in input

2. Analyzing output file...
   Inline links: 75
   Fallback links: 5

3. Results:
   Total links: 80
   Inline: 75 (93.8%)
   Fallback: 5 (6.2%)
   Broken: 0
   Potential false positives: 2

================================================================================
VALIDATION SUMMARY
================================================================================

Total links analyzed: 177

Placement:
  Inline: 165 (93.2%)
  Fallback: 12 (6.8%)

Issues:
  Broken links: 0
  Potential false positives: 4 (2.3%)


PER-FILE RESULTS:
File                           Total    Inline     Fallback   FP      
----------------------------------------------------------------------
Davies W43                     80       75         5          2       
Lang W43                       78       75         3          2       
Savoca W43                     19       19         0          0       


SUCCESS CRITERIA:
  ✓ PASS: Inline rate ≥ 45%
  ✓ PASS: FP rate ≤ 5%
  ✓ PASS: Zero broken links


FINAL RESULT:
  ✓ VALIDATION PASSED
  → Threshold change is working well
  → Safe to deploy to production

💾 Detailed results saved to: d:/LP/docs/validation/W43_validation_results.json
```

---

## 🔍 Understanding the Results

### **Inline Rate:**
- **Good:** >60%
- **Acceptable:** 45-60%
- **Poor:** <45%

### **False Positive Rate:**
- **Good:** <3%
- **Acceptable:** 3-5%
- **Poor:** >5%

### **Broken Links:**
- **Critical:** Any broken links = FAIL
- Must be zero

---

## ⚠️ If Validation Fails

### **High FP Rate (>5%):**

1. **Review the false positives:**
   - Check `W43_validation_results.json`
   - Look for patterns (duplicate text, generic names)

2. **Consider adjusting threshold:**
   - Try 0.58 or 0.60 (less aggressive)
   - Reprocess and validate again

3. **Or accept and monitor:**
   - If FPs are minor (5-8%)
   - Monitor in production
   - Can adjust later

### **Broken Links:**

1. **Critical issue** - Must fix
2. **Check if it's the threshold:**
   - Reprocess with old threshold (0.65)
   - Compare results
3. **If still broken:**
   - Issue with input files
   - Not related to threshold

### **Low Inline Rate (<45%):**

1. **Unexpected** - Should improve
2. **Check:**
   - Are files processed correctly?
   - Is threshold actually 0.55?
   - Any errors during processing?

---

## 📁 Output Files

**The script generates:**

1. **Console output** - Summary and results
2. **JSON file:** `docs/validation/W43_validation_results.json`
   - Detailed results
   - All link data
   - False positive details

---

## 🎯 Next Steps

### **If PASS:**
1. ✅ Review the output files manually (quick check)
2. ✅ Submit W43 lesson plans
3. ✅ Commit threshold change
4. ✅ Deploy to production

### **If FAIL:**
1. ⚠️ Review the issues
2. ⚠️ Decide: adjust threshold or revert
3. ⚠️ Reprocess if needed
4. ⚠️ Re-validate

---

## 💡 Tips

### **Quick Manual Spot-Check:**

Even with automated validation, do a quick visual check:
1. Open one output file in Word
2. Click 2-3 links to verify they work
3. Scan for obvious misplacements
4. Check "Referenced Links" section

### **Comparing to Previous Week:**

Check W42 outputs to see improvement:
- W42 Davies: 38% inline
- W43 Davies: Should be >60%

---

**This automated validation is much faster and more thorough than manual checking!**

**Just generate your files, update the script paths, and run it. Takes ~2 minutes!**
