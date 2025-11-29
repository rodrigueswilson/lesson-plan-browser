# Day 9 Session Plan: Single Weekly DOCX Consolidation

**Date**: 2025-10-06 (Next Session)  
**Status**: PLANNED  
**Priority**: HIGH - User Experience Enhancement

---

## 🎯 Session Objective

**Convert the current 5 separate DOCX files into a single consolidated weekly DOCX file** that contains all class slots organized by day, maintaining district template formatting.

---

## 📋 Current State Analysis

### What We Have Now

**Current Behavior** (batch_processor.py lines 283-310):
```python
# Multiple slots - create separate files
for lesson in lessons:
    slot_num = lesson['slot_number']
    subject = lesson['subject']
    
    # Create filename for this slot
    slot_filename = f"{user_name}_Slot{slot_num}_{subject}_W{week_num}.docx"
    
    # Render each slot to separate DOCX
    renderer.render(lesson_json, slot_output_path)
```

**Output**: 5 separate files
- `Lang_Slot1_ELA_W01_2025-09-15.docx`
- `Davies_Slot2_Math_W01_2025-09-15.docx`
- `Savoca_Slot3_Science_W01_2025-09-15.docx`
- `Lang_Slot4_Social Studies_W01_2025-09-15.docx`
- `Davies_Slot5_Math_W01_2025-09-15.docx`

### What We Already Have

✅ **JSON Merger** (`tools/json_merger.py`)
- Merges 5 individual lesson JSONs into single multi-slot structure
- Organizes by day with `slots` array
- Already validated and working

✅ **Multi-Slot Renderer** (`tools/docx_renderer.py` lines 207-280)
- `_fill_multi_slot_day()` method exists
- Combines multiple slots per day with separators
- Slot headers: `**Slot {num}: {subject}** ({teacher})`

✅ **Template Capacity Detection** (docx_renderer.py)
- Font-size + cell-dimension heuristics
- Already handles content fitting

---

## 🎯 Desired State

### Single Weekly DOCX Output

**Filename**: `{UserName}_Weekly_W{WeekNum}_{WeekOf}.docx`  
**Example**: `Lang_Weekly_W01_2025-09-15.docx`

**Structure**:
```
┌─────────────────────────────────────────────────────┐
│ Name: Multiple Teachers | Grade: 3rd | Week of: ... │
└─────────────────────────────────────────────────────┘

┌─────────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│             │ Monday   │ Tuesday  │ Wednesday│ Thursday │ Friday   │
├─────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ Unit/Lesson │ Slot 1:  │ Slot 1:  │ Slot 1:  │ Slot 1:  │ Slot 1:  │
│             │ ELA      │ ELA      │ ELA      │ ELA      │ ELA      │
│             │ (Lang)   │ (Lang)   │ (Lang)   │ (Lang)   │ (Lang)   │
│             │ Unit 2   │ Unit 2   │ Unit 2   │ Unit 2   │ Unit 2   │
│             │ ─────────│ ─────────│ ─────────│ ─────────│ ─────────│
│             │ Slot 2:  │ Slot 2:  │ Slot 2:  │ Slot 2:  │ Slot 2:  │
│             │ Math     │ Math     │ Math     │ Math     │ Math     │
│             │ (Davies) │ (Davies) │ (Davies) │ (Davies) │ (Davies) │
│             │ Chapter 3│ Chapter 3│ Chapter 3│ Chapter 3│ Chapter 3│
│             │ ─────────│ ─────────│ ─────────│ ─────────│ ─────────│
│             │ Slot 3:  │ Slot 3:  │ Slot 3:  │ Slot 3:  │ Slot 3:  │
│             │ Science  │ Science  │ Science  │ Science  │ Science  │
│             │ (Savoca) │ (Savoca) │ (Savoca) │ (Savoca) │ (Savoca) │
│             │ Lesson 5 │ Lesson 5 │ Lesson 5 │ Lesson 5 │ Lesson 5 │
├─────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ Objective   │ [All 5 slots combined with separators]              │
├─────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ ...         │ [Continue for all rows]                             │
└─────────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

---

## 📝 Implementation Plan

### Phase 1: Update Batch Processor (30 min)

**File**: `tools/batch_processor.py`

#### Changes Needed

**1. Modify `_combine_lessons()` method** (lines 226-310)

**Current Logic**:
```python
if len(lessons) == 1:
    # Single slot - use original logic
    renderer.render(merged_json, output_path)
else:
    # Multiple slots - create separate files
    for lesson in lessons:
        renderer.render(lesson_json, slot_output_path)
```

**New Logic**:
```python
# Always use merged JSON for rendering
print(f"Rendering consolidated weekly plan with {len(lessons)} slots...")

# Render merged JSON to single DOCX
renderer.render(merged_json, output_path)

# Add signature box
doc = Document(output_path)
self._add_signature_box(doc, generated_at)
doc.save(output_path)

print(f"Successfully created consolidated weekly plan: {output_path}")
return output_path
```

**2. Update output filename generation**

**Current**:
```python
output_path = file_mgr.get_output_path(week_folder, user['name'], week_of)
# Returns: Lang_Slot1_ELA_W01_2025-09-15.docx
```

**New**:
```python
# For multi-slot, use "Weekly" instead of slot-specific name
if len(lessons) > 1:
    week_num = self._get_week_num(week_of)
    filename = f"{user['name'].replace(' ', '_')}_Weekly_W{week_num:02d}_{week_of.replace('/', '-')}.docx"
    output_path = str(week_folder / filename)
else:
    # Single slot keeps original naming
    output_path = file_mgr.get_output_path(week_folder, user['name'], week_of)
```

**3. Update metadata handling**

**Current**:
```python
merged_json['metadata']['user_name'] = user['name']
```

**New**:
```python
# Add consolidated metadata
merged_json['metadata']['user_name'] = user['name']
merged_json['metadata']['teacher_name'] = "Multiple Teachers"  # Or combine names
merged_json['metadata']['subject'] = "Multiple Subjects"  # Or combine subjects
merged_json['metadata']['total_slots'] = len(lessons)
```

### Phase 2: Enhance Metadata Display (20 min)

**File**: `tools/docx_renderer.py`

#### Update `_fill_metadata()` method (lines 107-144)

**Current**:
```python
cell.text = f"Name: {metadata['teacher_name']}"
cell.text = f"Subject: {metadata['subject']}"
```

**New**:
```python
# Handle multiple teachers
if 'total_slots' in metadata and metadata['total_slots'] > 1:
    # Extract unique teacher names from days/slots
    teachers = self._extract_unique_teachers(json_data)
    cell.text = f"Name: {', '.join(teachers[:3])}"  # Show first 3
    if len(teachers) > 3:
        cell.text += f" (+{len(teachers) - 3} more)"
    
    # Extract unique subjects
    subjects = self._extract_unique_subjects(json_data)
    cell.text = f"Subject: {', '.join(subjects[:3])}"
    if len(subjects) > 3:
        cell.text += f" (+{len(subjects) - 3} more)"
else:
    # Single slot - use original logic
    cell.text = f"Name: {metadata['teacher_name']}"
    cell.text = f"Subject: {metadata['subject']}"
```

**Add helper methods**:
```python
def _extract_unique_teachers(self, json_data: Dict) -> List[str]:
    """Extract unique teacher names from all slots."""
    teachers = set()
    for day_data in json_data['days'].values():
        if 'slots' in day_data:
            for slot in day_data['slots']:
                if slot.get('teacher_name'):
                    teachers.add(slot['teacher_name'])
    return sorted(teachers)

def _extract_unique_subjects(self, json_data: Dict) -> List[str]:
    """Extract unique subjects from all slots."""
    subjects = set()
    for day_data in json_data['days'].values():
        if 'slots' in day_data:
            for slot in day_data['slots']:
                if slot.get('subject'):
                    subjects.add(slot['subject'])
    return sorted(subjects)
```

### Phase 3: Enhance Multi-Slot Rendering (30 min)

**File**: `tools/docx_renderer.py`

#### Update `_fill_multi_slot_day()` method (lines 207-280)

**Current Implementation**: Already exists and works!

**Enhancements Needed**:

**1. Add visual separators between slots**
```python
# Current separator
slot_header = f"**Slot {slot_num}: {subject}**"

# Enhanced separator with line
slot_header = f"{'─' * 40}\n**Slot {slot_num}: {subject}**"
if teacher:
    slot_header += f" ({teacher})"
slot_header += f"\n{'─' * 40}"
```

**2. Handle empty slots gracefully**
```python
# If a slot has no content for a particular day
if not slot.get('unit_lesson') and not slot.get('objective'):
    # Add placeholder
    unit_lessons.append(f"{slot_header}\n[No lesson planned]")
```

**3. Add slot ordering consistency**
```python
# Ensure slots are always in order
slots = sorted(slots, key=lambda x: x.get('slot_number', 0))
```

### Phase 4: Content Fitting & Overflow Handling (45 min)

**Challenge**: 5 slots of content may not fit in a single cell

**Solutions**:

#### Option 1: Abbreviated Format (Recommended)
```python
def _format_abbreviated_slot(self, slot: Dict, field: str) -> str:
    """Format slot content in abbreviated form for multi-slot display."""
    slot_num = slot.get('slot_number', '?')
    subject = slot.get('subject', 'Unknown')
    
    # Abbreviated header
    header = f"[{slot_num}] {subject[:15]}"  # Truncate subject
    
    # Abbreviated content (first 100 chars)
    content = slot.get(field, '')
    if isinstance(content, dict):
        content = self._format_field(content)  # Use existing formatter
    
    if len(content) > 100:
        content = content[:97] + "..."
    
    return f"{header}: {content}"
```

#### Option 2: Summary + Detail Pages
```python
# Page 1: Summary view (abbreviated)
# Page 2+: Full detail for each slot (separate pages)

def render_with_detail_pages(self, merged_json: Dict, output_path: str):
    """Render with summary page + detail pages."""
    doc = Document(self.template_path)
    
    # Page 1: Summary (abbreviated multi-slot)
    self._fill_summary_page(doc, merged_json)
    
    # Page 2+: Full detail for each slot
    for slot_num in range(1, merged_json['metadata']['total_slots'] + 1):
        doc.add_page_break()
        slot_json = self._extract_slot_json(merged_json, slot_num)
        self._fill_detail_page(doc, slot_json)
    
    doc.save(output_path)
```

#### Option 3: Dynamic Font Sizing (Simple)
```python
def _calculate_font_size(self, content_length: int, num_slots: int) -> int:
    """Calculate appropriate font size based on content."""
    base_size = 11  # Template default
    
    if num_slots <= 2:
        return base_size
    elif num_slots <= 3:
        return base_size - 1  # 10pt
    elif num_slots <= 4:
        return base_size - 2  # 9pt
    else:
        return base_size - 3  # 8pt (minimum readable)
```

**Recommendation**: Start with **Option 1 (Abbreviated)** for MVP, add Option 2 if users request full detail.

### Phase 5: Testing & Validation (30 min)

#### Test Cases

**Test 1: Single Slot (Regression)**
```python
# Input: 1 lesson
# Expected: Original behavior (single slot DOCX)
# Filename: Lang_Slot1_ELA_W01_2025-09-15.docx
```

**Test 2: Two Slots**
```python
# Input: 2 lessons (ELA + Math)
# Expected: Consolidated DOCX with 2 slots per day
# Filename: User_Weekly_W01_2025-09-15.docx
```

**Test 3: Five Slots (Full Week)**
```python
# Input: 5 lessons (all subjects)
# Expected: Consolidated DOCX with 5 slots per day
# Verify: Content fits, readable font size
```

**Test 4: Mixed Content Lengths**
```python
# Input: 5 lessons with varying content lengths
# Expected: Proper truncation/abbreviation
# Verify: No overflow, consistent formatting
```

**Test 5: Empty Slots**
```python
# Input: 3 lessons, one has empty Monday
# Expected: Placeholder text for empty slot
```

#### Validation Checklist
- [ ] Single slot still works (regression test)
- [ ] Multi-slot creates single file (not 5 files)
- [ ] Filename is correct (Weekly instead of Slot#)
- [ ] Metadata shows multiple teachers/subjects
- [ ] All 5 days rendered correctly
- [ ] Slot separators visible
- [ ] Content fits in cells
- [ ] Font size readable
- [ ] Template formatting preserved
- [ ] Signature box present

### Phase 6: Update API & Database (20 min)

**File**: `backend/api.py`

#### Update batch process endpoint

**Current**:
```python
@app.post("/api/batch-process")
async def batch_process(request: BatchProcessRequest):
    # Returns list of output files
    return {"output_files": [file1, file2, file3, file4, file5]}
```

**New**:
```python
@app.post("/api/batch-process")
async def batch_process(request: BatchProcessRequest):
    # Returns single consolidated file
    return {
        "output_file": "Lang_Weekly_W01_2025-09-15.docx",
        "total_slots": 5,
        "consolidated": True
    }
```

**File**: `backend/database.py`

#### Update weekly_plans table schema

**Add column**:
```sql
ALTER TABLE weekly_plans ADD COLUMN consolidated BOOLEAN DEFAULT 1;
ALTER TABLE weekly_plans ADD COLUMN total_slots INTEGER DEFAULT 1;
```

---

## 📊 Implementation Checklist

### Phase 1: Batch Processor (30 min)
- [ ] Modify `_combine_lessons()` to always use merged JSON
- [ ] Update output filename for multi-slot
- [ ] Update metadata handling
- [ ] Remove separate file creation loop
- [ ] Test with 2 slots

### Phase 2: Metadata Display (20 min)
- [ ] Update `_fill_metadata()` for multiple teachers
- [ ] Add `_extract_unique_teachers()` helper
- [ ] Add `_extract_unique_subjects()` helper
- [ ] Handle truncation for many teachers/subjects
- [ ] Test metadata display

### Phase 3: Multi-Slot Rendering (30 min)
- [ ] Enhance slot separators (visual lines)
- [ ] Add empty slot handling
- [ ] Ensure slot ordering consistency
- [ ] Test with 3 slots

### Phase 4: Content Fitting (45 min)
- [ ] Implement abbreviated format (Option 1)
- [ ] Add content truncation logic
- [ ] Test with 5 slots (full content)
- [ ] Verify readability
- [ ] Consider dynamic font sizing if needed

### Phase 5: Testing (30 min)
- [ ] Run Test 1: Single slot regression
- [ ] Run Test 2: Two slots
- [ ] Run Test 3: Five slots
- [ ] Run Test 4: Mixed content
- [ ] Run Test 5: Empty slots
- [ ] Verify all validation checklist items

### Phase 6: API & Database (20 min)
- [ ] Update API response format
- [ ] Add database columns
- [ ] Update frontend expectations (if applicable)
- [ ] Test end-to-end workflow

---

## 🎯 Success Criteria

### Functional Requirements
- [x] Single DOCX file generated for multi-slot weeks
- [x] All 5 slots visible in each day column
- [x] Slot separators clearly distinguish content
- [x] Metadata shows all teachers/subjects
- [x] Content fits within template cells
- [x] Template formatting preserved

### User Experience
- [x] Filename clearly indicates "Weekly" plan
- [x] Easy to identify which slot is which
- [x] Readable font size (minimum 8pt)
- [x] Professional appearance
- [x] Consistent with district template

### Technical Requirements
- [x] No breaking changes to single-slot workflow
- [x] JSON merger already validated
- [x] Multi-slot renderer already exists
- [x] All tests passing
- [x] API updated accordingly

---

## 🚀 Estimated Timeline

| Phase | Duration | Complexity |
|-------|----------|------------|
| **Phase 1: Batch Processor** | 30 min | Low |
| **Phase 2: Metadata Display** | 20 min | Low |
| **Phase 3: Multi-Slot Rendering** | 30 min | Low |
| **Phase 4: Content Fitting** | 45 min | Medium |
| **Phase 5: Testing** | 30 min | Low |
| **Phase 6: API & Database** | 20 min | Low |
| **Buffer** | 15 min | - |
| **Total** | **3 hours** | **Low-Medium** |

---

## 💡 Key Design Decisions

### 1. Always Consolidate (Recommended)
**Decision**: Always create single DOCX for multi-slot, even if only 2 slots

**Rationale**:
- Simpler user experience (one file to manage)
- Consistent behavior
- Easier to print/share

**Alternative**: Only consolidate if >3 slots (rejected - adds complexity)

### 2. Abbreviated Format for MVP
**Decision**: Use abbreviated/truncated content for multi-slot display

**Rationale**:
- Fits within template constraints
- Faster implementation
- Users can see overview at a glance

**Future Enhancement**: Add detail pages if users request full content

### 3. Preserve Single-Slot Behavior
**Decision**: Keep original filename/format for single slot

**Rationale**:
- No breaking changes
- Backward compatibility
- Clear distinction between single/multi

### 4. Metadata Shows "Multiple"
**Decision**: Show "Multiple Teachers" / "Multiple Subjects" in header

**Rationale**:
- Accurate representation
- Avoids confusion
- Can list specific names in smaller text

---

## 📝 Code Changes Summary

### Files to Modify
1. **tools/batch_processor.py** (~50 lines changed)
   - `_combine_lessons()` method
   - Output filename logic
   - Remove separate file loop

2. **tools/docx_renderer.py** (~100 lines added)
   - `_fill_metadata()` enhancement
   - Helper methods for teacher/subject extraction
   - `_fill_multi_slot_day()` enhancements
   - Abbreviated formatting

3. **backend/api.py** (~10 lines changed)
   - Update response format
   - Add consolidated flag

4. **backend/database.py** (~5 lines added)
   - Add schema columns

### Files to Test
1. **tests/test_batch_processor.py** (update existing)
2. **tests/test_docx_renderer.py** (add multi-slot tests)
3. **tests/test_json_merger.py** (already exists, verify)

---

## 🔄 Migration Strategy

### For Existing Users
1. **No data migration needed** - only affects new generations
2. **Old files remain** - separate DOCX files still accessible
3. **Gradual rollout** - can toggle via feature flag if needed

### Feature Flag (Optional)
```python
# backend/config.py
CONSOLIDATE_WEEKLY_DOCX = True  # Set to False to revert to separate files
```

---

## 📚 Documentation Updates

### Files to Update
1. **README.md** - Update features section
2. **docs/guides/USER_TRAINING_GUIDE.md** - Update workflow
3. **CHANGELOG.md** - Add v1.1.0 entry
4. **docs/ARCHITECTURE_MULTI_USER.md** - Update output flow

### New Documentation
1. **docs/guides/WEEKLY_DOCX_FORMAT.md** - Explain consolidated format
2. **docs/examples/weekly_consolidated_sample.png** - Screenshot

---

## 🎓 Learning Objectives

### What We'll Learn
1. How to leverage existing JSON merger for DOCX consolidation
2. Content fitting strategies for multi-slot display
3. Metadata aggregation techniques
4. Backward compatibility patterns

### Skills Applied
- Python DOCX manipulation
- Content truncation algorithms
- User experience design
- Testing multi-variant scenarios

---

## ✅ Pre-Session Checklist

Before starting Day 9:
- [ ] Review `tools/json_merger.py` implementation
- [ ] Review `tools/docx_renderer.py` multi-slot methods
- [ ] Verify current test suite passes
- [ ] Have sample 5-slot data ready for testing
- [ ] Review district template structure

---

**Status**: Ready for Day 9  
**Complexity**: Low-Medium (mostly leveraging existing code)  
**Risk**: Low (non-breaking change)  
**User Impact**: High (major UX improvement)

---

*Created: 2025-10-05*  
*Estimated Session Duration: 3 hours*  
*Prerequisites: Day 8 complete (✅)*
