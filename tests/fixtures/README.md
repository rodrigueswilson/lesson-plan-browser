# Test Fixtures

This directory contains test DOCX files for validation and testing.

## Files

### regular_lesson.docx
- **Purpose**: Baseline test with normal lesson plan structure
- **Features**: Standard text-based lesson plan for Monday-Tuesday
- **Use Cases**: 
  - Test basic parsing
  - Test normal processing flow
  - Baseline for comparison

### no_school_day.docx
- **Purpose**: Tests "No School" day detection
- **Features**: Contains multiple "No School" indicators:
  - "NO SCHOOL - Professional Development Day"
  - "No School - Thanksgiving Break"
  - "HOLIDAY - Thanksgiving"
  - "School Closed - Holiday Weekend"
- **Use Cases**:
  - Test `is_no_school_day()` detection
  - Test copy-without-processing workflow
  - Test various "No School" patterns

### lesson_with_tables.docx
- **Purpose**: Tests table handling and width normalization
- **Features**: 
  - Table 1: Simple 3x3 table
  - Table 2: Wide 5-column table with unequal widths
  - Table 3: Table with merged cells
- **Use Cases**:
  - Test table width normalization
  - Test merged cell handling
  - Test multiple table structures

### lesson_with_image.docx
- **Purpose**: Tests image handling (when implemented)
- **Features**: 
  - Image placeholder text
  - Image caption
  - Context: Materials section
- **Use Cases**:
  - Future: Test image extraction
  - Future: Test image preservation
  - Currently: Placeholder for future feature

### lesson_with_hyperlinks.docx
- **Purpose**: Tests hyperlink handling (when implemented)
- **Features**:
  - 2 styled hyperlinks (blue, underlined text)
  - URLs as text
  - Context: Online resources section
- **Use Cases**:
  - Future: Test hyperlink extraction
  - Future: Test hyperlink preservation
  - Currently: Placeholder for future feature

## Notes

- **Images**: Actual image embedding requires image files. Current fixture uses placeholder text.
- **Hyperlinks**: True hyperlinks require complex XML manipulation. Current fixture uses styled text.
- **Created**: 2025-10-18 during validation phase
- **Generator**: `tests/create_test_fixtures.py`

## Regenerating Fixtures

To regenerate all fixtures:

```bash
python tests/create_test_fixtures.py
```

This will overwrite existing fixtures with fresh versions.
