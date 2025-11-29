# Implementation Plan - Final Version 2.0

**Status:** Ready for implementation  
**Date:** 2025-10-19  
**Supersedes:** All previous plans (Consensus Summary, Implementation Plan Final, etc.)  

---

## 🎯 What We're Actually Doing

**ONE CHANGE ONLY:** Lower fuzzy matching threshold from 0.65 to 0.55

**That's it. Nothing else.**

---

## 📊 Why This Change?

### **Evidence:**
- Current inline rate: 34.4%
- Research-validated approach (industry best practices)
- Expected improvement: +10-15% (conservative)
- Low risk, easily reversible

### **Why NOT other approaches:**
- ❌ Parser enhancement: Only fixes 32% of missing hints (not 90%)
- ❌ Coordinate placement: Templates don't match input→output
- ❌ "Keep in cells": No teacher validation

**See ADR_001 for full rationale.**

---

## 📋 Implementation Steps

### **Step 1: Fix Pairing Logic (1 hour) - PREREQUISITE**

**Problem:** Current simulation pairs first output found, making all metrics unreliable.

**Solution:** Create deterministic pairing script

**File:** `d:\LP\tools\fix_pairing_logic.py`

```python
"""
Fix input/output pairing logic.
Match by teacher name + date range.
"""

import re
from pathlib import Path
from typing import Optional, Tuple

def extract_teacher(filename: str) -> str:
    """Extract teacher name from filename."""
    name_lower = filename.lower()
    if 'davies' in name_lower:
        return 'Davies'
    elif 'lang' in name_lower:
        return 'Lang'
    elif 'savoca' in name_lower:
        return 'Savoca'
    elif 'piret' in name_lower:
        return 'Piret'
    return 'Unknown'

def extract_date_range(filename: str) -> Optional[str]:
    """Extract date range from filename (MM-DD-MM-DD format)."""
    # Try MM_DD_YY-MM_DD_YY
    match = re.search(r'(\d{1,2})[_-](\d{1,2})[_-](\d{2,4})[_-](\d{1,2})[_-](\d{1,2})', filename)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(4)}-{match.group(5)}"
    
    # Try MM-DD-MM-DD
    match = re.search(r'(\d{1,2})-(\d{1,2})-(\d{1,2})-(\d{1,2})', filename)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}-{match.group(4)}"
    
    return None

def find_matching_output(input_file: Path, output_files: list[Path]) -> Optional[Path]:
    """Find matching output file for input."""
    input_dates = extract_date_range(input_file.name)
    
    if not input_dates:
        return None
    
    for output_file in output_files:
        output_dates = extract_date_range(output_file.name)
        if output_dates == input_dates:
            return output_file
    
    return None

def validate_pairing(folder_path: str):
    """Validate pairing logic on all files."""
    folder = Path(folder_path)
    week_folders = [d for d in folder.iterdir() if d.is_dir() and 'W' in d.name]
    
    results = []
    
    for week_dir in sorted(week_folders):
        all_files = [f for f in week_dir.glob('*.docx') if not f.name.startswith('~')]
        
        primary_files = []
        bilingual_files = []
        
        for f in all_files:
            if 'rodrigues' in f.name.lower() or 'wilson' in f.name.lower():
                bilingual_files.append(f)
            else:
                primary_files.append(f)
        
        for primary in primary_files:
            match = find_matching_output(primary, bilingual_files)
            results.append({
                'week': week_dir.name,
                'input': primary.name,
                'output': match.name if match else None,
                'teacher': extract_teacher(primary.name),
                'matched': bool(match)
            })
    
    # Print summary
    matched = sum(1 for r in results if r['matched'])
    total = len(results)
    
    print(f"\nPairing Results:")
    print(f"  Matched: {matched}/{total} ({matched/total*100:.1f}%)")
    print(f"  Unmatched: {total-matched}")
    
    print(f"\nUnmatched files:")
    for r in results:
        if not r['matched']:
            print(f"  {r['week']}: {r['input']}")
    
    return results

if __name__ == '__main__':
    results = validate_pairing(r'F:\rodri\Documents\OneDrive\AS\Lesson Plan')
    
    # Save results
    import json
    with open('d:/LP/pairing_validation.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: d:/LP/pairing_validation.json")
```

**Deliverable:** Validated pairing logic + results JSON

**Success criteria:** >80% files matched

---

### **Step 2: Implement Threshold Change + Logging (1 hour)**

**File:** `d:\LP\tools\docx_renderer.py`

**Changes:**

```python
# At top of file (after imports)
import logging

# Feature flag for threshold experiment
FUZZY_MATCH_THRESHOLD = 0.55  # Lowered from 0.65 for improved placement
# To revert: change back to 0.65

logger = logging.getLogger(__name__)
```

**In `_calculate_match_confidence` method (around line 910):**

```python
if context_score >= FUZZY_MATCH_THRESHOLD:
    # Log successful placement
    logger.info("hyperlink_placement", extra={
        "link_text": media.get('text', '')[:100],
        "link_url": media.get('url', ''),
        "section_hint": media.get('section_hint'),
        "day_hint": media.get('day_hint'),
        "target_section": section_name,
        "target_day": day_name,
        "strategy": "fuzzy_context",
        "confidence": float(context_score),
        "threshold": FUZZY_MATCH_THRESHOLD,
        "success": True
    })
    
    # Check for hint matches to boost confidence
    hint_matches = 0
    if day_name and media.get('day_hint') == day_name:
        hint_matches += 1
    if section_name and media.get('section_hint') == section_name:
        hint_matches += 1
    
    if hint_matches > 0:
        boosted_score = min(1.0, context_score + (hint_matches * 0.1))
        return (boosted_score, f'context_with_{hint_matches}_hints')
    
    return (context_score, 'fuzzy_context')
```

**In `_append_unmatched_media` method:**

```python
def _append_unmatched_media(self, doc, pending_hyperlinks, pending_images):
    """Append unmatched media to fallback section."""
    
    # Log fallback count
    logger.info("referenced_links_fallback", extra={
        "hyperlink_count": len(pending_hyperlinks),
        "image_count": len(pending_images),
        "file": getattr(self, 'current_file', 'unknown')
    })
    
    # Log each fallback link
    for link in pending_hyperlinks:
        logger.info("hyperlink_placement", extra={
            "link_text": link.get('text', '')[:100],
            "link_url": link.get('url', ''),
            "section_hint": link.get('section_hint'),
            "day_hint": link.get('day_hint'),
            "target_section": None,
            "target_day": None,
            "strategy": "fallback",
            "confidence": 0.0,
            "threshold": FUZZY_MATCH_THRESHOLD,
            "success": False
        })
    
    # ... existing logic to append to document
```

**Deliverable:** Updated `docx_renderer.py` with threshold + logging

---

### **Step 3: Manual Validation (2 hours)**

**Select 3 files:**
1. **High baseline:** W38 Lang (80% inline)
2. **Medium baseline:** W42 Davies (38% inline)
3. **Low baseline:** W37 Davies (24% inline)

**For EACH file, check EVERY hyperlink:**

**Validation spreadsheet:** `manual_validation_results.xlsx`

| File | Link Text | Expected Cell | Actual Cell | Strategy | Confidence | Result |
|------|-----------|---------------|-------------|----------|------------|--------|
| W38_Lang | LESSON 5 | Unit/Lesson Mon | Unit/Lesson Mon | exact | 1.0 | TP |
| W38_Lang | Cool Down | Instruction Tue | Assessment Tue | fuzzy_0.55 | 0.58 | FP |
| W38_Lang | Stage 6 | Referenced Links | Referenced Links | fallback | 0.0 | TN |

**Categories:**
- **TP (True Positive):** Correct cell, inline
- **FP (False Positive):** Wrong cell, incorrect
- **TN (True Negative):** Correctly in fallback
- **FN (False Negative):** Should be inline, but in fallback

**Calculate rates:**
```
TP rate = TP / (TP + FN) * 100
FP rate = FP / (FP + TN) * 100
```

**Success criteria:**
- TP rate ≥ 90%
- FP rate ≤ 5%
- Zero broken links

**Deliverable:** Validation spreadsheet + summary JSON

---

### **Step 4: Deploy + Monitor (1 week)**

**If validation passes:**

1. **Commit changes:**
   ```bash
   git add tools/docx_renderer.py
   git commit -m "Lower fuzzy match threshold to 0.55 for improved placement"
   ```

2. **Deploy to production**

3. **Process 10-20 files**

4. **Monitor daily (5 min):**
   - Check logs for "referenced_links_fallback" count
   - Spot-check 2-3 output files
   - Note any teacher complaints

5. **Track metrics:**
   ```python
   # Parse logs
   inline_count = count(strategy != "fallback")
   fallback_count = count(strategy == "fallback")
   inline_rate = inline_count / total * 100
   
   fp_count = count(manual_validation_FP)
   fp_rate = fp_count / total * 100
   ```

**Red flags (revert immediately):**
- FP rate >8%
- Teacher complaints
- Broken links

**Reversion:**
```python
# In docx_renderer.py
FUZZY_MATCH_THRESHOLD = 0.65  # Revert to original
```

**Deliverable:** Daily monitoring log

---

### **Step 5: Teacher Feedback (Week 2)**

**Schedule NOW (not "later"):**

**Participants:** 3-5 teachers  
**Format:** 30-minute interview + mockups  
**Date:** [Schedule specific date]

**Mockups to prepare:**
1. **Version A:** Current (inline + Referenced Links)
2. **Version B:** Inline + end-of-cell "Links:"
3. **Version C:** All links at end of document

**Questions:**
1. How do you use hyperlinks in lesson plans?
2. Is "Referenced Links" section helpful or annoying?
3. Which version do you prefer? (Show mockups)
4. How many links per cell is too many?
5. Any issues with current placement?

**Deliverable:** `teacher_feedback_summary.md`

---

### **Step 6: Final Decision (Week 3)**

**Review data:**
- Manual validation results
- Telemetry (1 week)
- Teacher feedback
- FP rate actual vs. expected

**Decision matrix:**

| Metric | Target | Actual | Pass? |
|--------|--------|--------|-------|
| Inline rate | ≥45% | ??? | ??? |
| FP rate | ≤5% | ??? | ??? |
| Teacher satisfaction | Positive | ??? | ??? |
| Broken links | 0 | ??? | ??? |

**Outcomes:**
- **All pass:** Keep change, document success
- **Most pass:** Keep with adjustment (e.g., 0.58)
- **Any fail:** Revert to 0.65, reassess

**Deliverable:** Final decision document

---

## ⏱️ Timeline

| Day | Activity | Time |
|-----|----------|------|
| 1 | Step 1: Fix pairing | 1 hour |
| 1 | Step 2: Implement threshold + logging | 1 hour |
| 2 | Step 3: Manual validation | 2 hours |
| 3 | Deploy to production | 30 min |
| 3-10 | Step 4: Monitor daily | 5 min/day |
| 8-10 | Step 5: Teacher feedback | 2 hours |
| 15 | Step 6: Final decision | 1 hour |

**Total coding:** 4 hours  
**Total calendar:** 3 weeks (mostly monitoring)

---

## ✅ Success Criteria

### **Must Achieve:**
- ✅ Inline placement ≥ 45% (from 34.4%)
- ✅ FP rate ≤ 5%
- ✅ Zero broken links
- ✅ No teacher complaints

### **Revert If:**
- ❌ FP rate >8%
- ❌ Teacher complaints
- ❌ Broken links
- ❌ Links in obviously wrong cells

---

## 📁 Deliverables

1. ✅ `fix_pairing_logic.py` - Validated pairing
2. ✅ Updated `docx_renderer.py` - Threshold + logging
3. ✅ `manual_validation_results.xlsx` - Validation data
4. ✅ `pairing_validation.json` - Pairing results
5. ✅ `teacher_feedback_summary.md` - User feedback
6. ✅ `ADR_001_hyperlink_placement_strategy.md` - Decision record
7. ✅ Daily monitoring logs

---

## 🚫 What We're NOT Doing

### **Parser Enhancement - DEFERRED**
- **Why:** Only fixes 32% of missing hints (not 90%)
- **See:** ADR_001 for full analysis

### **Coordinate Placement - REJECTED**
- **Why:** Templates don't match input→output
- **See:** ADR_001 for full analysis

### **"Keep Links in Cells" - DEFERRED**
- **Why:** No teacher validation
- **See:** ADR_001 for full analysis

---

## 📚 References

- **ADR_001:** Full decision rationale
- **Pre-implementation audit:** `pre_implementation_audit_results.json`
- **Research:** `THRESHOLD_CHANGE_IMPLEMENTATION.md`
- **Diagnostic:** `hyperlink_diagnostic.csv`

---

## 🎯 Key Points

1. **ONE change:** Threshold 0.65 → 0.55
2. **Fix pairing FIRST:** Prerequisite for valid metrics
3. **Manual validation:** Required before deploy
4. **Teacher feedback:** Schedule NOW (Week 2)
5. **Reversible:** Feature flag for quick revert
6. **Realistic:** +10-15% improvement (not 25-35%)

---

**Status:** Ready for implementation  
**Approved by:** [Pending user approval]  
**Next step:** Run Step 1 (fix pairing logic)
