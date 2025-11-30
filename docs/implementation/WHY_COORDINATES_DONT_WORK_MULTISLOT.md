# Why Coordinate Placement Doesn't Work for Multi-Slot

## The Problem You Discovered

You asked: "Why can't we have each link from the input cell in the corresponding output cell?"

**Initial answer:** We can! Use coordinates!

**Reality:** Coordinates DON'T work for multi-slot. Here's why.

---

## The Fundamental Issue

### Single-Slot: Table Structure Preserved

**Input (Lang.docx):**
```
| Unit, Lesson #, Module | MONDAY              |
|------------------------|---------------------|
|                        | Unit 2 - Lesson 9   |
```

**Output (Wilson's doc):**
```
| Unit, Lesson #, Module | MONDAY              |
|------------------------|---------------------|
|                        | Unit 2 - Lesson 9   |
```

✅ **Same structure** → Coordinates work perfectly!

### Multi-Slot: Table Structure CHANGED

**Input File 1 (Lang.docx - Slot 1):**
```
| Unit, Lesson #, Module | MONDAY              |
|------------------------|---------------------|
|                        | Unit 2 - Lesson 9   |
```

**Input File 2 (Savoca.docx - Slot 2):**
```
| Unit, Lesson #, Module | MONDAY                         |
|------------------------|---------------------------------|
|                        | LESSON 9: MEASURE TO FIND AREA |
```

**Output (Combined):**
```
| Unit, Lesson #, Module | MONDAY                                    |
|------------------------|-------------------------------------------|
|                        | **Slot 1: ELA**                           |
|                        | Unit 2 - Lesson 9                         |
|                        | ---                                       |
|                        | **Slot 2: Math**                          |
|                        | LESSON 9: MEASURE TO FIND AREA            |
```

❌ **Different structure** → Coordinates DON'T work!

---

## What Happens with Coordinate Placement

### Step 1: Parser Extracts Coordinates

**From Lang.docx (Slot 1):**
```python
# No hyperlinks in ELA file
hyperlinks = []
```

**From Savoca.docx (Slot 2):**
```python
hyperlink = {
    'text': 'LESSON 9: MEASURE TO FIND AREA',
    'url': 'https://...',
    'row_idx': 2,    # "Unit, Lesson #, Module" row
    'cell_idx': 1,   # Monday column
}
```

### Step 2: Coordinate Placement Runs

```python
# Place hyperlink at coordinates from Savoca.docx
row = 2  # "Unit, Lesson #, Module" row
col = 1  # Monday column

# Insert hyperlink WITH ITS ORIGINAL TEXT
cell = table.rows[row].cells[col]
cell.add_hyperlink(text='LESSON 9: MEASURE TO FIND AREA', url='https://...')
```

### Step 3: Multi-Slot Rendering Runs

```python
# Combine all slots' content
combined_text = """**Slot 1: ELA**
Unit 2 - Lesson 9
---
**Slot 2: Math**
LESSON 9: MEASURE TO FIND AREA"""

# Check if cell has existing hyperlinks
if cell.has_hyperlinks():
    # APPEND combined text to preserve hyperlinks
    cell.append_text(combined_text)
```

### Step 4: Result

**Cell now contains:**
```
LESSON 9: MEASURE TO FIND AREA (hyperlink from coordinate placement)
**Slot 1: ELA**
Unit 2 - Lesson 9
---
**Slot 2: Math**
LESSON 9: MEASURE TO FIND AREA
```

**Problem:** The hyperlink text "LESSON 9: MEASURE TO FIND AREA" appears BEFORE the slot headers, making it look like it's part of Slot 1 (ELA)!

---

## Why This Happens

**Coordinate placement assumes:**
- Input cell (row=2, col=1) contains "LESSON 9..."
- Output cell (row=2, col=1) will contain "LESSON 9..."
- ✅ True for single-slot
- ❌ False for multi-slot

**Multi-slot reality:**
- Input cell (row=2, col=1) in Savoca.docx contains "LESSON 9..."
- Output cell (row=2, col=1) contains "Slot 1: ELA\nLesson 9\n---\nSlot 2: Math\nLESSON 9..."
- **Different content!**

When coordinate placement inserts the hyperlink with its original text, it's inserting Math content into a cell that will later contain BOTH ELA and Math content.

---

## The Solution

**For multi-slot: Disable inline hyperlink placement entirely.**

**Why:**
1. Coordinate placement doesn't work (table structure changed)
2. Semantic matching doesn't work (causes cross-contamination)
3. No reliable way to place hyperlinks inline without mixing slots

**Trade-off:**
- ❌ Multi-slot hyperlinks at end of document (less convenient)
- ✅ No cross-contamination (safe)
- ✅ Single-slot still has inline hyperlinks (works perfectly)

---

## Alternative: Refactor Multi-Slot Rendering

**To get inline hyperlinks for multi-slot, we'd need to:**

1. **Don't combine slots' content first**
2. **Fill each slot separately** with its own hyperlinks
3. **Append to cells** instead of replacing

**Pseudo-code:**
```python
# Clear cell
cell.text = ""

# Fill each slot separately
for slot in slots:
    # Filter hyperlinks for THIS slot only
    slot_hyperlinks = [h for h in all_hyperlinks if h['_source_slot'] == slot.number]
    
    # Add slot header
    cell.add_paragraph(f"**Slot {slot.number}: {slot.subject}**")
    
    # Add slot content with its hyperlinks
    add_content_with_hyperlinks(cell, slot.content, slot_hyperlinks)
    
    # Add separator if not last slot
    if not last_slot:
        cell.add_paragraph("---")
```

**Estimated effort:** 6-8 hours
**Risk:** Medium (major refactoring)

---

## Current Status

**Reverted to:** Disable inline placement for multi-slot

**Files:**
- `tools/docx_renderer.py` line 134: `and not is_multi_slot` (coordinate placement disabled)
- `tools/docx_renderer.py` line 609: `multi_slot_hyperlinks = None` (inline placement disabled)

**Result:**
- ✅ Single-slot: Hyperlinks inline
- ❌ Multi-slot: Hyperlinks at end ("Referenced Links" section)
- ✅ No cross-contamination

---

## Summary

**Your question was excellent** - it made us realize coordinate placement SHOULD work. But after implementation and testing, we discovered the fundamental issue: **multi-slot changes the table structure**, so coordinates from the input files don't map correctly to the output file.

**The only way to get inline hyperlinks for multi-slot** is to refactor the rendering to fill each slot separately, which is a significant architectural change.

**For now:** Multi-slot hyperlinks go to "Referenced Links" section at end of document.
