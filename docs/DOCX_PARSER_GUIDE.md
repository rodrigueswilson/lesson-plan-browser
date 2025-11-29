# DOCX Parser Guide

## Overview

The DOCX Parser extracts structured content from primary teacher lesson plan files. It handles various DOCX formats and intelligently identifies lesson components like objectives, activities, assessments, and materials.

## Features

- **Multi-format Support**: Handles different DOCX structures
- **Subject Detection**: Automatically identifies subject sections
- **Component Extraction**: Parses objectives, activities, assessments, materials
- **Table Support**: Extracts tabular data
- **Metadata Extraction**: Retrieves document properties and week information
- **Flexible Search**: Find content by headings or keywords

## Basic Usage

### Simple Parsing

```python
from tools.docx_parser import parse_docx

# Parse entire document
result = parse_docx("input/primary_teacher_plan.docx")
print(result['full_text'])
print(result['available_subjects'])

# Parse specific subject
math_content = parse_docx("input/primary_teacher_plan.docx", subject="Math")
print(math_content['objectives'])
print(math_content['activities'])
```

### Advanced Usage

```python
from tools.docx_parser import DOCXParser

# Initialize parser
parser = DOCXParser("input/primary_teacher_plan.docx")

# Get full text
full_text = parser.get_full_text()

# Find all subject sections
sections = parser.find_subject_sections()
# Returns: {'math': [...], 'science': [...], 'ela': [...]}

# Extract specific subject
math_content = parser.extract_subject_content("Math")
# Returns structured dict with objectives, activities, etc.

# List available subjects
subjects = parser.list_available_subjects()
# Returns: ['math', 'science', 'ela']

# Get metadata
metadata = parser.get_metadata()
# Returns: {title, author, created, modified, paragraph_count, ...}
```

## Content Structure

### Extracted Subject Content

```python
{
    'subject': 'Math',
    'raw_content': '...',  # Full text for this subject
    'objectives': [
        'Students will solve linear equations',
        'Students will graph solutions'
    ],
    'activities': [
        'Warm-up: Review previous concepts',
        'Main lesson: Introduce linear equations',
        'Group work: Practice problems'
    ],
    'assessments': [
        'Exit ticket: 3 equations to solve',
        'Homework: Worksheet pages 45-47'
    ],
    'materials': [
        'Whiteboard and markers',
        'Student worksheets',
        'Graphing calculators'
    ],
    'full_text': '...'  # Same as raw_content
}
```

## Subject Detection

### Automatic Detection

The parser automatically identifies subjects using:

1. **Heading Styles**: Looks for Heading 1, Heading 2
2. **Keywords**: Searches for subject names (math, science, ela, etc.)
3. **Context**: Analyzes surrounding content

Supported subjects:
- Math
- Science
- ELA / English / Reading / Writing
- Social Studies / History / Geography

### Manual Extraction

```python
# Extract by specific heading
content = parser.extract_by_heading("Mathematics")

# Extract by table header
table = parser.extract_table_by_header("Weekly Schedule")
```

## Component Extraction

### Objectives

Identifies learning objectives using keywords:
- "objective", "objectives"
- "goal", "goals"
- "learning target"
- "SWBAT" (Students Will Be Able To)
- "students will"

```python
objectives = parser._extract_objectives(content)
```

### Activities

Identifies activities using keywords:
- "activity", "activities"
- "procedure", "procedures"
- "lesson"
- "instruction"

```python
activities = parser._extract_activities(content)
```

### Assessments

Identifies assessments using keywords:
- "assessment", "assessments"
- "evaluate", "evaluation"
- "check for understanding"
- "exit ticket"

```python
assessments = parser._extract_assessments(content)
```

### Materials

Identifies materials using keywords:
- "material", "materials"
- "resource", "resources"
- "supplies"
- "equipment"

```python
materials = parser._extract_materials(content)
```

## Table Extraction

### Extract All Tables

```python
parser = DOCXParser("input/lesson_plan.docx")

# Get all tables
tables = parser.tables
# Returns: [[[cell1, cell2], [cell3, cell4]], ...]

# Each table is a list of rows
# Each row is a list of cell values
```

### Extract Specific Table

```python
# Find table by header text
schedule_table = parser.extract_table_by_header("Daily Schedule")

if schedule_table:
    for row in schedule_table:
        print(row)
```

## Metadata Extraction

### Document Properties

```python
metadata = parser.get_metadata()

print(f"Title: {metadata['title']}")
print(f"Author: {metadata['author']}")
print(f"Created: {metadata['created']}")
print(f"Modified: {metadata['modified']}")
print(f"Paragraphs: {metadata['paragraph_count']}")
print(f"Tables: {metadata['table_count']}")
print(f"Subjects: {metadata['available_subjects']}")
print(f"Week: {metadata['week_info']}")
```

### Week Information

The parser attempts to extract week information using patterns:
- "Week of 10/07"
- "Week 6"
- "10/07-10/11"

```python
week_info = parser.extract_week_info()
# Returns: "10/07-10/11" or None
```

## Integration with Batch Processor

### Workflow

```python
from tools.docx_parser import DOCXParser
from backend.llm_service import get_llm_service

# 1. Parse primary teacher's DOCX
parser = DOCXParser("input/primary_math.docx")
content = parser.extract_subject_content("Math")

# 2. Transform with LLM
llm_service = get_llm_service()
lesson_json = await llm_service.transform_to_bilingual(
    primary_content=content['full_text'],
    grade="6",
    subject="Math",
    week_of="10/07-10/11"
)

# 3. Render to DOCX
from tools.docx_renderer import render_lesson_plan
render_lesson_plan(lesson_json, "output/bilingual_math.docx")
```

## Handling Different Formats

### Format 1: Heading-Based

```
Math
Objectives: Students will...
Activities: Warm-up, main lesson...
Assessment: Exit ticket...
```

Parser uses `extract_by_heading()` to find sections.

### Format 2: Table-Based

```
| Subject | Objectives | Activities |
|---------|-----------|------------|
| Math    | ...       | ...        |
```

Parser uses `extract_table_by_header()` to find content.

### Format 3: Mixed Format

```
Week of 10/07-10/11

Math - Grade 6
Learning Goals:
- Solve equations
- Graph solutions

Lesson Activities:
1. Warm-up
2. Main lesson
3. Practice
```

Parser uses multiple strategies to extract content.

## Error Handling

### File Not Found

```python
try:
    parser = DOCXParser("nonexistent.docx")
except FileNotFoundError as e:
    print(f"File not found: {e}")
```

### Empty Content

```python
content = parser.extract_subject_content("Physics")
if not content['full_text']:
    print("No content found for Physics")
```

### Malformed DOCX

```python
try:
    parser = DOCXParser("corrupted.docx")
except Exception as e:
    print(f"Failed to parse DOCX: {e}")
```

## Best Practices

### 1. Verify Subject Availability

```python
parser = DOCXParser("input/plan.docx")
available = parser.list_available_subjects()

if 'math' in available:
    content = parser.extract_subject_content('Math')
else:
    print("Math section not found")
```

### 2. Use Case-Insensitive Search

```python
# Parser automatically handles case
content = parser.extract_subject_content("MATH")  # Works
content = parser.extract_subject_content("math")  # Works
content = parser.extract_subject_content("Math")  # Works
```

### 3. Validate Extracted Content

```python
content = parser.extract_subject_content("Math")

if not content['objectives']:
    print("Warning: No objectives found")

if not content['activities']:
    print("Warning: No activities found")
```

### 4. Handle Multiple Formats

```python
# Try multiple extraction methods
content = parser.extract_subject_content("Math")

if not content['full_text']:
    # Try heading-based extraction
    content_list = parser.extract_by_heading("Math")
    content['full_text'] = '\n'.join(content_list)
```

## Testing

### Unit Tests

```bash
pytest tests/test_docx_parser.py -v
```

### Test Coverage

- File reading and initialization
- Text extraction
- Table extraction
- Subject detection
- Component extraction (objectives, activities, etc.)
- Metadata extraction
- Error handling

### Sample Test

```python
def test_extract_objectives():
    parser = DOCXParser("test_files/sample.docx")
    content = parser.extract_subject_content("Math")
    
    assert len(content['objectives']) > 0
    assert any('equation' in obj.lower() for obj in content['objectives'])
```

## Performance

### Optimization Tips

1. **Reuse Parser Instance**: Create once, extract multiple subjects
2. **Cache Results**: Store extracted content if processing multiple times
3. **Limit Scope**: Extract only needed subjects
4. **Parallel Processing**: Process multiple files concurrently

### Benchmarks

- Small DOCX (< 10 pages): < 100ms
- Medium DOCX (10-50 pages): < 500ms
- Large DOCX (> 50 pages): < 2s

## Troubleshooting

### Subject Not Detected

**Problem**: Parser doesn't find your subject

**Solutions**:
1. Check heading format (should be short, < 50 chars)
2. Verify subject keyword is present
3. Use manual extraction: `extract_by_heading()`

### Incorrect Component Extraction

**Problem**: Objectives mixed with activities

**Solutions**:
1. Ensure clear section headings
2. Use consistent formatting
3. Manually parse if needed

### Missing Content

**Problem**: Some content not extracted

**Solutions**:
1. Check if content is in tables (use `extract_table_by_header()`)
2. Verify content isn't in headers/footers
3. Use `get_full_text()` to see all content

## Future Enhancements

- [ ] PDF support via conversion
- [ ] OCR for scanned documents
- [ ] Machine learning for better section detection
- [ ] Support for more document formats
- [ ] Custom extraction rules/templates
- [ ] Improved table parsing
