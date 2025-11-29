# Objectives Print Module - Planning Document

## Overview

Create a simple module to generate a DOCX file for printing lesson plan objectives. Each page contains one lesson's objectives with specific layout requirements.

## Requirements

1. **One lesson per page** - Each page represents one lesson (slot)
2. **Landscape orientation** - Pages are landscape
3. **Margins** - All margins set to 0.5 inches
4. **Layout proportions**:
   - **Student Goal**: 3/4 of page height (top section)
   - **WIDA/Bilingual Objective**: 1/4 of page height (bottom section) with 50% gray font
5. **Font sizing**: Automatically calculated to fit content within proportions

---

## Key Decisions - CONFIRMED

### 1. What Constitutes "One Lesson"?

**DECISION: One Slot Per Day**
- Each page = one slot from one day
- Example: Monday Slot 1 (ELA) = one page, Tuesday Slot 1 (ELA) = another page
- Each slot has 5 days, so 5 pages per slot
- **Rationale**: Bilingual teacher needs to post one objective per lesson in each class

### 2. Content to Display

**DECISION: Student Goal + WIDA Objective Only**

**Top Section (3/4 of page) - Student Goal:**
- **Student Goal** text (main content, large font, base 48pt)
- No Content Objective (content objective is posted on wall by primary teacher)

**Bottom Section (1/4 of page) - WIDA/Bilingual:**
- **WIDA Objective** text (smaller font, 50% gray, base 14pt)
- Thin gray line separator between sections

**Header (top of page, 10pt font):**
- Date (from week_of)
- Subject
- Grade
- Homeroom name

### 3. Font Size Calculation Strategy

**Challenge**: Calculate font sizes so content fits in 3/4 and 1/4 sections.

**Page Dimensions (Landscape, 0.5" margins):**
- Standard US Letter: 11" × 8.5"
- With margins: 10" × 7.5" usable area
- Top section (3/4): 7.5" × 10" = 75 square inches
- Bottom section (1/4): 2.5" × 10" = 25 square inches

**Calculation Approach:**

**Option A: Fixed Font Sizes** (Simplest)
- Student Goal: Fixed size (e.g., 24pt or 28pt)
- WIDA Objective: Fixed size (e.g., 12pt or 14pt)
- **Pros**: Simple, predictable
- **Cons**: May overflow or leave too much space

**Option B: Dynamic Font Sizing** (Recommended)
- Measure text length
- Calculate optimal font size to fit in available space
- Use maximum font size that fits
- **Pros**: Always fits, maximizes readability
- **Cons**: More complex, requires text measurement

**Option C: Hybrid Approach**
- Start with base font sizes
- If text overflows, reduce font size proportionally
- If text is short, increase font size (up to max)
- **Pros**: Balance of simplicity and fit
- **Cons**: Still requires overflow detection

**DECISION: Hybrid Approach**

**Implementation:**
1. Start with base font sizes:
   - Student Goal: **48pt** (top section)
   - WIDA Objective: **14pt** (bottom section)
2. Measure text dimensions
3. If overflow detected:
   - Reduce font size proportionally
   - Minimum sizes: Student Goal **16pt**, WIDA Objective **10pt**
4. If text is short (less than 50% of available space):
   - Increase font size up to maximum: Student Goal **88pt**, WIDA Objective **18pt**

**Text Measurement:**
- Use python-docx's text measurement or estimate:
  - Approximate: 1pt font ≈ 0.0139 inches height
  - Width depends on font and characters
  - Use average character width for estimation

### 4. Generation Workflow

**When should this file be generated?**

**Option A: After Main Lesson Plan DOCX** (Recommended)
- Generate objectives DOCX immediately after main lesson plan DOCX
- Same workflow, just an additional output file
- **Pros**: Integrated workflow, all outputs together
- **Cons**: Slightly longer generation time

**Option B: On-Demand Generation**
- Generate objectives DOCX separately when teacher requests it
- New API endpoint or UI button
- **Pros**: Flexible, only generate when needed
- **Cons**: Requires separate action from teacher

**Option C: Both**
- Generate automatically after main DOCX
- Also allow on-demand regeneration
- **Pros**: Best of both worlds
- **Cons**: More code to maintain

**DECISION: Both Automatic and On-Demand**
- Generate automatically after main lesson plan DOCX
- Also provide on-demand generation via API endpoint
- Teachers can regenerate if needed

**File Naming:**
- Main file: `{TeacherName}_Lesson plan_{Week}_output.docx`
- Objectives file: `{TeacherName}_Objectives_{Week}_output.docx`

### 5. Page Layout Specifications

**Page Setup:**
- Orientation: Landscape
- Size: US Letter (11" × 8.5")
- Margins: 0.5" all sides
- Usable area: 10" × 7.5"

**Section Layout:**

**Header Section (top of page):**
- Height: ~0.3" (small, compact)
- Width: 10" (full width)
- Font: 10pt, regular
- Content: Date | Subject | Grade | Homeroom
- Alignment: Left-aligned
- Format: Single line, separated by " | " or tabs

**Top Section (Student Goal) - 3/4 of page:**
- Height: 7.5" (75% of 10" usable height)
- Width: 10" (full width)
- Padding: 0.3" internal padding
- Content area: 9.4" × 6.9"
- Font: Bold, calculated size (base 48pt, min 16pt, max 88pt)
- Alignment: Left-aligned, top-aligned
- Line spacing: 1.15 (slightly tight for fitting)

**Separator:**
- Thin gray line (0.5pt or 1pt)
- RGB: 128, 128, 128 (50% gray)
- Full width (10")
- Between top and bottom sections

**Bottom Section (WIDA Objective) - 1/4 of page:**
- Height: 2.5" (25% of 10" usable height)
- Width: 10" (full width)
- Padding: 0.2" internal padding
- Content area: 9.6" × 2.1"
- Font: Regular, calculated size (base 14pt, min 10pt, max 18pt), 50% gray (RGB: 128, 128, 128)
- Alignment: Left-aligned, top-aligned
- Line spacing: 1.1 (tight for fitting)

**Header Information (if included):**
- Day name: Small, bold, top-left (e.g., "Monday")
- Slot/Subject: Small, italic, top-right (e.g., "Slot 1: ELA")
- Unit/Lesson: Small, below day name (if available)

### 6. Template Structure

**Page Template:**

```
┌─────────────────────────────────────────────────────────┐
│ [0.5" margin]                                           │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 11/18/2024 | ELA | Grade 3 | Room 101              │ │ ← Header (10pt)
│ │                                                     │ │
│ │ STUDENT GOAL                                        │ │
│ │ (Large font, bold, base 48pt)                      │ │
│ │                                                     │ │
│ │ I will understand...                                │ │
│ │                                                     │ │
│ │                                                     │ │
│ │                                                     │ │ ← 3/4 of page
│ │                                                     │ │
│ │                                                     │ │
│ │                                                     │ │
│ ├─────────────────────────────────────────────────────┤ │ ← Thin gray line
│ │ WIDA/Bilingual:                                     │ │
│ │ (Smaller font, 50% gray, base 14pt)                │ │
│ │ Students will use language to...                    │ │
│ │                                                     │ │ ← 1/4 of page
│ └─────────────────────────────────────────────────────┘ │
│ [0.5" margin]                                           │
└─────────────────────────────────────────────────────────┘
```

### 7. Font Size Calculation Algorithm

**Implementation:**

```python
def calculate_font_size(text: str, available_width: float, available_height: float, 
                       base_font_size: int, min_font_size: int, max_font_size: int) -> int:
    """
    Calculate optimal font size to fit text in available space.
    
    Base sizes: Student Goal 48pt, WIDA Objective 14pt
    Min sizes: Student Goal 16pt, WIDA Objective 10pt
    Max sizes: Student Goal 88pt, WIDA Objective 18pt
    
    Assumptions:
    - Average character width ≈ font_size * 0.6 (for Arial/Calibri)
    - Line height ≈ font_size * 1.15 (with line spacing)
    """
    if not text or not text.strip():
        return base_font_size
    
    # Estimate text dimensions at base font size
    lines = text.split('\n')
    max_line_length = max(len(line) for line in lines) if lines else 0
    
    # Try base font size first
    font_size = base_font_size
    
    # Check if fits
    estimated_width = max_line_length * font_size * 0.6 / 72  # Convert to inches
    estimated_height = len(lines) * font_size * 1.15 / 72
    
    if estimated_width <= available_width and estimated_height <= available_height:
        # Fits! Try to increase if text is short
        if estimated_height < available_height * 0.5:
            # Text uses less than 50% of height, can increase
            scale_factor = min(available_height / estimated_height, 1.83)  # Max ~88/48 = 1.83x
            font_size = min(int(font_size * scale_factor), max_font_size)
    else:
        # Doesn't fit, need to reduce
        width_scale = available_width / estimated_width if estimated_width > 0 else 1.0
        height_scale = available_height / estimated_height if estimated_height > 0 else 1.0
        scale_factor = min(width_scale, height_scale)
        font_size = max(int(font_size * scale_factor * 0.9), min_font_size)  # 0.9 for safety margin
    
    return font_size
```

### 8. Handling Edge Cases

**Long Objectives:**
- If text still doesn't fit at minimum font size:
  - Truncate with ellipsis (...)
  - Or: Use smaller line spacing (1.0)
  - Or: Reduce padding

**Empty/No School:**
- If objective is "No School" or empty:
  - Still create page
  - Display "No School" in appropriate section
  - Use standard font size

**Multiple Lines:**
- Preserve line breaks in objectives
- Calculate based on longest line and total lines

**Special Characters:**
- Handle Unicode characters properly
- Ensure proper encoding in DOCX

### 9. Implementation Plan

**Phase 1: Core Module** (Week 1)
- [ ] Create `ObjectivesPrinter` class
- [ ] Implement page layout (landscape, margins, sections)
- [ ] Implement basic font sizing (fixed sizes first)
- [ ] Generate DOCX with one lesson per page
- [ ] Test with sample lesson plan

**Phase 2: Dynamic Font Sizing** (Week 1-2)
- [ ] Implement font size calculation algorithm
- [ ] Add text measurement utilities
- [ ] Test with various text lengths
- [ ] Refine sizing algorithm

**Phase 3: Integration** (Week 2)
- [ ] Integrate into batch processor workflow
- [ ] Generate after main DOCX
- [ ] Add to output folder
- [ ] Test end-to-end

**Phase 4: Polish** (Week 2)
- [ ] Handle edge cases (long text, empty objectives)
- [ ] Add header information (day, slot, subject)
- [ ] Fine-tune spacing and padding
- [ ] User testing and feedback

### 10. File Structure

```
backend/
├── services/
│   └── objectives_printer.py  (already created, needs DOCX generation)
└── utils/
    └── docx_objectives.py     (new: DOCX generation utilities)

tools/
└── generate_objectives_docx.py  (new: CLI tool for testing)
```

### 11. API Integration

**Add to batch processor:**
```python
# After generating main lesson plan DOCX
if lesson_json:
    objectives_printer = ObjectivesPrinter()
    objectives_docx_path = objectives_printer.generate_docx(
        lesson_json=lesson_json,
        output_path=objectives_output_path,
        user_name=user_name,
        week_of=week_of
    )
```

**New API endpoint (optional, for on-demand generation):**
```python
@app.post("/api/plans/{plan_id}/objectives-docx")
async def generate_objectives_docx(plan_id: str):
    """Generate objectives DOCX for a plan."""
    # Load lesson_json from database or file
    # Generate DOCX
    # Return file path or stream
```

---

## Questions for User

1. **What is "one lesson"?**
   - ✅ Recommended: One slot per day (e.g., Monday Slot 1 = one page)
   - Alternative: One day (all slots) or one slot across week?

2. **Content to display:**
   - ✅ Recommended: Student Goal (top 3/4) and WIDA Objective (bottom 1/4)
   - Should we include Content Objective? If yes, where?

3. **Header information:**
   - Include day name, slot number, subject, unit/lesson?
   - Where should it appear? (top of page, small font?)

4. **Font sizing:**
   - ✅ Recommended: Hybrid approach (base sizes with dynamic adjustment)
   - Acceptable minimum font sizes? (Student Goal: 16pt, WIDA: 10pt?)

5. **Generation timing:**
   - ✅ Recommended: Generate automatically after main lesson plan DOCX
   - Or: On-demand only?

6. **File naming:**
   - `{TeacherName}_Objectives_{Week}_output.docx`?
   - Or different format?

7. **Border between sections:**
   - Include thin border between Student Goal and WIDA sections?
   - Or just spacing?

8. **Page breaks:**
   - Each lesson on separate page (yes, required)
   - Page break before each new lesson?

---

## Final Decisions Summary - IMPLEMENTED

Based on user requirements, the following decisions were made and implemented:

1. **One lesson = One slot per day** ✅ (e.g., Monday Slot 1 = one page)
2. **Content**: Student Goal (top 3/4) + WIDA Objective (bottom 1/4, 50% gray) ✅
3. **Header**: Date | Subject | Grade | Homeroom (10pt font, top of page) ✅
4. **Font sizing**: Hybrid approach (base 48pt/14pt, min 16pt/10pt, max 88pt/18pt) ✅
5. **Generation**: Both automatic (after main DOCX) and on-demand ✅
6. **File naming**: `{TeacherName}_Objectives_{Week}_output.docx` ✅
7. **Border**: Thin gray line between sections ✅
8. **Page breaks**: Each lesson on separate page ✅
9. **Page setup**: Landscape, 0.5" margins all sides ✅

---

## Implementation Status

✅ **COMPLETED**

1. ✅ **Confirmed decisions** with user
2. ✅ **Created DOCX generation** with python-docx
3. ✅ **Implemented font sizing algorithm** (hybrid approach with dynamic adjustment)
4. ⏳ **Integrate into batch processor** (pending - see Integration section below)
5. ⏳ **Test with real lesson plans** (pending user testing)

## Integration

### Automatic Generation (After Main DOCX)

Add to batch processor after generating main lesson plan DOCX:

```python
from backend.services.objectives_printer import ObjectivesPrinter

# After generating main lesson plan DOCX
if lesson_json:
    objectives_printer = ObjectivesPrinter()
    objectives_output_path = output_path.replace('_output.docx', '_Objectives_output.docx')
    objectives_docx_path = objectives_printer.generate_docx(
        lesson_json=lesson_json,
        output_path=objectives_output_path,
        user_name=user_name,
        week_of=week_of
    )
```

### On-Demand Generation (API Endpoint)

Add new API endpoint for on-demand generation:

```python
@app.post("/api/plans/{plan_id}/objectives-docx")
async def generate_objectives_docx(plan_id: str):
    """Generate objectives DOCX for a plan."""
    from backend.services.objectives_printer import ObjectivesPrinter
    from backend.database import get_db
    
    db = get_db()
    plan = db.get_weekly_plan(plan_id)
    
    if not plan or not plan.get('lesson_json'):
        raise HTTPException(status_code=404, detail="Plan or lesson_json not found")
    
    lesson_json = plan['lesson_json']
    if isinstance(lesson_json, str):
        lesson_json = json.loads(lesson_json)
    
    objectives_printer = ObjectivesPrinter()
    output_path = f"output/{plan_id}_Objectives_output.docx"
    
    objectives_docx_path = objectives_printer.generate_docx(
        lesson_json=lesson_json,
        output_path=output_path,
        user_name=plan.get('user_name'),
        week_of=plan.get('week_of')
    )
    
    return {"output_path": objectives_docx_path}
```

---

## Technical Notes

**python-docx Limitations:**
- python-docx doesn't have built-in text measurement
- Need to estimate text dimensions
- Alternative: Use reportlab for more precise control (but adds dependency)

**Text Measurement Approach:**
- Use average character width estimates
- Account for font family (Arial/Calibri)
- Test with various text lengths to calibrate

**Section Division:**
- Use table with 2 rows (not recommended - harder to control)
- Use paragraph spacing and section breaks (recommended)
- Use text boxes (python-docx doesn't support well)

**Recommended Approach:**
- Use paragraphs with calculated spacing
- Set paragraph height/width using spacing before/after
- Use section breaks for page breaks

