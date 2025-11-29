# Session 10: Hyperlink Placement Strategy - Validation Framework

## 🎯 Purpose
Before implementing the "keep links in cells" strategy, we need to validate assumptions and answer critical questions raised by the other AI.

---

## 📊 Questions Requiring Data Validation

### **Q1: Fallback Mapping - How to prevent conflicts?**

**Question:** When both "Unit/Lesson" and a potential "Resources" row could contain curriculum links, which wins?

**Data needed:**
- Analyze where curriculum links ("LESSON X", "Teacher Guide") appear in INPUT files
- Are they in Unit/Lesson row? Instruction row? Both?
- What percentage appear in each location?

**Validation script:**
```python
# Analyze input files to see WHERE curriculum links actually appear
for link in curriculum_links:
    original_row = link['table_row_index']
    original_section = infer_section_from_row(original_row)
    print(f"{link['text']} → Row {original_row} ({original_section})")
```

**Decision criteria:**
- If >80% in one row type → Use that as default
- If mixed → Need deterministic rule (e.g., "Unit/Lesson" wins)

---

### **Q2: Overflow Policy - What happens with 8+ links?**

**Question:** When a cell has too many links, where do extras go?

**Data needed:**
- Distribution of links per cell (current data)
- Maximum observed links in a single cell
- Teacher feedback on acceptable link count

**Current data from diagnostic:**
- "Capture Squares": 8 occurrences
- "Stage 6": 7 occurrences
- Some cells could have 10+ links

**Options:**
1. **No limit** - Keep all in cell (risk: clutter)
2. **Limit 5-6** - Overflow to "Resources" row
3. **Limit 3** - Show "...and X more" with link to Resources
4. **Collapsible** - Show first 3, expand for more

**Recommendation:** Start with Option 2 (limit 5-6), measure in practice

---

### **Q3: Grouping Heuristics - How effective are they?**

**Question:** Can we reliably classify links as "Curriculum," "Activity," or "Assessment"?

**Test on real data:**
```python
def classify_link(link_text):
    text_upper = link_text.upper()
    
    # Curriculum
    if any(x in text_upper for x in ['LESSON', 'UNIT', 'TEACHER GUIDE']):
        return 'Curriculum'
    
    # Activity
    if 'ACTIVITY' in text_upper:
        return 'Activity'
    
    # Assessment
    if any(x in text_upper for x in ['ASSESSMENT', 'TEST', 'QUIZ']):
        return 'Assessment'
    
    return 'Other'

# Test on our 294 links
for link in all_links:
    category = classify_link(link['text'])
    print(f"{link['text'][:40]} → {category}")
```

**Validation:**
- Run on all 294 links from metadata audit
- Measure: % correctly classified, % "Other"
- Adjust patterns based on results

---

### **Q4: Template Variability - Same structure across files?**

**Question:** Do all teachers use the same template structure?

**Data needed:**
- Analyze table structure across multiple input files
- Check row labels, column count, row count
- Identify variations

**Validation:**
```python
def analyze_template_structure(docx_file):
    doc = Document(docx_file)
    table = doc.tables[0]
    
    return {
        'rows': len(table.rows),
        'columns': len(table.columns),
        'row_labels': [table.rows[i].cells[0].text for i in range(len(table.rows))]
    }

# Compare across files
for file in input_files:
    structure = analyze_template_structure(file)
    print(f"{file.name}: {structure}")
```

**Decision:**
- If all identical → Hardcode mapping
- If variations exist → Need dynamic detection

---

### **Q5: User Acceptance - Do teachers want this?**

**Question:** Have teachers requested links at end of cells?

**Current state:**
- No direct teacher feedback yet
- Assumption based on UX principles

**Validation needed:**
1. **Survey teachers:**
   - "Where would you prefer hyperlinks?"
   - A) Inline in text (current goal)
   - B) At end of cell under "Links:"
   - C) At end of document (current fallback)

2. **Show mockups:**
   - Example cell with inline links
   - Example cell with links at end
   - Example with "Referenced Links" section

3. **A/B test:**
   - Generate 2 versions of same lesson plan
   - Ask which is more usable

**Until we have feedback:** Implement as configurable option

---

## ⚠️ Addressing Weaknesses

### **Weakness 1: Hint quality (29% missing)**

**Mitigation:**
```python
# Three-tier approach with confidence scoring
def place_link_with_confidence(link):
    if link.has_section_hint():
        return place_by_hint(link), confidence=1.0
    
    inferred_section = infer_from_text(link)
    if inferred_section:
        return place_by_inference(link), confidence=0.7
    
    # Last resort: Resources row
    return place_in_resources(link), confidence=0.3

# Log confidence for monitoring
logger.info("link_placement", extra={
    "text": link['text'],
    "strategy": strategy,
    "confidence": confidence
})
```

**Validation:** Run on test data, measure accuracy of inference

---

### **Weakness 2: Cell clutter (8-10 links)**

**Mitigation:**
```python
MAX_LINKS_PER_CELL = 6

def add_links_to_cell(cell, links):
    if len(links) <= MAX_LINKS_PER_CELL:
        # Add all
        add_links_section(cell, links)
    else:
        # Add first 5, overflow rest
        add_links_section(cell, links[:5])
        overflow_links.extend(links[5:])
        
        # Add note
        note = cell.add_paragraph()
        note.add_run(f"...and {len(links)-5} more (see Resources)")
        note.runs[0].font.size = Pt(8)
```

**Validation:** Test with real cells that have 8+ links

---

### **Weakness 3: Inconsistent grouping**

**Solution:** Use explicit rules, not fuzzy matching

```python
GROUPING_RULES = {
    'Curriculum': [
        r'LESSON \d+',
        r'UNIT \d+',
        r'Teacher Guide',
        r'Curriculum'
    ],
    'Activities': [
        r'activity',
        r'worksheet',
        r'practice'
    ],
    'Assessments': [
        r'assessment',
        r'test',
        r'quiz',
        r'evaluation'
    ]
}

def classify_link_strict(link_text):
    for category, patterns in GROUPING_RULES.items():
        for pattern in patterns:
            if re.search(pattern, link_text, re.IGNORECASE):
                return category
    return 'Resources'  # Default
```

**Validation:** Test on all 294 links, measure classification accuracy

---

### **Weakness 4: Template assumptions**

**Solution:** Dynamic template detection

```python
def detect_template_structure(doc):
    """Detect template structure dynamically."""
    table = doc.tables[0]
    
    # Analyze row labels
    row_mapping = {}
    for i, row in enumerate(table.rows):
        label = row.cells[0].text.lower()
        
        if 'unit' in label or 'lesson' in label:
            row_mapping['unit_lesson'] = i
        elif 'objective' in label:
            row_mapping['objective'] = i
        elif 'instruction' in label:
            row_mapping['instruction'] = i
        # etc.
    
    return row_mapping

# Use detected mapping instead of hardcoded
ROW_MAPPING = detect_template_structure(output_doc)
```

**Validation:** Test on files from different teachers/weeks

---

### **Weakness 5: Inline context loss**

**Solution:** ALWAYS try inline first!

```python
def place_hyperlinks_hybrid(cell, text, links):
    """Try inline first, fall back to end."""
    
    # Step 1: Inline placement (preserves context)
    inline_placed = []
    for link in links:
        if link['text'] in text:
            inject_inline(cell, link, text)
            inline_placed.append(link)
    
    # Step 2: End of cell (for non-matches)
    remaining = [l for l in links if l not in inline_placed]
    if remaining:
        add_links_section(cell, remaining)
    
    # Log results
    logger.info("placement_results", extra={
        "inline": len(inline_placed),
        "end_of_cell": len(remaining),
        "total": len(links)
    })
```

**This preserves inline context when possible!**

---

### **Weakness 6: No fallback for true mismatches**

**Solution:** Keep "Referenced Links" as last resort

```python
# After all cells filled:
if pending_hyperlinks:  # Still have unplaced links?
    # These are truly unplaceable (bad metadata, unknown template)
    _append_unmatched_media(doc, pending_hyperlinks, pending_images)
    
    logger.warning("links_in_fallback_section", extra={
        "count": len(pending_hyperlinks),
        "links": [l['text'] for l in pending_hyperlinks]
    })
```

**This ensures 100% preservation, even for edge cases**

---

## 🎯 Validation Plan

### **Phase 1: Data Analysis (2 hours)**

1. ✅ Run metadata audit (DONE - 294 links analyzed)
2. ⏳ Analyze template structure across files
3. ⏳ Test grouping heuristics on real data
4. ⏳ Measure links-per-cell distribution
5. ⏳ Identify where curriculum links appear in input

### **Phase 2: Teacher Feedback (1 week)**

1. Create mockups of 3 approaches:
   - Inline only (current goal)
   - Inline + end-of-cell (proposed)
   - End-of-document (current fallback)

2. Survey 3-5 teachers:
   - Which is most usable?
   - How many links per cell is too many?
   - Prefer grouped or flat list?

3. Collect feedback on actual outputs

### **Phase 3: Prototype & Test (3 hours)**

1. Implement hybrid approach (inline + end-of-cell)
2. Add telemetry (log placement strategy per link)
3. Test on 10 real lesson plans
4. Measure:
   - % inline
   - % end-of-cell
   - % in Resources row
   - % in Referenced Links (fallback)

### **Phase 4: Iterate (2 hours)**

1. Analyze telemetry data
2. Adjust thresholds (MAX_LINKS_PER_CELL, etc.)
3. Refine grouping rules
4. Fix edge cases

---

## 📊 Success Criteria

**Before implementation:**
- ✅ Template structure validated across 5+ files
- ✅ Grouping heuristics tested on 294 links (>80% accuracy)
- ✅ Teacher feedback collected (3+ teachers)
- ✅ Mockups approved

**After implementation:**
- ✅ >90% of links in table cells (not end-of-document)
- ✅ <10% in "Referenced Links" fallback
- ✅ Average <5 links per cell
- ✅ Teacher satisfaction >4/5

---

## 🚫 What NOT to Do

1. ❌ **Don't implement without teacher feedback**
2. ❌ **Don't hardcode template structure without validation**
3. ❌ **Don't remove "Referenced Links" fallback entirely**
4. ❌ **Don't assume grouping works without testing**
5. ❌ **Don't skip telemetry (we need data!)**

---

## ✅ Recommended Next Steps

1. **Run validation scripts** (template structure, grouping test)
2. **Create mockups** for teacher feedback
3. **Implement as configurable option** (can toggle on/off)
4. **Add comprehensive telemetry**
5. **Test on 10 real files**
6. **Collect teacher feedback**
7. **Iterate based on data**

---

## 🎯 Decision Points

**The other AI is right to push for validation. We should:**

1. **Pause implementation** until we have:
   - Template structure validation
   - Grouping heuristic testing
   - Teacher feedback

2. **Create validation scripts** to answer open questions

3. **Build mockups** for user testing

4. **Implement as experiment** with telemetry

5. **Make data-driven decisions** based on results

---

**Want me to create the validation scripts to answer these questions with real data?**
