# Table Structure Instrumentation Added

## Status: ✅ IMPLEMENTED

Added comprehensive table structure logging to gather real-world data before implementing slot-aware extraction.

---

## What Was Added

### Location: `tools/batch_processor.py` lines 382-419

After parser creation in `_process_slot()`, we now log:

1. **Document-level info:**
   - Total table count
   - Slot number being processed
   - Subject
   - Filename

2. **Per-table details:**
   - Table index (0-based)
   - First cell text (up to 100 chars)
   - First row text (all cells, up to 200 chars)
   - Row count
   - Column count

---

## Log Output Format

### Document Level:
```json
{
  "event": "document_table_structure",
  "slot": 1,
  "subject": "ELA",
  "file": "Lang Lesson Plans 10_27_25-10_31_25.docx",
  "total_tables": 9
}
```

### Per Table:
```json
{
  "event": "table_structure_detail",
  "slot": 1,
  "file": "Lang Lesson Plans 10_27_25-10_31_25.docx",
  "table_idx": 0,
  "first_cell": "Name: Kelsey Lang",
  "first_row": "Name: Kelsey Lang | Grade: 3 | Subject: ELA | Week of: 10/27-10/31 | ",
  "row_count": 1,
  "col_count": 5
}
```

---

## What We'll Learn

### 1. Slot Table Patterns
- Do metadata tables always have "Name:" in first cell?
- Do daily plan tables have weekday headers?
- Are they always paired (metadata + daily)?

### 2. Extra Tables
- Summary tables before slot 1?
- Signature tables at end?
- Referenced links sections?
- Where do they appear?

### 3. Layout Variations
- Do all files follow (slot-1)*2 pattern?
- Are there missing tables?
- Are there extra tables between slots?

### 4. Slot Boundaries
- How can we reliably detect where one slot ends and another begins?
- What markers are consistent across files?

---

## Next Steps

### 1. Collect Data
Run processing on W44 files and capture logs:
```bash
cd d:\LP
python -m uvicorn backend.api:app --reload --port 8000 > instrumentation_logs.txt 2>&1
```

Then process W44 files through the UI.

### 2. Analyze Logs
Extract table structure logs:
```bash
grep "table_structure" instrumentation_logs.txt > table_analysis.txt
```

### 3. Design Slot Map
Based on real data, create detection logic:
```python
def build_slot_map(doc):
    """Build map of which tables belong to which slots."""
    # Implementation based on what we learn from logs
```

### 4. Implement Slot-Aware Extraction
Once we have confident detection:
- Extract only from slot's tables
- Skip paragraph links
- Handle signature tables
- Validate structure

### 5. Add Tests
Create fixtures for:
- Standard layout (2 tables per slot + signature)
- Missing metadata table
- Extra summary table
- Paragraph-only links
- Out-of-order slots

---

## Questions to Answer from Data

1. **Metadata Table Detection:**
   - What text patterns identify metadata tables?
   - "Name:", "Teacher:", "Subject:"?
   - Are they always in first cell?

2. **Daily Plan Table Detection:**
   - Do they have "Monday", "Tuesday", etc. in first row?
   - Are they always immediately after metadata?
   - What if they're missing?

3. **Signature Table Detection:**
   - Always last table?
   - Always contains "Signature" or "Required Signatures"?
   - Always 1 column?

4. **Slot Counting:**
   - How many slots per file typically?
   - Are they always sequential?
   - Can we detect slot number from content?

5. **Paragraph Links:**
   - Where do they appear in the document?
   - Are they between tables?
   - Are they in specific sections?

---

## Expected Timeline

1. **Data Collection:** 10 minutes (process W44 files)
2. **Log Analysis:** 30 minutes (extract and review patterns)
3. **Slot Map Design:** 1 hour (design detection logic)
4. **Implementation:** 2 hours (slot-aware extraction)
5. **Testing:** 1 hour (fixtures and validation)

**Total:** ~4-5 hours for complete, data-driven solution

---

## Success Criteria

After implementation, we should be able to:

✅ Detect slot boundaries in any standard file
✅ Extract hyperlinks only from correct tables
✅ Exclude paragraph links during slot extraction
✅ Handle signature tables gracefully
✅ Warn on unexpected layouts
✅ Pass all test fixtures
✅ Eliminate cross-contamination

---

**Status:** Instrumentation ready. Waiting for data collection run. 📊
