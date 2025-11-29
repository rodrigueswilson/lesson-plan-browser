# Decluttering Inventory Notes

**Date:** 2025-01-27  
**Author:** AI Assistant  
**Purpose:** Document pilot inventory findings, judgment calls, and decision criteria for decluttering process

## Pilot Inventory Scope

Completed manual inventory of representative slice:
- Diagnostic scripts (`check_*.py`)
- Test files (`test_*.py`)
- Completed documentation (`*_COMPLETE.md`)
- Session summaries (`SESSION_*.md`)

## Findings

### Diagnostic Scripts (`check_*.py`)

**Total found:** 46 files

**Root-level:** 37 files
- All appear to be diagnostic/one-time scripts
- Examples: `check_config.py`, `check_schema.py`, `check_db_url.py`, `check_daniela_slots.py`
- Decision: Move all to `tools/diagnostics/`

**Already in tools/:** 8 files
- `tools/check_lesson_json_in_db.py`
- `tools/check_db_schema.py`
- `tools/check_recent_outputs.py`
- `tools/check_table_structure.py`
- `tools/check_paragraphs.py`
- `tools/check_all_tables.py`
- `tools/check_db_status.py`
- `tools/check_snapshot_updates.py`
- Decision: Keep in `tools/` (already organized)

**In tools/archive/:** 4 files
- `tools/archive/check_slots.py`
- `tools/archive/check_piret.py`
- `tools/archive/check_savoca.py`
- `tools/archive/check_lang.py`
- `tools/archive/check_template.py`
- Decision: Already archived, leave as-is

**In tests/:** 1 file
- `tests/check_page_breaks.py`
- Decision: Keep in tests (test-related)

**In tools/strategy_converter/:** 1 file
- `tools/strategy_converter/check_weights.py`
- Decision: Keep in subdirectory (belongs to converter module)

### Test Files (`test_*.py`)

**Total found:** 102 files

**Root-level:** ~30 files
- Examples: `test_file_matching.py`, `test_w44_dry_run.py`, `test_slot_aware_real.py`
- Decision: Move to `tests/` directory

**Already in tests/:** ~70 files
- Already organized
- Decision: Keep in `tests/`, organize by category if needed

**In tools/:** 3 files
- `tools/test_phase2_renderer.py`
- `tools/test_structure_detector.py`
- `tools/test_phase1_parser.py`
- `tools/test_setup_checker.py`
- `tools/test_end_to_end.py`
- `tools/test_json_merger.py`
- Decision: Move to `tests/` (test files should be in tests directory)

**In tools/strategy_converter/:** 2 files
- `tools/strategy_converter/tests/test_round_trip.py`
- `tools/strategy_converter/test_converter.py`
- Decision: Keep in subdirectory (module-specific tests)

### Completed Documentation (`*_COMPLETE.md`)

**Total found:** 50 files

**Root-level:** ~30 files
- Examples: `SESSION_1_COMPLETE.md`, `PHASE_1_COMPLETE.md`, `HYPERLINK_FIX_COMPLETE.md`
- Decision: Archive to appropriate `docs/archive/` subdirectories

**Already in docs/:** ~20 files
- Some already in `docs/implementation/`, `docs/progress/`, `docs/sessions/`, `docs/archive/`
- Decision: Consolidate into `docs/archive/` structure per plan

### Session Summaries (`SESSION_*.md`)

**Total found:** 53 files

**Root-level:** ~25 files
- Examples: `SESSION_1_COMPLETE.md`, `SESSION_7_COMPLETE.md`, `SESSION_8_HANG_FIX_COMPLETE.md`
- Decision: Archive to `docs/archive/sessions/`

**Already in docs/:** ~28 files
- In `docs/sessions/`, `docs/planning/`
- Decision: Consolidate into `docs/archive/sessions/`

## Decision Criteria Established

1. **Diagnostic scripts:** All root-level `check_*.py` → `tools/diagnostics/`
2. **Test files:** All root-level `test_*.py` → `tests/`
3. **Completed docs:** All `*_COMPLETE.md` → appropriate `docs/archive/` subdirectories
4. **Session summaries:** All `SESSION_*.md` → `docs/archive/sessions/`

## Open Questions

1. Some scripts in `tools/` might be reusable utilities vs diagnostics - need review
2. Test files in `tools/` may have path dependencies - need pytest validation before moving
3. Some `*_COMPLETE.md` files might still be referenced - need link audit before archiving

## Next Steps

1. Create `docs/maintenance/DECLUTTERING_INVENTORY.md` with full inventory
2. Run Phase 2.0 audit to identify all script consumers
3. Run Phase 3.0 validation to ensure pytest config supports test moves
4. Run Phase 4.2 audit to identify all documentation links

