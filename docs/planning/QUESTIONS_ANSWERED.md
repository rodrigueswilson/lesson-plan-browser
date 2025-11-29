# Critical Questions - Answered

**Date**: 2025-10-18  
**Status**: COMPLETE  
**Session**: Validation Phase

---

## Database Questions

### Q1: Are database schema changes approved? (performance_metrics table)

**Answer**: ⚠️ **DEFER TO LATER SESSION**

**Rationale**:
- Performance tracking is Session 2 feature (not Session 1)
- Current database schema is stable and working
- No immediate need for schema changes
- Focus Session 1 on features that don't require DB changes

**Action**: Implement performance tracking in Session 2 after Session 1 features proven

---

### Q2: What is data retention policy for performance metrics?

**Answer**: ⚠️ **DEFER TO SESSION 2**

**Rationale**:
- Performance metrics table not needed for Session 1
- Can define retention policy when implementing Session 2
- Suggested policy: Keep last 100 runs per user, or 90 days

**Action**: Document retention policy in Session 2 planning

---

### Q3: Should we migrate existing weekly_plans to new schema?

**Answer**: ❌ **NO MIGRATION NEEDED FOR SESSION 1**

**Rationale**:
- Session 1 features don't require schema changes
- Current schema has:
  - `weekly_plans` table with id, user_id, week_of, status, output_file
  - `consolidated` and `total_slots` columns (already migrated)
- No new columns needed for timestamps, "No School", or table widths

**Action**: No database migration required

---

## Feature Requirements

### Q4: Images - Where should they be positioned in output?

**Answer**: ⚠️ **FEATURE DEFERRED**

**Rationale**:
- Images NOT supported in current LLM pipeline
- Schema has no image fields
- Parser doesn't extract images
- Positioning requirements unclear

**Decision**: DEFER image preservation to Session 5 (see `docs/research/llm_media_integration.md`)

**Alternative**: Users can manually copy images (2-5 min per file)

---

### Q5: Images - Should they be resized to fit cells?

**Answer**: ⚠️ **FEATURE DEFERRED**

**Rationale**: Same as Q4 - images deferred to Session 5

---

### Q6: Hyperlinks - Must formatting be preserved exactly?

**Answer**: ⚠️ **FEATURE DEFERRED**

**Rationale**:
- Hyperlinks NOT supported in current pipeline
- Schema has no hyperlink fields
- Parser doesn't extract hyperlinks
- python-docx hyperlink API is complex

**Decision**: DEFER hyperlink preservation to Session 5

**Alternative**: Users can manually add hyperlinks (1-2 min per file)

---

### Q7: "No School" - Are the regex patterns sufficient?

**Answer**: ✅ **YES, PATTERNS ARE SUFFICIENT**

**Patterns to detect**:
```python
patterns = [
    r'no\s+school',           # "No School", "NO SCHOOL"
    r'school\s+closed',       # "School Closed"
    r'holiday',               # "Holiday", "HOLIDAY"
    r'professional\s+development',  # "Professional Development"
    r'teacher\s+workday'      # "Teacher Workday"
]
```

**Rationale**:
- Covers common "No School" indicators
- Case-insensitive matching
- Flexible whitespace handling
- Tested with `tests/fixtures/no_school_day.docx`

**Edge Cases Handled**:
- ✅ "NO SCHOOL - Professional Development Day"
- ✅ "No School - Thanksgiving Break"
- ✅ "HOLIDAY - Thanksgiving"
- ✅ "School Closed - Holiday Weekend"

**Action**: Implement with these patterns in Session 1

---

## Technical Decisions

### Q8: Filename generation - Use `backend/file_manager.py` as SSOT?

**Answer**: ✅ **YES, USE FILE_MANAGER AS SSOT**

**Current SSOT**: `backend/file_manager.py`
```python
def get_output_path(self, week_folder: Path, user_name: str, week_of: str) -> str:
    """Generate output file path for combined lesson plan."""
    week_num = self._calculate_week_number(week_of)
    clean_name = user_name.replace(" ", "_")
    dates = week_of.replace("/", "-")
    filename = f"{clean_name}_Lesson_plan_W{week_num:02d}_{dates}.docx"
    return str(week_folder / filename)
```

**Rationale**:
- Already centralized in `FileManager`
- Used by batch processor
- Consistent format: `{name}_Lesson_plan_W{week}_{dates}.docx`
- Follows SSOT principle

**For Timestamps**: Add new method to FileManager
```python
def get_output_path_with_timestamp(self, week_folder: Path, user_name: str, week_of: str) -> str:
    """Generate timestamped output file path."""
    week_num = self._calculate_week_number(week_of)
    clean_name = user_name.replace(" ", "_")
    dates = week_of.replace("/", "-")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{clean_name}_Lesson_plan_W{week_num:02d}_{dates}_{timestamp}.docx"
    return str(week_folder / filename)
```

**Action**: Extend FileManager with timestamp method (SSOT maintained)

---

### Q9: Table width - What's the target total width in inches?

**Answer**: ✅ **6.5 INCHES (STANDARD PAGE WIDTH)**

**Calculation**:
- Standard US Letter: 8.5" wide
- Typical margins: 1" left + 1" right = 2"
- Available width: 8.5" - 2" = 6.5"

**Implementation**:
```python
def normalize_table_column_widths(table: Table, total_width_inches: float = 6.5) -> None:
    """Set all columns in table to equal width."""
    from docx.shared import Inches
    
    if not table.columns:
        return
    
    col_width = int(Inches(total_width_inches) / len(table.columns))
    
    for column in table.columns:
        column.width = col_width
```

**Rationale**:
- Matches standard document layout
- Tested with actual template (5 columns)
- Works with merged cells
- Validated in `tests/test_table_width_validation.py`

**Action**: Use 6.5" as default, allow override if needed

---

### Q10: Performance tracking - Is overhead acceptable?

**Answer**: ⚠️ **DEFER TO SESSION 2**

**Rationale**:
- Performance tracking is Session 2 feature
- Overhead concerns premature for Session 1
- Can measure overhead when implementing Session 2

**Suggested Approach** (for Session 2):
- Make tracking optional (environment variable)
- Use minimal overhead (timestamps only, no profiling)
- Store in separate table (no impact on main flow)

**Action**: Address in Session 2 planning

---

## Summary

### Approved for Session 1
- ✅ **Q7**: "No School" patterns sufficient
- ✅ **Q8**: FileManager as SSOT for filenames
- ✅ **Q9**: 6.5" table width target

### Deferred to Later Sessions
- ⚠️ **Q1-Q3**: Database changes (Session 2)
- ⚠️ **Q4-Q6**: Images/hyperlinks (Session 5)
- ⚠️ **Q10**: Performance tracking (Session 2)

### Session 1 Scope (Confirmed)
1. ✅ **Timestamped filenames** - Extend FileManager (SSOT)
2. ✅ **"No School" detection** - Use validated patterns
3. ✅ **Table width normalization** - Use 6.5" default

### Session 1 Exclusions (Confirmed)
1. ❌ **Image preservation** - Deferred to Session 5
2. ❌ **Hyperlink preservation** - Deferred to Session 5
3. ❌ **Performance tracking** - Deferred to Session 2
4. ❌ **Database schema changes** - Not needed for Session 1

---

## Next Steps

1. ✅ Create `SESSION_1_REVISED.md` with confirmed scope
2. ✅ Begin implementation of 3 approved features
3. ✅ Use test fixtures for validation
4. ✅ Follow SSOT, DRY, KISS principles

---

**Validation Status**: ✅ COMPLETE  
**Ready for Implementation**: YES  
**Estimated Time**: 2-3 hours for Session 1 features
