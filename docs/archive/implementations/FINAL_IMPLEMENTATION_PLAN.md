# Final Slot-Aware Extraction Implementation Plan

## Status: 📋 READY TO IMPLEMENT

All decisions made, clear path forward.

---

## Decisions Locked In

### 1. Paragraph Hyperlinks: **EXCLUDE (Option A)**
- Slot-aware mode = table-only extraction
- Skip all paragraph links during slot extraction
- They're document-wide references and primary contaminant
- Can move to referenced-links appendix if needed later

### 2. Images: **ADD table_idx**
- Extend `_find_image_context()` to populate `table_idx`
- Filter images by table index like hyperlinks
- Must be done before slot extraction works

### 3. Validation: **FAIL LOUDLY**
- Throw exceptions for unexpected layouts
- No silent fallbacks
- Clear error messages
- Immediate visibility of issues

### 4. Slot Selection: **USE CONFIGURED SLOTS**
- Only extract slots configured in UI/database
- Ignore extra tables in document
- Map configured `slot_number` to table indices
- Respect user's slot configuration

---

## Implementation Steps

### Step 1: Add table_idx to Image Extraction

**File:** `tools/docx_parser.py`

**Current `_find_image_context()`:**
```python
def _find_image_context(self, image_rel_id):
    # ... existing code ...
    return {
        'context_snippet': ...,
        'section_hint': ...,
        'day_hint': ...,
        # table_idx is missing!
    }
```

**Updated:**
```python
def _find_image_context(self, image_rel_id):
    """Find context for image with table index."""
    
    # Search tables for this image
    for table_idx, table in enumerate(self.doc.tables):
        for row_idx, row in enumerate(table.rows):
            for cell_idx, cell in enumerate(row.cells):
                # Check if image is in this cell
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        if hasattr(run._element, 'xml'):
                            if image_rel_id in run._element.xml:
                                # Found it!
                                row_label = row.cells[0].text.strip() if row.cells else ""
                                col_header = table.rows[0].cells[cell_idx].text.strip() if table.rows else ""
                                
                                return {
                                    'context_snippet': paragraph.text[:100],
                                    'section_hint': self._infer_section(row_label),
                                    'day_hint': self._extract_day_from_header(col_header),
                                    'table_idx': table_idx,  # ADD THIS
                                    'row_idx': row_idx,
                                    'cell_idx': cell_idx,
                                    'row_label': row_label,
                                    'col_header': col_header
                                }
    
    # Not found in tables
    return {
        'context_snippet': '',
        'section_hint': None,
        'day_hint': None,
        'table_idx': None,  # Not in a table
        'row_idx': None,
        'cell_idx': None,
        'row_label': None,
        'col_header': None
    }
```

---

### Step 2: Add Slot Validation Function

**File:** `tools/docx_parser.py`

```python
def validate_slot_structure(doc, slot_number):
    """
    Validate document structure for slot extraction.
    
    Args:
        doc: Document object
        slot_number: Requested slot number (1-indexed)
        
    Raises:
        ValueError: If structure is invalid with detailed message
        
    Returns:
        tuple: (table_start, table_end) indices for the slot
    """
    from backend.telemetry import logger
    
    table_count = len(doc.tables)
    
    if table_count == 0:
        raise ValueError("Document has no tables")
    
    # Check for signature table
    last_table = doc.tables[-1]
    has_signature = False
    
    if last_table.rows and last_table.rows[0].cells:
        first_cell = last_table.rows[0].cells[0].text.strip().lower()
        if "signature" in first_cell or "required signatures" in first_cell:
            has_signature = True
    
    if not has_signature:
        raise ValueError(
            f"Missing signature table. Document has {table_count} tables but "
            f"last table doesn't contain 'signature' in first cell."
        )
    
    # Calculate available slots (excluding signature)
    available_slots = (table_count - 1) // 2
    
    # Validate table count matches expected pattern
    expected_table_count = (available_slots * 2) + 1
    if table_count != expected_table_count:
        raise ValueError(
            f"Unexpected table count: {table_count}. "
            f"Expected {expected_table_count} for {available_slots} slots. "
            f"Valid counts are: 3 (1 slot), 9 (4 slots), 11 (5 slots)."
        )
    
    # Validate requested slot exists
    if slot_number < 1:
        raise ValueError(f"Slot number must be >= 1, got {slot_number}")
    
    if slot_number > available_slots:
        raise ValueError(
            f"Slot {slot_number} requested but only {available_slots} slots available. "
            f"Document has {table_count} tables."
        )
    
    # Calculate table indices for this slot
    table_start = (slot_number - 1) * 2
    table_end = table_start + 1
    
    # Validate metadata table
    meta_table = doc.tables[table_start]
    if not meta_table.rows or not meta_table.rows[0].cells:
        raise ValueError(f"Slot {slot_number} metadata table (index {table_start}) is empty")
    
    first_cell = meta_table.rows[0].cells[0].text.strip()
    if not first_cell.startswith("Name:"):
        raise ValueError(
            f"Slot {slot_number} table {table_start} doesn't look like metadata table. "
            f"Expected 'Name:' but got: '{first_cell[:50]}'"
        )
    
    # Validate daily plans table
    daily_table = doc.tables[table_end]
    if not daily_table.rows or not daily_table.rows[0].cells:
        raise ValueError(f"Slot {slot_number} daily plans table (index {table_end}) is empty")
    
    first_row = " ".join(cell.text.strip() for cell in daily_table.rows[0].cells[:5]).upper()
    if not any(day in first_row for day in ["MONDAY", "TUESDAY", "WEDNESDAY"]):
        raise ValueError(
            f"Slot {slot_number} table {table_end} doesn't look like daily plans table. "
            f"Expected weekday headers but got: '{first_row[:100]}'"
        )
    
    logger.info(
        "slot_structure_validated",
        extra={
            "slot_number": slot_number,
            "table_start": table_start,
            "table_end": table_end,
            "total_tables": table_count,
            "available_slots": available_slots
        }
    )
    
    return table_start, table_end
```

---

### Step 3: Add Slot-Aware Extraction Methods

**File:** `tools/docx_parser.py`

```python
def extract_hyperlinks_for_slot(self, slot_number: int) -> List[Dict[str, str]]:
    """
    Extract hyperlinks for specific slot only.
    
    Table-only extraction - paragraph links are excluded to prevent
    cross-slot contamination.
    
    Args:
        slot_number: Slot number (1-indexed, from configured slots)
        
    Returns:
        List of hyperlink dictionaries from slot's tables only
        
    Raises:
        ValueError: If slot structure is invalid
    """
    from backend.telemetry import logger
    
    # Validate and get table indices
    table_start, table_end = validate_slot_structure(self.doc, slot_number)
    
    logger.info(
        "extracting_slot_hyperlinks",
        extra={
            "slot_number": slot_number,
            "table_start": table_start,
            "table_end": table_end
        }
    )
    
    hyperlinks = []
    
    # Extract ONLY from slot's tables (no paragraphs!)
    for table_idx in range(table_start, table_end + 1):
        table = self.doc.tables[table_idx]
        
        # Get column headers
        col_headers = []
        if table.rows:
            col_headers = [cell.text.strip() for cell in table.rows[0].cells]
        
        for row_idx, row in enumerate(table.rows):
            row_label = row.cells[0].text.strip() if row.cells else ""
            
            for cell_idx, cell in enumerate(row.cells):
                col_header = col_headers[cell_idx] if cell_idx < len(col_headers) else ""
                day_hint = self._extract_day_from_header(col_header)
                
                for paragraph in cell.paragraphs:
                    for hyperlink in paragraph._element.xpath('.//w:hyperlink'):
                        try:
                            r_id = hyperlink.get(qn('r:id'))
                            if r_id and r_id in paragraph.part.rels:
                                url = paragraph.part.rels[r_id].target_ref
                                text = ''.join(node.text for node in hyperlink.xpath('.//w:t') if node.text)
                                
                                if text and url:
                                    hyperlinks.append({
                                        'schema_version': '2.0',
                                        'text': text,
                                        'url': url,
                                        'context_snippet': self._get_context_snippet(paragraph, text),
                                        'context_type': 'table',
                                        'section_hint': self._infer_section(row_label),
                                        'day_hint': day_hint,
                                        'table_idx': table_idx,
                                        'row_idx': row_idx,
                                        'cell_idx': cell_idx,
                                        'row_label': row_label,
                                        'col_header': col_header
                                    })
                        except Exception as e:
                            logger.warning(
                                "hyperlink_extraction_failed",
                                extra={"error": str(e), "table_idx": table_idx}
                            )
    
    logger.info(
        "slot_hyperlinks_extracted",
        extra={
            "slot_number": slot_number,
            "hyperlink_count": len(hyperlinks)
        }
    )
    
    return hyperlinks


def extract_images_for_slot(self, slot_number: int) -> List[Dict]:
    """
    Extract images for specific slot only.
    
    Args:
        slot_number: Slot number (1-indexed, from configured slots)
        
    Returns:
        List of image dictionaries from slot's tables only
        
    Raises:
        ValueError: If slot structure is invalid
    """
    from backend.telemetry import logger
    
    # Validate and get table indices
    table_start, table_end = validate_slot_structure(self.doc, slot_number)
    
    # Extract all images (with table_idx now populated)
    all_images = self.extract_images()
    
    # Filter to slot's tables only
    slot_images = [
        img for img in all_images
        if img.get('table_idx') is not None and
        table_start <= img['table_idx'] <= table_end
    ]
    
    logger.info(
        "slot_images_extracted",
        extra={
            "slot_number": slot_number,
            "total_images": len(all_images),
            "slot_images": len(slot_images),
            "table_start": table_start,
            "table_end": table_end
        }
    )
    
    return slot_images
```

---

### Step 4: Update Batch Processor

**File:** `tools/batch_processor.py` in `_process_slot()` method

**Change from:**
```python
images = await asyncio.to_thread(parser.extract_images)
hyperlinks = await asyncio.to_thread(parser.extract_hyperlinks)
```

**To:**
```python
slot_num = slot['slot_number']

# Use slot-aware extraction (table-only, no paragraphs)
try:
    images = await asyncio.to_thread(parser.extract_images_for_slot, slot_num)
    hyperlinks = await asyncio.to_thread(parser.extract_hyperlinks_for_slot, slot_num)
    
    logger.info(
        "slot_extraction_success",
        extra={
            "slot": slot_num,
            "images": len(images),
            "hyperlinks": len(hyperlinks)
        }
    )
except ValueError as e:
    # Structure validation failed - log and re-raise
    logger.error(
        "slot_structure_invalid",
        extra={
            "slot": slot_num,
            "file": primary_file,
            "error": str(e)
        }
    )
    raise
```

---

### Step 5: Testing Plan

#### Unit Tests (`tests/test_slot_extraction.py`):

```python
def test_validate_slot_structure_valid():
    """Test validation passes for valid structure."""
    # 9 tables (4 slots + signature)
    assert validate_slot_structure(doc, 1) == (0, 1)
    assert validate_slot_structure(doc, 4) == (6, 7)

def test_validate_slot_structure_missing_signature():
    """Test validation fails without signature."""
    with pytest.raises(ValueError, match="Missing signature table"):
        validate_slot_structure(doc_no_sig, 1)

def test_validate_slot_structure_invalid_table_count():
    """Test validation fails for unexpected table count."""
    with pytest.raises(ValueError, match="Unexpected table count"):
        validate_slot_structure(doc_7_tables, 1)

def test_validate_slot_structure_slot_exceeds():
    """Test validation fails when slot > available."""
    with pytest.raises(ValueError, match="only 4 slots available"):
        validate_slot_structure(doc_9_tables, 5)

def test_extract_hyperlinks_for_slot():
    """Test slot extraction gets only slot's links."""
    links = parser.extract_hyperlinks_for_slot(1)
    # All links should be from tables 0-1
    assert all(0 <= link['table_idx'] <= 1 for link in links)

def test_extract_hyperlinks_for_slot_no_paragraphs():
    """Test paragraph links are excluded."""
    links = parser.extract_hyperlinks_for_slot(1)
    # No paragraph links (context_type != 'paragraph')
    assert all(link['context_type'] == 'table' for link in links)

def test_extract_images_for_slot():
    """Test slot extraction gets only slot's images."""
    images = parser.extract_images_for_slot(1)
    # All images should be from tables 0-1
    assert all(0 <= img['table_idx'] <= 1 for img in images)
```

#### Integration Test:

```python
def test_w44_no_cross_contamination():
    """Test W44 files have no cross-contamination."""
    # Process all W44 files
    # Check diagnostic logs
    # Verify slot 1 hyperlinks != slot 2 hyperlinks
    # Verify no overlap
```

---

## Deployment Checklist

- [ ] Step 1: Add `table_idx` to image extraction
- [ ] Step 2: Add validation function
- [ ] Step 3: Add slot-aware extraction methods
- [ ] Step 4: Update batch processor
- [ ] Step 5: Write unit tests
- [ ] Step 6: Test with W44 files
- [ ] Step 7: Check diagnostic logs
- [ ] Step 8: Verify output quality
- [ ] Step 9: Deploy to production
- [ ] Step 10: Monitor for issues

---

## Expected Results

### Before:
```
Slot 1 (ELA): 94 hyperlinks (all slots mixed)
Slot 2 (Math): 94 hyperlinks (all slots mixed)
Cross-contamination: YES
```

### After:
```
Slot 1 (ELA): ~20 hyperlinks (ELA only, tables 0-1)
Slot 2 (Math): ~20 hyperlinks (Math only, tables 2-3)
Cross-contamination: NO
```

---

**Status: Ready to implement. All decisions made, clear path forward.** ✅
