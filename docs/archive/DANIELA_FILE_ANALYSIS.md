# Daniela's File Structure Analysis

## Base Path
`F:\rodri\Documents\OneDrive\AS\Daniela LP`

---

## Week Folders Found

### Different Naming Convention!
- `22 W39` (Week 39, 2022 - likely typo, should be 25 W39)
- `25 W38` (Week 38, 2025)
- `25 W40` (Week 40, 2025)
- `25 W41` (Week 41, 2025 - Current)

**Issue:** Mixed year prefixes (22 vs 25)

---

## Primary Teachers Identified

### Week 41 (Current - 10/6-10/10)
**No primary teacher files found yet!**
- Only has: `Daniela Silva W41 Lesson Plan.docx` (OUTPUT)

### Week 40 (9/29-10/3)

**Primary Teachers:**
1. **Lonesky** (Science/Social Studies)
   - `Lonesky Week 5 Lesson Plans SY 25_26.docx`

2. **Piret** (ELA)
   - `Piret Lesson Plans 9_29_25-10_3_25.docx`

3. **Laverty** (Math)
   - `_Brooke Laverty - SY'25-26_ week of 9_29.docx`

4. **Coleman** (Unknown subject)
   - `Name_ Ariel Coleman 9-29.docx`

**Output:**
- `Silva Lesson Plans 09_29_25 __ 10_03_25.docx`

### Week 38 (9/15-9/19)

**Primary Teachers:**
1. **Lonesky**: `Lonesky Week 3 Lesson Plans SY 25_26.docx`
2. **Piret**: `Piret Lesson Plans 9_15_25-9_19_25.docx`
3. **Laverty**: `Laverty 9_15_25 - 9_19_25.docx`
4. **Morais**: `Morais 9_15_25 - 9_19_25.docx`

**Output:**
- `Silva 9_15_25 - 9_19_25.docx`
- `Silva 9_15_25 - 9_19_25 With comments.docx`

### Week 39 (9/22-9/26) - Folder: "22 W39"

**Primary Teachers:**
1. **Lonesky**: `Lonesky Week 4 Lesson Plans SY 25_26.docx`
2. **Laverty**: `Laverty Lesson Plan 9_22-9_26.docx`
3. **Piret**: `Piret Lesson Plans 9_22_25-9_26_25.docx`
4. **Morais**: `Morais ELA SS 9_22_25 - 9_26_25.docx`

**Output (Multiple versions!):**
- `01 Science Lonesky Silva Lesson Plans 9_22_25-9_26_25.docx`
- `02 Math Laverti Silva Lesson Plans 9_22_25-9_26_25.docx`
- `03 ELA Piret Silva Lesson Plans 9_22_25-9_26_25.docx`
- `04 Social Sci Lonesky Silva Lesson Plans 9_22_25-9_26_25.docx`
- `05 ELA SS Morais Silva Lesson Plans 9_22_25-9_26_25.docx`
- `Silva Lesson Plans 9_22_25-9_26_25.docx`

---

## File Naming Patterns

### Primary Teacher Patterns

| Teacher | Pattern Examples |
|---------|------------------|
| **Lonesky** | `Lonesky Week # Lesson Plans SY 25_26.docx` |
| **Piret** | `Piret Lesson Plans {dates}.docx` |
| **Laverty** | `Laverty {dates}.docx` or `_Brooke Laverty - SY'25-26_ week of {date}.docx` |
| **Morais** | `Morais {dates}.docx` or `Morais ELA SS {dates}.docx` |
| **Coleman** | `Name_ Ariel Coleman {date}.docx` |

### Output File Patterns

**Different from yours!**
- `Silva Lesson Plans {dates}.docx` (simple)
- `Daniela Silva W41 Lesson Plan.docx` (with week number)
- `## Subject Teacher Silva Lesson Plans {dates}.docx` (numbered by subject)

---

## Key Differences from Your Setup

### 1. Folder Naming
**Your folders:** `25 W37`, `25 W38`, `25 W39`, `25 W40`, `25 W41`
**Daniela's folders:** `22 W39`, `25 W38`, `25 W40`, `25 W41`
- ⚠️ Has typo: `22 W39` should be `25 W39`

### 2. Primary Teacher Files
**Your teachers:** Davies, Lang, Savoca (consistent names)
**Daniela's teachers:** Lonesky, Piret, Laverty, Morais, Coleman (more variety)

### 3. File Naming Complexity
**Your files:** Simple patterns
**Daniela's files:** 
- Numbered prefixes (`01 Science`, `02 Math`)
- Full names (`_Brooke Laverty`)
- Different formats per teacher

### 4. Output Files
**Your output:** One combined file per week
**Daniela's output:** 
- Sometimes one combined file
- Sometimes separate files per subject (numbered)

---

## Recommended Slot Configuration for Daniela

Based on Week 40 files:

### Slot 1: Science (Lonesky)
- `primary_teacher_name`: "Lonesky"
- `subject`: "Science"
- Matches: `Lonesky Week 5 Lesson Plans SY 25_26.docx`

### Slot 2: Math (Laverty)
- `primary_teacher_name`: "Laverty"
- `subject`: "Math"
- Matches: `_Brooke Laverty - SY'25-26_ week of 9_29.docx`

### Slot 3: ELA (Piret)
- `primary_teacher_name`: "Piret"
- `subject`: "ELA"
- Matches: `Piret Lesson Plans 9_29_25-10_3_25.docx`

### Slot 4: Social Studies (Lonesky)
- `primary_teacher_name`: "Lonesky"
- `subject`: "Social Studies"
- Matches: `Lonesky Week 5 Lesson Plans SY 25_26.docx` (same file)

### Slot 5: ELA/SS (Morais)
- `primary_teacher_name`: "Morais"
- `subject`: "ELA"
- Note: Morais not in W40, need to check other weeks

### Slot 6: Unknown (Coleman)
- `primary_teacher_name`: "Coleman"
- `subject`: "Unknown"
- Matches: `Name_ Ariel Coleman 9-29.docx`

---

## Challenges to Address

### 1. Inconsistent Folder Names
**Problem:** `22 W39` instead of `25 W39`
**Solution:** File manager should handle both patterns or rename folder

### 2. Complex File Names
**Problem:** `_Brooke Laverty - SY'25-26_ week of 9_29.docx`
**Solution:** Enhanced pattern matching (already implemented)

### 3. Numbered Output Files
**Problem:** Week 39 has 6 separate output files
**Solution:** Decide on single combined file vs separate files

### 4. Missing Week 41 Files
**Problem:** No primary teacher files in W41 yet
**Solution:** Wait for files or use previous week's teachers

---

## File Manager Updates Needed

### 1. Handle Year Prefix Variations
```python
def get_week_folder(self, week_of: str, user_id: str = None) -> Path:
    """Get week folder, handling different year formats."""
    week_num = self._calculate_week_number(week_of)
    year = datetime.now().strftime('%y')
    
    # Try current year first
    folder_name = f"{year} W{week_num:02d}"
    folder_path = self.base_path / folder_name
    
    if folder_path.exists():
        return folder_path
    
    # Try other year formats (22, 23, 24, etc.)
    for y in ['22', '23', '24', '25', '26']:
        folder_name = f"{y} W{week_num:02d}"
        folder_path = self.base_path / folder_name
        if folder_path.exists():
            return folder_path
    
    # Return expected path (will be created)
    return self.base_path / f"{year} W{week_num:02d}"
```

### 2. Enhanced Teacher Matching
Already handles:
- ✅ "Lonesky" → `Lonesky Week 5 Lesson Plans SY 25_26.docx`
- ✅ "Piret" → `Piret Lesson Plans 9_29_25-10_3_25.docx`
- ✅ "Laverty" → `_Brooke Laverty - SY'25-26_ week of 9_29.docx`
- ✅ "Morais" → `Morais 9_15_25 - 9_19_25.docx`
- ✅ "Coleman" → `Name_ Ariel Coleman 9-29.docx`

### 3. Output File Exclusion
Update skip patterns to include "Silva":
```python
skip_patterns = [
    '~',                    # Temp files
    'rodrigues',           # Your output
    'silva',               # Daniela's output
    'old ',                # Old versions
    'template',            # Templates
    'copy of',             # Copies
]
```

---

## Multi-User Configuration

### User 1: Maria Rodriguez
- **Base Path:** `F:\rodri\Documents\OneDrive\AS\Lesson Plan`
- **Teachers:** Davies, Lang, Savoca
- **Output Pattern:** `Rodrigues_Lesson_plan_W##_{dates}.docx`

### User 2: Daniela Silva
- **Base Path:** `F:\rodri\Documents\OneDrive\AS\Daniela LP`
- **Teachers:** Lonesky, Piret, Laverty, Morais, Coleman
- **Output Pattern:** `Silva_Lesson_plan_W##_{dates}.docx`

---

## Implementation Plan

### 1. Update File Manager
- [ ] Handle year prefix variations (22 W39 vs 25 W39)
- [ ] Add "Silva" to skip patterns
- [ ] Support user-specific base paths

### 2. Database Configuration
- [ ] Add `base_path_override` to user settings
- [ ] Store per-user teacher configurations

### 3. Test Both Users
- [ ] Test Maria's setup (already working)
- [ ] Test Daniela's setup
- [ ] Verify file matching for both

---

## Next Steps

1. ✅ Analyzed Daniela's file structure
2. ⏳ Update file manager for year variations
3. ⏳ Add user-specific base paths
4. ⏳ Test with both users
5. ⏳ Build UI with user switching

---

**Status:** Multi-user analysis complete, ready to implement user-specific configurations
