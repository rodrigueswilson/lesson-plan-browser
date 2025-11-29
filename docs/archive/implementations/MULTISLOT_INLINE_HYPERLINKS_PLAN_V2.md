# Multi-Slot Inline Hyperlinks - Implementation Plan V2

## Goal

Enable inline hyperlink placement for multi-slot documents by refactoring the rendering to fill each slot separately with its own hyperlinks.

**Key insight from review:** Reuse existing `_fill_cell` logic instead of creating new helpers.

---

## Revised Architecture

### Current Flow

```python
# _fill_multi_slot_day()
1. Collect all slots' content into arrays
2. Combine: "Slot 1: ELA\n...\n---\nSlot 2: Math\n..."
3. Call _fill_cell(combined_text, pending_hyperlinks=None)
4. Result: No inline hyperlinks
```

### New Flow

```python
# _fill_multi_slot_day()
1. For each row (Unit/Lesson, Objective, etc.):
   a. Clear cell once
   b. For each slot:
      - Filter hyperlinks for this slot
      - Build slot text: "**Slot 1: ELA**\nContent..."
      - Call _fill_cell(slot_text, pending_hyperlinks=slot_hyperlinks, 
                        current_slot_number=slot_num, append_mode=True)
      - Add separator if not last slot
2. Result: Each slot's hyperlinks inline with its content
```

**Key changes:**
- ✅ Reuse `_fill_cell` (no new helpers)
- ✅ Use existing `current_slot_number` filtering
- ✅ Add `append_mode` flag to skip clearing
- ✅ Keep coordinate placement disabled for multi-slot

---

## Implementation Steps

### Phase 1: Add Append Mode to `_fill_cell` (1-2 hours)

**Current `_fill_cell` signature:**
```python
def _fill_cell(self, table, row_idx: int, col_idx: int, text: str,
               day_name: str = None, section_name: str = None,
               pending_hyperlinks: List[Dict] = None,
               pending_images: List[Dict] = None,
               current_slot_number: int = None,
               current_subject: str = None):
```

**Add `append_mode` parameter:**
```python
def _fill_cell(self, table, row_idx: int, col_idx: int, text: str,
               day_name: str = None, section_name: str = None,
               pending_hyperlinks: List[Dict] = None,
               pending_images: List[Dict] = None,
               current_slot_number: int = None,
               current_subject: str = None,
               append_mode: bool = False):  # NEW
    """
    Fill a cell with formatted text and inject matched media inline.
    
    Args:
        ...existing args...
        append_mode: If True, append to existing content instead of clearing cell
    """
    cell = table.rows[row_idx].cells[col_idx]
    
    # Check if cell already has hyperlinks (from coordinate placement)
    existing_hyperlinks = cell._element.xpath('.//w:hyperlink')
    has_coordinate_hyperlinks = len(existing_hyperlinks) > 0
    
    # Clear existing content ONLY if:
    # 1. No coordinate-placed hyperlinks exist, AND
    # 2. Not in append mode
    if not has_coordinate_hyperlinks and not append_mode:
        cell.text = ""
        # Add formatted text
        if text:
            MarkdownToDocx.add_multiline_text(cell, text)
            # Apply font formatting...
    else:
        # Append mode OR has coordinate hyperlinks - append text without clearing
        if text:
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if line.strip():
                    if i == 0 and not append_mode:
                        # First line, add to new paragraph
                        new_para = cell.add_paragraph()
                        MarkdownToDocx.add_formatted_text(new_para, line)
                    else:
                        # Subsequent lines or append mode
                        MarkdownToDocx.add_paragraph(cell, line)
    
    # Rest of method unchanged (hyperlink injection, etc.)
    ...
```

**Testing for Phase 1:**
```python
def test_append_mode():
    # Create test document
    doc = Document()
    table = doc.add_table(rows=3, cols=2)
    
    # Fill cell normally
    renderer._fill_cell(table, 0, 0, "First content")
    assert len(table.rows[0].cells[0].paragraphs) == 1
    
    # Append to cell
    renderer._fill_cell(table, 0, 0, "Second content", append_mode=True)
    assert len(table.rows[0].cells[0].paragraphs) == 2
    
    # Verify both contents present
    text = '\n'.join(p.text for p in table.rows[0].cells[0].paragraphs)
    assert "First content" in text
    assert "Second content" in text
```

---

### Phase 2: Refactor `_fill_multi_slot_day` (3-4 hours)

**Current method:** Lines 506-680 (175 lines)

**New implementation:**

```python
def _fill_multi_slot_day(self, table, col_idx: int, day_name: str, slots: List[Dict],
                         pending_hyperlinks: List[Dict] = None,
                         pending_images: List[Dict] = None):
    """
    Fill multiple slots' data for one day, with per-slot hyperlink placement.
    
    Strategy:
    - For each row (Unit/Lesson, Objective, etc.):
      - Clear cell once
      - For each slot:
        - Filter hyperlinks for this slot
        - Build slot text with header
        - Call _fill_cell with append_mode=True
        - Add separator between slots
    """
    # Sort slots by slot_number
    sorted_slots = sorted(slots, key=lambda s: s.get("slot_number", 0))
    num_slots = len(sorted_slots)
    
    # Define rows to fill
    rows_config = [
        ('unit_lesson', self.UNIT_LESSON_ROW, self._format_unit_lesson),
        ('objective', self.OBJECTIVE_ROW, self._format_objective),
        ('anticipatory_set', self.ANTICIPATORY_SET_ROW, self._format_anticipatory_set),
        ('instruction', self.INSTRUCTION_ROW, self._format_instruction),
        ('misconceptions', self.MISCONCEPTIONS_ROW, self._format_misconceptions),
        ('assessment', self.ASSESSMENT_ROW, self._format_assessment),
        ('homework', self.HOMEWORK_ROW, self._format_homework),
    ]
    
    # Fill each row
    for field_name, row_idx, format_func in rows_config:
        cell = table.rows[row_idx].cells[col_idx]
        
        # Clear cell once at the start
        cell.text = ""
        
        # Fill each slot
        for i, slot in enumerate(sorted_slots):
            slot_num = slot.get("slot_number", "?")
            subject = slot.get("subject", "Unknown")
            
            # Get slot content
            slot_content = format_func(slot) if slot.get(field_name) else ""
            
            if not slot_content:
                continue
            
            # Abbreviate for multi-slot
            slot_content = self._abbreviate_content(slot_content, num_slots)
            
            # Build slot text with header
            slot_header = f"**Slot {slot_num}: {subject}**"
            slot_text = f"{slot_header}\n{slot_content}"
            
            # Add separator if not last slot
            if i < len(sorted_slots) - 1:
                slot_text += "\n\n---"
            
            # Filter hyperlinks for this slot
            slot_hyperlinks = [
                link for link in (pending_hyperlinks or [])
                if link.get('_source_slot') == slot_num
            ]
            
            # Fill cell with this slot's content
            # Use append_mode=True for all slots after the first
            self._fill_cell(
                table,
                row_idx,
                col_idx,
                slot_text,
                day_name=day_name,
                section_name=field_name,
                pending_hyperlinks=slot_hyperlinks,
                pending_images=pending_images if i == 0 else None,  # Images only on first slot
                current_slot_number=slot_num,
                current_subject=subject,
                append_mode=(i > 0)  # Append for all slots after first
            )
```

**Key points:**
1. ✅ Reuses `_fill_cell` - no new helpers
2. ✅ Uses `current_slot_number` - existing filtering works
3. ✅ Uses `append_mode` - accumulates content
4. ✅ Separator included in text - consistent formatting
5. ✅ Coordinate placement stays disabled - no timing issues

**Testing for Phase 2:**
```python
def test_multislot_rendering():
    # Create test data
    slots = [
        {
            'slot_number': 1,
            'subject': 'ELA',
            'unit_lesson': {'content': 'Unit 2 - Lesson 9'},
        },
        {
            'slot_number': 2,
            'subject': 'Math',
            'unit_lesson': {'content': 'LESSON 9: MEASURE TO FIND AREA'},
        }
    ]
    
    hyperlinks = [
        {
            'text': 'LESSON 9: MEASURE TO FIND AREA',
            'url': 'https://example.com',
            '_source_slot': 2,
            '_source_subject': 'Math'
        }
    ]
    
    # Render
    renderer._fill_multi_slot_day(table, 1, 'Monday', slots, hyperlinks)
    
    # Verify structure
    cell = table.rows[renderer.UNIT_LESSON_ROW].cells[1]
    paragraphs = [p.text for p in cell.paragraphs]
    
    # Should have:
    # 1. "Slot 1: ELA"
    # 2. "Unit 2 - Lesson 9"
    # 3. "---"
    # 4. "Slot 2: Math"
    # 5. "LESSON 9: MEASURE TO FIND AREA" (with hyperlink)
    
    assert "Slot 1: ELA" in paragraphs[0]
    assert "Unit 2 - Lesson 9" in paragraphs[1]
    assert "---" in paragraphs[2]
    assert "Slot 2: Math" in paragraphs[3]
    
    # Verify hyperlink is in Math section (paragraph 4+)
    hyperlinks_in_cell = cell._element.xpath('.//w:hyperlink')
    assert len(hyperlinks_in_cell) == 1
    
    # Find which paragraph has the hyperlink
    for i, para in enumerate(cell.paragraphs):
        if para._element.xpath('.//w:hyperlink'):
            assert i >= 4  # Should be in Slot 2 section
```

---

### Phase 3: Testing & Validation (2-3 hours)

#### 3.1: Unit Tests

**Test 1: Append mode works**
```python
def test_fill_cell_append_mode():
    """Verify append_mode preserves existing content."""
    # See Phase 1 test above
```

**Test 2: Slot filtering works**
```python
def test_slot_hyperlink_filtering():
    """Verify hyperlinks are filtered by _source_slot."""
    # Create hyperlinks for different slots
    # Verify only correct slot's hyperlinks are placed
```

**Test 3: Separator placement**
```python
def test_separator_between_slots():
    """Verify separators appear between slots."""
    # Render multi-slot
    # Check for "---" between slot sections
```

#### 3.2: Integration Tests

**Test 4: Single-slot (regression)**
```python
def test_single_slot_no_regression():
    """Verify single-slot rendering unchanged."""
    # Process Daniela's week
    # Verify hyperlinks still inline
    # Verify formatting correct
```

**Test 5: Multi-slot with hyperlinks**
```python
def test_multislot_with_hyperlinks():
    """Verify multi-slot hyperlinks inline."""
    # Process Wilson's W44
    # Open output DOCX
    # Verify:
    #   - Slot 1 (ELA) has no Math hyperlinks
    #   - Slot 2-4 (Math) have Math hyperlinks inline
    #   - Slot 5 (Science) has Science hyperlinks inline
    #   - Hyperlinks appear AFTER their slot headers
```

**Test 6: Multi-slot without hyperlinks**
```python
def test_multislot_no_hyperlinks():
    """Verify multi-slot works without hyperlinks."""
    # Process week with no hyperlinks
    # Verify no errors
    # Verify content displays correctly
```

#### 3.3: XML Structure Validation

**Test 7: Verify paragraph ordering**
```python
def test_paragraph_ordering():
    """Verify slot headers precede hyperlink text in XML."""
    # Process multi-slot week
    # Parse output DOCX XML
    # For each cell:
    #   - Find "Slot X: Subject" paragraphs
    #   - Find hyperlink paragraphs
    #   - Verify hyperlinks come AFTER their slot header
    
    from docx import Document
    doc = Document(output_file)
    table = doc.tables[1]
    cell = table.rows[2].cells[1]  # Monday, Unit/Lesson
    
    # Get all paragraphs with their indices
    slot_headers = {}
    hyperlink_paras = {}
    
    for i, para in enumerate(cell.paragraphs):
        text = para.text
        
        # Find slot headers
        if "Slot" in text and ":" in text:
            slot_num = extract_slot_number(text)
            slot_headers[slot_num] = i
        
        # Find hyperlinks
        if para._element.xpath('.//w:hyperlink'):
            link = para._element.xpath('.//w:hyperlink')[0]
            link_text = ''.join(link.xpath('.//w:t/text()'))
            hyperlink_paras[link_text] = i
    
    # Verify each hyperlink comes after its slot header
    for link_text, link_para_idx in hyperlink_paras.items():
        # Determine which slot this hyperlink belongs to
        # (based on _source_slot metadata)
        slot_num = get_hyperlink_slot(link_text)
        
        # Verify hyperlink paragraph comes after slot header
        assert link_para_idx > slot_headers[slot_num], \
            f"Hyperlink '{link_text}' appears before Slot {slot_num} header!"
```

---

## Revised Timeline

| Phase | Task | Hours |
|-------|------|-------|
| 1 | Add `append_mode` to `_fill_cell` | 1-2 |
| 2 | Refactor `_fill_multi_slot_day` | 3-4 |
| 3 | Testing & validation | 2-3 |
| **Total** | | **6-9 hours** |

---

## Key Improvements from V1

✅ **Reuses existing code** - No new low-level helpers
✅ **Uses existing filtering** - `current_slot_number` already works
✅ **Simpler append logic** - Just add one flag to `_fill_cell`
✅ **Keeps coordinate placement disabled** - No timing issues
✅ **Better testing** - XML structure validation

---

## Files to Modify

### 1. `tools/docx_renderer.py`

**Changes:**
- Line 682: Add `append_mode: bool = False` parameter to `_fill_cell`
- Line 709: Update clearing logic to check `append_mode`
- Lines 506-680: Replace `_fill_multi_slot_day` implementation

**Estimated lines changed:** ~200 lines

### 2. Create test file: `tests/test_multislot_hyperlinks.py`

**New file with 7 test cases** (see Phase 3)

**Estimated lines:** ~300 lines

---

## Decision Point

**This revised plan:**
- ✅ Aligns with existing architecture
- ✅ Reuses existing utilities
- ✅ Stays within 6-9 hour estimate
- ✅ Includes comprehensive testing

**Ready to proceed?**

1. **Yes, start now** - Begin with Phase 1
2. **Yes, new session** - Fresh start
3. **Review plan first** - Any questions/concerns?

Let me know! 🚀
