# Files That Can Be Decluttered - Analysis

**Date:** 2025-01-27  
**Analysis:** Review of 56 remaining files in root directory

---

## Files to KEEP (Active/Required)

### Core Project Files (KEEP)
- `README.md` - Main project readme (referenced in README)
- `CHANGELOG.md` - Project changelog
- `decluttering_plan.md` - Active decluttering plan
- `DIAGNOSIS_CHECKLIST.md` - Diagnostic checklist (may be active)
- `prompt_v4.md` - Referenced in `strategies_pack_v2/_index.json` (line 154)

### Configuration Files (KEEP)
- `.env`, `.env.example` - Environment configuration
- `.gitignore` - Git ignore rules
- `.pre-commit-config.yaml` - Pre-commit hooks
- `pytest.ini` - Pytest configuration
- `requirements.txt` - Python dependencies

### Batch Files (KEEP - May organize later)
- All `.bat` files (14 files) - Startup/utility scripts

### Code Files (KEEP - May move to proper location)
- `api_tauri_fixed.ts` - Fixed API file (should be in frontend/)
- `UserSelector_improved.tsx` - Improved component (should be in frontend/)

---

## Files That Can Be ARCHIVED (31 files)

### Planning/Implementation Docs → `docs/archive/implementations/`

1. **`ANALYTICS_TEST_REPORT.md`** - Test report (Oct 18)
2. **`ANALYTICS_WORKFLOW_IMPROVEMENTS.md`** - Workflow improvements (Oct 18)
3. **`ANSWERS_TO_CRITICAL_QUESTIONS.md`** - Q&A document (Oct 19)
4. **`ARCHITECTURE_HYBRID_APPROACH.md`** - Architecture approach (Oct 26)
5. **`CACHE_CLEARING_IMPLEMENTATION.md`** - Implementation doc (Oct 26)
6. **`CODE_REVIEW_RESPONSE.md`** - Code review (Oct 26)
7. **`CONSENSUS_SUMMARY.md`** - Summary document (Oct 19)
8. **`COORDINATE_PLACEMENT_FOR_MULTISLOT.md`** - Implementation doc (Oct 26)
9. **`FINAL_RECOMMENDATION.md`** - Recommendation (Oct 19)
10. **`INSTRUMENTATION_ADDED.md`** - Implementation doc (Oct 26)
11. **`LLM_PROMPT_IMPROVEMENTS.md`** - Already archived in Phase 4 (duplicate?)
12. **`NEXT_STEPS_FRONTEND.md`** - Planning doc (Oct 18)
13. **`READY_FOR_VALIDATION.md`** - Status doc (Oct 19)
14. **`ROOT_CAUSE_FOUND.md`** - Analysis doc (Oct 26)
15. **`STRUCTURED_OUTPUTS_SOLUTION.md`** - Solution doc (Oct 19)
16. **`SUBJECT_BASED_SLOT_DETECTION.md`** - Implementation doc (Oct 26)
17. **`SUBJECT_DETECTION_IMPROVEMENTS.md`** - Implementation doc (Oct 26)
18. **`TABLE_STRUCTURE_DATA.md`** - Data doc (Oct 26)
19. **`THRESHOLD_CHANGE_IMPLEMENTATION.md`** - Implementation doc (Oct 19)
20. **`WHY_COORDINATES_DONT_WORK_MULTISLOT.md`** - Analysis doc (Oct 26)

### Debug/Diagnostic Files → `docs/archive/analysis/`

21. **`console-messages.md`** - Console output (4MB+, Oct 18) - Very large debug file
22. **`debuginfo001.md`** - Debug info (131KB, Oct 19)
23. **`Debuginfo002.md`** - Debug info (38KB, Oct 19)
24. **`FOR_OTHER_AI_DEBUGGING_REQUEST.md`** - Debug request (Oct 19)
25. **`FOR_OTHER_AI_HYPERLINK_BUG.md`** - Bug report (Oct 19)

### Test/Results Docs → `docs/archive/analysis/`

26. **`END_TO_END_TESTING_GUIDE.md`** - Testing guide (Oct 26) - May be active, review
27. **`QUICK_START_DIAGNOSTICS.md`** - Diagnostics guide (Oct 18) - May be active, review
28. **`REAL_WORLD_TEST_RESULTS.md`** - Test results (Oct 18)
29. **`TEST_RESULTS_SUMMARY.md`** - Test summary (Oct 26)

### Review Needed Before Archiving

30. **`END_TO_END_TESTING_GUIDE.md`** - Could be active testing guide
31. **`QUICK_START_DIAGNOSTICS.md`** - Could be active diagnostic guide

---

## Summary

### Files to Keep: 25 files
- Core project files: 5
- Configuration files: 5
- Batch files: 14
- Code files: 2 (may move to frontend/)

### Files to Archive: 29 files
- Planning/Implementation: 20 files
- Debug/Diagnostic: 5 files
- Test/Results: 4 files

### Files to Review: 2 files
- `END_TO_END_TESTING_GUIDE.md` - Check if active testing guide
- `QUICK_START_DIAGNOSTICS.md` - Check if active diagnostic guide

---

## Recommended Actions

1. **Archive 29 files** to `docs/archive/` subdirectories
2. **Review 2 files** (`END_TO_END_TESTING_GUIDE.md`, `QUICK_START_DIAGNOSTICS.md`) - determine if active or archive
3. **Move 2 code files** (`api_tauri_fixed.ts`, `UserSelector_improved.tsx`) to `frontend/` if they're fixes
4. **Consider organizing batch files** - Could create `scripts/` directory (optional)

**Potential reduction:** 56 → 27 files (52% reduction)

