# Hyperlinks & Images Cell Location Fix

**Priority**: HIGH - Production Issue  
**Estimated Time**: 1-2 hours  
**Status**: Ready for Implementation

---

## 🐛 Problem Statement

**Hyperlinks Issue:**
- Hyperlinks are extracted from input table cells
- But restored at the END of document in a "Referenced Links" section
- Should be restored IN THE EXACT SAME TABLE CELL where they were found

**Images Issue:**
- Images are extracted from input table cells
- But appear outside tables and too large
- Should be placed in the correct cell with proper sizing (fit cell width)

---

## 🔍 Root Cause

### Current Implementation Flaw

**Extraction** (`tools/docx_parser.py` lines 548-604):
```python
hyperlinks.append({
    'text': text,
    'url': url
})
# ❌ NO LOCATION INFO!
```

**Restoration** (`tools/docx_renderer.py` lines 715-762):
```python
# Adds "Referenced Links" section at END of document
heading = doc.add_paragraph()
heading_run.add_run("Referenced Links")
# ❌ NOT in original cell!
```

### What's Missing

**Need to track:**
- Table index (which table?)
- Row index (which row?)
- Cell index (which cell?)
- Position within cell (before/after which text?)

---

## 🎯 Solution Design

### Phase 1: Enhanced Extraction (docx_parser.py)

**Change hyperlink data structure:**
```python
# OLD (current):
{
    'text': 'Click here',
    'url': 'https://example.com'
}

# NEW (proposed):
{
    'text': 'Click here',
    'url': 'https://example.com',
    'location': {
        'type': 'table',  # or 'paragraph'
        'table_index': 0,  # which table (0-based)
        'row_index': 2,    # which row
        'cell_index': 1,   # which cell
        'paragraph_index': 0  # which paragraph in cell
    }
}
```

**Change image data structure:**
```python
# OLD (current):
{
    'image_id': 'rId5',
    'filename': 'image1.png',
    'content_type': 'image/png',
    'data': b'...'
}

# NEW (proposed):
{
    'image_id': 'rId5',
    'filename': 'image1.png',
    'content_type': 'image/png',
    'data': b'...',
    'location': {
        'type': 'table',
        'table_index': 0,
        'row_index': 1,
        'cell_index': 0,
        'width': 200000  # EMUs (English Metric Units)
    }
}
```

### Phase 2: Smart Restoration (docx_renderer.py)

**For Hyperlinks:**
1. When rendering tables, check if any hyperlinks belong to current cell
2. Insert hyperlink at correct position in cell paragraph
3. Remove the "Referenced Links" section at end

**For Images:**
1. When rendering tables, check if any images belong to current cell
2. Insert image in correct cell
3. Size image to fit cell width (with max-width constraint)
4. Maintain aspect ratio

---

## 📝 Implementation Steps

### Step 1: Update docx_parser.py (30 min)

**File**: `tools/docx_parser.py`

**Modify `extract_hyperlinks()` method:**
```python
def extract_hyperlinks(self) -> List[Dict[str, Any]]:
    hyperlinks = []
    
    # Track table hyperlinks with location
    for table_idx, table in enumerate(self.doc.tables):
        for row_idx, row in enumerate(table.rows):
            for cell_idx, cell in enumerate(row.cells):
                for para_idx, paragraph in enumerate(cell.paragraphs):
                    for hyperlink in paragraph._element.xpath('.//w:hyperlink'):
                        # Extract hyperlink
                        hyperlinks.append({
                            'text': text,
                            'url': url,
                            'location': {
                                'type': 'table',
                                'table_index': table_idx,
                                'row_index': row_idx,
                                'cell_index': cell_idx,
                                'paragraph_index': para_idx
                            }
                        })
    
    return hyperlinks
```

**Modify `extract_images()` method:**
- Similar changes to track table location
- Extract original image width from cell

### Step 2: Update docx_renderer.py (45 min)

**File**: `tools/docx_renderer.py`

**Replace `_restore_hyperlinks()` method:**
```python
def _restore_hyperlinks(self, doc: Document, hyperlinks: List[Dict]):
    """Restore hyperlinks to their original table cell locations."""
    
    # Group hyperlinks by location
    table_links = {}  # {table_idx: {row_idx: {cell_idx: [links]}}}
    
    for link in hyperlinks:
        if link.get('location', {}).get('type') == 'table':
            loc = link['location']
            # Build nested dict structure
            # ...
    
    # Restore to tables
    for table_idx, table in enumerate(doc.tables):
        if table_idx in table_links:
            for row_idx, row in enumerate(table.rows):
                if row_idx in table_links[table_idx]:
                    for cell_idx, cell in enumerate(row.cells):
                        if cell_idx in table_links[table_idx][row_idx]:
                            # Add hyperlinks to this cell
                            for link in table_links[table_idx][row_idx][cell_idx]:
                                self._add_hyperlink_to_cell(cell, link)
```

**Add `_restore_images_to_cells()` method:**
```python
def _restore_images_to_cells(self, doc: Document, images: List[Dict]):
    """Restore images to their original table cell locations with proper sizing."""
    
    for image in images:
        if image.get('location', {}).get('type') == 'table':
            loc = image['location']
            table = doc.tables[loc['table_index']]
            cell = table.rows[loc['row_index']].cells[loc['cell_index']]
            
            # Calculate cell width
            cell_width = cell.width  # in EMUs
            
            # Add image to cell with max width = cell width
            paragraph = cell.paragraphs[0]
            run = paragraph.add_run()
            
            # Add image with sizing
            inline_shape = run.add_picture(
                io.BytesIO(image['data']),
                width=min(cell_width, Inches(2))  # Max 2 inches
            )
```

### Step 3: Update Rendering Flow (15 min)

**In `render_lesson_plan()` method:**
```python
# After filling tables
if "_hyperlinks" in json_data:
    self._restore_hyperlinks(doc, json_data["_hyperlinks"])

if "_images" in json_data:
    self._restore_images_to_cells(doc, json_data["_images"])
```

### Step 4: Testing (30 min)

**Test Cases:**
1. ✅ Hyperlink in Monday/Activity cell → Should appear in same cell
2. ✅ Image in Tuesday/Materials cell → Should appear in same cell, sized correctly
3. ✅ Multiple hyperlinks in same cell → All should appear
4. ✅ Image aspect ratio → Should be maintained
5. ✅ Large image → Should be constrained to cell width

---

## 🧪 Test Plan

### Input Document Requirements
- At least 1 hyperlink in a table cell
- At least 1 image in a table cell
- Note the exact location (table, row, cell)

### Expected Output
- Hyperlink appears in SAME cell as input
- Image appears in SAME cell as input
- Image fits cell width (not oversized)
- No "Referenced Links" section at end

### Verification Steps
1. Process a lesson plan with hyperlinks/images in tables
2. Open output DOCX
3. Verify hyperlinks are in correct cells (not at end)
4. Verify images are in correct cells and properly sized
5. Check that aspect ratio is maintained

---

## 📁 Files to Modify

1. **`tools/docx_parser.py`**
   - `extract_hyperlinks()` method (lines 548-604)
   - `extract_images()` method (lines 505-546)

2. **`tools/docx_renderer.py`**
   - `_restore_hyperlinks()` method (lines 715-762) - REPLACE
   - Add `_restore_images_to_cells()` method - NEW
   - Update `render_lesson_plan()` flow (lines 120-140)

---

## ⚠️ Edge Cases to Handle

1. **Hyperlink in non-table paragraph** - Keep current behavior (add at end)
2. **Image outside table** - Keep current behavior
3. **Table structure changed by LLM** - Match by row/cell index, skip if out of bounds
4. **Multiple images in same cell** - Add all in sequence
5. **Cell too narrow for image** - Scale down to fit

---

## 🎯 Success Criteria

✅ Hyperlinks appear in their original table cells  
✅ Images appear in their original table cells  
✅ Images are properly sized to fit cells  
✅ No "Referenced Links" section at document end  
✅ Aspect ratios are maintained  
✅ All existing tests still pass  

---

## 📊 Estimated Impact

**Before Fix:**
- ❌ Hyperlinks at end of document (confusing)
- ❌ Images outside tables (breaks layout)
- ❌ Images too large (unprofessional)

**After Fix:**
- ✅ Hyperlinks in correct cells (intuitive)
- ✅ Images in correct cells (proper layout)
- ✅ Images properly sized (professional)

---

## 🚀 Next Session Checklist

- [ ] Review this document
- [ ] Prepare test input document with hyperlinks/images in tables
- [ ] Implement Phase 1: Enhanced Extraction
- [ ] Implement Phase 2: Smart Restoration
- [ ] Test with real lesson plan
- [ ] Verify all edge cases
- [ ] Update documentation

---

**Ready to implement!** 🎉
