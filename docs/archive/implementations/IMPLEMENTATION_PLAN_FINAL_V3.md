# Implementation Plan - Final Version 3.0

**Status:** Ready for implementation  
**Date:** 2025-10-19  
**Version:** 3.0 (incorporates all feedback from Other AI)  
**Supersedes:** All previous plans  

---

## 🎯 Scope

**ONE PRODUCTION CHANGE:** Lower fuzzy matching threshold from 0.65 to 0.55

**PLUS ONE VALIDATION PREREQUISITE:** Fix pairing logic (standalone tool, no runtime impact)

---

## 📋 Implementation Steps

### **Step 0: Pairing Validation (1 hour) - PREREQUISITE**

**Purpose:** Standalone validation tool with NO runtime impact. Used to verify pairing accuracy before relying on simulation metrics.

**What it is:**
- Validation script to test pairing logic
- Generates `pairing_validation.json` with match statistics
- **Does NOT affect production code**

**What it does:**
- Matches input files to output files by teacher + date
- Handles filename variations (9_2-9_5 vs 09_02-09_05)
- Normalizes leading zeros in dates
- Tests both "Lesson Plan" and "Daniela LP" folders

**File:** `d:\LP\tools\fix_pairing_logic.py` ✅ CREATED

**Run:**
```bash
python tools/fix_pairing_logic.py
```

**Success criteria:** ≥80% match rate

**Deliverable:** `pairing_validation.json` with actual match percentage

**Update plan after running:** Document actual match % in ADR_001

---

### **Step 1: Implement Threshold + Logging (1 hour)**

**File:** `d:\LP\tools\docx_renderer.py`

**Changes:**

#### **1.1 Add imports and constant (top of file)**

```python
# Use existing telemetry logger for consistency
from backend.telemetry import logger  # NOT logging.getLogger(__name__)

# Feature flag for threshold experiment
FUZZY_MATCH_THRESHOLD = 0.55  # Lowered from 0.65 for improved placement
# To revert: change back to 0.65
```

#### **1.2 Update `_calculate_match_confidence` method**

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
        "success": True,
        "file": getattr(self, 'current_file', 'unknown'),
        "teacher": getattr(self, 'current_teacher', 'unknown')
    })
    
    # ... existing hint matching logic
    return (context_score, 'fuzzy_context')

# Log when threshold NOT hit (below threshold)
elif context_score > 0:
    logger.info("hyperlink_below_threshold", extra={
        "link_text": media.get('text', '')[:100],
        "context_score": float(context_score),
        "threshold": FUZZY_MATCH_THRESHOLD,
        "gap": float(FUZZY_MATCH_THRESHOLD - context_score)
    })
```

#### **1.3 Update `_append_unmatched_media` method**

```python
def _append_unmatched_media(self, doc, pending_hyperlinks, pending_images):
    """Append unmatched media to fallback section."""
    
    # Log fallback count
    logger.info("referenced_links_fallback", extra={
        "hyperlink_count": len(pending_hyperlinks),
        "image_count": len(pending_images),
        "file": getattr(self, 'current_file', 'unknown'),
        "teacher": getattr(self, 'current_teacher', 'unknown')
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
            "success": False,
            "file": getattr(self, 'current_file', 'unknown'),
            "teacher": getattr(self, 'current_teacher', 'unknown')
        })
    
    # ... existing logic to append to document
```

**TODO:** Verify `self.current_file` and `self.current_teacher` are set before logging. If not, add them or use 'unknown'.

**Deliverable:** Updated `docx_renderer.py`

---

### **Step 2: Manual Validation (2 hours)**

**Performed by:** [Specify team member name]  
**Location:** `docs/validation/manual_validation_results.xlsx`

**Select 3 files:**
1. **High baseline (>80%):** W38 Lang (80% inline, ~46 links)
2. **Medium baseline (40-60%):** W42 Davies (38% inline, ~65 links)
3. **Low baseline (<40%):** W37 Davies (24% inline, ~79 links)

**Total links to validate:** ~190 links

**For EACH link, record:**

| File | Link# | Link Text | Expected Cell | Actual Cell | Strategy | Confidence | Result |
|------|-------|-----------|---------------|-------------|----------|------------|--------|
| W38_Lang | 1 | LESSON 5 | Unit/Lesson Mon | Unit/Lesson Mon | exact | 1.0 | TP |
| W38_Lang | 2 | Cool Down | Instruction Tue | Assessment Tue | fuzzy_0.55 | 0.58 | FP |
| W38_Lang | 3 | Stage 6 | Referenced Links | Referenced Links | fallback | 0.0 | TN |

**Categories:**
- **TP (True Positive):** Correct cell, inline placement
- **FP (False Positive):** Wrong cell, incorrect placement
- **TN (True Negative):** Correctly in "Referenced Links" fallback
- **FN (False Negative):** Should be inline, but in fallback

**Calculate rates:**
```
TP rate = TP / (TP + FN) * 100
FP rate = FP / (FP + TN) * 100
Accuracy = (TP + TN) / Total * 100
```

**Success criteria:**
- TP rate ≥ 90%
- FP rate ≤ 5%
- Zero broken links

**Save as:**
- `docs/validation/manual_validation_results.xlsx` (spreadsheet)
- `docs/validation/manual_validation_results.json` (for automation)

**Deliverable:** Validation spreadsheet + JSON + summary report

---

### **Step 3: Deploy + Monitor (1 week)**

**If validation passes (TP ≥90%, FP ≤5%):**

#### **3.1 Version Control**

```bash
# Tag before deployment for easy rollback
git add tools/docx_renderer.py
git commit -m "Lower fuzzy match threshold to 0.55 for improved placement

- Changed FUZZY_MATCH_THRESHOLD from 0.65 to 0.55
- Added comprehensive logging for all placements
- Added fallback counter
- See ADR_001 for rationale"

git tag threshold-0.55-v1
git push origin main --tags
```

#### **3.2 Deploy to Production**

[Deployment steps specific to your environment]

#### **3.3 Process Files**

Process 10-20 files over the week

#### **3.4 Daily Monitoring (5 min/day)**

**Automated script:** `tools/parse_telemetry.py` (create this)

```python
"""
Parse telemetry logs for inline/fallback counts.
Run daily to monitor threshold change impact.
"""

import json
from pathlib import Path

def parse_logs(log_file):
    inline_count = 0
    fallback_count = 0
    fp_candidates = []
    
    with open(log_file) as f:
        for line in f:
            try:
                log = json.loads(line)
                if log.get('event') == 'hyperlink_placement':
                    if log['extra']['strategy'] == 'fallback':
                        fallback_count += 1
                    else:
                        inline_count += 1
                        
                        # Flag potential FPs (low confidence)
                        if log['extra']['confidence'] < 0.60:
                            fp_candidates.append({
                                'text': log['extra']['link_text'],
                                'confidence': log['extra']['confidence'],
                                'file': log['extra']['file']
                            })
            except:
                pass
    
    total = inline_count + fallback_count
    inline_pct = (inline_count / total * 100) if total > 0 else 0
    
    print(f"Inline: {inline_count}/{total} ({inline_pct:.1f}%)")
    print(f"Fallback: {fallback_count}/{total} ({100-inline_pct:.1f}%)")
    print(f"Potential FPs: {len(fp_candidates)}")
    
    return {
        'inline_count': inline_count,
        'fallback_count': fallback_count,
        'inline_pct': inline_pct,
        'fp_candidates': fp_candidates
    }

if __name__ == '__main__':
    results = parse_logs('path/to/telemetry.log')
    # Save daily results
```

**Manual checks:**
- Spot-check 2-3 output files
- Note any teacher complaints
- Check for broken links

**Red flags (revert immediately):**
- FP rate >8%
- Teacher complaints about wrong links
- Broken links
- Links in obviously wrong cells

#### **3.5 Reversion Plan**

```python
# In docx_renderer.py
FUZZY_MATCH_THRESHOLD = 0.65  # Revert to original

# Git rollback
git revert HEAD  # Or: git reset --hard threshold-0.65-baseline
git push origin main
```

**Time to revert:** <5 minutes

**Deliverable:** Daily monitoring logs + weekly summary

---

### **Step 4: Teacher Feedback (Week 2)**

**Schedule:** [Specific date/time - SCHEDULE NOW]  
**Participants:** 3-5 teachers (Davies, Lang, Savoca, Piret, etc.)  
**Format:** 30-minute interview + mockups  
**Facilitator:** [Specify team member]

**Mockups location:** `docs/mockups/hyperlinks/`
- `version_A_current.docx` - Current (inline + Referenced Links)
- `version_B_end_of_cell.docx` - Inline + end-of-cell "Links:"
- `version_C_end_of_doc.docx` - All links at end of document

**Questions:**
1. How do you use hyperlinks in lesson plans?
2. Is "Referenced Links" section helpful or annoying?
3. Which version do you prefer? (Show mockups A/B/C)
4. How many links per cell is too many?
5. Any issues with current placement?

**Feedback integration:**
- If 3/5 prefer end-of-cell → Revisit "keep in cells" option
- If 4/5 find fallback annoying → Prioritize inline improvements
- If satisfied with current → Keep as-is

**Deliverable:** `docs/feedback/teacher_feedback_summary.md`

---

### **Step 5: Final Decision (Week 3)**

**Review data:**
- Manual validation results (Step 2)
- Telemetry data (Step 3, 1 week)
- Teacher feedback (Step 4)
- FP rate actual vs. expected

**Decision matrix:**

| Metric | Target | Actual | Pass? | Notes |
|--------|--------|--------|-------|-------|
| Inline rate | ≥45% | ??? | ??? | From telemetry |
| FP rate | ≤5% | ??? | ??? | From manual validation |
| Teacher satisfaction | Positive | ??? | ??? | From feedback |
| Broken links | 0 | ??? | ??? | From spot checks |

**Outcomes:**
- **All pass:** Keep change, document success, update ADR_001
- **Most pass:** Keep with adjustment (e.g., try 0.58 or 0.60)
- **Any fail:** Revert to 0.65, document lessons learned

**Deliverable:** `docs/decisions/threshold_change_outcome.md`

---

## ⏱️ Timeline

| Day | Activity | Time | Owner |
|-----|----------|------|-------|
| 0 | Step 0: Pairing validation | 1 hour | [Name] |
| 1 | Step 1: Implement threshold + logging | 1 hour | [Name] |
| 2 | Step 2: Manual validation | 2 hours | [Name] |
| 3 | Deploy to production | 30 min | [Name] |
| 3-10 | Step 3: Monitor daily | 5 min/day | [Name] |
| 8-10 | Step 4: Teacher feedback | 2 hours | [Name] |
| 15 | Step 5: Final decision | 1 hour | [Name] |

**Total coding:** 4 hours  
**Total calendar:** 3 weeks (mostly monitoring)

---

## ✅ Success Criteria

### **Must Achieve:**
- Inline placement ≥ 45% (from 34.4%)
- FP rate ≤ 5%
- Zero broken links
- No teacher complaints

### **Revert If:**
- FP rate >8%
- Teacher complaints
- Broken links
- Links in obviously wrong cells

---

## 📁 Deliverables & Locations

1. ✅ `tools/fix_pairing_logic.py` - Pairing validation (CREATED)
2. ⏳ `pairing_validation.json` - Pairing results
3. ⏳ Updated `tools/docx_renderer.py` - Threshold + logging
4. ⏳ `docs/validation/manual_validation_results.xlsx` - Validation data
5. ⏳ `docs/validation/manual_validation_results.json` - Automation format
6. ⏳ `tools/parse_telemetry.py` - Daily monitoring script
7. ⏳ `docs/mockups/hyperlinks/` - Teacher feedback mockups
8. ⏳ `docs/feedback/teacher_feedback_summary.md` - User feedback
9. ⏳ `docs/decisions/threshold_change_outcome.md` - Final decision
10. ✅ `docs/ADR_001_hyperlink_placement_strategy.md` - Decision record (CREATED)

---

## 🚫 What We're NOT Doing

### **Parser Enhancement - DEFERRED**
- **Why:** Only fixes 32% of missing hints (not 90%)
- **See:** ADR_001 Section "Why DEFER Parser Enhancement?"

### **Coordinate Placement - REJECTED**
- **Why:** Templates don't match input→output
- **See:** ADR_001 Section "Why REJECT Coordinate-Based Placement?"

### **"Keep Links in Cells" - DEFERRED**
- **Why:** No teacher validation yet
- **See:** ADR_001 Section "Why DEFER 'Keep Links in Cells' Strategy?"

---

## 📚 References

- **ADR_001:** `docs/ADR_001_hyperlink_placement_strategy.md` (updated to reference this plan)
- **Pre-implementation audit:** `pre_implementation_audit_results.json`
- **Research:** `THRESHOLD_CHANGE_IMPLEMENTATION.md`
- **Session summary:** `SESSION_10_COMPLETE.md`

---

## 🔄 Version Control & Archival

**This plan (v3.0) supersedes:**
- IMPLEMENTATION_PLAN_FINAL_V2.md
- IMPLEMENTATION_PLAN_FINAL.md
- CONSENSUS_SUMMARY.md
- All other planning documents

**Action after implementation:**
1. Add "SUPERSEDED" note to top of old files
2. Or move to `docs/archive/` folder
3. Update ADR_001 to reference this plan explicitly

---

## 🎯 Key Improvements from Other AI Feedback

1. ✅ **Clarified scope** - Pairing is prerequisite, not production change
2. ✅ **Enhanced pairing** - Handles leading zeros, year variations
3. ✅ **Consistent logging** - Uses `backend.telemetry.logger`
4. ✅ **Added TODO** - Verify `current_file`/`current_teacher` are set
5. ✅ **Log below-threshold** - Track links that almost matched
6. ✅ **Specified validator** - Who performs manual review
7. ✅ **File locations** - Where deliverables live
8. ✅ **Automated monitoring** - Script to parse telemetry
9. ✅ **Git tagging** - Easy rollback
10. ✅ **Mockup locations** - Where teacher feedback materials live
11. ✅ **Feedback integration** - How it affects decisions
12. ✅ **ADR alignment** - Explicit reference to this plan
13. ✅ **Version control** - Archive old plans

---

## 🚀 Ready to Proceed

**Status:** ✅ All feedback incorporated, ready for implementation

**Next step:** Run Step 0 (pairing validation)

```bash
python tools/fix_pairing_logic.py
```

**Expected output:** `pairing_validation.json` with ≥80% match rate

**If pass:** Proceed to Step 1  
**If fail:** Fix pairing logic before continuing

---

**Approved by:** [Pending user approval]  
**Implementation start:** [Date]
