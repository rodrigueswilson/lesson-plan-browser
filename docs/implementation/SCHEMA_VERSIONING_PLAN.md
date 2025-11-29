# Hyperlink Schema Versioning Plan

**Phase 0.1: Pre-Implementation Analysis**

---

## 📊 Current Schema (v1.1)

### **Current Hyperlink Structure:**

```python
{
    'text': str,                    # Link display text
    'url': str,                     # Target URL
    'context_snippet': str,         # Surrounding text for fuzzy matching
    'context_type': str,            # 'paragraph' or 'table_cell'
    'section_hint': Optional[str],  # Inferred section (e.g., 'instruction')
    'day_hint': Optional[str]       # Inferred day (e.g., 'monday')
}
```

### **Schema Version Tracking:**
- Currently tracked at **document level**: `_media_schema_version: "1.1"`
- No version field in individual hyperlink objects

---

## 🎯 Proposed Schema (v2.0)

### **New Hyperlink Structure:**

```python
{
    # Schema version (NEW)
    'schema_version': '2.0',
    
    # v1.1 fields (KEEP - backward compatibility)
    'text': str,
    'url': str,
    'context_snippet': str,
    'context_type': str,            # 'paragraph', 'table_cell', or 'non_table'
    'section_hint': Optional[str],
    'day_hint': Optional[str],
    
    # v2.0 fields (NEW - coordinate-based placement)
    'table_idx': Optional[int],     # Index of table in document (None if not in table)
    'row_idx': Optional[int],       # Row index within table (None if not in table)
    'cell_idx': Optional[int],      # Cell index within row (None if not in table)
    'row_label': Optional[str],     # First cell text of row (e.g., "Objective:")
    'col_header': Optional[str]     # Column header text (e.g., "MONDAY")
}
```

---

## 🔍 Breaking Change Analysis

### **Code that Reads Hyperlinks:**

1. **`tools/batch_processor.py`:**
   - Line 344: `hyperlinks = await asyncio.to_thread(parser.extract_hyperlinks)`
   - Line 444: `hyperlink_texts = [h['text'] for h in hyperlinks if h.get('text')]`
   - Line 548: `lesson_json["_hyperlinks"] = hyperlinks`
   - **Impact:** ✅ No breaking changes (only reads 'text' field)

2. **`tools/docx_renderer.py`:**
   - Line 117: `pending_hyperlinks = json_data.get('_hyperlinks', []).copy()`
   - Line 155: `self._restore_hyperlinks(doc, json_data["_hyperlinks"])`
   - Multiple `_fill_cell()` calls with `pending_hyperlinks` parameter
   - **Impact:** ⚠️ Need to check `_restore_hyperlinks()` implementation

3. **Test files:**
   - `test_media_preservation.py`
   - `test_media_e2e.py`
   - `validate_threshold_change_v2.py`
   - **Impact:** ⚠️ May need to update test fixtures

---

## 🔧 Migration Strategy

### **Option 1: Additive Migration (RECOMMENDED)**

**Approach:** Add new fields without removing old ones

**Pros:**
- ✅ Zero breaking changes
- ✅ Backward compatible
- ✅ Can roll back easily
- ✅ Old code continues to work

**Cons:**
- Slightly larger data structure
- Need to maintain both field sets

**Implementation:**
```python
# Parser adds new fields while keeping old ones
hyperlink = {
    # v1.1 fields (keep)
    'text': text,
    'url': url,
    'context_snippet': context,
    'context_type': 'table_cell',
    'section_hint': section,
    'day_hint': day,
    
    # v2.0 fields (add)
    'schema_version': '2.0',
    'table_idx': table_idx,
    'row_idx': row_idx,
    'cell_idx': cell_idx,
    'row_label': row_label,
    'col_header': col_header
}

# Renderer checks for new fields
if link.get('schema_version') == '2.0' and link.get('table_idx') is not None:
    # Use coordinate-based placement
    use_coordinates(link)
else:
    # Fall back to fuzzy matching
    use_fuzzy_matching(link)
```

---

### **Option 2: Versioned Migration**

**Approach:** Create separate v1 and v2 handlers

**Pros:**
- Clean separation
- Easier to test each version

**Cons:**
- More code duplication
- Harder to maintain

**Not recommended for this case**

---

## ✅ Recommended Approach: Additive Migration

### **Phase 1: Parser Enhancement**

```python
# tools/docx_parser.py

HYPERLINK_SCHEMA_VERSION = "2.0"

def extract_hyperlinks(self) -> List[Dict[str, Any]]:
    """Extract hyperlinks with v2.0 schema (coordinate-based)."""
    hyperlinks = []
    
    # Extract from paragraphs (non-table)
    for paragraph in self.doc.paragraphs:
        for hyperlink in paragraph._element.xpath('.//w:hyperlink'):
            # ... extract text, url ...
            
            hyperlinks.append({
                'schema_version': HYPERLINK_SCHEMA_VERSION,
                'text': text,
                'url': url,
                'context_snippet': self._get_context_snippet(paragraph, text),
                'context_type': 'paragraph',
                'section_hint': self._infer_section(paragraph.text),
                'day_hint': None,
                # v2.0: No table coordinates for paragraphs
                'table_idx': None,
                'row_idx': None,
                'cell_idx': None,
                'row_label': None,
                'col_header': None
            })
    
    # Extract from tables (with coordinates)
    for table_idx, table in enumerate(self.doc.tables):
        # Get column headers from first row
        col_headers = [
            cell.text.strip() for cell in table.rows[0].cells
        ] if table.rows else []
        
        for row_idx, row in enumerate(table.rows):
            # Get row label (first cell)
            row_label = row.cells[0].text.strip() if row.cells else ""
            
            for cell_idx, cell in enumerate(row.cells):
                # Get column header for this cell
                col_header = col_headers[cell_idx] if cell_idx < len(col_headers) else ""
                
                for paragraph in cell.paragraphs:
                    for hyperlink in paragraph._element.xpath('.//w:hyperlink'):
                        # ... extract text, url ...
                        
                        hyperlinks.append({
                            'schema_version': HYPERLINK_SCHEMA_VERSION,
                            'text': text,
                            'url': url,
                            'context_snippet': self._get_context_snippet(paragraph, text),
                            'context_type': 'table_cell',
                            'section_hint': self._infer_section(cell.text),
                            'day_hint': self._extract_day_from_header(col_header),
                            # v2.0: Table coordinates
                            'table_idx': table_idx,
                            'row_idx': row_idx,
                            'cell_idx': cell_idx,
                            'row_label': row_label,
                            'col_header': col_header
                        })
    
    return hyperlinks
```

### **Phase 2: Renderer Enhancement**

```python
# tools/docx_renderer.py

def _restore_hyperlinks(self, doc: Document, hyperlinks: List[Dict]):
    """Restore hyperlinks using hybrid placement strategy."""
    
    for link in hyperlinks:
        # Check schema version
        schema_version = link.get('schema_version', '1.0')
        
        if schema_version == '2.0':
            # Use hybrid placement (coordinate + fallback)
            self._place_hyperlink_v2(doc, link)
        else:
            # Use legacy fuzzy matching
            self._place_hyperlink_v1(doc, link)

def _place_hyperlink_v2(self, doc: Document, link: Dict):
    """Place hyperlink using v2.0 schema (coordinate-based)."""
    
    # Check if link has table coordinates
    if link.get('table_idx') is None:
        # Non-table link - use fallback
        self._add_to_fallback(link)
        return
    
    # Try coordinate-based placement
    if self._try_coordinate_placement(doc, link):
        return
    
    # Fall back to fuzzy matching
    if self._try_fuzzy_placement(doc, link):
        return
    
    # Last resort: fallback section
    self._add_to_fallback(link)

def _place_hyperlink_v1(self, doc: Document, link: Dict):
    """Place hyperlink using v1.0 schema (fuzzy matching only)."""
    # Use existing fuzzy matching logic
    # ... (current implementation)
    pass
```

---

## 🧪 Testing Strategy

### **Test Backward Compatibility:**

```python
# test_schema_compatibility.py

def test_v1_hyperlinks_still_work():
    """Verify v1.0 hyperlinks still work with new code."""
    
    # Old format (no schema_version, no coordinates)
    v1_hyperlink = {
        'text': 'Cool Down',
        'url': 'https://example.com',
        'context_snippet': 'Students will complete...',
        'context_type': 'table_cell',
        'section_hint': 'assessment',
        'day_hint': 'monday'
    }
    
    # Should still place correctly using fuzzy matching
    renderer = DOCXRenderer(template_path)
    renderer._place_hyperlink_v1(doc, v1_hyperlink)
    
    # Verify link was placed
    assert link_exists_in_doc(doc, 'Cool Down')

def test_v2_hyperlinks_use_coordinates():
    """Verify v2.0 hyperlinks use coordinate placement."""
    
    # New format (with coordinates)
    v2_hyperlink = {
        'schema_version': '2.0',
        'text': 'Cool Down',
        'url': 'https://example.com',
        'context_snippet': 'Students will complete...',
        'context_type': 'table_cell',
        'section_hint': 'assessment',
        'day_hint': 'monday',
        'table_idx': 1,
        'row_idx': 6,
        'cell_idx': 2,
        'row_label': 'Assessment:',
        'col_header': 'TUESDAY'
    }
    
    # Should use coordinate placement
    renderer = DOCXRenderer(template_path)
    renderer._place_hyperlink_v2(doc, v2_hyperlink)
    
    # Verify link was placed at exact coordinates
    assert link_at_coordinates(doc, table_idx=1, row=6, col=2)
```

---

## 📋 Migration Checklist

### **Parser Changes:**
- [ ] Add `HYPERLINK_SCHEMA_VERSION = "2.0"` constant
- [ ] Add `schema_version` field to all hyperlinks
- [ ] Add coordinate fields (`table_idx`, `row_idx`, `cell_idx`)
- [ ] Add label fields (`row_label`, `col_header`)
- [ ] Set coordinates to `None` for non-table links
- [ ] Add `_extract_day_from_header()` helper method
- [ ] Unit test: Verify v2.0 schema structure
- [ ] Unit test: Verify coordinates are correct

### **Renderer Changes:**
- [ ] Add schema version check in `_restore_hyperlinks()`
- [ ] Implement `_place_hyperlink_v2()` for new schema
- [ ] Keep `_place_hyperlink_v1()` for backward compatibility
- [ ] Add coordinate validation (bounds checking)
- [ ] Add telemetry for schema version usage
- [ ] Unit test: Verify v1.0 links still work
- [ ] Unit test: Verify v2.0 links use coordinates

### **Batch Processor:**
- [ ] No changes needed (just passes through)
- [ ] Verify hyperlinks are stored correctly in JSON
- [ ] Test: Load old JSON with v1.0 hyperlinks
- [ ] Test: Load new JSON with v2.0 hyperlinks

### **Documentation:**
- [ ] Document schema v2.0 structure
- [ ] Document migration path
- [ ] Update API documentation
- [ ] Add examples for both versions

---

## ✅ Success Criteria

1. **Zero breaking changes:** Old v1.0 hyperlinks still work
2. **New features work:** v2.0 hyperlinks use coordinates
3. **Graceful fallback:** Missing coordinates fall back to fuzzy
4. **All tests pass:** Both v1.0 and v2.0 test suites
5. **Performance:** No significant overhead from version checking

---

## 🚀 Rollout Plan

### **Week 1:**
- Implement parser changes (v2.0 schema)
- Test on 3-5 files
- Verify coordinates are captured

### **Week 2:**
- Implement renderer changes (hybrid placement)
- Test backward compatibility
- Validate on all file types

### **Week 3:**
- Full integration testing
- Performance validation
- Documentation update

---

**Status:** Ready for implementation  
**Risk Level:** Low (additive changes only, backward compatible)  
**Rollback Plan:** Remove v2.0 code, keep v1.0 path
