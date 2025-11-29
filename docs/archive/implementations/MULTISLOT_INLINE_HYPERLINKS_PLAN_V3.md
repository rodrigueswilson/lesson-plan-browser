# Multi-Slot Inline Hyperlinks - Implementation Plan V3 (FINAL)

## Goal

Enable inline hyperlink placement for multi-slot documents by refactoring the rendering to fill each slot separately with its own hyperlinks.

**Key principles:**
- ✅ Reuse existing `_fill_cell` logic
- ✅ Use existing `current_slot_number` filtering
- ✅ Handle both hyperlinks AND images per slot
- ✅ Preserve all existing formatting and placeholder logic

---

## Implementation Steps

### Phase 1: Add Append Mode to `_fill_cell` (1-2 hours)

#### 1.1: Add `append_mode` Parameter

**File:** `tools/docx_renderer.py`
**Line:** 682

**Current signature:**
```python
def _fill_cell(self, table, row_idx: int, col_idx: int, text: str,
               day_name: str = None, section_name: str = None,
               pending_hyperlinks: List[Dict] = None,
               pending_images: List[Dict] = None,
               current_slot_number: int = None,
               current_subject: str = None):
```

**New signature:**
```python
def _fill_cell(self, table, row_idx: int, col_idx: int, text: str,
               day_name: str = None, section_name: str = None,
               pending_hyperlinks: List[Dict] = None,
               pending_images: List[Dict] = None,
               current_slot_number: int = None,
               current_subject: str = None,
               append_mode: bool = False):  # NEW PARAMETER
```

#### 1.2: Update Cell Clearing Logic

**Current code (lines 703-720):**
```python
cell = table.rows[row_idx].cells[col_idx]

# Check if cell already has hyperlinks (from coordinate placement)
existing_hyperlinks = cell._element.xpath('.//w:hyperlink')
has_coordinate_hyperlinks = len(existing_hyperlinks) > 0

# Clear existing content ONLY if no coordinate-placed hyperlinks exist
# This preserves hyperlinks inserted by v2.0 coordinate placement
if not has_coordinate_hyperlinks:
    cell.text = ""
    # Add formatted text
    if text:
        MarkdownToDocx.add_multiline_text(cell, text)
        # Apply font formatting (Times New Roman 8pt) to content cells
        # Skip row 1 (days) and column 0 (section labels)
        if row_idx > 0 and col_idx > 0:
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(8)
```

**New code:**
```python
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
        # Apply font formatting (Times New Roman 8pt) to content cells
        # Skip row 1 (days) and column 0 (section labels)
        if row_idx > 0 and col_idx > 0:
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.name = 'Times New Roman'
                    run.font.size = Pt(8)
                    # CRITICAL: Unit/Lesson row must always be BOLD
                    if row_idx == self.UNIT_LESSON_ROW:
                        run.font.bold = True
else:
    # Cell has coordinate-placed hyperlinks OR append mode - append text without clearing
    # Add text with markdown formatting to preserve existing hyperlinks
    if text:
        # Add formatted text line by line, preserving Markdown
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if line.strip():
                if i == 0:
                    # First line - use MarkdownToDocx for proper formatting
                    new_para = cell.add_paragraph()
                    MarkdownToDocx.add_formatted_text(new_para, line)
                else:
                    # Subsequent lines
                    MarkdownToDocx.add_paragraph(cell, line)
                
                # Apply font formatting
                if row_idx > 0 and col_idx > 0:
                    for para in cell.paragraphs[-1:]:  # Only format newly added paragraph
                        for run in para.runs:
                            run.font.name = 'Times New Roman'
                            run.font.size = Pt(8)
                            if row_idx == self.UNIT_LESSON_ROW:
                                run.font.bold = True
```

**Key changes:**
- ✅ Check `append_mode` in addition to `has_coordinate_hyperlinks`
- ✅ Use `MarkdownToDocx.add_formatted_text` for first line in append mode
- ✅ Apply formatting to newly added paragraphs only

---

### Phase 2: Refactor `_fill_multi_slot_day` (3-4 hours)

#### 2.1: Row Configuration

**Current approach (lines 544-600):** Manually handles each field

**New approach:** Define row configuration table

```python
# Define rows to fill with correct field names and format functions
rows_config = [
    # (field_name, row_idx, format_func, placeholder_text)
    ('unit_lesson', self.UNIT_LESSON_ROW, None, '[No unit/lesson specified]'),
    ('objective', self.OBJECTIVE_ROW, self._format_objective, '[No objective specified]'),
    ('anticipatory_set', self.ANTICIPATORY_SET_ROW, self._format_anticipatory_set, None),
    ('tailored_instruction', self.INSTRUCTION_ROW, self._format_tailored_instruction, None),
    ('misconceptions', self.MISCONCEPTIONS_ROW, self._format_misconceptions, None),
    ('assessment', self.ASSESSMENT_ROW, self._format_assessment, None),
    ('homework', self.HOMEWORK_ROW, self._format_homework, None),
]
```

**Note:** 
- `unit_lesson` is a raw string, no format function
- `tailored_instruction` (not `instruction`) maps to `INSTRUCTION_ROW`
- Placeholders only for `unit_lesson` and `objective` (matching current behavior)

#### 2.2: New Implementation

**Replace lines 506-680 with:**

```python
def _fill_multi_slot_day(self, table, col_idx: int, day_name: str, slots: List[Dict],
                         pending_hyperlinks: List[Dict] = None,
                         pending_images: List[Dict] = None):
    """
    Fill multiple slots' data for one day, with per-slot hyperlink placement.
    
    Strategy:
    - For each row (Unit/Lesson, Objective, etc.):
      - Clear cell once (first _fill_cell call will do this)
      - For each slot:
        - Build slot text with header
        - Call _fill_cell with append_mode=True (after first)
        - Pass shared pending_hyperlinks/pending_images lists
        - Let _fill_cell filter by current_slot_number
        - Matched items removed from shared lists automatically
    """
    # Sort slots by slot_number
    sorted_slots = sorted(slots, key=lambda s: s.get("slot_number", 0))
    num_slots = len(sorted_slots)
    
    # Check if any slot has content (for placeholder logic)
    slots_have_content = []
    for slot in sorted_slots:
        has_content = any([
            slot.get("unit_lesson"),
            slot.get("objective"),
            slot.get("anticipatory_set"),
            slot.get("tailored_instruction"),
            slot.get("misconceptions"),
            slot.get("assessment"),
            slot.get("homework"),
        ])
        slots_have_content.append(has_content)
    
    # Define rows to fill
    rows_config = [
        # (field_name, row_idx, format_func, placeholder_text, max_length)
        ('unit_lesson', self.UNIT_LESSON_ROW, None, '[No unit/lesson specified]', 100),
        ('objective', self.OBJECTIVE_ROW, self._format_objective, '[No objective specified]', None),
        ('anticipatory_set', self.ANTICIPATORY_SET_ROW, self._format_anticipatory_set, None, None),
        ('tailored_instruction', self.INSTRUCTION_ROW, self._format_tailored_instruction, None, None),
        ('misconceptions', self.MISCONCEPTIONS_ROW, self._format_misconceptions, None, None),
        ('assessment', self.ASSESSMENT_ROW, self._format_assessment, None, None),
        ('homework', self.HOMEWORK_ROW, self._format_homework, None, 100),
    ]
    
    # Fill each row
    for field_name, row_idx, format_func, placeholder_text, max_length in rows_config:
        # NOTE: We don't manually clear the cell here. The first _fill_cell call
        # (with append_mode=False) will clear it automatically.
        
        # Fill each slot
        for i, slot in enumerate(sorted_slots):
            slot_num = slot.get("slot_number", "?")
            subject = slot.get("subject", "Unknown")
            teacher = slot.get("teacher_name", "")
            has_content = slots_have_content[i]
            
            # Build slot header
            slot_header = f"**Slot {slot_num}: {subject}**"
            if teacher:
                slot_header += f" ({teacher})"
            
            # Get slot content
            slot_content = slot.get(field_name)
            
            # Build slot text
            if slot_content:
                # Format if format function provided
                if format_func:
                    slot_text = format_func(slot_content)
                else:
                    # Raw string (e.g., unit_lesson)
                    slot_text = slot_content
                
                # Abbreviate for multi-slot
                if slot_text:
                    slot_text = self._abbreviate_content(
                        slot_text, num_slots, max_length=max_length
                    )
                    slot_text = f"{slot_header}\n{slot_text}"
                else:
                    slot_text = None
            elif has_content and placeholder_text:
                # Add placeholder if other fields exist but not this one
                slot_text = f"{slot_header}\n{placeholder_text}"
            else:
                # No content and no placeholder needed
                slot_text = None
            
            # Skip if no content
            if not slot_text:
                continue
            
            # Add separator only if there's another slot with content after this one
            # Look ahead to see if any remaining slots will produce content
            has_next_slot_with_content = False
            for j in range(i + 1, len(sorted_slots)):
                next_slot = sorted_slots[j]
                next_slot_content = next_slot.get(field_name)
                next_has_content = slots_have_content[j]
                
                # Check if next slot will produce text (content or placeholder)
                if next_slot_content:
                    # Has actual content
                    if format_func:
                        next_text = format_func(next_slot_content)
                    else:
                        next_text = next_slot_content
                    if next_text:
                        has_next_slot_with_content = True
                        break
                elif next_has_content and placeholder_text:
                    # Will show placeholder
                    has_next_slot_with_content = True
                    break
            
            # Only add separator if there's content coming after
            if has_next_slot_with_content:
                slot_text += "\n\n---"
            
            # Fill cell with this slot's content
            # IMPORTANT: Pass shared pending_hyperlinks and pending_images lists
            # _fill_cell will filter by current_slot_number and remove matched items
            self._fill_cell(
                table,
                row_idx,
                col_idx,
                slot_text,
                day_name=day_name,
                section_name=field_name,
                pending_hyperlinks=pending_hyperlinks,  # Shared list
                pending_images=pending_images,          # Shared list
                current_slot_number=slot_num,
                current_subject=subject,
                append_mode=(i > 0)  # Append for all slots after first
            )
```

**Key points:**
1. ✅ Uses correct field names (`tailored_instruction`, not `instruction`)
2. ✅ Passes shared `pending_hyperlinks` and `pending_images` lists
3. ✅ Relies on `_fill_cell`'s existing filtering by `current_slot_number`
4. ✅ Matched items removed from shared lists automatically
5. ✅ First `_fill_cell` call (append_mode=False) clears the cell
6. ✅ Preserves placeholder logic for unit_lesson and objective
7. ✅ Includes teacher name in slot header (current behavior)
8. ✅ **Look-ahead separator logic** - Only adds `---` if a later slot will produce content, preventing trailing separators

---

### Phase 3: Testing & Validation (2-3 hours)

#### 3.1: Unit Tests

**Test 1: Append mode preserves Markdown**
```python
def test_fill_cell_append_mode_markdown():
    """Verify append_mode preserves Markdown formatting."""
    doc = Document()
    table = doc.add_table(rows=3, cols=2)
    renderer = DOCXRenderer()
    
    # Fill cell normally with bold text
    renderer._fill_cell(table, 0, 0, "**First content**")
    assert table.rows[0].cells[0].paragraphs[0].runs[0].font.bold == True
    
    # Append to cell with italic text
    renderer._fill_cell(table, 0, 0, "*Second content*", append_mode=True)
    
    # Verify both contents present with formatting
    paragraphs = table.rows[0].cells[0].paragraphs
    assert len(paragraphs) >= 2
    assert "First content" in paragraphs[0].text
    assert "Second content" in paragraphs[-1].text
```

**Test 2: Slot filtering works for hyperlinks**
```python
def test_slot_hyperlink_filtering():
    """Verify hyperlinks are filtered by _source_slot."""
    hyperlinks = [
        {'text': 'ELA Link', 'url': 'http://ela.com', '_source_slot': 1},
        {'text': 'Math Link', 'url': 'http://math.com', '_source_slot': 2},
    ]
    
    # Render with current_slot_number=1
    renderer._fill_cell(
        table, 0, 0, "ELA Link content",
        pending_hyperlinks=hyperlinks,
        current_slot_number=1
    )
    
    # Verify only ELA link was placed (Math link still in list)
    assert len(hyperlinks) == 1
    assert hyperlinks[0]['text'] == 'Math Link'
```

**Test 3: Images filtered by slot**
```python
def test_slot_image_filtering():
    """Verify images are filtered by _source_slot."""
    images = [
        {'data': 'base64_ela', '_source_slot': 1},
        {'data': 'base64_math', '_source_slot': 2},
    ]
    
    # Render with current_slot_number=1
    renderer._fill_cell(
        table, 0, 0, "Content",
        pending_images=images,
        current_slot_number=1
    )
    
    # Verify only ELA image was placed
    assert len(images) == 1
    assert images[0]['_source_slot'] == 2
```

#### 3.2: Integration Tests

**Test 4: Single-slot (regression)**
```python
def test_single_slot_no_regression():
    """Verify single-slot rendering unchanged."""
    # Process Daniela's week
    output_file = process_week("Daniela", "W44", "10/27/2025")
    
    # Verify hyperlinks still inline
    doc = Document(output_file)
    table = doc.tables[1]
    monday_cell = table.rows[2].cells[1]
    
    hyperlinks = monday_cell._element.xpath('.//w:hyperlink')
    assert len(hyperlinks) > 0  # Should have inline hyperlinks
```

**Test 5: Multi-slot with hyperlinks**
```python
def test_multislot_with_hyperlinks():
    """Verify multi-slot hyperlinks inline in correct slots."""
    # Process Wilson's W44
    output_file = process_week("Wilson", "W44", "10/27/2025")
    
    doc = Document(output_file)
    table = doc.tables[1]
    monday_cell = table.rows[2].cells[1]  # Unit/Lesson row
    
    # Get all paragraphs
    paragraphs = [p.text for p in monday_cell.paragraphs]
    
    # Find slot headers
    slot1_idx = next(i for i, p in enumerate(paragraphs) if "Slot 1:" in p)
    slot2_idx = next(i for i, p in enumerate(paragraphs) if "Slot 2:" in p)
    
    # Find hyperlinks
    for para_idx, para in enumerate(monday_cell.paragraphs):
        hyperlinks = para._element.xpath('.//w:hyperlink')
        if hyperlinks:
            link_text = ''.join(hyperlinks[0].xpath('.//w:t/text()'))
            
            # Determine which slot this hyperlink should belong to
            # (Math hyperlinks should be in Slot 2+)
            if "LESSON" in link_text.upper():
                # Math hyperlink - should be after Slot 2 header
                assert para_idx > slot2_idx, \
                    f"Math hyperlink '{link_text}' at para {para_idx} " \
                    f"appears before Slot 2 header at para {slot2_idx}"
```

**Test 6: Paragraph ordering (XML validation)**
```python
def test_paragraph_ordering():
    """Verify slot headers precede hyperlink text in XML."""
    output_file = process_week("Wilson", "W44", "10/27/2025")
    
    doc = Document(output_file)
    table = doc.tables[1]
    monday_cell = table.rows[2].cells[1]
    
    # Build mapping of slot headers to paragraph indices
    slot_headers = {}
    for i, para in enumerate(monday_cell.paragraphs):
        text = para.text
        if "Slot" in text and ":" in text:
            # Extract slot number
            import re
            match = re.search(r'Slot (\d+):', text)
            if match:
                slot_num = int(match.group(1))
                slot_headers[slot_num] = i
    
    # Check each hyperlink
    for para_idx, para in enumerate(monday_cell.paragraphs):
        hyperlinks = para._element.xpath('.//w:hyperlink')
        if hyperlinks:
            # Get hyperlink's source slot from the shared pending_hyperlinks list
            # (we'd need to track this during rendering for proper validation)
            # For now, use heuristic: if contains "LESSON", it's Math (Slot 2+)
            link_text = ''.join(hyperlinks[0].xpath('.//w:t/text()'))
            
            if "LESSON" in link_text.upper():
                # Math hyperlink - should be after Slot 2 header
                assert para_idx > slot_headers.get(2, -1), \
                    f"Hyperlink at para {para_idx} appears before its slot header"
```

#### 3.3: Edge Cases

**Test 7: Empty slots**
```python
def test_empty_slots():
    """Verify slots without content don't break rendering."""
    slots = [
        {'slot_number': 1, 'subject': 'ELA'},  # No content
        {'slot_number': 2, 'subject': 'Math', 'unit_lesson': 'LESSON 9'},
    ]
    
    # Should not raise errors
    renderer._fill_multi_slot_day(table, 1, 'Monday', slots)
```

**Test 8: Mixed content (some slots with hyperlinks, some without)**
```python
def test_mixed_hyperlinks():
    """Verify slots with and without hyperlinks both work."""
    slots = [
        {'slot_number': 1, 'subject': 'ELA', 'unit_lesson': 'Unit 2'},
        {'slot_number': 2, 'subject': 'Math', 'unit_lesson': 'LESSON 9'},
    ]
    
    hyperlinks = [
        {'text': 'LESSON 9', 'url': 'http://math.com', '_source_slot': 2}
    ]
    
    renderer._fill_multi_slot_day(table, 1, 'Monday', slots, hyperlinks)
    
    # Verify Slot 1 has no hyperlinks, Slot 2 has hyperlink
    # (detailed assertions here)
```

**Test 9: No trailing separators**
```python
def test_no_trailing_separators():
    """Verify no trailing --- when last slots have no content for a row."""
    slots = [
        {
            'slot_number': 1, 
            'subject': 'ELA', 
            'unit_lesson': 'Unit 2',
            'objective': {'content': 'ELA objective'}
        },
        {
            'slot_number': 2, 
            'subject': 'Math', 
            'unit_lesson': 'LESSON 9',
            # No objective
        },
        {
            'slot_number': 3, 
            'subject': 'Science',
            # No unit_lesson, no objective
        },
    ]
    
    renderer._fill_multi_slot_day(table, 1, 'Monday', slots)
    
    # Check Unit/Lesson row
    unit_cell = table.rows[renderer.UNIT_LESSON_ROW].cells[1]
    unit_text = '\n'.join(p.text for p in unit_cell.paragraphs)
    
    # Should have separator between Slot 1 and Slot 2
    assert '---' in unit_text
    
    # Should NOT end with separator (Slot 3 has no content)
    assert not unit_text.strip().endswith('---')
    
    # Check Objective row
    obj_cell = table.rows[renderer.OBJECTIVE_ROW].cells[1]
    obj_text = '\n'.join(p.text for p in obj_cell.paragraphs)
    
    # Should NOT have separator (only Slot 1 has objective)
    # OR should not end with separator if placeholder is added
    if '---' in obj_text:
        assert not obj_text.strip().endswith('---')
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

## Key Corrections from V2

✅ **Correct field names** - `tailored_instruction`, not `instruction`
✅ **Shared hyperlink/image lists** - Pass to `_fill_cell`, let it filter and remove
✅ **Images handled per slot** - Same filtering as hyperlinks
✅ **Markdown in append mode** - Use `MarkdownToDocx.add_formatted_text` for first line
✅ **Relative ordering tests** - No hard-coded paragraph indices
✅ **Placeholder logic preserved** - Only for unit_lesson and objective

---

## Files to Modify

### 1. `tools/docx_renderer.py`

**Changes:**
- Line 682: Add `append_mode: bool = False` parameter
- Lines 703-720: Update clearing logic to check `append_mode`
- Lines 724-739: Update append branch to use `MarkdownToDocx.add_formatted_text`
- Lines 506-680: Replace `_fill_multi_slot_day` implementation (~175 lines)

**Estimated lines changed:** ~200 lines

### 2. Create test file: `tests/test_multislot_hyperlinks.py`

**New file with 9 test cases**

**Estimated lines:** ~450 lines

---

## Ready to Implement

This plan is now fully aligned with the existing architecture:
- ✅ Correct field names and format functions
- ✅ Shared hyperlink/image lists with automatic filtering
- ✅ Markdown formatting preserved in append mode
- ✅ Relative ordering tests (no brittle assertions)
- ✅ Look-ahead separator logic (no trailing separators)
- ✅ All edge cases covered

**Decision time:**

1. **Start now** - Begin with Phase 1
2. **New session** - Fresh start
3. **Questions** - Any concerns?

Let me know! 🚀
