# File Pattern Analysis - Real Data

## Actual Files Found in `F:\rodri\Documents\OneDrive\AS\Lesson Plan`

### Week Folders Structure ✅
```
25 W37/  (Week 37, 2025)
25 W38/  (Week 38, 2025)
25 W39/  (Week 39, 2025)
25 W40/  (Week 40, 2025)
25 W41/  (Week 41, 2025 - Current)
Code/    (Not a week folder)
```

---

## Primary Teacher File Patterns

### Week 41 (Current - 10/6-10/10)

**Primary Teachers Identified:**

1. **Davies** (Math/General)
   - `10_6-10_10 Davies Lesson Plans.docx`
   - Pattern: `{dates} Davies Lesson Plans.docx`

2. **Lang** (ELA/Language Arts)
   - `Lang Lesson Plans 10_6_25-10_10_25.docx`
   - Pattern: `Lang Lesson Plans {dates}.docx`

3. **Ms. Savoca** (Science/Social Studies)
   - `Ms. Savoca-10_6_25-10_10_25 Lesson plans.docx`
   - Pattern: `Ms. Savoca-{dates} Lesson plans.docx`

### Week 40 (9/29-10/3)

**Primary Teachers:**
1. **Davies**: `9_29-10_3 Davies Lesson Plans.docx`
2. **Lang**: `Lang Lesson Plans 9_29_25-10_3_25.docx`
3. **Ms. Savoca**: `Ms. Savoca- 9_29_25-10_3_25 Lesson plans.docx`

### Week 39 (9/22-9/26)

**Primary Teachers:**
1. **Davies**: `9_22-9_26 Davies Lesson Plans.docx`
2. **Lang**: `Lang Lesson Plans 9_22_25-9_26_25.docx`
3. **Ms. Savoca**: `Ms. Savoca- 922_24-9_26_24 Lesson plans.docx`

### Week 38 (9/15-9/19)

**Primary Teachers:**
1. **Davies**: `9_15-9_19 Davies Lesson Plans.docx`
2. **Lang**: `Lang Lesson Plans 9_15_25-9_19_25.docx`
3. **Ms. Savoca**: `Ms. Savoca- 9_15_24-9_19_24 Lesson plans.docx`

### Week 37 (9/8-9/12)

**Primary Teachers:**
1. **Lang**: `Copy of Lang Lesson Plans 9_8_25-9_12_25.docx`
2. **Ms. Savoca**: `Copy of Ms. Savoca- 9_8_24-9_12_24 Lesson plans.docx`
3. **Generic**: `math primary teacher lesson plan.docx`
4. **Generic**: `science second grade primary lesson plan.docx`
5. **Generic**: `_2nd Grade Science .docx`

---

## Output Files (Your Generated Plans)

**Pattern:** `Rodrigues Lesson Plans {dates}.docx`

Examples:
- `Rodrigues Lesson Plans 9_8_25-9_12_25.docx` (W37)
- `Rodrigues Lesson plans W38 9_15-9_19.docx` (W38)
- `Rodrigues Lesson Plans 9_22_25 ____ 9_26_25.docx` (W39)
- `Rodrigues Lesson Plans 09_29_25 __ 10_03_25.docx` (W40)

**Note:** Inconsistent date separators (`-`, `____`, `__`)

---

## File Naming Patterns Analysis

### Primary Teacher Name Patterns

| Teacher | Pattern | Examples |
|---------|---------|----------|
| **Davies** | `{dates} Davies Lesson Plans.docx` | `10_6-10_10 Davies Lesson Plans.docx` |
| **Lang** | `Lang Lesson Plans {dates}.docx` | `Lang Lesson Plans 10_6_25-10_10_25.docx` |
| **Savoca** | `Ms. Savoca-{dates} Lesson plans.docx` | `Ms. Savoca-10_6_25-10_10_25 Lesson plans.docx` |

### Key Observations

1. **Teacher Name Position:**
   - Davies: Middle of filename
   - Lang: Beginning of filename
   - Savoca: Beginning with "Ms." prefix

2. **Date Formats:**
   - `10_6-10_10` (short)
   - `10_6_25-10_10_25` (with year)
   - `922_24-9_26_24` (typo: missing underscore)

3. **Case Sensitivity:**
   - "Lesson Plans" vs "Lesson plans" (inconsistent capitalization)

4. **Special Characters:**
   - Hyphens: `-`
   - Underscores: `_`
   - Spaces

---

## Matching Strategy

### Current Implementation Issues

**Problem:** Simple `teacher_pattern.lower() in file.name.lower()` won't work well because:
- "Davies" appears in middle of filename
- "Lang" is too short (might match "Language")
- "Savoca" has "Ms." prefix

### Improved Matching Strategy

```python
def find_primary_teacher_file(week_folder, teacher_pattern, subject=None):
    """
    Enhanced file matching with multiple strategies.
    """
    # Strategy 1: Exact teacher name match (case-insensitive)
    # Strategy 2: Teacher name with common prefixes (Ms., Mr., Mrs.)
    # Strategy 3: Subject-based matching
    # Strategy 4: Fuzzy matching with score
    
    patterns_to_try = [
        teacher_pattern,                    # "Davies"
        f"Ms. {teacher_pattern}",          # "Ms. Davies"
        f"Mr. {teacher_pattern}",          # "Mr. Davies"
        f"Mrs. {teacher_pattern}",         # "Mrs. Davies"
        f"{teacher_pattern} Lesson",       # "Davies Lesson"
    ]
    
    for file in week_folder.glob("*.docx"):
        filename_lower = file.name.lower()
        
        # Skip temp and output files
        if filename_lower.startswith('~') or 'rodrigues' in filename_lower:
            continue
        
        # Try each pattern
        for pattern in patterns_to_try:
            if pattern.lower() in filename_lower:
                # If subject specified, prefer files with subject
                if subject and subject.lower() in filename_lower:
                    return str(file)
                # Store as candidate
                candidate = file
        
        if candidate:
            return str(candidate)
    
    return None
```

---

## Recommended Slot Configuration

### For Your Setup

Based on the files, here's how to configure slots:

**Slot 1: Math (Davies)**
- `primary_teacher_name`: "Davies"
- `subject`: "Math"
- Matches: `10_6-10_10 Davies Lesson Plans.docx`

**Slot 2: ELA (Lang)**
- `primary_teacher_name`: "Lang"
- `subject`: "ELA"
- Matches: `Lang Lesson Plans 10_6_25-10_10_25.docx`

**Slot 3: Science (Savoca)**
- `primary_teacher_name`: "Savoca"
- `subject`: "Science"
- Matches: `Ms. Savoca-10_6_25-10_10_25 Lesson plans.docx`

**Slot 4: Social Studies (Savoca)**
- `primary_teacher_name`: "Savoca"
- `subject`: "Social Studies"
- Matches: `Ms. Savoca-10_6_25-10_10_25 Lesson plans.docx` (same file, different subject)

---

## Files to Exclude

### Patterns to Skip

1. **Temporary Files:**
   - Starts with `~` (Word temp files)

2. **Output Files:**
   - Contains "Rodrigues" (your output)
   - Contains "OLD" prefix

3. **Templates:**
   - "Lesson Plan Template"
   - "Template SY'25-26"

4. **Copies:**
   - Starts with "Copy of"

### Updated Exclusion Logic

```python
def should_skip_file(filename):
    """Check if file should be skipped."""
    filename_lower = filename.lower()
    
    skip_patterns = [
        '~',                    # Temp files
        'rodrigues',           # Your output
        'old ',                # Old versions
        'template',            # Templates
        'copy of',             # Copies
        'lesson plan template' # Templates
    ]
    
    for pattern in skip_patterns:
        if pattern in filename_lower:
            return True
    
    return False
```

---

## Output File Naming

### Current Issues
- Inconsistent date separators
- Sometimes includes week number, sometimes doesn't

### Recommended Format
```
Rodrigues_Lesson_plan_W{##}_{MM-DD-MM-DD}.docx
```

Examples:
- `Rodrigues_Lesson_plan_W41_10-06-10-10.docx`
- `Rodrigues_Lesson_plan_W42_10-13-10-17.docx`

**Benefits:**
- Consistent format
- Easy to sort
- Week number visible
- No special characters issues

---

## Implementation Updates Needed

### 1. Enhanced File Finder

```python
def find_primary_teacher_file(week_folder, teacher_pattern, subject=None):
    """Enhanced matching with real-world patterns."""
    
    if not week_folder.exists():
        return None
    
    candidates = []
    
    for file in week_folder.glob("*.docx"):
        # Skip excluded files
        if should_skip_file(file.name):
            continue
        
        filename_lower = file.name.lower()
        teacher_lower = teacher_pattern.lower()
        
        # Check if teacher name is in filename
        if teacher_lower in filename_lower:
            score = 0
            
            # Bonus points for subject match
            if subject and subject.lower() in filename_lower:
                score += 10
            
            # Bonus for exact teacher name match (not substring)
            if f" {teacher_lower} " in f" {filename_lower} ":
                score += 5
            
            candidates.append((score, file))
    
    # Return highest scoring match
    if candidates:
        candidates.sort(reverse=True, key=lambda x: x[0])
        return str(candidates[0][1])
    
    return None
```

### 2. Better Output Naming

```python
def get_output_path(week_folder, user_name, week_of):
    """Generate consistent output filename."""
    week_num = calculate_week_number(week_of)
    
    # Parse dates from week_of (MM/DD-MM/DD)
    dates = week_of.replace('/', '-')
    
    # Clean user name (remove spaces, special chars)
    clean_name = user_name.replace(' ', '_')
    
    filename = f"{clean_name}_Lesson_plan_W{week_num:02d}_{dates}.docx"
    
    week_folder.mkdir(parents=True, exist_ok=True)
    return str(week_folder / filename)
```

---

## Testing Checklist

### Test Cases

- [ ] Find "Davies" → Matches `10_6-10_10 Davies Lesson Plans.docx`
- [ ] Find "Lang" → Matches `Lang Lesson Plans 10_6_25-10_10_25.docx`
- [ ] Find "Savoca" → Matches `Ms. Savoca-10_6_25-10_10_25 Lesson plans.docx`
- [ ] Skip temp files (starting with `~`)
- [ ] Skip output files (containing "Rodrigues")
- [ ] Skip templates
- [ ] Handle missing files gracefully
- [ ] Subject matching works correctly

---

## Next Steps

1. ✅ Analyzed real file patterns
2. ⏳ Update `file_manager.py` with enhanced matching
3. ⏳ Add exclusion logic for temp/output files
4. ⏳ Test with real Week 41 files
5. ⏳ Verify output naming consistency

---

**Status:** Pattern analysis complete, ready to implement enhanced matching logic
