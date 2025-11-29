# Next Session - Day 6: Fix Multi-Slot Document Combining

**Priority**: CRITICAL  
**Estimated Time**: 1-2 hours  
**Goal**: Generate single DOCX with all 5 slots across all 5 days

---

## 🎯 Session Objective

Fix the document combining logic so the final DOCX contains:
- ✅ All 5 class slots (not just one)
- ✅ All 5 days (Monday-Friday, not just Monday)
- ✅ Properly merged content (no duplicates, no missing data)

---

## 🔍 Investigation Phase (30 minutes)

### Step 1: Understand Current JSON Structure

**Action**: Examine what the LLM returns for each slot

```python
# Add to batch_processor.py after line 74 (after LLM transformation):
import json
print(f"\n=== Slot {slot['slot_number']} JSON Structure ===")
print(f"Keys: {lesson_json.keys()}")
if 'days' in lesson_json:
    print(f"Days present: {list(lesson_json['days'].keys())}")
    for day, content in lesson_json['days'].items():
        print(f"  {day}: {list(content.keys())}")
print(f"JSON preview:\n{json.dumps(lesson_json, indent=2)[:800]}\n")
```

**Questions to Answer**:
1. What is the exact structure of each slot's JSON?
2. Which days does each slot have data for?
3. Is there a "slots" array within each day, or is it flat?
4. How is metadata stored (teacher name, subject, etc.)?

### Step 2: Review Template Structure

**Action**: Open `input/Lesson Plan Template SY'25-26.docx` and examine:

1. **Does the template support multiple slots per day?**
   - Look for repeating sections
   - Check for slot/subject placeholders
   - Identify table structure

2. **How are days organized?**
   - Separate pages?
   - Separate sections?
   - Single table with columns?

3. **What placeholders exist?**
   - `{{teacher_name}}`?
   - `{{subject}}`?
   - `{{slot_number}}`?

**Action**: Document the template structure in comments

### Step 3: Review Current Renderer

**Action**: Examine `tools/docx_renderer.py`

```python
# Check how it processes the JSON:
# - Does it expect a single slot or multiple slots?
# - How does it handle the 'days' structure?
# - Can it render multiple slots for the same day?
```

**Questions to Answer**:
1. Does the renderer support multiple slots per day?
2. How does it map JSON to template placeholders?
3. What changes are needed to support merged JSON?

---

## 💡 Solution Design (30 minutes)

### Option A: Merge JSON Before Rendering (RECOMMENDED)

**Approach**: Combine all slot JSONs into a single structure, then render once

**Merged JSON Structure**:
```json
{
  "metadata": {
    "week_of": "10/06-10/10",
    "grade": "3",
    "user_name": "Wilson Rodrigues"
  },
  "days": {
    "monday": {
      "slots": [
        {
          "slot_number": 1,
          "subject": "ELA",
          "teacher_name": "Lang",
          "unit_lesson": "...",
          "bilingual_strategies": [...]
        },
        {
          "slot_number": 3,
          "subject": "Science",
          "teacher_name": "Savoca",
          "unit_lesson": "...",
          "bilingual_strategies": [...]
        }
      ]
    },
    "tuesday": {
      "slots": [...]
    },
    ...
  }
}
```

**Pros**:
- Clean separation of concerns
- Single rendering pass
- Template can be designed for multi-slot layout
- Easy to debug

**Cons**:
- Requires template update to support slots array
- More complex JSON structure

### Option B: Render Separately, Combine Smartly

**Approach**: Render each slot to DOCX, then use docxcompose to merge properly

**Implementation**:
```python
from docxcompose.composer import Composer

# Render each slot
docs = []
for lesson in lessons:
    doc = render_to_document(lesson['lesson_json'])
    docs.append(doc)

# Combine using docxcompose
master = docs[0]
composer = Composer(master)
for doc in docs[1:]:
    composer.append(doc)

composer.save(output_path)
```

**Pros**:
- No template changes needed
- Uses proven library (docxcompose)
- Simpler implementation

**Cons**:
- May have formatting issues
- Less control over layout
- Could duplicate headers/footers

### Option C: Hybrid Approach

**Approach**: Merge JSON for same-day slots, render day-by-day

**Implementation**:
1. Group slots by day
2. For each day, merge slots into day structure
3. Render each day to a section
4. Combine sections into final document

**Pros**:
- Balanced complexity
- Good control over layout
- Can handle day-specific formatting

**Cons**:
- More complex than other options
- Requires both JSON merging and DOCX combining

---

## 🛠️ Implementation Plan

### Recommended Approach: Option A (Merge JSON First)

#### Phase 1: Create JSON Merger (30 minutes)

**File**: `tools/json_merger.py` (new file)

```python
"""
JSON Merger for combining multiple lesson plan JSONs.
"""

from typing import List, Dict, Any
from collections import defaultdict

def merge_lesson_jsons(lessons: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple lesson JSONs into a single combined structure.
    
    Args:
        lessons: List of dicts with 'slot_number', 'subject', 'lesson_json'
        
    Returns:
        Combined JSON with all slots organized by day
    """
    # Initialize merged structure
    merged = {
        "metadata": {
            "week_of": "",
            "grade": "",
            "user_name": ""
        },
        "days": {
            "monday": {"slots": []},
            "tuesday": {"slots": []},
            "wednesday": {"slots": []},
            "thursday": {"slots": []},
            "friday": {"slots": []}
        }
    }
    
    # Extract metadata from first lesson
    if lessons:
        first_lesson = lessons[0]['lesson_json']
        if 'metadata' in first_lesson:
            merged['metadata'] = first_lesson['metadata'].copy()
    
    # Merge slots by day
    for lesson in lessons:
        lesson_json = lesson['lesson_json']
        slot_info = {
            'slot_number': lesson['slot_number'],
            'subject': lesson['subject']
        }
        
        # Add each day's content to the merged structure
        if 'days' in lesson_json:
            for day, day_content in lesson_json['days'].items():
                if day in merged['days']:
                    # Combine slot info with day content
                    slot_data = {**slot_info, **day_content}
                    merged['days'][day]['slots'].append(slot_data)
    
    # Sort slots by slot_number within each day
    for day in merged['days']:
        merged['days'][day]['slots'].sort(key=lambda x: x['slot_number'])
    
    return merged


def validate_merged_json(merged: Dict[str, Any]) -> bool:
    """
    Validate the merged JSON structure.
    
    Args:
        merged: Merged JSON to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Check required keys
    if 'metadata' not in merged or 'days' not in merged:
        return False
    
    # Check all days present
    required_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    for day in required_days:
        if day not in merged['days']:
            return False
        if 'slots' not in merged['days'][day]:
            return False
    
    return True
```

#### Phase 2: Update Batch Processor (15 minutes)

**File**: `tools/batch_processor.py`

**Change in `_combine_lessons` method** (around line 175):

```python
def _combine_lessons(self, user: Dict[str, Any], lessons: List[Dict[str, Any]], 
                    week_of: str, generated_at: datetime) -> str:
    """Combine multiple lessons into a single DOCX."""
    from tools.json_merger import merge_lesson_jsons, validate_merged_json
    
    # Sort lessons by slot number
    lessons.sort(key=lambda x: x['slot_number'])
    
    # MERGE JSON FIRST (NEW APPROACH)
    merged_json = merge_lesson_jsons(lessons)
    
    # Validate merged structure
    if not validate_merged_json(merged_json):
        raise ValueError("Merged JSON validation failed")
    
    # Add user info to metadata
    merged_json['metadata']['user_name'] = user['name']
    
    # Get output path
    file_mgr = get_file_manager()
    week_folder = file_mgr.get_week_folder(week_of)
    output_path = file_mgr.get_output_path(week_folder, user['name'], week_of)
    
    # Render merged JSON to single DOCX
    template_path = "input/Lesson Plan Template SY'25-26.docx"
    renderer = DOCXRenderer(template_path)
    renderer.render(merged_json, output_path)
    
    # Add signature
    doc = Document(output_path)
    self._add_signature_box(doc, generated_at)
    doc.save(output_path)
    
    return output_path
```

#### Phase 3: Update Renderer (if needed) (30 minutes)

**File**: `tools/docx_renderer.py`

**Check if renderer needs updates to handle slots array**:

1. If template has `{{#slots}}...{{/slots}}` loop → No changes needed
2. If template expects flat structure → Need to update rendering logic

**Possible changes**:
```python
# In render method, handle slots array for each day:
for day_name, day_data in lesson_json['days'].items():
    if 'slots' in day_data:
        for slot in day_data['slots']:
            # Render each slot within the day
            self._render_slot(slot, day_name)
```

---

## ✅ Testing Plan (30 minutes)

### Test 1: JSON Merging
```python
# Create test script: test_json_merger.py
from tools.json_merger import merge_lesson_jsons

# Sample data
slot1 = {
    'slot_number': 1,
    'subject': 'ELA',
    'lesson_json': {
        'metadata': {'week_of': '10/06-10/10', 'grade': '3'},
        'days': {
            'monday': {'unit_lesson': 'Reading'},
            'tuesday': {'unit_lesson': 'Writing'}
        }
    }
}

slot2 = {
    'slot_number': 2,
    'subject': 'Math',
    'lesson_json': {
        'metadata': {'week_of': '10/06-10/10', 'grade': '3'},
        'days': {
            'tuesday': {'unit_lesson': 'Addition'},
            'wednesday': {'unit_lesson': 'Subtraction'}
        }
    }
}

# Test merge
merged = merge_lesson_jsons([slot1, slot2])

# Verify
assert 'monday' in merged['days']
assert len(merged['days']['monday']['slots']) == 1
assert len(merged['days']['tuesday']['slots']) == 2
print("✓ JSON merging works!")
```

### Test 2: Full Pipeline
```python
# In Tauri app:
# 1. Configure 5 slots with teacher names
# 2. Click "Generate"
# 3. Wait for processing
# 4. Open generated DOCX
# 5. Verify:
#    - All 5 slots present
#    - All 5 days present
#    - Content properly organized
```

### Test 3: Edge Cases
- [ ] Slot with no days (should skip)
- [ ] Multiple slots same subject (should both appear)
- [ ] Different grades in same day (should show both)
- [ ] Missing metadata (should use defaults)

---

## 🚨 Potential Issues & Solutions

### Issue 1: Template Doesn't Support Slots Array

**Symptom**: Renderer fails or only shows first slot

**Solution**: Update template to have repeating section:
```
{{#days.monday.slots}}
  Slot {{slot_number}}: {{subject}} - {{teacher_name}}
  {{unit_lesson}}
  ...
{{/days.monday.slots}}
```

### Issue 2: Formatting Lost in Merge

**Symptom**: Combined DOCX looks different from individual ones

**Solution**: 
- Ensure merged JSON preserves all formatting fields
- Check that renderer applies styles correctly
- May need to copy styles from template

### Issue 3: Slots Not in Correct Order

**Symptom**: Slots appear in wrong sequence

**Solution**: 
- Ensure sorting by `slot_number` in merger
- Verify `display_order` field is used if present
- Check template rendering order

---

## 📋 Session Checklist

### Before Starting
- [ ] Review DAY5_SESSION_COMPLETE.md
- [ ] Understand current JSON structure (add logging)
- [ ] Examine template structure
- [ ] Review docx_renderer.py

### Investigation
- [ ] Log JSON structure for each slot
- [ ] Identify which days each slot covers
- [ ] Determine if template supports multi-slot
- [ ] Choose merging approach (A, B, or C)

### Implementation
- [ ] Create json_merger.py with merge function
- [ ] Update batch_processor.py to use merger
- [ ] Update renderer if needed
- [ ] Add validation for merged JSON

### Testing
- [ ] Test JSON merging with sample data
- [ ] Run full pipeline with 5 slots
- [ ] Verify all slots in output DOCX
- [ ] Verify all days in output DOCX
- [ ] Check formatting and layout

### Documentation
- [ ] Update this file with solution details
- [ ] Document any template changes
- [ ] Add comments to new code
- [ ] Create examples of merged JSON

---

## 🎯 Success Criteria

Session is complete when:
1. ✅ Generated DOCX contains all 5 slots
2. ✅ Generated DOCX contains all 5 days (Monday-Friday)
3. ✅ Slots are properly ordered by slot_number
4. ✅ No duplicate content
5. ✅ No missing content
6. ✅ Formatting preserved from template
7. ✅ Code is clean and well-documented

---

## 📚 Reference Files

### Key Files to Modify
- `tools/json_merger.py` (NEW - create this)
- `tools/batch_processor.py` (UPDATE - lines 175-236)
- `tools/docx_renderer.py` (MAYBE UPDATE - depends on template)

### Files to Review
- `schemas/lesson_output_schema.json` - JSON structure
- `input/Lesson Plan Template SY'25-26.docx` - Template layout
- `prompt_v4.md` - LLM prompt (to understand JSON format)

### Test Files
- `test_json_merger.py` (NEW - create for testing)
- `check_slots.py` (EXISTING - use for debugging)

---

## 💭 Think Hard About...

1. **JSON Structure**: 
   - Should each day have a `slots` array?
   - Or should we flatten it differently?
   - What's the most intuitive structure for the renderer?

2. **Template Design**:
   - Can the current template handle multiple slots per day?
   - Do we need to modify the template?
   - How should slots be visually separated?

3. **Edge Cases**:
   - What if a slot has no days? (teacher doesn't teach that week)
   - What if all slots teach on the same day? (5 slots on Monday)
   - What if slots have different metadata? (different grades)

4. **Performance**:
   - Is merging JSON fast enough?
   - Should we cache merged results?
   - Any memory concerns with large JSONs?

5. **Future Enhancements**:
   - Should we support custom slot ordering?
   - Should we allow filtering by day?
   - Should we support exporting individual slots?

---

## 🔄 Iterative Approach

If the first solution doesn't work perfectly:

### Iteration 1: Basic Merge
- Just get all slots into one DOCX
- Don't worry about formatting
- Focus on data completeness

### Iteration 2: Improve Layout
- Add visual separation between slots
- Ensure proper ordering
- Fix any formatting issues

### Iteration 3: Polish
- Add headers/footers
- Improve readability
- Add any missing metadata

---

**Remember**: The hard part (LLM transformation) is done! This is just a data structure and rendering issue. Take time to understand the problem before coding the solution.

**Good luck!** 🚀
