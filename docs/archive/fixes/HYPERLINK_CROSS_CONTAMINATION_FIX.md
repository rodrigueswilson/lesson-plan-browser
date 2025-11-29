# Hyperlink Cross-Contamination Fix

## Problem

Hyperlinks from one slot (Math) are appearing in another slot's output (ELA).

**Root Cause:** The semantic hyperlink matcher is finding false matches across different slots during document merging.

## Example

**Slot 1 (ELA):**
- Input: "Unit 2- Maps and Globes Lesson 9" (no hyperlinks)
- Output: Should have NO hyperlinks

**Slot 2 (Math):**
- Input: "LESSON 9: MEASURE TO FIND THE AREA" (with hyperlink)
- Output: Should have this hyperlink

**Bug:** The Math hyperlink "LESSON 9" matches the ELA text "Lesson 9" with high confidence, so it gets placed in the ELA output.

## Solution Options

### Option 1: Disable Semantic Matching for Unit/Lesson Row

The "Unit, Lesson #, Module" row should NEVER have hyperlinks placed inline. It's metadata, not content.

```python
# In docx_renderer.py - _restore_hyperlinks()
def _should_skip_paragraph(self, paragraph):
    """Check if paragraph is metadata that shouldn't have hyperlinks"""
    text = paragraph.text.strip().lower()
    
    # Skip metadata rows
    if any(keyword in text for keyword in [
        'unit, lesson',
        'lesson 3 day',
        'unit 2- maps',
    ]):
        return True
    
    return False

def _restore_hyperlinks(self, doc, hyperlinks):
    for link in hyperlinks:
        for paragraph in doc.paragraphs:
            if self._should_skip_paragraph(paragraph):
                continue  # Skip metadata paragraphs
            
            # Try to place hyperlink
            ...
```

### Option 2: Stricter Context Matching

Only place hyperlinks if the FULL context matches, not just the link text.

```python
# In docx_renderer.py
def _calculate_match_confidence(self, link_text, link_context, target_text, target_context):
    # Current: Only matches link_text
    # Fix: Also require context to match
    
    text_score = fuzzy_match(link_text, target_text)
    context_score = fuzzy_match(link_context, target_context)
    
    # Both must match well
    if text_score > 0.8 and context_score > 0.6:
        return (text_score + context_score) / 2
    else:
        return 0  # No match
```

### Option 3: Subject-Based Filtering

Tag hyperlinks with their source subject and only place them in matching subjects.

```python
# In batch_processor.py - when extracting hyperlinks
hyperlinks = parser.extract_hyperlinks()
for link in hyperlinks:
    link['source_subject'] = slot['subject']  # 'ELA' or 'Math'

# In docx_renderer.py - when placing hyperlinks
def _restore_hyperlinks(self, doc, hyperlinks, current_subject):
    for link in hyperlinks:
        # Only place if subjects match
        if link.get('source_subject') != current_subject:
            continue  # Skip cross-subject links
        
        # Try to place hyperlink
        ...
```

### Option 4: Disable Cross-Slot Matching (Safest)

Each slot's hyperlinks should ONLY be placed in that slot's content, never in other slots.

```python
# In batch_processor.py - multi-slot rendering
for i, lesson_json in enumerate(lessons):
    temp_path = str(temp_dir / f"slot_{i+1}.docx")
    
    # Render with ONLY this slot's hyperlinks
    slot_hyperlinks = lesson_json.get('_hyperlinks', [])
    
    # Clear any global hyperlink state
    renderer.clear_hyperlink_cache()
    
    # Render this slot in isolation
    renderer.render(lesson_json, temp_path)
    temp_files.append(temp_path)

# After merging, DO NOT try to place more hyperlinks
# Each slot already has its hyperlinks placed
```

## Recommended Fix

**Combination of Option 1 + Option 4:**

1. **Skip metadata rows** - Never place hyperlinks in "Unit, Lesson #, Module" row
2. **Isolate per slot** - Each slot's hyperlinks are placed during that slot's rendering, not during merge

This ensures:
- ✅ No cross-contamination between slots
- ✅ Metadata rows stay clean
- ✅ Hyperlinks only appear in their original context

## Implementation

See `HYPERLINK_ISOLATION_FIX.py` for the actual code changes.
