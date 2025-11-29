# Phase 5: DOCX Renderer Implementation

**Status:** ✅ COMPLETE  
**Date:** 2025-10-04  
**Duration:** ~2 hours

---

## Overview

Phase 5 implements the DOCX renderer that converts validated JSON lesson plans into formatted DOCX files using the district template. This is a critical component that bridges the JSON pipeline with the final deliverable format.

## Goals

- ✅ Load and parse district DOCX template
- ✅ Convert JSON to DOCX while preserving formatting
- ✅ Handle markdown formatting in content
- ✅ Support all lesson plan fields
- ✅ Maintain template structure and styling
- ✅ Comprehensive test coverage

## Implementation

### 1. Markdown to DOCX Converter (`tools/markdown_to_docx.py`)

**Purpose:** Convert markdown formatting to DOCX runs with proper styling.

**Features:**
- Bold text: `**text**` or `__text__`
- Italic text: `*text*` or `_text_`
- Bullet lists: `- item` or `* item`
- Numbered lists: `1. item`
- Multi-line text handling
- Nested formatting (bold + italic)

**Key Functions:**
```python
MarkdownToDocx.add_formatted_text(paragraph, text)
MarkdownToDocx.add_multiline_text(cell, text)
MarkdownToDocx.clean_markdown(text)
```

**Design Decisions:**
- Uses regex patterns for markdown detection
- Handles template compatibility (no List Bullet style requirement)
- Preserves whitespace and line breaks
- Supports nested formatting

### 2. DOCX Renderer (`tools/docx_renderer.py`)

**Purpose:** Main renderer that converts JSON to DOCX using district template.

**Template Structure:**
```
Table 0: Metadata (1 row x 5 cols)
  | Name: | Grade: | Homeroom: | Subject: | Week of: |

Table 1: Daily Plans (8 rows x 6 cols)
  |           | Monday | Tuesday | Wednesday | Thursday | Friday |
  | Unit/Lesson
  | Objective
  | Anticipatory Set
  | Instruction
  | Misconceptions
  | Assessment
  | Homework

Table 2: Signatures (4 rows x 1 col)
```

**Key Features:**
- Template cloning preserves all formatting
- Cell-by-cell population
- Markdown formatting support
- Handles missing optional fields
- Comprehensive error handling

**Formatting Functions:**
```python
_format_objective(objective)          # Tri-objective structure
_format_anticipatory_set(anticipatory)  # Original + bilingual bridge
_format_tailored_instruction(instruction)  # Co-teaching + ELL support
_format_misconceptions(misconceptions)  # Content + linguistic notes
_format_assessment(assessment)        # Assessment + bilingual overlay
_format_homework(homework)            # Homework + family connection
```

### 3. CLI Usage

```bash
# Basic usage
python tools/docx_renderer.py input.json output.docx

# With custom template
python tools/docx_renderer.py input.json output.docx template.docx

# Example
python tools/docx_renderer.py \
  tests/fixtures/valid_lesson_minimal.json \
  output/lesson_plan.docx
```

### 4. Programmatic Usage

```python
from tools.docx_renderer import DOCXRenderer
import json

# Load JSON
with open('lesson.json', 'r') as f:
    json_data = json.load(f)

# Render
renderer = DOCXRenderer('input/Lesson Plan Template SY\'25-26.docx')
success = renderer.render(json_data, 'output/lesson.docx')
```

## Testing

### Test Suite (`tests/test_docx_renderer.py`)

**7 comprehensive tests:**

1. **Basic Rendering** - End-to-end rendering test
2. **Metadata Population** - Verify metadata table filling
3. **Daily Plan Population** - Verify daily plans table filling
4. **Markdown Formatting** - Test bold, italic, lists
5. **Missing Optional Fields** - Handle incomplete data
6. **Template Preservation** - Verify structure maintained
7. **Markdown Utilities** - Test helper functions

**Results:** ✅ 7/7 passing

**Run tests:**
```bash
python tests/test_docx_renderer.py
```

## Files Created

### Core Implementation
- `tools/markdown_to_docx.py` (234 lines) - Markdown converter
- `tools/docx_renderer.py` (377 lines) - Main renderer

### Testing
- `tests/test_docx_renderer.py` (382 lines) - Comprehensive tests

### Utilities
- `tools/inspect_template.py` - Template structure inspector
- `tools/inspect_template_detailed.py` - Detailed template analysis

### Documentation
- `requirements_phase5.txt` - Dependencies
- `PHASE5_IMPLEMENTATION.md` - This file

## Key Design Decisions

### 1. Template Cloning Approach

**Decision:** Clone template and populate cells directly

**Rationale:**
- Preserves all original formatting automatically
- No need to recreate styles, borders, colors
- Simpler than bookmark/field replacement
- Works with any template structure

**Alternatives Considered:**
- Bookmark replacement (requires bookmarks in template)
- Field replacement (complex, fragile)
- Build from scratch (loses formatting)

### 2. Markdown Support

**Decision:** Support markdown in JSON content

**Rationale:**
- LLMs naturally output markdown
- Easier to read in JSON
- Flexible formatting
- No HTML complexity

**Supported:**
- Bold: `**text**`
- Italic: `*text*`
- Bullets: `- item`
- Numbers: `1. item`

### 3. Template Compatibility

**Decision:** Don't require specific paragraph styles

**Rationale:**
- District templates vary
- List Bullet style may not exist
- Manual bullet characters work universally
- More robust across templates

### 4. Error Handling

**Decision:** Graceful degradation for missing fields

**Rationale:**
- Optional fields should be truly optional
- Empty cells better than errors
- Allows partial data rendering
- Supports iterative development

## Content Formatting

### Objective Section
```
**Content:** [content_objective]

**Student Goal:** [student_goal]

**WIDA/Bilingual:** [wida_objective]
```

### Anticipatory Set
```
[original_content]

**Bilingual Bridge:** [bilingual_bridge]
```

### Tailored Instruction
```
[original_content]

**Co-Teaching Model:** [model_name]

**Phase Plan:**
- **[phase_name]** ([minutes] min)
  - Bilingual: [bilingual_teacher_role]
  - Primary: [primary_teacher_role]

**ELL Support:**
- **[strategy_name]** ([proficiency_levels]): [implementation]

**Materials:** [materials list]
```

### Misconceptions
```
[original_content]

**Linguistic Note:** [note]
**Prevention:** [prevention_tip]
```

### Assessment
```
**Assessment:** [primary_assessment]

**Instrument:** [instrument]

**Supports by Level:**
- **Levels 1-2:** [supports]
- **Levels 3-4:** [supports]
- **Levels 5-6:** [supports]
```

### Homework
```
[original_content]

**Family Connection:** [family_connection]
```

## Performance

**Metrics:**
- Template loading: ~50ms
- JSON to DOCX conversion: ~200-500ms
- File saving: ~100ms
- **Total:** < 1 second per lesson plan

**Optimization opportunities:**
- Template caching (if rendering multiple plans)
- Parallel day processing (minimal gain)
- Pre-compiled regex patterns (already done)

## Integration Points

### Input
- Validated JSON from Phase 1 schema
- District DOCX template

### Output
- Formatted DOCX file
- Preserves template styling
- Ready for teacher use

### Dependencies
- `python-docx` - DOCX manipulation
- `lxml` - XML processing
- `tools/markdown_to_docx.py` - Formatting

### Used By
- CLI tools (direct usage)
- Future FastAPI endpoint (Phase 6)
- Integration tests (Phase 4)

## Known Limitations

1. **List Styles**
   - Uses manual bullet characters (•)
   - Doesn't use Word's list styles
   - Sufficient for current needs

2. **Complex Formatting**
   - No support for tables within cells
   - No support for images
   - No support for hyperlinks
   - Not needed for current schema

3. **Template Assumptions**
   - Assumes 3-table structure
   - Assumes specific row/column layout
   - Works with current district template
   - May need adjustment for other templates

4. **Markdown Limitations**
   - No nested lists
   - No code blocks
   - No blockquotes
   - Not needed for lesson plans

## Future Enhancements

### Phase 6 Integration
- FastAPI endpoint for rendering
- SSE progress updates
- Batch rendering support

### Template Detection
- Auto-detect table structure
- Support multiple template formats
- Configurable cell mapping

### Advanced Formatting
- Hyperlinks in content
- Embedded images
- Custom styles
- Color coding

### Performance
- Template caching
- Async rendering
- Parallel processing

## Troubleshooting

### Issue: "no style with name 'List Bullet'"
**Solution:** Template doesn't have List Bullet style. Fixed by using manual bullet characters.

### Issue: Import errors
**Solution:** Added try/except for both CLI and module usage patterns.

### Issue: Empty cells
**Solution:** Check that JSON has required fields. Optional fields can be empty.

### Issue: Formatting lost
**Solution:** Ensure using markdown syntax (`**bold**`, `*italic*`) in JSON content.

## Success Criteria

- ✅ Renders valid JSON to DOCX
- ✅ Preserves template formatting
- ✅ Handles markdown formatting
- ✅ Supports all schema fields
- ✅ Handles missing optional fields
- ✅ All tests passing (7/7)
- ✅ CLI tool functional
- ✅ Documentation complete

## Next Steps

**Phase 6: FastAPI Backend**
- Create REST API endpoints
- Add SSE progress streaming
- Integrate all components
- Add authentication
- Deploy as localhost service

**Estimated time:** 4-6 hours

---

**Phase 5 Complete!** 🎉

The DOCX renderer is fully functional and tested. We can now convert validated JSON lesson plans into formatted DOCX files that preserve the district template styling.

**Progress:** 62.5% → 75% (6 of 8 phases complete)
