# Multi-Slot Inline Hyperlinks - Implementation Plan

## Goal

Enable inline hyperlink placement for multi-slot documents by refactoring the rendering to fill each slot separately with its own hyperlinks.

---

## Current Architecture Problem

**Current flow:**
```python
# _fill_multi_slot_day()
1. Collect all slots' content into arrays
2. Combine into single strings: "Slot 1: ELA\n...\n---\nSlot 2: Math\n..."
3. Fill cell once with combined text
4. Pass all_hyperlinks (or None)
5. Result: Can't isolate hyperlinks per slot
```

**Why it fails:**
- Coordinate placement inserts hyperlink text BEFORE slot headers
- Semantic matching can't distinguish which slot a text snippet belongs to
- No way to prevent cross-contamination

---

## New Architecture

**New flow:**
```python
# _fill_multi_slot_day()
1. Clear cell
2. For each slot:
   a. Filter hyperlinks for this slot only
   b. Add slot header
   c. Add slot content with inline hyperlinks
   d. Add separator (if not last slot)
3. Result: Each slot's hyperlinks stay with its content
```

---

## Implementation Steps

### Phase 1: Create Helper Methods (2-3 hours)

#### 1.1: `_clear_cell_content()`

**Purpose:** Clear cell content while preserving structure.

```python
def _clear_cell_content(self, table, row_idx: int, col_idx: int):
    """Clear all content from a cell."""
    cell = table.rows[row_idx].cells[col_idx]
    # Remove all paragraphs except the first (required)
    for para in cell.paragraphs[1:]:
        p = para._element
        p.getparent().remove(p)
    # Clear first paragraph
    cell.paragraphs[0].clear()
```

#### 1.2: `_append_text_to_cell()`

**Purpose:** Append formatted text to cell without clearing.

```python
def _append_text_to_cell(self, cell, text: str, apply_formatting: bool = True):
    """
    Append text to cell, preserving existing content.
    
    Args:
        cell: Cell object
        text: Text to append (may contain markdown)
        apply_formatting: Whether to apply Times New Roman 8pt
    """
    if not text:
        return
    
    # Add text as new paragraphs
    lines = text.split('\n')
    for line in lines:
        if line.strip():
            para = cell.add_paragraph()
            MarkdownToDocx.add_formatted_text(para, line)
            
            if apply_formatting:
                for run in para.runs:
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(8)
```

#### 1.3: `_append_separator_to_cell()`

**Purpose:** Add horizontal rule separator between slots.

```python
def _append_separator_to_cell(self, cell):
    """Add a horizontal rule separator to cell."""
    para = cell.add_paragraph()
    para.add_run("---")
    for run in para.runs:
        run.font.name = 'Times New Roman'
        run.font.size = Pt(8)
```

#### 1.4: `_append_slot_content_to_cell()`

**Purpose:** Append one slot's content with its hyperlinks.

```python
def _append_slot_content_to_cell(
    self, 
    cell, 
    slot_text: str, 
    slot_hyperlinks: List[Dict],
    row_idx: int,
    is_unit_lesson_row: bool = False
):
    """
    Append a slot's content to a cell with inline hyperlinks.
    
    Args:
        cell: Cell object
        slot_text: Text content for this slot
        slot_hyperlinks: Hyperlinks belonging to this slot
        row_idx: Row index (for formatting)
        is_unit_lesson_row: Whether this is the Unit/Lesson row (needs bold)
    
    Strategy:
    1. Split text into lines
    2. For each line, try to match hyperlinks
    3. If match found, insert hyperlink inline
    4. If no match, insert plain text
    """
    if not slot_text:
        return
    
    lines = slot_text.split('\n')
    
    for line in lines:
        if not line.strip():
            continue
        
        # Try to find hyperlinks that match this line
        matched_hyperlink = None
        for hyperlink in slot_hyperlinks[:]:
            link_text = hyperlink.get('text', '')
            # Simple substring match (can be improved with fuzzy matching)
            if link_text.lower() in line.lower():
                matched_hyperlink = hyperlink
                slot_hyperlinks.remove(hyperlink)
                break
        
        # Add paragraph
        para = cell.add_paragraph()
        
        if matched_hyperlink:
            # Add text with hyperlink
            self._add_hyperlink_to_paragraph(
                para, 
                line, 
                matched_hyperlink['url'],
                matched_hyperlink['text']
            )
        else:
            # Add plain text
            MarkdownToDocx.add_formatted_text(para, line)
        
        # Apply formatting
        for run in para.runs:
            run.font.name = 'Times New Roman'
            run.font.size = Pt(8)
            if is_unit_lesson_row:
                run.font.bold = True
```

---

### Phase 2: Refactor `_fill_multi_slot_day()` (2-3 hours)

**Current method:** Lines 506-680 (175 lines)

**New structure:**

```python
def _fill_multi_slot_day(self, table, col_idx: int, day_name: str, slots: List[Dict],
                         pending_hyperlinks: List[Dict] = None,
                         pending_images: List[Dict] = None):
    """
    Fill multiple slots' data for one day, with per-slot hyperlink placement.
    
    NEW APPROACH:
    - Clear each cell
    - For each slot:
      - Filter hyperlinks for this slot
      - Append slot header
      - Append slot content with inline hyperlinks
      - Append separator (if not last)
    """
    # Sort slots by slot_number
    sorted_slots = sorted(slots, key=lambda s: s.get("slot_number", 0))
    num_slots = len(sorted_slots)
    
    # Collect content per slot (keep existing logic)
    slots_data = []
    for slot in sorted_slots:
        slot_num = slot.get("slot_number", "?")
        subject = slot.get("subject", "Unknown")
        
        # Filter hyperlinks for THIS slot
        slot_hyperlinks = [
            link for link in (pending_hyperlinks or [])
            if link.get('_source_slot') == slot_num
        ]
        
        # Collect this slot's content
        slot_data = {
            'slot_number': slot_num,
            'subject': subject,
            'hyperlinks': slot_hyperlinks,
            'unit_lesson': self._format_unit_lesson(slot) if slot.get("unit_lesson") else "",
            'objective': self._format_objective(slot) if slot.get("objective") else "",
            'anticipatory_set': self._format_anticipatory_set(slot) if slot.get("anticipatory_set") else "",
            'instruction': self._format_instruction(slot) if slot.get("instruction") else "",
            'misconceptions': self._format_misconceptions(slot) if slot.get("misconceptions") else "",
            'assessment': self._format_assessment(slot) if slot.get("assessment") else "",
            'homework': self._format_homework(slot) if slot.get("homework") else "",
        }
        
        # Abbreviate for multi-slot
        for key in ['unit_lesson', 'objective', 'anticipatory_set', 'instruction', 
                    'misconceptions', 'assessment', 'homework']:
            if slot_data[key]:
                slot_data[key] = self._abbreviate_content(slot_data[key], num_slots)
        
        slots_data.append(slot_data)
    
    # Fill each row
    rows_to_fill = [
        (self.UNIT_LESSON_ROW, 'unit_lesson', True),   # (row_idx, field, is_bold)
        (self.OBJECTIVE_ROW, 'objective', False),
        (self.ANTICIPATORY_SET_ROW, 'anticipatory_set', False),
        (self.INSTRUCTION_ROW, 'instruction', False),
        (self.MISCONCEPTIONS_ROW, 'misconceptions', False),
        (self.ASSESSMENT_ROW, 'assessment', False),
        (self.HOMEWORK_ROW, 'homework', False),
    ]
    
    for row_idx, field_name, is_bold in rows_to_fill:
        cell = table.rows[row_idx].cells[col_idx]
        
        # Clear cell
        self._clear_cell_content(table, row_idx, col_idx)
        
        # Fill each slot
        for i, slot_data in enumerate(slots_data):
            # Add slot header
            slot_header = f"**Slot {slot_data['slot_number']}: {slot_data['subject']}**"
            self._append_text_to_cell(cell, slot_header, apply_formatting=True)
            
            # Add slot content with hyperlinks
            if slot_data[field_name]:
                self._append_slot_content_to_cell(
                    cell,
                    slot_data[field_name],
                    slot_data['hyperlinks'],
                    row_idx,
                    is_unit_lesson_row=(row_idx == self.UNIT_LESSON_ROW)
                )
            
            # Add separator if not last slot
            if i < len(slots_data) - 1:
                self._append_separator_to_cell(cell)
        
        # Mark hyperlinks as placed
        for slot_data in slots_data:
            for hyperlink in slot_data['hyperlinks']:
                if hyperlink in pending_hyperlinks:
                    pending_hyperlinks.remove(hyperlink)
```

---

### Phase 3: Testing (2-3 hours)

#### Test Cases

1. **Single-slot document (Daniela)**
   - ✅ Hyperlinks inline (no regression)
   - ✅ Formatting correct

2. **Multi-slot document (Wilson) - with hyperlinks**
   - ✅ Slot 1 (ELA) has no Math hyperlinks
   - ✅ Slot 2-4 (Math) have Math hyperlinks inline
   - ✅ Slot 5 (Science) has Science hyperlinks inline
   - ✅ Hyperlinks appear in correct slot sections

3. **Multi-slot document - without hyperlinks**
   - ✅ No errors
   - ✅ Content displays correctly

4. **Multi-slot document - mixed (some slots with, some without)**
   - ✅ Slots with hyperlinks show them inline
   - ✅ Slots without hyperlinks show plain text

#### Validation

```python
# Create test script
def test_multislot_hyperlinks():
    # Process Wilson's W44
    output_file = process_week("Wilson", "W44", "10/27/2025")
    
    # Open output DOCX
    doc = Document(output_file)
    table = doc.tables[1]  # Daily plans table
    
    # Check Monday, Unit/Lesson row
    monday_cell = table.rows[2].cells[1]
    
    # Verify structure
    paragraphs = monday_cell.paragraphs
    
    # Should have:
    # 1. "**Slot 1: ELA**"
    # 2. ELA content (no hyperlinks)
    # 3. "---"
    # 4. "**Slot 2: Math**"
    # 5. Math content (WITH hyperlinks)
    
    # Check for hyperlinks
    hyperlinks = monday_cell._element.xpath('.//w:hyperlink')
    
    # Verify hyperlinks are in Math section, not ELA section
    for hyperlink in hyperlinks:
        # Get hyperlink text
        link_text = ''.join(hyperlink.xpath('.//w:t/text()'))
        
        # Find which paragraph contains this hyperlink
        para_idx = find_paragraph_with_hyperlink(monday_cell, hyperlink)
        
        # Verify it's after "Slot 2: Math" header
        assert para_idx > get_slot2_header_index(monday_cell)
```

---

## Estimated Timeline

| Phase | Task | Hours |
|-------|------|-------|
| 1.1 | Create helper methods | 2-3 |
| 1.2 | Refactor `_fill_multi_slot_day()` | 2-3 |
| 1.3 | Testing & validation | 2-3 |
| **Total** | | **6-9 hours** |

---

## Risks & Mitigation

### Risk 1: Hyperlink Matching Complexity

**Problem:** Matching hyperlinks to text lines might be complex.

**Mitigation:**
- Start with simple substring matching
- Can enhance with fuzzy matching later
- Use existing `_calculate_match_confidence()` logic

### Risk 2: Formatting Issues

**Problem:** Appending content might break formatting.

**Mitigation:**
- Test thoroughly with different content types
- Preserve existing formatting logic
- Add unit tests for edge cases

### Risk 3: Performance

**Problem:** Per-slot rendering might be slower.

**Mitigation:**
- Profile before/after
- Optimize if needed
- Likely negligible impact (< 1 second)

---

## Decision Point

**Do you want to proceed with this implementation?**

**Options:**
1. **Yes, implement now** - We can start in this session
2. **Yes, but in a new session** - Fresh start, clear plan
3. **No, keep current solution** - Multi-slot hyperlinks at end of document

**If yes, we'll start with Phase 1.1** - creating the helper methods.

Let me know!
