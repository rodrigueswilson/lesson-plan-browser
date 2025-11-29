# Manual Validation Instructions

**Time required:** ~2 hours  
**Files to validate:** 3 files, ~190 links total  

---

## Step-by-Step Instructions

### **Step 1: Locate Input Files**

Find these files in your lesson plan folders:

1. **W38 Lang:**
   - `F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W38\Lang Lesson Plans 9_15_25-9_19_25.docx`

2. **W42 Davies:**
   - `F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W42\10_13-10_17 Davies Lesson Plans.docx`

3. **W37 Davies:**
   - `F:\rodri\Documents\OneDrive\AS\Lesson Plan\25 W37\Copy of 9_8-9_12 Davies Lesson Plans.docx`

---

### **Step 2: Process Each File**

**Using your normal workflow:**

1. Open the Bilingual Weekly Plan Builder app
2. Select the input file
3. Process it (the new threshold 0.55 will be used automatically)
4. Wait for processing to complete
5. Note the output file location

**OR if using command line:**
```bash
# Your normal processing command
python process_lesson_plan.py --input "path/to/input.docx"
```

---

### **Step 3: Open Output in Microsoft Word**

1. Navigate to the output file location
2. Open in Microsoft Word (not a text editor)
3. Enable editing if prompted

---

### **Step 4: Check Every Hyperlink**

**For EACH hyperlink in the document:**

#### **A. Find the link:**
- Hyperlinks appear as blue underlined text
- Or in the "Referenced Links" section at the end

#### **B. Click the link:**
- Does it open correctly? ☐ Yes ☐ No
- If broken, note it as a critical issue

#### **C. Check placement:**
- Which cell is it in? (Day + Section)
- Is this the correct cell?
  - Look at the link text (e.g., "LESSON 5")
  - Does it match the cell content?
  - Is it in the right day (Monday-Friday)?
  - Is it in the right section (Unit/Lesson, Objective, Instruction, etc.)?

#### **D. Classify the result:**
- **TP (True Positive):** Correct cell, inline ✓
- **FP (False Positive):** Wrong cell, inline ✗
- **TN (True Negative):** Correctly in "Referenced Links" ✓
- **FN (False Negative):** Should be inline, but in "Referenced Links" ✗

#### **E. Record in spreadsheet:**
```
Link# | Link Text | Expected Cell | Actual Cell | Working? | Result
1     | LESSON 5  | Unit Mon      | Unit Mon    | Yes      | TP
2     | Cool Down | Instr Tue     | Assess Tue  | Yes      | FP
```

---

### **Step 5: Calculate Rates**

**After checking all links in a file:**

```
TP rate = TP / (TP + FN) × 100
FP rate = FP / (FP + TN) × 100
Accuracy = (TP + TN) / Total × 100
```

**Example:**
- Total links: 46
- TP: 40, FP: 2, TN: 3, FN: 1
- TP rate = 40 / (40 + 1) × 100 = 97.6% ✓
- FP rate = 2 / (2 + 3) × 100 = 40% ✗ (FAIL)

---

### **Step 6: Check Success Criteria**

**Must achieve ALL:**
- ☐ TP rate ≥ 90%
- ☐ FP rate ≤ 5%
- ☐ Zero broken links
- ☐ No obvious misplacements

**If ANY fails:**
- ❌ DO NOT deploy
- ❌ Document the issues
- ❌ Revert threshold to 0.65
- ❌ Investigate problems

---

### **Step 7: Document Results**

**Save your findings:**

1. **Spreadsheet:** `docs/validation/manual_validation_results.xlsx`
   - Include all link checks
   - Summary statistics
   - Notes on issues

2. **Summary:** `docs/validation/manual_validation_results.md`
   - Use the template provided
   - Include aggregate results
   - Pass/fail decision

3. **Screenshots:** (if any false positives found)
   - Save to `docs/validation/screenshots/`
   - Show the incorrect placement

---

## Tips for Efficient Validation

### **Speed up the process:**

1. **Use keyboard shortcuts:**
   - Ctrl+Click to follow links
   - Alt+Tab to switch between Word and spreadsheet

2. **Batch similar checks:**
   - Check all "LESSON X" links together
   - Check all "Cool Down" links together

3. **Focus on suspicious links:**
   - Links with generic names ("Stage 6", "Activity")
   - Links that appear multiple times
   - Links in unexpected sections

4. **Use Word's navigation:**
   - Ctrl+F to find specific link text
   - Navigation pane to jump between sections

---

## Common Issues to Watch For

### **False Positives (Wrong Cell):**
- Link text: "Cool Down"
- Expected: Instruction section
- Actual: Assessment section
- **Why:** Generic text matches multiple cells

### **False Negatives (Should be inline):**
- Link text: "LESSON 5: REPRESENT PRODUCTS AS AREAS"
- Expected: Unit/Lesson Monday
- Actual: Referenced Links section
- **Why:** Text too long, no exact match

### **Broken Links:**
- Link doesn't open
- Opens to wrong URL
- 404 error
- **Critical:** Must be fixed before deploy

---

## What to Do If Validation Fails

### **If FP rate >5%:**

1. **Document the false positives:**
   - Which links?
   - What pattern? (generic text, duplicate text, etc.)
   - Which cells affected?

2. **Consider adjustments:**
   - Try threshold 0.58 or 0.60 (less aggressive)
   - Add safeguards for duplicate text
   - Improve hint matching

3. **Revert for now:**
   ```python
   # In docx_renderer.py line 29
   FUZZY_MATCH_THRESHOLD = 0.65  # Revert
   ```

### **If broken links found:**

1. **Critical issue** - Must fix before deploy
2. **Investigate:**
   - Is it the threshold change?
   - Or pre-existing issue?
3. **Test with threshold 0.65** to confirm

---

## Questions During Validation?

**If you're unsure about a classification:**

- **"Is this the right cell?"**
  - Look at the link text and cell content
  - Does it make sense contextually?
  - When in doubt, mark as FP (be conservative)

- **"Should this be inline or fallback?"**
  - If the link text appears in the cell → Should be inline
  - If the link text doesn't appear → Fallback is OK

- **"Is this a false positive?"**
  - If you have ANY doubt about the placement → Mark as FP
  - Better to be conservative

---

## After Validation

### **If PASS:**
1. Commit changes to git
2. Deploy to production
3. Begin daily monitoring

### **If FAIL:**
1. Revert threshold to 0.65
2. Document issues found
3. Investigate root causes
4. Consider alternative approaches

---

**Good luck with the validation! Take your time and be thorough.**
