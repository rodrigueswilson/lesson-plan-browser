# Data Flow Analysis: Table Contents & Hyperlinks

## Overview
This document traces the complete path of table contents and hyperlinks from input DOCX files to final output DOCX files in the Bilingual Weekly Plan Builder.

---

## Phase 1: Input Extraction (DOCXParser)

### Location: `tools/docx_parser.py`

### Table Content Extraction

**Entry Point:** `extract_subject_content(subject)`

1. **Table Discovery** (lines 196-231)
   - `find_subject_sections()` scans all tables in the input document
   - Identifies subject-specific tables (e.g., Math, ELA, Science)
   - Returns table indices and metadata

2. **Table Data Extraction** (lines 286-324)
   - `extract_table_lesson(table_index)` processes each table
   - **Structure:**
     - Row 0: Column headers (days of week: Monday, Tuesday, Wednesday, Thursday, Friday)
     - Column 0: Row labels (Unit/Lesson, Objective, Anticipatory Set, etc.)
     - Cells [row][col]: Content for each day/section combination
   
3. **Content Conversion** (lines 326-410)
   - Converts table structure to text format
   - Creates dictionary: `{day: {row_label: cell_text}}`
   - Detects "No School" days and marks them
   - Returns: `{'full_text': str, 'table_content': dict, 'no_school_days': list}`

### Hyperlink Extraction

**Entry Point:** `extract_hyperlinks()` (lines 645-746)

**Schema v2.0** includes both semantic and coordinate information:

1. **Paragraph Links** (lines 658-688)
   - Extracts from non-table paragraphs
   - Captures: text, url, context_snippet
   - **Coordinates:** `table_idx=None` (not in table)

2. **Table Links** (lines 690-738)
   - **Critical: Captures exact position in input table**
   - For each table → row → cell:
     ```python
     {
       'text': 'LESSON 5: REPRESENT PRODUCTS AS AREAS',
       'url': 'https://example.com',
       'table_idx': 0,        # Which table (0-indexed)
       'row_idx': 2,          # Which row (0-indexed)
       'cell_idx': 3,         # Which cell/column (0-indexed)
       'row_label': 'Unit/Lesson:',  # First cell text
       'col_header': 'Wednesday',     # Column header
       'day_hint': 'wednesday',       # Parsed day name
       'section_hint': 'unit_lesson', # Inferred section
       'context_snippet': '...'       # Surrounding text
     }
     ```

3. **Context Capture** (lines 748-772)
   - `_get_context_snippet()` extracts ±50 chars around link
   - Used for semantic matching later

4. **Section Inference** (lines 774-803)
   - `_infer_section()` analyzes cell text
   - Maps to: unit_lesson, objective, anticipatory_set, instruction, misconceptions, assessment, homework

---

## Phase 2: LLM Transformation (BatchProcessor)

### Location: `tools/batch_processor.py`

### Content Transformation (lines 289-562)

1. **Text Extraction** (line 431)
   ```python
   content = parser.extract_subject_content(slot["subject"])
   primary_content = content["full_text"]
   ```

2. **Hyperlink Preservation** (lines 443-451)
   - Extracts hyperlink texts: `[h['text'] for h in hyperlinks]`
   - **Adds instruction to LLM:** "Preserve these exact phrases..."
   - **Problem:** LLM often rephrases despite instruction
   - Example:
     - Input: "LESSON 5: REPRESENT PRODUCTS AS AREAS"
     - LLM Output: "Lección 5: Representar productos como áreas"

3. **LLM Call** (lines 470-478)
   - Sends text to LLM for bilingual transformation
   - Returns transformed JSON structure
   - **Content is now rephrased/translated**

4. **Metadata Attachment** (lines 544-556)
   - Original hyperlinks stored in: `lesson_json["_hyperlinks"]`
   - Original images stored in: `lesson_json["_images"]`
   - Schema version: `lesson_json["_media_schema_version"] = "2.0"`
   - **Key Point:** Hyperlinks retain original coordinates from input

### JSON Structure After LLM

```json
{
  "metadata": {...},
  "days": {
    "monday": {
      "unit_lesson": "Lección 5: Representar productos...",  // REPHRASED
      "objective": {...},
      "anticipatory_set": {...},
      ...
    },
    ...
  },
  "_hyperlinks": [
    {
      "text": "LESSON 5: REPRESENT PRODUCTS AS AREAS",  // ORIGINAL
      "url": "https://...",
      "table_idx": 0,
      "row_idx": 2,      // From INPUT table
      "cell_idx": 3,     // From INPUT table
      "row_label": "Unit/Lesson:",
      "col_header": "Wednesday",
      "day_hint": "wednesday",
      "section_hint": "unit_lesson"
    }
  ],
  "_media_schema_version": "2.0"
}
```

---

## Phase 3: Output Rendering (DOCXRenderer)

### Location: `tools/docx_renderer.py`

### Template Structure

**Template:** `input/Lesson Plan Template SY'25-26.docx`

- **Table 0:** Metadata (Name, Grade, Homeroom, Subject, Week)
- **Table 1:** Daily Plans (8 rows × 6 columns)
  - Row 0: Headers (blank, Monday, Tuesday, Wednesday, Thursday, Friday)
  - Row 1: Unit/Lesson
  - Row 2: Objective
  - Row 3: Anticipatory Set
  - Row 4: Tailored Instruction
  - Row 5: Misconceptions
  - Row 6: Assessment
  - Row 7: Homework
- **Table 2:** Signatures

### Content Filling Process

**Entry Point:** `render(json_data, output_path)` (lines 90-225)

1. **Load Template** (line 114)
   ```python
   doc = Document(self.template_path)
   ```

2. **Fill Metadata** (lines 227-264)
   - Fills Table 0 with teacher name, grade, subject, etc.

3. **Hyperlink Placement - v2.0 Hybrid Strategy** (lines 129-149)
   
   **Before filling daily content**, attempts coordinate-based placement:
   
   ```python
   for hyperlink in pending_hyperlinks[:]:
       strategy = self._place_hyperlink_hybrid(hyperlink, table, structure)
       if strategy != 'fallback':
           pending_hyperlinks.remove(hyperlink)
   ```

4. **Fill Daily Content** (lines 152-162)
   - For each day (Monday-Friday):
     - Fills Unit/Lesson row
     - Fills Objective row
     - Fills Anticipatory Set row
     - Fills Instruction row
     - Fills Misconceptions row
     - Fills Assessment row
     - Fills Homework row
   - Uses **REPHRASED/TRANSLATED** text from LLM

5. **Fallback Media** (lines 164-170)
   - Unmatched hyperlinks → "Referenced Links" section at end
   - Unmatched images → "Attached Images" section at end

### Hyperlink Placement Strategies

**Method:** `_place_hyperlink_hybrid()` (lines 1037-1075)

#### Strategy 1: Coordinate-Based (lines 1077-1111)

**Goal:** Place link at exact coordinates from input

```python
target_row = link['row_idx'] + structure.row_offset
cell = table.rows[target_row].cells[link['cell_idx']]
self._inject_hyperlink_inline(cell, link)
```

**Problem:** This assumes input and output tables have identical structure!

**Reality Check:**
- Input table structure may differ from output template
- Row indices may not align (e.g., input has extra rows)
- Column indices may not align (e.g., different day ordering)
- **This is likely where misplacement occurs**

#### Strategy 2: Label + Day Matching (lines 1113-1146)

**Goal:** Match by semantic labels instead of coordinates

```python
target_row = structure.get_row_index(link['row_label'])  // "Unit/Lesson:"
target_col = structure.get_col_index(link['day_hint'])   // "wednesday"
cell = table.rows[target_row].cells[target_col]
```

**Better:** Uses semantic matching, more robust

#### Strategy 3: Fuzzy Text Matching (lines 1148-1196)

**Goal:** Find cell with similar text content

```python
for each cell in table:
    confidence = calculate_match_confidence(cell.text, link)
    if confidence >= 0.65:
        place_link_here()
```

**Problem:** LLM rephrased the text!
- Input link text: "LESSON 5: REPRESENT PRODUCTS AS AREAS"
- Output cell text: "Lección 5: Representar productos como áreas"
- Fuzzy match score: LOW (different language)

#### Strategy 4: Fallback (lines 1227-1257)

**Last Resort:** Add to "Referenced Links" section at document end

---

## Root Cause of Hyperlink Misplacement

### Problem 1: Coordinate Mismatch

**Coordinate-based placement assumes:**
```
Input Table Structure = Output Table Structure
```

**Reality:**
- Input tables vary by teacher (different formats)
- Output template is standardized (8×6 grid)
- Row/column indices don't align

**Example:**
```
INPUT (Teacher's format):
Row 0: [Subject Header]
Row 1: [Days: Mon, Tue, Wed, Thu, Fri]
Row 2: [Unit/Lesson content]
Row 3: [Objective content]
...

OUTPUT (Template):
Row 0: [Days: Mon, Tue, Wed, Thu, Fri]  ← No subject header!
Row 1: [Unit/Lesson content]
Row 2: [Objective content]
...

Link with row_idx=2 from INPUT → placed at row 2 in OUTPUT
But row 2 in INPUT = Unit/Lesson
And row 2 in OUTPUT = Objective
→ WRONG CELL!
```

### Problem 2: Text Rephrasing

**Fuzzy matching fails because:**
- Original text: English
- Output text: Bilingual (English + Portuguese)
- LLM rephrases even English portions
- Fuzzy match threshold (0.65) too high for cross-language matching

**Example:**
```
Original: "LESSON 5: REPRESENT PRODUCTS AS AREAS"
Output:   "Lección 5: Representar productos como áreas"
Fuzzy similarity: ~30% (below 65% threshold)
→ NO MATCH → FALLBACK
```

### Problem 3: Section Inference Errors

**Parser may misidentify sections:**
- "LESSON X" might be inferred as 'unit_lesson'
- But could also be in 'instruction' section
- Curriculum links often lack clear section markers

---

## Recommendations to Fix Hyperlink Placement

### Fix 1: Improve Label+Day Matching (Highest Priority)

**Current Issue:** Strategy 2 should work but may have bugs

**Action:**
1. Debug `structure.get_row_index()` and `get_col_index()`
2. Add case-insensitive matching
3. Handle label variations:
   - "Unit/Lesson:" vs "Unit/Lesson" vs "Unit & Lesson"
4. Add logging to see why label matching fails

### Fix 2: Add Semantic Matching for Bilingual Text

**Current Issue:** Fuzzy matching fails on translated text

**Action:**
1. Use semantic embeddings (already implemented in `tools/semantic_matcher.py`)
2. Lower threshold for bilingual content (0.55 instead of 0.65)
3. Match on English portion only before translation

### Fix 3: Disable Coordinate Placement

**Current Issue:** Coordinates from input don't map to output

**Action:**
1. Set `structure_type != "standard_8x6"` to skip coordinate strategy
2. Rely on label+day matching (more robust)
3. Only use coordinates if input format is verified to match template

### Fix 4: Improve Context Preservation

**Current Issue:** LLM rephrases hyperlink text

**Action:**
1. Extract hyperlink text before LLM
2. Post-process LLM output to restore exact hyperlink text
3. Use regex to find and replace rephrased versions

---

## Data Flow Summary

```
INPUT DOCX
    ↓
[DOCXParser.extract_hyperlinks()]
    → Captures: text, url, table_idx, row_idx, cell_idx, row_label, col_header
    ↓
[BatchProcessor._process_slot()]
    → Extracts table content as text
    → Sends to LLM with "preserve hyperlink text" instruction
    → LLM REPHRASES content (including hyperlink text)
    → Attaches original hyperlinks to JSON: lesson_json["_hyperlinks"]
    ↓
[DOCXRenderer.render()]
    → Loads template (standardized 8×6 table)
    → Attempts coordinate placement: table.rows[row_idx].cells[cell_idx]
    → ❌ FAILS: Input coordinates don't match output structure
    → Attempts label+day placement: find row by "Unit/Lesson:", col by "Wednesday"
    → ❌ MAY FAIL: Bugs in label matching logic
    → Attempts fuzzy text matching: compare cell text to hyperlink context
    → ❌ FAILS: LLM rephrased text, fuzzy score < threshold
    → Fallback: Add to "Referenced Links" section at end
    ↓
OUTPUT DOCX
    → Hyperlinks appear in wrong cells OR in fallback section
```

---

## Debugging Steps

1. **Check coordinate alignment:**
   - Compare input table structure to output template
   - Log `row_idx`, `cell_idx` from parser
   - Log actual placement in renderer
   - Verify if coordinates match

2. **Check label+day matching:**
   - Log `row_label` and `day_hint` from parser
   - Log `structure.get_row_index()` and `get_col_index()` results
   - Check if labels are normalized (case, whitespace, punctuation)

3. **Check fuzzy matching:**
   - Log cell text vs. hyperlink context
   - Log fuzzy match scores
   - Check if threshold is too high for bilingual content

4. **Check LLM rephrasing:**
   - Compare original hyperlink text to output cell text
   - Measure similarity (should be low if rephrased)
   - Consider post-processing to restore original text

---

## Conclusion

**The hyperlink misplacement occurs because:**

1. **Coordinate-based placement** assumes input and output tables have identical structure, which is false
2. **Label+day matching** should work but may have implementation bugs
3. **Fuzzy text matching** fails because LLM rephrases content, breaking similarity matching
4. **Fallback** catches all failed placements, resulting in links at document end instead of inline

**Primary fix:** Debug and improve label+day matching (Strategy 2) as it's the most robust approach for handling varying input formats and translated content.
