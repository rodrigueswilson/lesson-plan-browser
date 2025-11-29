# Subject Detection Improvements - Code Review Response

## Status: 🔄 IN PROGRESS (Issue #1 Complete, #2-5 Pending)

Response to code review identifying 5 critical gaps in subject-based slot detection.

---

## Issue #1: Alias Matching Brittleness ✅ FIXED

### Problem
- Overlapping aliases: `'social studies'` included `'ela/ss'`, `'ela'` included `'ela/ss'`
- Substring matching: `name in subject_value` caused cross-matching
- Example: "Social Studies" request matched "ELA/SS" slot

### Solution Implemented

**1. Non-Overlapping Aliases:**
```python
subject_mappings = {
    'ela': ['ela', 'english', 'language arts', 'reading', 'literacy'],  # NO ela/ss
    'math': ['math', 'mathematics'],
    'science': ['science', 'sci'],
    'social studies': ['ss', 'social studies', 'history'],  # NO ela/ss
    'ela/ss': ['ela/ss', 'elass', 'language arts/social studies']  # Separate entry
}
```

**2. Text Normalization:**
```python
def normalize_text(text):
    """Remove punctuation, lowercase, strip whitespace."""
    text = text.translate(str.maketrans('', '', string.punctuation))
    return text.lower().strip()
```

**3. Token-Based Matching for Combined Subjects:**
```python
def tokenize_subject(text):
    """Split 'ela/ss' → ['ela', 'ss']"""
    for sep in ['/', '-', '&', 'and']:
        if sep in text:
            return [normalize_text(t) for t in text.split(sep)]
    return [normalize_text(text)]

# Match logic:
# 1. Try exact match with aliases
if subject_value_normalized == alias:
    matched = True

# 2. For combined subjects, ALL tokens must match
if len(subject_tokens) > 1:
    if all(any(st == vt for vt in subject_value_tokens) for st in subject_tokens):
        matched = True  # Both 'ela' AND 'ss' found
```

**4. Debug Logging:**
```python
logger.debug(
    "subject_exact_match",
    extra={
        "slot": slot_num,
        "requested": subject,
        "metadata": slot_subject,
        "matched_alias": alias  # Shows WHICH alias matched
    }
)
```

---

## Issue #2: Multiple Slots with Same Subject ✅ FIXED

### Problem
Two Math slots → always returns first match, ignoring teacher

### Solution Implemented

**1. Collect All Matches:**
```python
matches = []  # Store all matching slots
for slot_num in range(1, available_slots + 1):
    # ... scan metadata ...
    if matched:
        matches.append({
            'slot_num': slot_num,
            'subject': slot_subject,
            'teacher': slot_teacher,  # Extract teacher from metadata
            'matched_alias': matched_alias
        })
```

**2. Disambiguate by Teacher:**
```python
def find_slot_by_subject(self, subject: str, teacher_name: str = None) -> int:
    # ... collect matches ...
    
    # Multiple matches - use teacher to disambiguate
    if teacher_normalized:
        for match in matches:
            if match['teacher'] and teacher_normalized in normalize_text(match['teacher']):
                logger.info("subject_slot_found_via_teacher", ...)
                return match['slot_num']
    
    # Can't disambiguate - warn and return first
    logger.warning("multiple_subject_matches", ...)
    return matches[0]['slot_num']
```

**3. Extract Teacher from Metadata:**
```python
for row in meta_table.rows:
    for cell in row.cells:
        cell_lower = cell.text.lower()
        
        if 'name:' in cell_lower or 'teacher:' in cell_lower:
            slot_teacher = cell.text.split(':', 1)[-1].strip()
```

---

## Issue #3: Hyperlink/Image Helpers Not Subject-Aware ⚠️ TODO

### Problem
`extract_hyperlinks_for_slot(slot_num)` and `extract_images_for_slot(slot_num)` still accept only slot number. Tests/scripts bypass subject logic.

### Proposed Solution

**Add subject-aware overloads:**

```python
def extract_hyperlinks_for_slot(self, slot_number: int = None, subject: str = None, teacher_name: str = None) -> List[Dict]:
    """
    Extract hyperlinks for a specific slot (slot-aware).
    
    Args:
        slot_number: Slot number (1-indexed) - optional if subject provided
        subject: Subject name - will find correct slot if provided
        teacher_name: Teacher name for disambiguation
    """
    # If subject provided, find actual slot
    if subject:
        slot_number = self.find_slot_by_subject(subject, teacher_name)
    elif slot_number is None:
        raise ValueError("Must provide either slot_number or subject")
    
    # ... existing extraction logic ...
```

**Same for images:**
```python
def extract_images_for_slot(self, slot_number: int = None, subject: str = None, teacher_name: str = None) -> List[Dict]:
    # Same pattern as hyperlinks
```

**Benefits:**
- All entry points use subject detection
- Backward compatible (slot_number still works)
- Tests can use subject-based calls

---

## Issue #4: Lack of Regression Tests ⚠️ TODO

### Problem
No tests for:
- `find_slot_by_subject()`
- Misaligned slot numbers
- Multiple subjects
- Teacher disambiguation

### Proposed Tests

**File:** `tests/test_subject_slot_detection.py`

```python
class TestFindSlotBySubject:
    """Test subject-based slot detection."""
    
    def test_find_slot_exact_match(self, tmp_path):
        """Test finding slot by exact subject match."""
        # Create doc: Slot 1 = Math, Slot 2 = ELA
        # Request: "Math"
        # Expected: Returns 1
    
    def test_find_slot_alias_match(self, tmp_path):
        """Test finding slot using subject alias."""
        # Create doc: Slot 1 has "Mathematics"
        # Request: "Math"
        # Expected: Returns 1 (alias match)
    
    def test_find_slot_combined_subject(self, tmp_path):
        """Test finding combined subject like ELA/SS."""
        # Create doc: Slot 1 = "ELA/SS"
        # Request: "ELA/SS"
        # Expected: Returns 1 (token match)
    
    def test_find_slot_no_cross_match(self, tmp_path):
        """Test that SS doesn't match ELA/SS."""
        # Create doc: Slot 1 = "ELA/SS", Slot 2 = "Social Studies"
        # Request: "Social Studies"
        # Expected: Returns 2 (NOT 1)
    
    def test_find_slot_misaligned_numbers(self, tmp_path):
        """Test misaligned slot numbers (Savoca scenario)."""
        # Create doc: Slot 1 = ELA/SS, Slot 2 = Math
        # Config: Slot 2 wants ELA/SS
        # Expected: Returns 1 (finds ELA/SS in slot 1)
    
    def test_find_slot_multiple_math_teachers(self, tmp_path):
        """Test disambiguating duplicate subjects by teacher."""
        # Create doc: Slot 1 = Math (Teacher A), Slot 2 = Math (Teacher B)
        # Request: "Math", teacher="Teacher B"
        # Expected: Returns 2
    
    def test_find_slot_multiple_math_no_teacher(self, tmp_path):
        """Test multiple matches without teacher."""
        # Create doc: Slot 1 = Math, Slot 2 = Math
        # Request: "Math" (no teacher)
        # Expected: Returns 1 (first match) + warning logged
    
    def test_find_slot_not_found(self, tmp_path):
        """Test subject not found raises ValueError."""
        # Create doc: Slot 1 = Math
        # Request: "Science"
        # Expected: Raises ValueError


class TestSubjectAwareExtraction:
    """Test extraction using subject instead of slot number."""
    
    def test_extract_hyperlinks_by_subject(self, tmp_path):
        """Test hyperlink extraction using subject."""
        # Create doc: Slot 1 = ELA (5 links), Slot 2 = Math (3 links)
        # Extract: subject="Math"
        # Expected: Returns 3 links from slot 2
    
    def test_extract_images_by_subject(self, tmp_path):
        """Test image extraction using subject."""
        # Similar to hyperlinks
    
    def test_extract_content_by_subject_misaligned(self, tmp_path):
        """Test content extraction with misaligned slots."""
        # Create doc: Slot 1 = ELA/SS, Slot 2 = Math
        # Extract: slot_number=2, subject="ELA/SS"
        # Expected: Extracts from slot 1, logs mismatch warning
```

---

## Issue #5: Alias List / Logging ✅ PARTIALLY FIXED

### What's Fixed
- ✅ Non-overlapping aliases
- ✅ Debug logging at each comparison
- ✅ Captures matched alias in logs

### What's Still Needed
- ⚠️ Document alias list in code comments
- ⚠️ Add validation that aliases don't overlap
- ⚠️ Consider moving aliases to config file

### Current Logging

```python
# Exact match
logger.debug("subject_exact_match", extra={
    "slot": slot_num,
    "requested": subject,
    "metadata": slot_subject,
    "matched_alias": alias  # Shows which alias matched
})

# Token match
logger.debug("subject_token_match", extra={
    "slot": slot_num,
    "requested_tokens": subject_tokens,
    "metadata_tokens": subject_value_tokens
})

# Final match
logger.info("subject_slot_found", extra={
    "requested_subject": subject,
    "found_in_slot": match['slot_num'],
    "metadata_subject": match['subject'],
    "metadata_teacher": match['teacher'],
    "matched_via": match['matched_alias']  # Shows how it matched
})
```

---

## Summary of Changes

### Completed ✅
1. **Non-overlapping aliases** - Prevents cross-matching
2. **Text normalization** - Strips punctuation, lowercase
3. **Token-based matching** - Handles combined subjects (ELA/SS)
4. **Teacher disambiguation** - Handles duplicate subjects
5. **Debug logging** - Shows matched alias at each step

### Pending ⚠️
1. **Subject-aware helper overloads** - For hyperlinks/images
2. **Regression tests** - Comprehensive test suite
3. **Alias documentation** - Comments + validation

---

## Next Steps

1. ✅ Test current implementation with Savoca file
2. ⚠️ Add subject-aware overloads to helpers
3. ⚠️ Write comprehensive test suite
4. ⚠️ Document alias mappings
5. ⚠️ Consider config-based aliases

---

**Status:** Core matching logic fixed. Need to add helper overloads and tests before production-ready.
