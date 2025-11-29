# Table Structure Knowledge Base - Key Insights

**Generated:** 2025-10-19  
**Files Analyzed:** 100 lesson plans  
**Success Rate:** 100/100 (100%)  

---

## 📊 Summary Statistics

- **Total files analyzed:** 100
- **Successfully analyzed:** 100 (100%)
- **Standard structure (8x6):** 83 files (83%)
- **Variations:** 17 files (17%)

---

## ✅ Standard Structure (83% of files)

### **Dimensions:**
- **8 rows x 6 columns**

### **Row Labels:**
```
Row 0: (empty)
Row 1: Unit, Lesson #, Module:
Row 2: Objective:
Row 3: Anticipatory Set:
Row 4: Tailored Instruction:
Row 5: Misconception:
Row 6: Assessment:
Row 7: Homework:
```

### **Column Headers:**
```
Col 0: (empty)
Col 1: MONDAY
Col 2: TUESDAY
Col 3: WEDNESDAY
Col 4: THURSDAY
Col 5: FRIDAY
```

---

## 🔍 Variations Found

### **Dimension Variations (7 patterns):**
1. **8x6** - 83 files (STANDARD)
2. **9x6** - 9 files
3. **13x6** - 3 files
4. **14x6** - 1 file
5. **10x6** - 1 file
6. **4x6** - 1 file
7. **8x2** - 1 file (observation template)

### **Row Sequence Variations (14 patterns):**
- Most common: Standard 8-row structure (83 files)
- Variations include:
  - Additional "Day" row at top
  - "Essential Question" instead of "Objective"
  - Extra rows for specific activities
  - Merged or split sections

### **Column Header Variations (6 patterns):**
1. **Standard:** ` | MONDAY | TUESDAY | WEDNESDAY | THURSDAY | FRIDAY` (93 files)
2. **With "Day":** `Day | MONDAY | TUESDAY | ...` (3 files)
3. **With dates:** ` | MONDAY 9/22 | TUESDAY 9/23 | ...` (various)
4. **Partial week:** `THURSDAY | FRIDAY` (1 file - observation)

---

## 💡 Key Insights for Code Improvement

### **1. Coordinate-Based Placement IS Viable**

**✓ Pros:**
- 83% of files have identical structure
- Row labels are highly consistent
- Column headers are very consistent

**⚠️ Cons:**
- 17% of files have variations
- Need fallback logic for non-standard structures

**Recommendation:**
```python
# Try coordinate-based placement first
if table_structure_matches_standard(output_table):
    place_link_at_coordinates(row_index, col_index)
else:
    # Fall back to fuzzy matching
    place_link_by_context(link_text, context)
```

---

### **2. Row Label Matching is Highly Reliable**

**Standard row labels are present in 83%+ of files:**
- "Unit, Lesson #, Module:" → Row 1
- "Objective:" → Row 2
- "Anticipatory Set:" → Row 3
- "Tailored Instruction:" → Row 4
- "Misconception:" → Row 5
- "Assessment:" → Row 6
- "Homework:" → Row 7

**Recommendation:**
```python
# Use row_label as primary hint
row_label_map = {
    'Unit, Lesson #, Module:': 1,
    'Objective:': 2,
    'Anticipatory Set:': 3,
    'Tailored Instruction:': 4,
    'Misconception:': 5,
    'Assessment:': 6,
    'Homework:': 7
}

target_row = row_label_map.get(link.row_label, link.row_index)
```

---

### **3. Column Headers are Very Consistent**

**Day names are standard across 99% of files:**
- Col 1: MONDAY
- Col 2: TUESDAY
- Col 3: WEDNESDAY
- Col 4: THURSDAY
- Col 5: FRIDAY

**Variations:**
- Some include dates (e.g., "MONDAY 9/22")
- Some have "Day" label in Col 0
- One file has only THURSDAY | FRIDAY

**Recommendation:**
```python
# Extract day name from column header (ignore dates)
day_map = {
    'monday': 1,
    'tuesday': 2,
    'wednesday': 3,
    'thursday': 4,
    'friday': 5
}

# Match flexibly
for col_idx, header in enumerate(col_headers):
    day = extract_day_name(header.lower())  # "monday 9/22" → "monday"
    if day in day_map:
        day_to_col[day] = col_idx
```

---

### **4. Empty First Row is Common**

**96 out of 100 files have empty Row 0:**
- This is the header row with day names
- Row 0, Col 0 is always empty
- Actual content starts at Row 1

**Recommendation:**
```python
# Skip Row 0 when placing content links
if row_index == 0:
    # This is header row, don't place content links here
    pass
```

---

## 🎯 Recommended Implementation Strategy

### **Phase 1: Hybrid Approach (Immediate)**

```python
def place_hyperlink(link, output_table):
    """
    Hybrid placement strategy:
    1. Try coordinate-based (if structure matches)
    2. Fall back to row_label + day matching
    3. Fall back to fuzzy text matching
    4. Last resort: Referenced Links section
    """
    
    # Check if table structure is standard
    if is_standard_structure(output_table):
        # Use exact coordinates
        return place_at_coordinates(link.row_index, link.column_index)
    
    # Try row_label + day matching
    target_row = find_row_by_label(link.row_label, output_table)
    target_col = find_col_by_day(link.day_hint, output_table)
    
    if target_row and target_col:
        return place_at_cell(target_row, target_col)
    
    # Fall back to fuzzy matching (current approach)
    return place_by_fuzzy_match(link, output_table, threshold=0.55)
```

### **Phase 2: Structure Detection (Future)**

```python
def detect_table_structure(table):
    """
    Detect which structure pattern this table follows.
    Returns structure type and mapping rules.
    """
    
    dimensions = f"{len(table.rows)}x{len(table.rows[0].cells)}"
    row_labels = extract_row_labels(table)
    
    # Check against known patterns
    if dimensions == "8x6" and matches_standard_rows(row_labels):
        return "standard", STANDARD_MAPPING
    elif dimensions == "9x6" and has_day_row(row_labels):
        return "with_day_row", DAY_ROW_MAPPING
    elif dimensions == "13x6":
        return "extended", EXTENDED_MAPPING
    else:
        return "unknown", None
```

---

## 📈 Expected Improvement

**Current (with threshold 0.55):**
- Inline rate: 84.2%
- Fallback: 15.8%

**With coordinate-based placement:**
- Expected inline rate: **95-100%** (for standard 8x6 files)
- Expected fallback: **0-5%** (only for truly ambiguous links)

**For non-standard files:**
- Fall back to current fuzzy matching
- Still achieve 80-85% inline rate

---

## 🚀 Next Steps

1. **Implement structure detection** in parser
2. **Add coordinate-based placement** in renderer
3. **Test on standard files** (83% of corpus)
4. **Validate on non-standard files** (17% of corpus)
5. **Monitor and refine** based on results

---

## 📁 Generated Files

- `table_structure_knowledge_base.json` - Structured data for code
- `table_structure_analysis_results.json` - Detailed analysis
- `TABLE_STRUCTURE_INSIGHTS.md` - This document

---

**Conclusion:** Coordinate-based placement is highly viable for 83% of files and will dramatically improve inline placement rates. The remaining 17% can fall back to fuzzy matching.
