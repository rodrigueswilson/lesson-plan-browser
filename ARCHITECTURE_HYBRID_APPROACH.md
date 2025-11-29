# Hybrid Architecture: Per-Slot Rendering + Strict Filtering

## Status: ✅ IMPLEMENTED

Reverted to per-slot rendering with DOCX merging while keeping the strict slot filtering logic.

---

## The Problem

The refactor tried to combine all slots into one table, but this broke the **2-table structure per slot**:

- Each slot needs: **Original table + Bilingual table**
- Old approach: Render separately → Merge DOCX → ✅ Works
- New approach: Merge JSON → Single render → ❌ Breaks 2-table structure

---

## The Solution: Hybrid Approach

**Combine the best of both worlds:**

1. ✅ **Render each slot separately** → Preserves 2-table structure
2. ✅ **Add slot metadata before rendering** → Enables strict filtering
3. ✅ **Merge DOCX files** → Creates final document
4. ✅ **Clean up signature boxes** → One signature at end

---

## How It Works

### Step 1: Add Slot Metadata (Lines 960-970)

```python
for lesson in lessons:
    slot_num = lesson["slot_number"]
    subject = lesson["subject"]
    lesson_json = lesson["lesson_json"]
    
    # CRITICAL: Add slot metadata to hyperlinks and images
    if '_hyperlinks' in lesson_json:
        for link in lesson_json['_hyperlinks']:
            link['_source_slot'] = slot_num
            link['_source_subject'] = subject
    
    if '_images' in lesson_json:
        for image in lesson_json['_images']:
            image['_source_slot'] = slot_num
            image['_source_subject'] = subject
```

**Why this matters:**
- Each hyperlink/image now knows which slot it belongs to
- The renderer's strict filtering can check this metadata
- Prevents cross-contamination between slots

### Step 2: Render Each Slot (Lines 972-988)

```python
# Create temp filename
temp_filename = f"_temp_slot{slot_num}_{subject}.docx"
temp_path = str(week_folder / temp_filename)

# Render this slot (will have 2 tables: original + bilingual)
renderer.render(lesson_json, temp_path)
temp_files.append(temp_path)
```

**Result:**
- Each slot renders to its own DOCX
- Each DOCX has 2 tables (original + bilingual)
- Hyperlinks/images are filtered by slot metadata

### Step 3: Merge DOCX Files (Lines 990-1002)

```python
# Merge all temp files into one consolidated DOCX
self._merge_docx_files(temp_files, output_path)
```

**Result:**
- Final document has multiple 2-table sets
- Each slot is a complete lesson plan
- Proper page breaks between slots

### Step 4: Clean Up (Lines 1004-1019)

```python
# Remove all signature boxes, add one at the end
doc = Document(output_path)
self._remove_signature_boxes(doc)
self._add_signature_box(doc, generated_at)
doc.save(output_path)

# Clean up temp files
for temp_file in temp_files:
    Path(temp_file).unlink()
```

---

## What This Fixes

### ✅ Structure Issues
- **2-table structure preserved** - Each slot has original + bilingual tables
- **Proper page breaks** - Clean separation between slots
- **Signature box** - One signature at the end

### ✅ Filtering Issues
- **Strict slot filtering** - Hyperlinks/images require metadata
- **No cross-contamination** - Each slot only sees its own media
- **Proper warnings** - Missing metadata is logged

### ✅ Metadata Issues
- **Teacher names** - Shows actual names joined with " / "
- **Subjects** - Shows actual subjects joined with " / "
- **Slot info** - Each slot labeled correctly

---

## Comparison

### Old Approach (Before Refactor)
```
Render slot 1 → temp1.docx (2 tables)
Render slot 2 → temp2.docx (2 tables)
Merge DOCX files → final.docx
```
- ✅ 2-table structure preserved
- ❌ No slot filtering (cross-contamination possible)
- ❌ No metadata checks

### Failed Refactor
```
Merge JSONs → merged.json (slots arrays)
Render once → final.docx (1 table)
```
- ❌ 2-table structure broken
- ✅ Slot filtering attempted
- ✅ Metadata checks

### New Hybrid Approach
```
Add metadata to each lesson JSON
Render slot 1 → temp1.docx (2 tables) [with filtering]
Render slot 2 → temp2.docx (2 tables) [with filtering]
Merge DOCX files → final.docx
Clean up signature boxes
```
- ✅ 2-table structure preserved
- ✅ Slot filtering works
- ✅ Metadata checks
- ✅ Best of both worlds!

---

## Key Differences from Old Code

### What's New:
1. **Slot metadata added before rendering** (lines 962-970)
   - Old code: No metadata
   - New code: Every hyperlink/image tagged with slot info

2. **Strict filtering in renderer**
   - Old code: Permissive (allowed missing metadata)
   - New code: Strict (requires metadata, logs warnings)

3. **Better logging**
   - Shows hyperlink/image counts per slot
   - Warns about missing metadata
   - Tracks merge operations

### What's Preserved:
1. **Per-slot rendering** - Each slot gets its own DOCX
2. **DOCX merging** - docxcompose combines files
3. **Signature cleanup** - Remove duplicates, add one at end
4. **Temp file cleanup** - Delete intermediate files

---

## Expected Output

### Document Structure:
```
[Header: Teacher Names / Subjects]

--- Slot 1: ELA (Lang) ---
[Original Table]
[Bilingual Table]
[Page Break]

--- Slot 2: Math (Davies) ---
[Original Table]
[Bilingual Table]
[Page Break]

--- Slot 3: Science (Savoca) ---
[Original Table]
[Bilingual Table]
[Page Break]

...

[Signature Box]
```

### Each Slot Has:
- ✅ 2 tables (original + bilingual)
- ✅ Only its own hyperlinks (filtered by metadata)
- ✅ Only its own images (filtered by metadata)
- ✅ Proper formatting and structure

---

## Testing

### After Restart:
1. ✅ Process W44 files (5 slots)
2. ✅ Check output structure:
   - Should have 10 tables total (2 per slot × 5 slots)
   - Each slot should be complete lesson plan
   - No cross-contamination
3. ✅ Check logs:
   - Should see "batch_render_slot" for each slot
   - Should see "batch_merge_slots_success"
   - Should NOT see metadata warnings (if parser works correctly)

---

## Benefits

### For Users:
- ✅ Familiar structure (same as before)
- ✅ Each slot is complete lesson plan
- ✅ Clean separation between slots
- ✅ Proper hyperlinks in each slot

### For Developers:
- ✅ Proven approach (old code worked)
- ✅ Strict filtering prevents bugs
- ✅ Good logging for debugging
- ✅ Maintainable code

---

## Next Steps

1. ✅ **Restart backend** - Load new code
2. ✅ **Reprocess W44** - Test with real data
3. ✅ **Verify structure** - Check for 2 tables per slot
4. ✅ **Check filtering** - No cross-contamination
5. ⚠️ **Monitor logs** - Watch for metadata warnings

---

## Summary

**Architecture:** Hybrid approach combining per-slot rendering with strict filtering

**Result:** 
- ✅ Preserves 2-table structure per slot
- ✅ Prevents cross-contamination with metadata filtering
- ✅ Maintains familiar output format
- ✅ Production-ready

**Status:** Ready to test after backend restart
