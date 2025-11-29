# Coordinate-Based Placement Implementation Plan

**Status:** Ready for Implementation  
**Based on:** Analysis of 100 lesson plans + Other AI feedback  
**Expected Improvement:** 84.2% → 93-97% inline placement  

---

## 📋 Implementation Checklist

### **Phase 1: Parser Enhancement** ✓ Addresses Gap #1

**Goal:** Capture coordinates and labels for every hyperlink

**Changes to `tools/docx_parser.py`:**

```python
def extract_hyperlinks(self):
    """Extract hyperlinks with complete coordinate information."""
    
    hyperlinks = []
    
    for table_idx, table in enumerate(self.doc.tables):
        for row_idx, row in enumerate(table.rows):
            # Get row label (first cell)
            row_label = row.cells[0].text.strip() if row.cells else ""
            
            for cell_idx, cell in enumerate(row.cells):
                # Get column header (from first row)
                col_header = ""
                if table.rows and len(table.rows[0].cells) > cell_idx:
                    col_header = table.rows[0].cells[cell_idx].text.strip()
                
                for para in cell.paragraphs:
                    for hyperlink in para._element.xpath('.//w:hyperlink'):
                        # ... extract text, url, etc ...
                        
                        hyperlinks.append({
                            'text': text,
                            'url': url,
                            # NEW: Coordinate information
                            'table_idx': table_idx,
                            'row_idx': row_idx,
                            'cell_idx': cell_idx,
                            'row_label': row_label,
                            'col_header': col_header,
                            # Existing: Context information
                            'section_hint': section_hint,
                            'day_hint': day_hint,
                            'context_snippet': context
                        })
    
    return hyperlinks
```

**Validation:**
- Unit test: Verify coordinates are captured correctly
- Test on standard 8x6 file
- Test on 9x6 file with Day row
- Verify non-table links are excluded or marked

---

### **Phase 2: Structure Detection** ✓ Addresses Gaps #2, #6

**Goal:** Detect output table structure and create mapping

**New file: `tools/table_structure.py`:**

```python
from dataclasses import dataclass
from typing import Optional, Dict, List

@dataclass
class StructureMetadata:
    """Metadata about table structure."""
    structure_type: str  # "standard_8x6", "with_day_row_9x6", etc.
    num_rows: int
    num_cols: int
    row_offset: int  # Offset to apply to row indices
    has_day_row: bool
    row_label_map: Dict[str, int]  # Label → row_index
    col_header_map: Dict[str, int]  # Day → col_index
    
    def get_row_index(self, label: str) -> Optional[int]:
        """Get row index by label."""
        return self.row_label_map.get(label.strip().lower())
    
    def get_col_index(self, day: str) -> Optional[int]:
        """Get column index by day."""
        return self.col_header_map.get(day.strip().lower())


class TableStructureDetector:
    """Detect and classify table structures."""
    
    # Standard row labels (case-insensitive)
    STANDARD_ROWS = [
        '',  # Row 0
        'unit, lesson #, module:',
        'objective:',
        'anticipatory set:',
        'tailored instruction:',
        'misconception:',
        'assessment:',
        'homework:'
    ]
    
    # Row label patterns for matching
    ROW_PATTERNS = {
        'unit': ['unit', 'lesson', 'module'],
        'objective': ['objective', 'essential question', 'learning goal'],
        'anticipatory': ['anticipatory set', 'warm-up', 'do now'],
        'instruction': ['tailored instruction', 'instruction', 'teaching'],
        'misconception': ['misconception', 'common error'],
        'assessment': ['assessment', 'check for understanding'],
        'homework': ['homework', 'independent practice', 'extension']
    }
    
    def detect_structure(self, table) -> StructureMetadata:
        """
        Detect table structure and return metadata.
        
        Args:
            table: python-docx Table object
        
        Returns:
            StructureMetadata with structure info
        """
        
        if not table or not table.rows:
            return self._create_unknown_structure(table)
        
        num_rows = len(table.rows)
        num_cols = len(table.rows[0].cells) if table.rows else 0
        
        # Extract row labels
        row_labels = [
            row.cells[0].text.strip().lower() if row.cells else ""
            for row in table.rows
        ]
        
        # Extract column headers
        col_headers = [
            cell.text.strip() for cell in table.rows[0].cells
        ] if table.rows else []
        
        # Check for standard 8x6
        if num_rows == 8 and num_cols == 6:
            if self._matches_standard_rows(row_labels):
                return self._create_standard_8x6(row_labels, col_headers)
        
        # Check for 9x6 with Day row
        if num_rows == 9 and num_cols == 6:
            if row_labels[0] == 'day':
                return self._create_with_day_row(row_labels, col_headers)
        
        # Check for 13x6 extended
        if num_rows == 13 and num_cols == 6:
            return self._create_extended_13x6(row_labels, col_headers)
        
        # Unknown structure - create adaptive mapping
        return self._create_adaptive_structure(row_labels, col_headers)
    
    def _matches_standard_rows(self, row_labels: List[str]) -> bool:
        """Check if row labels match standard pattern."""
        if len(row_labels) < len(self.STANDARD_ROWS):
            return False
        
        for i, expected in enumerate(self.STANDARD_ROWS):
            if expected and row_labels[i] != expected:
                return False
        
        return True
    
    def _create_standard_8x6(self, row_labels, col_headers) -> StructureMetadata:
        """Create metadata for standard 8x6 structure."""
        return StructureMetadata(
            structure_type="standard_8x6",
            num_rows=8,
            num_cols=6,
            row_offset=0,
            has_day_row=False,
            row_label_map=self._build_row_map(row_labels),
            col_header_map=self._build_col_map(col_headers)
        )
    
    def _create_with_day_row(self, row_labels, col_headers) -> StructureMetadata:
        """Create metadata for 9x6 with Day row."""
        return StructureMetadata(
            structure_type="with_day_row_9x6",
            num_rows=9,
            num_cols=6,
            row_offset=1,  # All content rows shifted by 1
            has_day_row=True,
            row_label_map=self._build_row_map(row_labels[1:]),  # Skip Day row
            col_header_map=self._build_col_map(col_headers)
        )
    
    def _create_adaptive_structure(self, row_labels, col_headers) -> StructureMetadata:
        """Create adaptive metadata for unknown structure."""
        return StructureMetadata(
            structure_type="adaptive",
            num_rows=len(row_labels),
            num_cols=len(col_headers),
            row_offset=0,
            has_day_row=False,
            row_label_map=self._build_row_map(row_labels),
            col_header_map=self._build_col_map(col_headers)
        )
    
    def _build_row_map(self, row_labels: List[str]) -> Dict[str, int]:
        """Build mapping from row label to index."""
        row_map = {}
        
        for idx, label in enumerate(row_labels):
            if label:
                # Store normalized label
                normalized = label.strip().lower().rstrip(':')
                row_map[normalized] = idx
                
                # Also store pattern-based keys
                for pattern_key, patterns in self.ROW_PATTERNS.items():
                    if any(p in normalized for p in patterns):
                        row_map[pattern_key] = idx
        
        return row_map
    
    def _build_col_map(self, col_headers: List[str]) -> Dict[str, int]:
        """Build mapping from day name to column index."""
        col_map = {}
        
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        
        for idx, header in enumerate(col_headers):
            header_lower = header.lower()
            
            # Extract day name (ignore dates)
            for day in days:
                if day in header_lower:
                    col_map[day] = idx
                    break
        
        return col_map
```

**Validation:**
- Unit tests for each structure type
- Test on all 7 dimension patterns
- Verify row/column maps are correct

---

### **Phase 3: Hybrid Placement Logic** ✓ Addresses Gaps #3, #4, #5, #7

**Goal:** Implement safe, adaptive placement with fallbacks

**Changes to `tools/docx_renderer.py`:**

```python
from tools.table_structure import TableStructureDetector, StructureMetadata

class DOCXRenderer:
    
    def __init__(self):
        self.structure_detector = TableStructureDetector()
        self.placement_stats = {
            'coordinate': 0,
            'label_day': 0,
            'fuzzy': 0,
            'fallback': 0
        }
    
    def _restore_hyperlinks(self, table, hyperlinks):
        """Restore hyperlinks using hybrid placement strategy."""
        
        # Detect output table structure
        structure = self.structure_detector.detect_structure(table)
        
        logger.info(f"Detected table structure: {structure.structure_type}")
        
        for link in hyperlinks:
            strategy = self._place_hyperlink_hybrid(link, table, structure)
            self.placement_stats[strategy] += 1
    
    def _place_hyperlink_hybrid(self, link, table, structure: StructureMetadata) -> str:
        """
        Place hyperlink using hybrid strategy.
        
        Returns: strategy used ('coordinate', 'label_day', 'fuzzy', 'fallback')
        """
        
        # Skip non-table links
        if link.get('table_idx') is None:
            logger.debug(f"Link '{link['text']}' is not from a table, using fallback")
            self._add_to_fallback(link)
            return 'fallback'
        
        # Strategy 1: Coordinate-based (if standard structure)
        if structure.structure_type == "standard_8x6":
            if self._try_coordinate_placement(link, table, structure):
                return 'coordinate'
        
        # Strategy 2: Label + Day matching
        if self._try_label_day_placement(link, table, structure):
            return 'label_day'
        
        # Strategy 3: Fuzzy matching (current approach)
        if self._try_fuzzy_placement(link, table, threshold=0.55):
            return 'fuzzy'
        
        # Strategy 4: Fallback section
        self._add_to_fallback(link)
        return 'fallback'
    
    def _try_coordinate_placement(self, link, table, structure) -> bool:
        """Try to place link at exact coordinates."""
        
        row_idx = link.get('row_idx')
        cell_idx = link.get('cell_idx')
        
        if row_idx is None or cell_idx is None:
            return False
        
        # Apply row offset if needed
        target_row = row_idx + structure.row_offset
        
        # Guard against invalid coordinates
        try:
            if target_row >= len(table.rows):
                logger.warning(f"Row {target_row} out of bounds (table has {len(table.rows)} rows)")
                return False
            
            row = table.rows[target_row]
            
            if cell_idx >= len(row.cells):
                logger.warning(f"Cell {cell_idx} out of bounds (row has {len(row.cells)} cells)")
                return False
            
            cell = row.cells[cell_idx]
            
            # Place hyperlink
            self._add_hyperlink_to_cell(cell, link['text'], link['url'])
            
            logger.debug(f"Placed '{link['text']}' at coordinates ({target_row}, {cell_idx})")
            return True
            
        except (IndexError, AttributeError) as e:
            logger.warning(f"Coordinate placement failed for '{link['text']}': {e}")
            return False
    
    def _try_label_day_placement(self, link, table, structure) -> bool:
        """Try to place link using row label + day matching."""
        
        row_label = link.get('row_label', '').strip().lower().rstrip(':')
        day_hint = link.get('day_hint', '').strip().lower()
        
        if not row_label or not day_hint:
            return False
        
        # Find target row
        target_row = structure.get_row_index(row_label)
        if target_row is None:
            # Try pattern matching
            for pattern_key in ['unit', 'objective', 'instruction', 'assessment', 'homework']:
                if pattern_key in row_label:
                    target_row = structure.get_row_index(pattern_key)
                    if target_row is not None:
                        break
        
        # Find target column
        target_col = structure.get_col_index(day_hint)
        
        if target_row is None or target_col is None:
            logger.debug(f"Could not find row/col for '{link['text']}': row={row_label}, day={day_hint}")
            return False
        
        # Guard against invalid coordinates
        try:
            if target_row >= len(table.rows) or target_col >= len(table.rows[target_row].cells):
                logger.warning(f"Label/day placement out of bounds: ({target_row}, {target_col})")
                return False
            
            cell = table.rows[target_row].cells[target_col]
            self._add_hyperlink_to_cell(cell, link['text'], link['url'])
            
            logger.debug(f"Placed '{link['text']}' via label/day at ({target_row}, {target_col})")
            return True
            
        except (IndexError, AttributeError) as e:
            logger.warning(f"Label/day placement failed for '{link['text']}': {e}")
            return False
    
    def _try_fuzzy_placement(self, link, table, threshold=0.65) -> bool:
        """Try to place link using fuzzy text matching (existing logic)."""
        
        # Iterate through all cells in table
        for row_idx, row in enumerate(table.rows):
            # Get row label for section matching
            row_label = row.cells[0].text.strip() if row.cells else ""
            section_name = self._infer_section_from_label(row_label)
            
            for cell_idx, cell in enumerate(row.cells):
                # Get day hint from column header
                day_name = None
                if table.rows and cell_idx < len(table.rows[0].cells):
                    col_header = table.rows[0].cells[cell_idx].text.strip()
                    day_name = self._extract_day_from_header(col_header)
                
                # Use existing _calculate_match_confidence method
                confidence, match_type = self._calculate_match_confidence(
                    cell.text,
                    link,
                    day_name=day_name,
                    section_name=section_name
                )
                
                if confidence >= threshold:
                    # Use existing _inject_hyperlink_inline method
                    self._inject_hyperlink_inline(cell, link)
                    logger.debug(
                        f"Placed '{link['text']}' via fuzzy matching "
                        f"at ({row_idx}, {cell_idx}), confidence={confidence:.2f}, "
                        f"match_type={match_type}"
                    )
                    return True
        
        return False
```

**Validation:**
- Unit tests for each strategy
- Test error handling (IndexError, AttributeError)
- Verify fallback chain works correctly

---

### **Phase 4: Telemetry & Logging** ✓ Addresses Gap #8

**Goal:** Track which strategy is used for each link

**Add to `tools/docx_renderer.py`:**

```python
def _finalize_rendering(self):
    """Log placement statistics."""
    
    total = sum(self.placement_stats.values())
    
    if total > 0:
        logger.info("Hyperlink placement statistics:")
        for strategy, count in self.placement_stats.items():
            pct = count / total * 100
            logger.info(f"  {strategy}: {count} ({pct:.1f}%)")
        
        # Calculate inline rate
        inline = self.placement_stats['coordinate'] + self.placement_stats['label_day'] + self.placement_stats['fuzzy']
        inline_rate = inline / total * 100
        
        logger.info(f"  Overall inline rate: {inline_rate:.1f}%")
```

**Add to `backend/telemetry.py`:**

```python
def log_hyperlink_placement(strategy: str, link_text: str, success: bool):
    """Log hyperlink placement attempt."""
    logger.debug(f"Placement: strategy={strategy}, link='{link_text[:50]}', success={success}")
```

---

### **Phase 5: Validation & Testing** ✓ Addresses Gap #8

**Goal:** Verify improvement across all file types

**Test Suite:**

1. **Unit Tests:**
   - `test_table_structure_detection.py` - Test all 7 patterns
   - `test_coordinate_placement.py` - Test coordinate logic
   - `test_label_day_placement.py` - Test adaptive matching
   - `test_error_handling.py` - Test guards and fallbacks

2. **Integration Tests:**
   - Process standard 8x6 file → verify 95%+ inline
   - Process 9x6 with Day row → verify 90%+ inline
   - Process 13x6 extended → verify 85%+ inline
   - Process unknown structure → verify graceful fallback

3. **Validation Script:**
   ```bash
   python tools/validate_coordinate_placement.py
   ```
   - Run on all 100 files
   - Compare before/after inline rates
   - Generate report

---

### **Phase 6: Documentation** ✓ Addresses Gap #9

**Documents to Create/Update:**

1. **ADR:** `docs/adr/ADR_002_coordinate_based_placement.md`
   - Decision: Use hybrid coordinate + adaptive strategy
   - Rationale: 83% standard structure, 17% variations
   - Consequences: 93-97% expected inline rate

2. **Implementation Guide:** `docs/implementation/COORDINATE_PLACEMENT_GUIDE.md`
   - How the system works
   - How to add new structure patterns
   - Troubleshooting guide

3. **Update:** `docs/knowledge/TABLE_STRUCTURE_INSIGHTS.md`
   - Add "Implementation Status" section
   - Link to ADR and guide

---

## 📊 Expected Results

### **Before (Current):**
- Fuzzy matching only (threshold 0.55)
- Inline rate: 84.2%
- Fallback rate: 15.8%

### **After (Coordinate-based):**

| File Type | Files | Strategy | Expected Inline |
|-----------|-------|----------|----------------|
| Standard 8x6 | 83 | Coordinate | 95-100% |
| 9x6 with Day | 9 | Label/Day | 90-95% |
| 13x6 Extended | 3 | Label/Day | 85-90% |
| Others | 5 | Adaptive | 80-85% |
| **OVERALL** | **100** | **Hybrid** | **93-97%** |

**Improvement:** +9-13 percentage points

---

## 🚀 Implementation Timeline

### **Week 1:**
- Day 1-2: Phase 1 (Parser enhancement)
- Day 3-4: Phase 2 (Structure detection)
- Day 5: Phase 3 (Hybrid placement - part 1)

### **Week 2:**
- Day 1-2: Phase 3 (Hybrid placement - part 2)
- Day 3: Phase 4 (Telemetry)
- Day 4-5: Phase 5 (Testing & validation)

### **Week 3:**
- Day 1-2: Phase 6 (Documentation)
- Day 3-4: Bug fixes and refinement
- Day 5: Production deployment

---

## ✅ Success Criteria

1. **Parser captures coordinates:** ✓ All hyperlinks have table_idx, row_idx, cell_idx
2. **Structure detection works:** ✓ Correctly identifies all 7 patterns
3. **Coordinate placement works:** ✓ 95%+ inline for standard files
4. **Adaptive matching works:** ✓ 85%+ inline for non-standard files
5. **Error handling works:** ✓ No crashes on invalid coordinates
6. **Telemetry works:** ✓ Can track which strategy is used
7. **Overall improvement:** ✓ 93-97% inline rate across all files
8. **Zero regressions:** ✓ No broken links, no data loss

---

## 🎯 Risk Mitigation

### **Risk 1: Coordinates don't match between input/output**
- **Mitigation:** Fall back to label/day matching
- **Test:** Validate on files with different templates

### **Risk 2: Row labels vary more than expected**
- **Mitigation:** Expand pattern matching dictionary
- **Test:** Analyze all 17% variation files

### **Risk 3: Performance impact**
- **Mitigation:** Structure detection is O(n), minimal overhead
- **Test:** Benchmark on large files

### **Risk 4: Edge cases not covered**
- **Mitigation:** Comprehensive fallback chain
- **Test:** Manual validation on edge cases

---

**Ready to implement! All gaps from Other AI's feedback are addressed.**
