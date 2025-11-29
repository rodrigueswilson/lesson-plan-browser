# Critical Bugs Fixed - COMPLETE

## Status: ✅ BOTH ISSUES RESOLVED

Two critical bugs identified in code review have been fixed and validated.

---

## Bug 1: Images Missing table_idx ✅ FIXED

### Problem
`_find_image_context()` added `table_idx` to context dict, but `extract_images()` never propagated it to the `image_data` dictionaries. This caused `extract_images_for_slot()` to filter on `img.get('table_idx')` which was always `None`, resulting in zero images for all slots.

### Root Cause
```python
# In extract_images() - line 732-742
image_data = {
    'data': ...,
    'content_type': ...,
    'filename': ...,
    'rel_id': ...,
    'context_snippet': context_info.get('context', ''),
    'context_type': context_info.get('type', 'unknown'),
    'section_hint': context_info.get('section'),
    'day_hint': context_info.get('day'),
    'row_label': context_info.get('row_label'),
    'cell_index': context_info.get('cell_index')
    # MISSING: 'table_idx': context_info.get('table_idx')
}
```

### Fix
```python
image_data = {
    'data': base64.b64encode(rel.target_part.blob).decode('utf-8'),
    'content_type': rel.target_part.content_type,
    'filename': rel.target_ref.split('/')[-1],
    'rel_id': rel_id,
    'context_snippet': context_info.get('context', ''),
    'context_type': context_info.get('type', 'unknown'),
    'section_hint': context_info.get('section'),
    'day_hint': context_info.get('day'),
    'row_label': context_info.get('row_label'),
    'cell_index': context_info.get('cell_index'),
    'table_idx': context_info.get('table_idx')  # ✅ ADDED
}
```

### Impact
- **Before:** All slots returned 0 images (filtering failed)
- **After:** Images correctly filtered by table index

---

## Bug 2: Image Tests Not Exercising Code ✅ FIXED

### Problem
`TestExtractImagesForSlot` created tables but didn't embed actual images. Both `slot1_images` and `slot2_images` were empty, so assertions never executed and wouldn't catch bugs.

### Root Cause
```python
# Old test - no real images
daily_table = doc.add_table(rows=3, cols=6)
daily_table.rows[0].cells[1].text = "Monday"
# No images added!
```

### Fix
Added helper functions and real image embedding:

```python
def create_1x1_png():
    """Create a minimal 1x1 pixel PNG image using PIL."""
    from PIL import Image as PILImage
    img = PILImage.new('RGB', (1, 1), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def add_image_to_cell(cell, image_stream, width_inches=1.0):
    """Add a real image to a table cell."""
    run = cell.paragraphs[0].add_run()
    run.add_picture(image_stream, width=Inches(width_inches))
    return run

# Updated test - real images with unique colors
for slot_num in range(1, 3):
    # ... create tables ...
    
    # Add UNIQUE image (different color per slot)
    color = 'red' if slot_num == 1 else 'blue'
    img = PILImage.new('RGB', (2, 2), color=color)
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    add_image_to_cell(daily_table.rows[1].cells[1], img_bytes, width_inches=0.5)
```

**Key Insight:** python-docx reuses image relationships for identical images, so we create unique images (different colors) for each slot.

### Impact
- **Before:** Empty lists, assertions never executed
- **After:** Real images extracted, assertions validate filtering

---

## Validation Results

### Test Suite: ✅ 10/10 PASSING
```bash
$ python -m pytest tests/test_slot_extraction.py -v
================================ test session starts ================================
collected 10 items

tests/test_slot_extraction.py::TestValidateSlotStructure::test_validate_slot_structure_valid_4_slots PASSED [ 10%]
tests/test_slot_extraction.py::TestValidateSlotStructure::test_validate_slot_structure_valid_5_slots PASSED [ 20%]
tests/test_slot_extraction.py::TestValidateSlotStructure::test_validate_slot_structure_missing_signature PASSED [ 30%]
tests/test_slot_extraction.py::TestValidateSlotStructure::test_validate_slot_structure_invalid_table_count PASSED [ 40%]
tests/test_slot_extraction.py::TestValidateSlotStructure::test_validate_slot_structure_slot_exceeds PASSED [ 50%]
tests/test_slot_extraction.py::TestValidateSlotStructure::test_validate_slot_structure_no_tables PASSED [ 60%]
tests/test_slot_extraction.py::TestExtractHyperlinksForSlot::test_extract_hyperlinks_for_slot_filters_by_table PASSED [ 70%]
tests/test_slot_extraction.py::TestExtractHyperlinksForSlot::test_extract_hyperlinks_for_slot_no_paragraphs PASSED [ 80%]
tests/test_slot_extraction.py::TestExtractImagesForSlot::test_extract_images_for_slot_filters_by_table PASSED [ 90%]
tests/test_slot_extraction.py::TestIntegrationNoCrossContamination::test_no_cross_contamination_between_slots PASSED [100%]

=========================== 10 passed in 0.61s
```

### Real File Validation: ✅ ALL PASSING
```
Lang Lesson Plans (4 slots):
  ✅ Slot 1: 12 hyperlinks, 0 images (table 1)
  ✅ Slot 2: 25 hyperlinks, 0 images (table 3)
  ✅ Slot 3: 1 hyperlink, 0 images (table 5)
  ✅ Slot 4: 8 hyperlinks, 0 images (table 7)

Savoca Lesson Plans (4 slots):
  ✅ Slot 1: 5 hyperlinks, 0 images (table 1)
  ✅ Slot 2: 9 hyperlinks, 0 images (table 3)
  ✅ Slot 3: 5 hyperlinks, 0 images (table 5)
  ✅ Slot 4: 0 hyperlinks, 0 images (table 7)

Piret Lesson Plans (1 slot):
  ✅ Slot 1: 1 hyperlink, 0 images (table 1)
```

**Note:** Real files have 0 images (correct - they don't contain images). The important validation is that extraction doesn't crash and filtering works correctly.

---

## Test Coverage Improvements

### Image Test Now Validates:
- ✅ Real images are extracted
- ✅ `table_idx` is populated
- ✅ Images filtered by table index
- ✅ Slot 1 images ≠ Slot 2 images
- ✅ Image data is present (base64)
- ✅ Content type is correct (PNG)
- ✅ No overlap between slots

### Before vs After:
```python
# Before
slot1_images = []  # Empty, assertions never run
slot2_images = []  # Empty, assertions never run

# After
slot1_images = [{'table_idx': 1, 'data': '...', ...}]  # Real data
slot2_images = [{'table_idx': 3, 'data': '...', ...}]  # Real data
# All assertions execute and validate
```

---

## Files Modified

1. **tools/docx_parser.py** (+1 line)
   - Added `'table_idx': context_info.get('table_idx')` to image_data

2. **tests/test_slot_extraction.py** (+40 lines)
   - Added `create_1x1_png()` helper
   - Added `add_image_to_cell()` helper
   - Updated image test to use real PIL-generated images
   - Added comprehensive assertions

---

## Summary

### Issue 1: table_idx Missing
- **Severity:** Critical (images not filtered)
- **Fix:** 1-line addition
- **Status:** ✅ Fixed and tested

### Issue 2: Tests Not Exercising Code
- **Severity:** High (false confidence)
- **Fix:** Real image generation with PIL
- **Status:** ✅ Fixed and tested

### Overall Status
- ✅ Both bugs fixed
- ✅ 10/10 tests passing
- ✅ Real file validation passing
- ✅ Image filtering working correctly
- ✅ No cross-contamination

---

## Next Steps

As requested:
1. ✅ Updated `extract_images()` - table_idx added
2. ✅ Re-ran W44 validation - all passing
3. ✅ Tests embed real images - assertions execute
4. ✅ Re-ran test suite - 10/10 passing

**Ready for full W44 flow with OpenAI disabled to verify counts before LLM processing.**

---

**Status:** Production-ready! Both critical bugs fixed and thoroughly tested. 🚀
