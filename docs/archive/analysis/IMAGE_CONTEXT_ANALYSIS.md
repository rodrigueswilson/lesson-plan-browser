# Image Context Extraction Analysis

## Issue Identified

The `_find_image_context()` method in `docx_parser.py` is **not finding images** in the document structure, resulting in empty context snippets.

## Root Cause

The XPath search pattern used in `_find_image_context()` is not matching the image elements:

```python
run._element.xpath(f'.//a:blip[@r:embed="{rel_id}"]',
                  namespaces={'a': '...', 'r': '...'})
```

However, when we search using simple string matching (`rel_id in str(run._element.xml)`), we **DO find the images**.

## Images Found in Real Files

### Image 1: `image3.png` (96 bytes)
- **Location**: Table 8, Row 1, Cell 0
- **Cell text**: "I certify that these lessons are aligned with the New Jersey Student Learning Standards (NJSLS) and"
- **Type**: Signature/certification image
- **Current context**: Empty ❌
- **Should have context**: "I certify that these lessons are aligned..." ✅

### Image 2: `image2.jpg` (259KB)
- **Locations**: Tables 1, 3, 5, 7 - Row 3, Cell 3
- **Cell text**: (empty)
- **Type**: Repeated decorative/logo image in empty cells
- **Current context**: Empty ❌
- **Expected behavior**: Empty (no surrounding text) ✅

## Impact Assessment

### For Image 1 (Signature)
- **Problem**: Missing context despite having text
- **Impact**: Will fall back to "Attached Images" section
- **Fix needed**: Yes - XPath pattern needs correction

### For Image 2 (Logo/Decorative)
- **Problem**: No surrounding text (empty cells)
- **Impact**: Will fall back to "Attached Images" section
- **Fix needed**: No - this is expected behavior

## Recommended Fix

Update the `_find_image_context()` method in `tools/docx_parser.py` to use a more robust search:

```python
def _find_image_context(self, rel_id: str) -> Dict[str, Any]:
    """Find context for an image by locating it in document structure."""
    
    # Search paragraphs
    for paragraph in self.doc.paragraphs:
        for run in paragraph.runs:
            try:
                # Use string matching instead of XPath
                if rel_id in str(run._element.xml):
                    return {
                        'context': paragraph.text[:100],
                        'type': 'paragraph',
                        'section': self._infer_section(paragraph.text),
                        'day': None
                    }
            except:
                pass
    
    # Search tables
    for table in self.doc.tables:
        day_hint = self._detect_day_from_table(table)
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        try:
                            if rel_id in str(run._element.xml):
                                return {
                                    'context': cell.text[:100],
                                    'type': 'table_cell',
                                    'section': self._infer_section(cell.text),
                                    'day': day_hint
                                }
                        except:
                            pass
    
    return {'context': '', 'type': 'unknown', 'section': None, 'day': None}
```

## Expected Behavior After Fix

### Image 1 (Signature)
- **Context**: "I certify that these lessons are aligned with the New Jersey Student Learning Standards (NJSLS) and"
- **Section**: None (signatures section)
- **Day**: None
- **Matching**: Low confidence (generic text)
- **Result**: Will likely fall back to "Attached Images" section ✅

### Image 2 (Logo)
- **Context**: Empty (no text in cells)
- **Section**: None
- **Day**: Varies (monday, tuesday, etc.)
- **Matching**: Very low confidence
- **Result**: Will fall back to "Attached Images" section ✅

## Production Impact

### Current Behavior (Without Fix)
- **All images** → "Attached Images" section at document end
- **User experience**: Acceptable (images preserved, just not inline)

### After Fix
- **Images with context** → May match inline (low probability for these specific images)
- **Images without context** → "Attached Images" section
- **User experience**: Slightly better (some images may be inline)

## Recommendation

### Priority: **MEDIUM**

**Reasons**:
1. Images are still preserved (no data loss)
2. Most images in lesson plans are decorative (logos, signatures)
3. Hyperlinks are more important for inline placement (169 vs 4)
4. Fix is straightforward but not critical

### Action Items

1. **Short term**: Document current behavior
   - Images will appear in "Attached Images" section
   - This is acceptable for production

2. **Medium term**: Implement XPath fix
   - Update `_find_image_context()` method
   - Use string matching instead of XPath
   - Test with real files

3. **Long term**: Consider image classification
   - Detect signature images (keep at end)
   - Detect decorative images (keep at end)
   - Only place content images inline

## Conclusion

✅ **Images are being extracted correctly** (4 images found)  
⚠️ **Context extraction has XPath issue** (0 contexts extracted)  
✅ **Fallback mechanism works** (images will be preserved at document end)  
📊 **Impact is low** (most images are signatures/logos anyway)  

**Status**: Production-ready with known limitation  
**User impact**: Minimal (images preserved, just not inline)  
**Fix complexity**: Low (string matching instead of XPath)  
**Fix priority**: Medium (not blocking deployment)
