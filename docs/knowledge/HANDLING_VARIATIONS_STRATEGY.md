# Strategy for Handling Table Structure Variations

**Based on analysis of 100 lesson plans**

---

## 📊 The Variations We Need to Handle

### **Dimension Variations:**
1. **8x6** - 83 files (STANDARD)
2. **9x6** - 9 files (extra row at top)
3. **13x6** - 3 files (extended structure)
4. **14x6** - 1 file (extended + extra)
5. **10x6** - 1 file
6. **4x6** - 1 file (minimal)
7. **8x2** - 1 file (observation - partial week)

### **Row Label Variations:**
- Some have "Day" row at top (shifts all indices by +1)
- Some have "Essential Question" instead of "Objective"
- Some have extra activity rows
- Some have merged sections

### **Column Header Variations:**
- Standard: ` | MONDAY | TUESDAY | ...`
- With dates: ` | MONDAY 9/22 | TUESDAY 9/23 | ...`
- With "Day" label: `Day | MONDAY | TUESDAY | ...`
- Partial week: `THURSDAY | FRIDAY`

---

## 💡 Solution: Adaptive Matching Strategy

### **Core Principle:**
**Don't rely on fixed indices - use FLEXIBLE MATCHING based on content**

---

## 🔧 Implementation Strategy

### **1. Structure Detection (Identify Pattern)**

```python
class TableStructure:
    """Detect and classify table structure."""
    
    STANDARD_8X6 = "standard_8x6"
    WITH_DAY_ROW = "with_day_row_9x6"
    EXTENDED = "extended_13x6"
    UNKNOWN = "unknown"
    
    def detect_structure(self, table):
        """
        Detect which pattern this table follows.
        Returns: (structure_type, metadata)
        """
        num_rows = len(table.rows)
        num_cols = len(table.rows[0].cells) if table.rows else 0
        row_labels = self._extract_row_labels(table)
        
        # Check for standard 8x6
        if num_rows == 8 and num_cols == 6:
            if self._matches_standard_rows(row_labels):
                return self.STANDARD_8X6, {
                    'row_offset': 0,
                    'has_day_row': False
                }
        
        # Check for 9x6 with "Day" row
        if num_rows == 9 and num_cols == 6:
            if row_labels[0].lower() == 'day':
                return self.WITH_DAY_ROW, {
                    'row_offset': 1,  # All rows shifted by 1
                    'has_day_row': True
                }
        
        # Check for extended 13x6
        if num_rows == 13 and num_cols == 6:
            return self.EXTENDED, {
                'row_offset': 0,
                'has_extra_rows': True
            }
        
        # Unknown pattern
        return self.UNKNOWN, {
            'row_offset': 0,
            'dimensions': f"{num_rows}x{num_cols}"
        }
    
    def _matches_standard_rows(self, row_labels):
        """Check if row labels match standard pattern."""
        expected = [
            '',  # Row 0
            'Unit, Lesson #, Module:',
            'Objective:',
            'Anticipatory Set:',
            'Tailored Instruction:',
            'Misconception:',
            'Assessment:',
            'Homework:'
        ]
        
        # Allow some flexibility (case-insensitive, whitespace)
        for i, expected_label in enumerate(expected):
            if i >= len(row_labels):
                return False
            
            actual = row_labels[i].strip()
            expected_clean = expected_label.strip()
            
            if expected_clean and actual.lower() != expected_clean.lower():
                return False
        
        return True
```

---

### **2. Row Matching (Find Target Row)**

```python
class RowMatcher:
    """Match input row to output row, handling variations."""
    
    # Standard row label patterns
    ROW_PATTERNS = {
        'unit': ['Unit, Lesson #, Module:', 'Unit, Lesson #', 'Unit/Lesson'],
        'objective': ['Objective:', 'Essential Question', 'Learning Goal'],
        'anticipatory': ['Anticipatory Set:', 'Warm-up:', 'Do Now'],
        'instruction': ['Tailored Instruction:', 'Instruction:', 'Teaching'],
        'misconception': ['Misconception:', 'Common Errors'],
        'assessment': ['Assessment:', 'Check for Understanding'],
        'homework': ['Homework:', 'Independent Practice', 'Extension']
    }
    
    def find_row(self, input_row_label, output_table, structure_metadata):
        """
        Find matching row in output table.
        
        Args:
            input_row_label: Label from input (e.g., "Objective:")
            output_table: Output table to search
            structure_metadata: Info about structure (e.g., row_offset)
        
        Returns:
            row_index in output table, or None
        """
        
        # Apply row offset if needed
        row_offset = structure_metadata.get('row_offset', 0)
        
        # Extract output row labels
        output_labels = [
            row.cells[0].text.strip() if row.cells else ""
            for row in output_table.rows
        ]
        
        # Try exact match first
        for idx, label in enumerate(output_labels):
            if self._labels_match(input_row_label, label):
                return idx
        
        # Try pattern matching
        input_type = self._classify_row(input_row_label)
        if input_type:
            for idx, label in enumerate(output_labels):
                output_type = self._classify_row(label)
                if input_type == output_type:
                    return idx
        
        # Fallback: use input row index + offset
        # (This works if structure is similar)
        return None
    
    def _labels_match(self, label1, label2):
        """Check if two labels match (case-insensitive, flexible)."""
        l1 = label1.lower().strip().rstrip(':')
        l2 = label2.lower().strip().rstrip(':')
        return l1 == l2
    
    def _classify_row(self, label):
        """Classify row by its label."""
        label_lower = label.lower()
        
        for row_type, patterns in self.ROW_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in label_lower:
                    return row_type
        
        return None
```

---

### **3. Column Matching (Find Target Column)**

```python
class ColumnMatcher:
    """Match input column to output column, handling variations."""
    
    DAY_NAMES = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    
    def find_column(self, input_day_hint, output_table):
        """
        Find matching column in output table.
        
        Args:
            input_day_hint: Day from input (e.g., "monday")
            output_table: Output table to search
        
        Returns:
            column_index in output table, or None
        """
        
        if not input_day_hint:
            return None
        
        # Extract column headers (first row)
        if not output_table.rows:
            return None
        
        headers = [
            cell.text.strip() for cell in output_table.rows[0].cells
        ]
        
        # Normalize input day
        target_day = input_day_hint.lower().strip()
        
        # Try to find matching column
        for col_idx, header in enumerate(headers):
            header_lower = header.lower()
            
            # Extract day name from header (ignore dates)
            # "MONDAY 9/22" -> "monday"
            for day in self.DAY_NAMES:
                if day in header_lower:
                    if day == target_day:
                        return col_idx
                    break
        
        return None
```

---

### **4. Hybrid Placement Strategy**

```python
class HybridLinkPlacer:
    """Place links using adaptive strategy."""
    
    def __init__(self):
        self.structure_detector = TableStructure()
        self.row_matcher = RowMatcher()
        self.col_matcher = ColumnMatcher()
    
    def place_link(self, link, output_table):
        """
        Place link using best available method.
        
        Strategy:
        1. Detect output table structure
        2. Try coordinate-based (if standard structure)
        3. Try row+column matching (adaptive)
        4. Fall back to fuzzy text matching
        5. Last resort: Referenced Links section
        """
        
        # Step 1: Detect structure
        structure_type, metadata = self.structure_detector.detect_structure(output_table)
        
        # Step 2: Try coordinate-based (if standard)
        if structure_type == TableStructure.STANDARD_8X6:
            # Use exact coordinates
            if self._is_valid_coordinate(link.row_index, link.column_index, output_table):
                return self._place_at_coordinates(
                    link, 
                    output_table, 
                    link.row_index, 
                    link.column_index
                )
        
        # Step 3: Try adaptive row+column matching
        target_row = self.row_matcher.find_row(
            link.row_label,
            output_table,
            metadata
        )
        
        target_col = self.col_matcher.find_column(
            link.day_hint,
            output_table
        )
        
        if target_row is not None and target_col is not None:
            return self._place_at_coordinates(
                link,
                output_table,
                target_row,
                target_col
            )
        
        # Step 4: Fall back to fuzzy matching
        if target_row is not None:
            # At least we know the row
            return self._place_by_fuzzy_in_row(
                link,
                output_table,
                target_row,
                threshold=0.55
            )
        
        # Step 5: Last resort - Referenced Links
        return self._place_in_fallback(link)
    
    def _is_valid_coordinate(self, row_idx, col_idx, table):
        """Check if coordinates are valid."""
        return (0 <= row_idx < len(table.rows) and
                0 <= col_idx < len(table.rows[row_idx].cells))
    
    def _place_at_coordinates(self, link, table, row_idx, col_idx):
        """Place link at exact coordinates."""
        cell = table.rows[row_idx].cells[col_idx]
        # Add hyperlink to cell
        self._add_hyperlink_to_cell(cell, link.text, link.url)
        return True
    
    def _place_by_fuzzy_in_row(self, link, table, row_idx, threshold):
        """Use fuzzy matching within a specific row."""
        row = table.rows[row_idx]
        
        best_score = 0
        best_cell_idx = None
        
        for cell_idx, cell in enumerate(row.cells):
            score = self._calculate_similarity(link.context, cell.text)
            if score >= threshold and score > best_score:
                best_score = score
                best_cell_idx = cell_idx
        
        if best_cell_idx is not None:
            return self._place_at_coordinates(link, table, row_idx, best_cell_idx)
        
        return False
    
    def _place_in_fallback(self, link):
        """Place in Referenced Links section."""
        # Current fallback logic
        pass
```

---

## 📊 Expected Performance by Structure Type

### **Standard 8x6 (83% of files):**
- **Method:** Coordinate-based
- **Expected inline rate:** 95-100%
- **Fallback rate:** 0-5%

### **9x6 with Day row (9 files):**
- **Method:** Adaptive row matching (with +1 offset)
- **Expected inline rate:** 90-95%
- **Fallback rate:** 5-10%

### **13x6 Extended (3 files):**
- **Method:** Row label matching + fuzzy
- **Expected inline rate:** 85-90%
- **Fallback rate:** 10-15%

### **Other variations (5 files):**
- **Method:** Full adaptive strategy
- **Expected inline rate:** 80-85%
- **Fallback rate:** 15-20%

### **Overall Expected:**
- **Weighted average inline rate:** 93-97%
- **Current:** 84.2%
- **Improvement:** +9-13 percentage points

---

## 🎯 Implementation Priority

### **Phase 1: Core Infrastructure (Week 1)**
1. Implement `TableStructure` detector
2. Implement `RowMatcher` with pattern matching
3. Implement `ColumnMatcher` with flexible day extraction
4. Add unit tests for each component

### **Phase 2: Integration (Week 1-2)**
1. Integrate into `DOCXParser` (store row/col indices)
2. Integrate into `DOCXRenderer` (use `HybridLinkPlacer`)
3. Test on standard 8x6 files first
4. Validate improvement

### **Phase 3: Refinement (Week 2-3)**
1. Test on all variation types
2. Tune matching thresholds
3. Add logging for debugging
4. Document edge cases

---

## 🔍 Handling Specific Edge Cases

### **Case 1: Extra "Day" row at top**
```python
# Detection
if row_labels[0].lower() == 'day':
    row_offset = 1

# Adjustment
target_row = input_row_index + row_offset
```

### **Case 2: Different row labels**
```python
# Use pattern matching instead of exact match
if 'objective' in row_label.lower() or 'essential question' in row_label.lower():
    row_type = 'objective'
```

### **Case 3: Dates in column headers**
```python
# Extract day name, ignore dates
import re
day_match = re.search(r'(monday|tuesday|wednesday|thursday|friday)', 
                      header.lower())
if day_match:
    day_name = day_match.group(1)
```

### **Case 4: Partial week (THURSDAY | FRIDAY only)**
```python
# Map days to available columns
available_days = extract_days_from_headers(table)
if input_day in available_days:
    return day_to_column_map[input_day]
else:
    return None  # Day not in this week
```

---

## ✅ Benefits of This Approach

1. **Handles 100% of files** (not just 83%)
2. **Graceful degradation** (falls back to fuzzy if needed)
3. **Maintainable** (clear separation of concerns)
4. **Extensible** (easy to add new patterns)
5. **Testable** (each component can be unit tested)
6. **Robust** (multiple fallback strategies)

---

## 🚀 Migration Path

### **Current State:**
- Fuzzy matching only
- 84.2% inline rate

### **After Phase 1:**
- Coordinate-based for standard files
- 90-93% inline rate

### **After Phase 2:**
- Adaptive matching for all variations
- 93-97% inline rate

### **After Phase 3:**
- Optimized and refined
- 95-98% inline rate

---

**The key is: Don't fight the variations - embrace them with flexible, adaptive matching!**
