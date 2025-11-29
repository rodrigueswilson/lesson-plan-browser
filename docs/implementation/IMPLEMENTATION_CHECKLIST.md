# Coordinate-Based Placement - Implementation Checklist

**Based on Other AI's feedback - All 9 gaps addressed**

---

## ✅ Gap #1: Coordinate Capture

**Task:** Parser must store table_idx, row_idx, cell_idx

- [ ] Update `docx_parser.extract_hyperlinks()` to capture coordinates
- [ ] Add `table_idx`, `row_idx`, `cell_idx` to hyperlink dict
- [ ] Add `row_label`, `col_header` to hyperlink dict
- [ ] Unit test: Verify coordinates are correct
- [ ] Test on standard 8x6 file
- [ ] Test on 9x6 file with Day row

**Files:** `tools/docx_parser.py`

---

## ✅ Gap #2: Structure Metadata in Renderer

**Task:** Reliable structure detection in renderer

- [ ] Create `tools/table_structure.py` module
- [ ] Implement `StructureMetadata` dataclass
- [ ] Implement `TableStructureDetector` class
- [ ] Add detection for standard 8x6
- [ ] Add detection for 9x6 with Day row
- [ ] Add detection for 13x6 extended
- [ ] Add adaptive detection for unknown structures
- [ ] Unit tests for all structure types

**Files:** `tools/table_structure.py` (NEW)

---

## ✅ Gap #3: Guarding Coordinate Placement

**Task:** Wrap coordinate access in try/except

- [ ] Add `_try_coordinate_placement()` method
- [ ] Wrap `table.rows[row_idx].cells[col_idx]` in try/except
- [ ] Log warning on IndexError
- [ ] Fall back to next strategy on error
- [ ] Unit test: Test with invalid coordinates
- [ ] Unit test: Test with out-of-bounds indices

**Files:** `tools/docx_renderer.py`

---

## ✅ Gap #4: Row-Label Matching Coverage

**Task:** Pattern lists must reflect full variability

- [ ] Define `ROW_PATTERNS` dictionary with all variations
- [ ] Include: 'Objective' / 'Essential Question' / 'Learning Goal'
- [ ] Include: 'Instruction' / 'Tailored Instruction' / 'Teaching'
- [ ] Include: 'Misconception' / 'Common Errors'
- [ ] Validate patterns against 17% variant files
- [ ] Add case-insensitive matching
- [ ] Add whitespace normalization
- [ ] Unit test: Test all pattern variations

**Files:** `tools/table_structure.py`

---

## ✅ Gap #5: Column Header Normalization

**Task:** Strip dates from headers

- [ ] Implement `_build_col_map()` method
- [ ] Extract day name from "MONDAY 9/22" → "monday"
- [ ] Handle "Day | MONDAY" format
- [ ] Handle partial weeks (THURSDAY | FRIDAY)
- [ ] Unit test: Test various header formats
- [ ] Unit test: Test date extraction

**Files:** `tools/table_structure.py`

---

## ✅ Gap #6: Structure-to-Placement Hand-off

**Task:** Clean interface with StructureMap

- [ ] `StructureMetadata` provides row/column offsets
- [ ] `get_row_index(label)` method
- [ ] `get_col_index(day)` method
- [ ] Renderer consults StructureMetadata, not hard-coded offsets
- [ ] Unit test: Test metadata interface

**Files:** `tools/table_structure.py`, `tools/docx_renderer.py`

---

## ✅ Gap #7: Non-Table Links

**Task:** Skip links outside daily plan table

- [ ] Check if `link.get('table_idx')` is None
- [ ] Log non-table links
- [ ] Fall back to Referenced Links section
- [ ] Don't try coordinate placement on non-table links
- [ ] Unit test: Test with non-table links

**Files:** `tools/docx_renderer.py`

---

## ✅ Gap #8: Telemetry & Manual Validation

**Task:** Log strategy used for each placement

- [ ] Add `placement_stats` dictionary
- [ ] Track: 'coordinate', 'label_day', 'fuzzy', 'fallback'
- [ ] Log statistics at end of rendering
- [ ] Add `log_hyperlink_placement()` to telemetry
- [ ] Rerun validation script on all files
- [ ] Manual validation on standard and irregular files
- [ ] Generate before/after comparison report

**Files:** `tools/docx_renderer.py`, `backend/telemetry.py`

---

## ✅ Gap #9: Documentation Update

**Task:** ADRs and plans reflect new design

- [ ] Create `docs/adr/ADR_002_coordinate_based_placement.md`
- [ ] Document decision and rationale
- [ ] Document consequences and trade-offs
- [ ] Create implementation guide
- [ ] Update `TABLE_STRUCTURE_INSIGHTS.md`
- [ ] Add troubleshooting section
- [ ] Add examples for maintainers

**Files:** `docs/adr/`, `docs/implementation/`, `docs/knowledge/`

---

## 🧪 Testing Checklist

### **Unit Tests:**
- [ ] `test_table_structure_detection.py` - All 7 patterns
- [ ] `test_coordinate_placement.py` - Coordinate logic
- [ ] `test_label_day_placement.py` - Adaptive matching
- [ ] `test_error_handling.py` - Guards and fallbacks
- [ ] `test_row_patterns.py` - Pattern matching
- [ ] `test_column_normalization.py` - Header parsing

### **Integration Tests:**
- [ ] Standard 8x6 file → 95%+ inline
- [ ] 9x6 with Day row → 90%+ inline
- [ ] 13x6 extended → 85%+ inline
- [ ] Unknown structure → graceful fallback
- [ ] Non-table links → fallback section
- [ ] Invalid coordinates → no crash

### **Validation:**
- [ ] Run on all 100 files
- [ ] Compare before/after inline rates
- [ ] Generate detailed report
- [ ] Manual spot-check on 10 files
- [ ] Verify zero broken links
- [ ] Verify zero data loss

---

## 📊 Success Metrics

### **Must Achieve:**
- [ ] Overall inline rate: 93-97%
- [ ] Standard 8x6 files: 95%+ inline
- [ ] Zero crashes on invalid coordinates
- [ ] Zero broken links
- [ ] Zero data loss

### **Should Achieve:**
- [ ] 9x6 files: 90%+ inline
- [ ] 13x6 files: 85%+ inline
- [ ] Telemetry shows strategy distribution
- [ ] Fallback rate < 5% overall

### **Nice to Have:**
- [ ] Performance: <10% overhead
- [ ] Logging: Clear, actionable messages
- [ ] Documentation: Complete and clear

---

## 🚀 Implementation Order

### **Week 1:**
1. Gap #1: Coordinate capture (Parser)
2. Gap #2: Structure detection
3. Gap #6: Structure metadata interface

### **Week 2:**
4. Gap #3: Coordinate placement with guards
5. Gap #4: Row pattern matching
6. Gap #5: Column normalization
7. Gap #7: Non-table link handling

### **Week 3:**
8. Gap #8: Telemetry and validation
9. Gap #9: Documentation
10. Testing and refinement

---

## ✅ Sign-Off

- [ ] All 9 gaps addressed
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Validation shows expected improvement
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Ready for production

---

**Status:** Ready to implement  
**Expected Timeline:** 3 weeks  
**Expected Improvement:** +9-13 percentage points (84.2% → 93-97%)
