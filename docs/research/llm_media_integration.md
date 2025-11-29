# LLM Service Media Integration - Analysis

**Date**: 2025-10-18  
**Status**: ANALYZED  
**Decision**: DEFER image/hyperlink features

---

## Summary

After analyzing the LLM service pipeline and JSON schema, **images and hyperlinks are NOT supported** in the current architecture. Adding them would require significant changes to multiple components.

**Recommendation**: **DEFER** image and hyperlink preservation to a later session.

---

## Current Data Flow

### 1. DOCX Parser → Text Extraction
```python
# tools/docx_parser.py
class DOCXParser:
    def get_full_text(self) -> str:
        """Get all text content from document."""
        return "\n".join(self.paragraphs)
```

**Current behavior**:
- Extracts only TEXT from paragraphs and tables
- No image extraction
- No hyperlink extraction
- Returns plain string

### 2. Batch Processor → LLM Service
```python
# tools/batch_processor.py
primary_content = content["full_text"]  # Plain text string

success, lesson_json, error = self.llm_service.transform_lesson(
    primary_content=primary_content,  # String only
    grade=slot["grade"],
    subject=slot["subject"],
    week_of=slot["week_of"],
    teacher_name=slot.get("teacher_name"),
    homeroom=slot.get("homeroom")
)
```

**Current behavior**:
- Passes only plain text string to LLM
- No media data passed
- LLM receives text-only prompt

### 3. LLM Service → JSON Schema
```python
# backend/llm_service.py
def transform_lesson(...) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """Transform primary teacher content to bilingual lesson plan"""
    # Returns JSON matching lesson_output_schema.json
```

**Schema structure** (from `schemas/lesson_output_schema.json`):
```json
{
  "metadata": {
    "week_of": "string",
    "grade": "string",
    "subject": "string",
    "homeroom": "string",
    "teacher_name": "string"
  },
  "days": {
    "monday": { "unit_lesson": "...", "objective": {...}, ... },
    ...
  }
}
```

**Schema does NOT include**:
- ❌ No `images` key
- ❌ No `hyperlinks` key
- ❌ No `media` key
- ❌ No attachment fields

---

## Questions Answered

### Q1: Does schema allow `images` and `hyperlinks` keys?
**Answer**: ❌ **NO**

The schema only defines:
- `metadata` (week_of, grade, subject, homeroom, teacher_name)
- `days` (monday-friday with lesson structure)

No provision for media data.

### Q2: Will LLM prompt template handle these keys?
**Answer**: ❌ **NO**

The prompt template (`prompt_v4.md`) and schema example in `llm_service.py` only include lesson content fields. The LLM is instructed to output JSON matching the exact schema structure, which has no media fields.

### Q3: Should media be filtered before LLM or after?
**Answer**: ⚠️ **NOT APPLICABLE**

Media is never extracted or passed to the LLM in the current pipeline. The question is moot until we:
1. Extract media from input DOCX
2. Decide where to store it
3. Decide how to re-insert it into output DOCX

---

## Why Images/Hyperlinks Are Complex

### Issue 1: Extraction
**Current**: `DOCXParser` only extracts text
**Needed**: 
- Extract images (binary data, format, position)
- Extract hyperlinks (URL, display text, position)
- Track location context (which day, which section)

**Complexity**: Medium-High

### Issue 2: Storage During Processing
**Options**:
1. **Pass through LLM JSON** - Add `images`/`hyperlinks` keys to schema
   - ❌ Bloats LLM response with binary data
   - ❌ LLM might corrupt or modify media data
   - ❌ Increases token usage significantly
   
2. **Store separately, merge later** - Keep media in side channel
   - ✅ Clean separation of concerns
   - ⚠️ Requires position mapping logic
   - ⚠️ Risk of misalignment if structure changes

**Complexity**: High

### Issue 3: Re-insertion into Output
**Questions**:
- Where should images be positioned? (specific cell? end of document?)
- Should images be resized to fit cells?
- Should hyperlinks preserve exact formatting?
- What if output structure differs from input?

**Complexity**: High

### Issue 4: Template Compatibility
**Current**: Template-driven rendering with `markdown_to_docx.py`
**Needed**:
- Modify renderer to accept media data
- Determine insertion points in template
- Handle merged cells, variable layouts

**Complexity**: Medium-High

---

## Estimated Effort to Implement

### Image Preservation
**Time**: 4-6 hours
- 1-2 hours: Extend `DOCXParser` to extract images
- 1-2 hours: Design storage/passing mechanism
- 1-2 hours: Modify renderer to insert images
- 1 hour: Handle edge cases (sizing, positioning)

**Risk**: HIGH
- Unclear requirements (positioning, sizing)
- python-docx image API has limitations
- May break existing rendering

### Hyperlink Preservation
**Time**: 3-4 hours
- 1 hour: Extend `DOCXParser` to extract hyperlinks
- 1 hour: Design storage/passing mechanism
- 1-2 hours: Modify renderer to insert hyperlinks
- 1 hour: Preserve formatting

**Risk**: MEDIUM-HIGH
- python-docx hyperlink API is complex
- Formatting preservation tricky
- May conflict with template styles

---

## Decision: DEFER to Later Session

### Rationale

1. **Requirements Unclear**
   - No specification for image positioning
   - No specification for image sizing
   - No specification for hyperlink formatting
   - Need user validation before implementing

2. **High Complexity**
   - Requires changes to 5+ files
   - Requires schema changes
   - Requires renderer changes
   - High risk of breaking existing functionality

3. **YAGNI Principle**
   - No user has requested this feature yet
   - May not be needed in practice
   - Should validate need before investing effort

4. **Low Priority**
   - Other features (timestamps, "No School", table widths) are simpler
   - Get quick wins first
   - Build confidence before tackling complex features

### When to Revisit

**Session 5** (after other features proven):
1. Gather user feedback: Do they need images/hyperlinks?
2. Define requirements: Where, how, what format?
3. Create detailed design document
4. Implement with full test coverage

---

## Alternative: Manual Workaround

**For now**, users can:
1. Process lesson plans normally (text only)
2. Manually copy images from input to output DOCX
3. Manually add hyperlinks to output DOCX

**Effort**: 2-5 minutes per file
**Acceptable**: For v1.0, this is reasonable

---

## Files That Would Need Changes

If we implement image/hyperlink preservation:

### Parser Layer
- [ ] `tools/docx_parser.py` - Add image/hyperlink extraction

### Schema Layer
- [ ] `schemas/lesson_output_schema.json` - Add media fields (or don't)
- [ ] `backend/llm_service.py` - Handle media passthrough (or side channel)

### Renderer Layer
- [ ] `tools/markdown_to_docx.py` - Add image/hyperlink insertion
- [ ] `tools/docx_renderer.py` - Coordinate media placement

### Processor Layer
- [ ] `tools/batch_processor.py` - Pass media through pipeline

### Tests
- [ ] `tests/test_docx_parser.py` - Test extraction
- [ ] `tests/test_renderer.py` - Test insertion
- [ ] `tests/fixtures/lesson_with_image.docx` - Test fixture
- [ ] `tests/fixtures/lesson_with_hyperlinks.docx` - Test fixture

**Total**: 8+ files, 6-10 hours work

---

## Recommended Approach (If Implemented Later)

### Phase 1: Extraction (Session 5a)
1. Extend `DOCXParser.extract_images()` method
2. Extend `DOCXParser.extract_hyperlinks()` method
3. Return media data alongside text

### Phase 2: Storage (Session 5b)
1. Create `MediaData` dataclass
2. Store in side channel (not in LLM JSON)
3. Pass through batch processor

### Phase 3: Insertion (Session 5c)
1. Extend renderer to accept media data
2. Define insertion rules (end of document? specific cells?)
3. Handle sizing and formatting

### Phase 4: Testing (Session 5d)
1. Create test fixtures with images/hyperlinks
2. End-to-end tests
3. Edge case handling

---

## Conclusion

**Status**: ❌ **NOT SUPPORTED** in current architecture  
**Recommendation**: ✅ **DEFER** to Session 5  
**Rationale**: High complexity, unclear requirements, YAGNI  
**Alternative**: Manual workaround acceptable for v1.0

**Ready for Session 1**: Focus on simple wins (timestamps, "No School", table widths)
