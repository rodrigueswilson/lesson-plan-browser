# Complete Slot-Aware Extraction Plan

## Status: 📋 PLANNING - All Issues Must Be Resolved Before Implementation

Based on analysis of 34 teacher files showing 100% consistency, but critical gaps remain.

---

## Data Summary

**✅ What We Know:**
- 34 teacher files analyzed (Lang, Savoca, Davies, Morais, Santiago, Grande)
- 100% follow standard patterns (29 with 4 slots, 5 with 1 slot)
- All have signature tables at end
- Perfect metadata/daily plans pairing

**⚠️ What We Don't Know:**
- Behavior across multiple grades
- Behavior across full school year
- Edge cases in earlier/later weeks

---

## Critical Issues to Resolve

### 1. Paragraph Hyperlinks ⚠️ UNRESOLVED

**Problem:**
- "Referenced Links" sections contain paragraph-level hyperlinks
- These are document-scoped, not table-scoped
- Current plan would tag them with current slot → cross-contamination persists

**Options:**

#### Option A: Exclude All Paragraph Links (Recommended)
```python
def extract_hyperlinks_for_slot(parser, slot_number):
    # Skip paragraph extraction entirely
    # Only extract from tables
    hyperlinks = []
    
    table_start = (slot_number - 1) * 2
    table_end = table_start + 1
    
    for table_idx in range(table_start, table_end + 1):
        table_links = extract_from_table(parser, table_idx)
        hyperlinks.extend(table_links)
    
    return hyperlinks  # No paragraph links
```

**Pros:**
- Simple and clean
- Eliminates cross-contamination source
- Most links are in tables anyway

**Cons:**
- Loses "Referenced Links" sections
- May lose legitimate document-level links

#### Option B: Extract Paragraph Links Only for Full-Document Mode
```python
def extract_hyperlinks(parser, include_paragraphs=True):
    # Only include paragraphs when not filtering by slot
    if include_paragraphs:
        # Extract paragraph links
        pass
```

**Pros:**
- Preserves paragraph links for non-slot extraction
- Clean separation of concerns

**Cons:**
- Still doesn't solve where paragraph links belong

#### Option C: Try to Map Paragraph Links to Slots
```python
def map_paragraph_to_slot(paragraph, doc):
    # Find which tables this paragraph is between
    # Assign to nearest slot
    pass
```

**Pros:**
- Preserves all links
- Attempts intelligent mapping

**Cons:**
- Complex and error-prone
- Paragraph position may not correlate with slot
- "Referenced Links" at end → which slot?

**DECISION NEEDED:** Which option should we implement?

---

### 2. Image Table Index ⚠️ UNRESOLVED

**Problem:**
- `_find_image_context()` doesn't populate `table_idx`
- Slot filtering would drop ALL images
- Image placement would completely fail

**Required Fix:**

```python
def _find_image_context(self, image_rel_id):
    """Extract image context with table index."""
    # ... existing code ...
    
    # NEW: Add table index detection
    for table_idx, table in enumerate(self.doc.tables):
        for row in table.rows:
            for cell in row.cells:
                # Check if image is in this cell
                if image_rel_id in cell._element.xml:
                    return {
                        # ... existing fields ...
                        'table_idx': table_idx,  # ADD THIS
                        'row_idx': row_idx,
                        'cell_idx': cell_idx
                    }
    
    return {
        # ... existing fields ...
        'table_idx': None  # Not in a table
    }
```

**Then in slot extraction:**
```python
def extract_images_for_slot(parser, slot_number):
    all_images = parser.extract_images()
    
    table_start = (slot_number - 1) * 2
    table_end = table_start + 1
    
    # Filter by table_idx
    slot_images = [
        img for img in all_images
        if img.get('table_idx') is not None and
        table_start <= img['table_idx'] <= table_end
    ]
    
    return slot_images
```

**REQUIRED:** Must implement before slot extraction works.

---

### 3. Validation Strategy ⚠️ UNRESOLVED

**Problem:**
- Falling back to full extraction silently reintroduces the bug
- Need loud failures for unexpected structures
- Need clear error messages

**Proposed Validation:**

```python
def validate_slot_structure(doc, slot_number):
    """
    Validate document structure before slot extraction.
    Raises ValueError with clear message if invalid.
    """
    table_count = len(doc.tables)
    
    # Check for signature table
    has_signature = False
    if table_count > 0:
        last_table = doc.tables[-1]
        if last_table.rows and last_table.rows[0].cells:
            first_cell = last_table.rows[0].cells[0].text.strip().lower()
            if "signature" in first_cell or "required signatures" in first_cell:
                has_signature = True
    
    # Expected table counts
    if not has_signature:
        raise ValueError(
            f"Missing signature table. Found {table_count} tables. "
            f"Expected signature table at end."
        )
    
    # Calculate slots
    expected_slots = (table_count - 1) // 2
    
    if table_count not in [3, 9, 11]:
        raise ValueError(
            f"Unexpected table count: {table_count}. "
            f"Expected 3 (1 slot), 9 (4 slots), or 11 (5 slots). "
            f"Detected {expected_slots} slots."
        )
    
    # Validate slot number
    if slot_number > expected_slots:
        raise ValueError(
            f"Slot {slot_number} requested but only {expected_slots} slots available. "
            f"File has {table_count} tables."
        )
    
    # Validate metadata/daily pairing
    for slot_idx in range(1, expected_slots + 1):
        meta_idx = (slot_idx - 1) * 2
        daily_idx = meta_idx + 1
        
        if meta_idx >= table_count or daily_idx >= table_count:
            raise ValueError(f"Slot {slot_idx} tables out of range")
        
        meta_table = doc.tables[meta_idx]
        daily_table = doc.tables[daily_idx]
        
        # Check metadata table
        if not meta_table.rows or not meta_table.rows[0].cells:
            raise ValueError(f"Slot {slot_idx} metadata table is empty")
        
        first_cell = meta_table.rows[0].cells[0].text.strip()
        if not first_cell.startswith("Name:"):
            raise ValueError(
                f"Slot {slot_idx} table {meta_idx} doesn't look like metadata table. "
                f"First cell: '{first_cell[:50]}'"
            )
        
        # Check daily plans table
        if not daily_table.rows or not daily_table.rows[0].cells:
            raise ValueError(f"Slot {slot_idx} daily plans table is empty")
        
        first_row = " ".join(cell.text.strip() for cell in daily_table.rows[0].cells[:5])
        if not any(day in first_row.upper() for day in ["MONDAY", "TUESDAY", "WEDNESDAY"]):
            raise ValueError(
                f"Slot {slot_idx} table {daily_idx} doesn't look like daily plans table. "
                f"First row: '{first_row[:100]}'"
            )
    
    return True  # Validation passed
```

**Usage:**
```python
def extract_hyperlinks_for_slot(parser, slot_number):
    # Validate first - raises ValueError if invalid
    validate_slot_structure(parser.doc, slot_number)
    
    # If we get here, structure is valid
    table_start = (slot_number - 1) * 2
    table_end = table_start + 1
    
    return extract_from_tables(parser, table_start, table_end)
```

**DECISION NEEDED:** Should validation raise exceptions or return errors?

---

### 4. Data Coverage ⚠️ INCOMPLETE

**Current Coverage:**
- 34 files from 6 teachers
- Weeks from September-October 2025
- Grades 2-3 (mostly)

**Missing Coverage:**
- Earlier weeks (August, beginning of year)
- Later weeks (November-June)
- Other grades (K, 1, 4, 5, 6)
- Other teachers (if any)

**Recommendation:**
- Analyze at least 2-3 more weeks per teacher
- Include beginning and end of year if available
- Document any variations found

**DECISION NEEDED:** How much more data do we need before implementation?

---

## Implementation Checklist

### Phase 1: Prerequisites (MUST DO FIRST)
- [ ] **Decision:** Paragraph link handling (Option A, B, or C?)
- [ ] **Implementation:** Add `table_idx` to image extraction
- [ ] **Implementation:** Validation with clear error messages
- [ ] **Data:** Analyze more weeks/grades if available

### Phase 2: Core Implementation
- [ ] Add `extract_hyperlinks_for_slot()` to parser
- [ ] Add `extract_images_for_slot()` to parser
- [ ] Add validation function
- [ ] Update batch processor to use slot-aware extraction

### Phase 3: Testing
- [ ] Unit tests for slot detection
- [ ] Unit tests for validation
- [ ] Unit tests for edge cases
- [ ] Integration test with W44 files
- [ ] Verify no cross-contamination

### Phase 4: Deployment
- [ ] Test on production data
- [ ] Monitor diagnostic logs
- [ ] Verify output quality
- [ ] Document behavior

---

## Decisions Required

### 1. Paragraph Links
**Question:** What should we do with paragraph-level hyperlinks?
- [ ] Option A: Exclude them (recommended)
- [ ] Option B: Only in full-document mode
- [ ] Option C: Try to map to slots

**Your decision:** _____________

### 2. Validation Behavior
**Question:** How should validation failures be handled?
- [ ] Raise exceptions (fail loudly)
- [ ] Log warnings and fallback
- [ ] Return error codes

**Your decision:** _____________

### 3. Data Coverage
**Question:** How much more data analysis is needed?
- [ ] Current data is sufficient (34 files, 100% consistent)
- [ ] Need 2-3 more weeks per teacher
- [ ] Need full year coverage

**Your decision:** _____________

---

## Risk Assessment

### High Risk (Must Fix Before Implementation):
1. ❌ **Paragraph links** - Will cause continued cross-contamination
2. ❌ **Image table_idx** - Will break all image placement
3. ❌ **Weak validation** - Silent failures

### Medium Risk (Should Address):
4. ⚠️ **Limited data coverage** - May miss edge cases
5. ⚠️ **No rollback plan** - If something breaks

### Low Risk (Can Monitor):
6. ✅ **Table structure** - 100% consistent in current data
7. ✅ **Signature detection** - Works reliably

---

## Recommendation

**DO NOT IMPLEMENT YET**

Complete these steps first:
1. **Decide on paragraph link handling**
2. **Implement image table_idx**
3. **Implement strict validation**
4. **Analyze more data if available**
5. **Create comprehensive tests**

Then and only then implement slot-aware extraction.

---

**Status:** Waiting for decisions on paragraph links, validation, and data coverage. 🛑
