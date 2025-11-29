# Session 1: Document Processing Foundation

**Duration**: 3-4 hours  
**Features**: 1, 2, 4, 5  
**Priority**: HIGH  
**Dependencies**: None

---

## 🎯 Session Objectives

Implement core document processing enhancements:
1. Equal table width enforcement
2. Image preservation (input → output)
3. Hyperlink preservation
4. Timestamped output filenames

---

## 📋 Pre-Session Checklist

- [ ] Review python-docx documentation for images and hyperlinks
- [ ] Backup current `tools/docx_parser.py` and `tools/docx_renderer.py`
- [ ] Create test input DOCX files with:
  - [ ] Images
  - [ ] Hyperlinks
  - [ ] Various table structures
- [ ] Verify test suite runs successfully

---

## 🔧 Implementation Steps

### Step 1: Create DOCX Utilities Module (30 min)

**Rationale**: Follow DRY principle - extract common DOCX operations

**File**: `tools/docx_utils.py` (NEW)

```python
"""
Utility functions for DOCX manipulation.
Centralizes common operations to follow DRY and SSOT principles.
"""

from docx import Document
from docx.table import Table
from docx.shared import Inches, Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from typing import List, Dict, Any, Optional
from io import BytesIO
import re


def normalize_table_widths(table: Table) -> None:
    """
    Ensure all columns in table have equal width.
    
    Args:
        table: python-docx Table object
    """
    if not table.columns:
        return
    
    total_width = table.width
    num_cols = len(table.columns)
    col_width = total_width // num_cols
    
    for column in table.columns:
        for cell in column.cells:
            cell.width = col_width


def extract_images_from_document(doc: Document) -> List[Dict[str, Any]]:
    """
    Extract all images from document with metadata.
    
    Args:
        doc: python-docx Document object
    
    Returns:
        List of dicts with keys: data, content_type, filename, width, height
    """
    images = []
    
    # Extract from document relationships
    for rel in doc.part.rels.values():
        if "image" in rel.target_ref:
            image_part = rel.target_part
            images.append({
                'data': image_part.blob,
                'content_type': image_part.content_type,
                'filename': rel.target_ref.split('/')[-1],
                'rel_id': rel.rId
            })
    
    return images


def insert_image_into_paragraph(
    paragraph,
    image_data: bytes,
    width_inches: float = 3.0,
    height_inches: Optional[float] = None
):
    """
    Insert image into paragraph.
    
    Args:
        paragraph: python-docx Paragraph object
        image_data: Image binary data
        width_inches: Image width in inches
        height_inches: Image height in inches (auto if None)
    """
    run = paragraph.add_run()
    
    if height_inches:
        run.add_picture(
            BytesIO(image_data),
            width=Inches(width_inches),
            height=Inches(height_inches)
        )
    else:
        run.add_picture(BytesIO(image_data), width=Inches(width_inches))


def extract_hyperlinks_from_paragraph(paragraph) -> List[Dict[str, str]]:
    """
    Extract hyperlinks from paragraph.
    
    Args:
        paragraph: python-docx Paragraph object
    
    Returns:
        List of dicts with keys: text, url, position
    """
    hyperlinks = []
    
    # Get hyperlink elements from paragraph XML
    for hyperlink in paragraph._element.xpath('.//w:hyperlink'):
        # Get relationship ID
        r_id = hyperlink.get(qn('r:id'))
        if r_id:
            # Get URL from relationship
            try:
                url = paragraph.part.rels[r_id].target_ref
                # Get text from hyperlink
                text = ''.join(node.text for node in hyperlink.xpath('.//w:t'))
                
                hyperlinks.append({
                    'text': text,
                    'url': url,
                    'r_id': r_id
                })
            except KeyError:
                # Relationship not found, skip
                pass
    
    return hyperlinks


def add_hyperlink_to_paragraph(
    paragraph,
    text: str,
    url: str,
    color: str = "0000FF",
    underline: bool = True
):
    """
    Add hyperlink to paragraph.
    
    Args:
        paragraph: python-docx Paragraph object
        text: Display text
        url: Target URL
        color: Hex color code (default: blue)
        underline: Whether to underline (default: True)
    """
    # Get document part
    part = paragraph.part
    
    # Create relationship
    r_id = part.relate_to(
        url,
        'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',
        is_external=True
    )
    
    # Create hyperlink element
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)
    
    # Create run element
    new_run = OxmlElement('w:r')
    
    # Set run properties (color, underline)
    rPr = OxmlElement('w:rPr')
    
    if color:
        c = OxmlElement('w:color')
        c.set(qn('w:val'), color)
        rPr.append(c)
    
    if underline:
        u = OxmlElement('w:u')
        u.set(qn('w:val'), 'single')
        rPr.append(u)
    
    new_run.append(rPr)
    
    # Add text
    text_elem = OxmlElement('w:t')
    text_elem.text = text
    new_run.append(text_elem)
    
    hyperlink.append(new_run)
    
    # Add hyperlink to paragraph
    paragraph._element.append(hyperlink)


def generate_timestamped_filename(
    base_name: str,
    extension: str = ".docx",
    timestamp_format: str = "%Y%m%d_%H%M%S"
) -> str:
    """
    Generate filename with timestamp.
    
    Args:
        base_name: Base filename without extension
        extension: File extension (default: .docx)
        timestamp_format: strftime format string
    
    Returns:
        Filename with timestamp: {base_name}_{timestamp}{extension}
    
    Example:
        >>> generate_timestamped_filename("Weekly_Plan")
        'Weekly_Plan_20251018_143022.docx'
    """
    from datetime import datetime
    timestamp = datetime.now().strftime(timestamp_format)
    return f"{base_name}_{timestamp}{extension}"


def detect_no_school_day(text: str, patterns: Optional[List[str]] = None) -> bool:
    """
    Detect if document indicates 'No School' day.
    
    Args:
        text: Document text content
        patterns: Custom regex patterns (uses defaults if None)
    
    Returns:
        True if 'No School' day detected
    """
    if patterns is None:
        patterns = [
            r'no\s+school',
            r'school\s+closed',
            r'holiday',
            r'professional\s+development',
            r'teacher\s+workday',
            r'pd\s+day',
            r'vacation',
            r'break'
        ]
    
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in patterns)
```

**Testing**:
```python
# tests/test_docx_utils.py
import pytest
from tools.docx_utils import (
    generate_timestamped_filename,
    detect_no_school_day
)

def test_timestamped_filename():
    filename = generate_timestamped_filename("test")
    assert filename.startswith("test_")
    assert filename.endswith(".docx")
    assert len(filename) == len("test_YYYYMMDD_HHMMSS.docx")

def test_no_school_detection():
    assert detect_no_school_day("No School - Holiday")
    assert detect_no_school_day("Professional Development Day")
    assert not detect_no_school_day("Regular school day")
```

---

### Step 2: Update DOCX Parser (45 min)

**File**: `tools/docx_parser.py`

**Changes**:
1. Add image extraction method
2. Add hyperlink extraction method
3. Add "No School" detection method

```python
# Add to DOCXParser class

def extract_images(self) -> List[Dict[str, Any]]:
    """
    Extract all images from document.
    
    Returns:
        List of image metadata dicts
    """
    from tools.docx_utils import extract_images_from_document
    return extract_images_from_document(self.doc)


def extract_hyperlinks(self) -> List[Dict[str, str]]:
    """
    Extract all hyperlinks from document.
    
    Returns:
        List of hyperlink dicts with text and URL
    """
    from tools.docx_utils import extract_hyperlinks_from_paragraph
    
    all_hyperlinks = []
    for paragraph in self.doc.paragraphs:
        hyperlinks = extract_hyperlinks_from_paragraph(paragraph)
        for link in hyperlinks:
            link['context'] = paragraph.text[:100]  # First 100 chars for context
            all_hyperlinks.append(link)
    
    return all_hyperlinks


def is_no_school_day(self) -> bool:
    """
    Check if document indicates 'No School' day.
    
    Returns:
        True if 'No School' day detected
    """
    from tools.docx_utils import detect_no_school_day
    full_text = self.get_full_text()
    return detect_no_school_day(full_text)


def parse_with_media(self) -> Dict[str, Any]:
    """
    Parse document including media (images, hyperlinks).
    
    Returns:
        Dict with lesson data plus images and hyperlinks
    """
    # Get standard parsed data
    lesson_data = self.parse()
    
    # Add media
    lesson_data['images'] = self.extract_images()
    lesson_data['hyperlinks'] = self.extract_hyperlinks()
    lesson_data['is_no_school'] = self.is_no_school_day()
    
    return lesson_data
```

**Testing**:
```python
# tests/test_docx_parser_media.py
import pytest
from tools.docx_parser import DOCXParser
from pathlib import Path

def test_image_extraction():
    parser = DOCXParser("tests/fixtures/lesson_with_image.docx")
    images = parser.extract_images()
    assert len(images) > 0
    assert 'data' in images[0]
    assert 'content_type' in images[0]

def test_hyperlink_extraction():
    parser = DOCXParser("tests/fixtures/lesson_with_links.docx")
    links = parser.extract_hyperlinks()
    assert len(links) > 0
    assert 'text' in links[0]
    assert 'url' in links[0]

def test_no_school_detection():
    parser = DOCXParser("tests/fixtures/no_school_day.docx")
    assert parser.is_no_school_day() == True
    
    parser2 = DOCXParser("tests/fixtures/regular_lesson.docx")
    assert parser2.is_no_school_day() == False
```

---

### Step 3: Update DOCX Renderer (60 min)

**File**: `tools/docx_renderer.py`

**Changes**:
1. Add table width normalization
2. Add image insertion
3. Add hyperlink insertion
4. Use timestamped filenames

```python
# Add imports
from tools.docx_utils import (
    normalize_table_widths,
    insert_image_into_paragraph,
    add_hyperlink_to_paragraph,
    generate_timestamped_filename
)

# Update render() method
def render(
    self,
    lesson_json: Dict[str, Any],
    output_path: str,
    preserve_media: bool = True
) -> str:
    """
    Render lesson plan to DOCX.
    
    Args:
        lesson_json: Validated lesson plan JSON
        output_path: Output file path (can be directory or full path)
        preserve_media: Whether to preserve images and hyperlinks
    
    Returns:
        Path to generated DOCX file
    """
    # Generate timestamped filename
    if Path(output_path).is_dir():
        base_name = self._generate_base_filename(lesson_json)
        filename = generate_timestamped_filename(base_name)
        output_path = Path(output_path) / filename
    
    # Load template
    doc = Document(str(self.template_path))
    
    # Fill metadata
    self._fill_metadata(doc, lesson_json)
    
    # Fill daily plans
    self._fill_daily_plans(doc, lesson_json, preserve_media)
    
    # Normalize all table widths
    for table in doc.tables:
        normalize_table_widths(table)
    
    # Save
    doc.save(str(output_path))
    
    logger.info(
        "docx_render_complete",
        extra={
            "output_path": str(output_path),
            "has_images": len(lesson_json.get('images', [])) > 0,
            "has_hyperlinks": len(lesson_json.get('hyperlinks', [])) > 0
        }
    )
    
    return str(output_path)


def _fill_daily_plans(
    self,
    doc: Document,
    lesson_json: Dict[str, Any],
    preserve_media: bool = True
):
    """Fill daily plan table with content and media."""
    # ... existing code ...
    
    # Add images if present and preserve_media is True
    if preserve_media and 'images' in lesson_json:
        self._insert_images(doc, lesson_json['images'])
    
    # Add hyperlinks if present and preserve_media is True
    if preserve_media and 'hyperlinks' in lesson_json:
        self._insert_hyperlinks(doc, lesson_json['hyperlinks'])


def _insert_images(self, doc: Document, images: List[Dict[str, Any]]):
    """Insert images into appropriate locations."""
    # Strategy: Insert images at end of relevant cells
    # This is a simplified approach - can be enhanced based on context
    
    for image in images:
        # Find appropriate location (e.g., in materials section)
        # For now, add to a dedicated section or skip if no context
        pass  # TODO: Implement based on image context


def _insert_hyperlinks(self, doc: Document, hyperlinks: List[Dict[str, str]]):
    """Insert hyperlinks into document."""
    # Strategy: Find text matching hyperlink text and replace with link
    
    for link in hyperlinks:
        text_to_find = link['text']
        url = link['url']
        
        # Search through paragraphs
        for paragraph in doc.paragraphs:
            if text_to_find in paragraph.text:
                # Replace plain text with hyperlink
                # This is simplified - full implementation would preserve formatting
                paragraph.clear()
                add_hyperlink_to_paragraph(paragraph, text_to_find, url)
                break


def _generate_base_filename(self, lesson_json: Dict[str, Any]) -> str:
    """Generate base filename from lesson data."""
    metadata = lesson_json.get('metadata', {})
    teacher = metadata.get('teacher_name', 'Unknown')
    week_of = metadata.get('week_of', 'Unknown')
    
    # Clean filename
    teacher_clean = re.sub(r'[^\w\s-]', '', teacher).strip().replace(' ', '_')
    week_clean = week_of.replace('/', '-')
    
    return f"{teacher_clean}_Weekly_{week_clean}"
```

**Testing**:
```python
# tests/test_docx_renderer_media.py
import pytest
from tools.docx_renderer import DOCXRenderer
from tools.docx_parser import DOCXParser
from pathlib import Path

def test_table_width_normalization():
    renderer = DOCXRenderer()
    output = renderer.render(valid_lesson_json, "output/test.docx")
    
    # Verify all tables have equal column widths
    doc = Document(output)
    for table in doc.tables:
        widths = [col.width for col in table.columns]
        assert len(set(widths)) == 1  # All widths equal

def test_timestamped_filename():
    renderer = DOCXRenderer()
    output1 = renderer.render(valid_lesson_json, "output/")
    output2 = renderer.render(valid_lesson_json, "output/")
    
    assert output1 != output2  # Different timestamps
    assert Path(output1).exists()
    assert Path(output2).exists()

def test_image_preservation():
    # Parse input with image
    parser = DOCXParser("tests/fixtures/lesson_with_image.docx")
    lesson_data = parser.parse_with_media()
    
    # Render with media preservation
    renderer = DOCXRenderer()
    output = renderer.render(lesson_data, "output/test_images.docx")
    
    # Verify images in output
    doc = Document(output)
    # Check for image relationships
    assert len([r for r in doc.part.rels.values() if "image" in r.target_ref]) > 0
```

---

### Step 4: Update Batch Processor (30 min)

**File**: `tools/batch_processor.py`

**Changes**:
1. Use `parse_with_media()` instead of `parse()`
2. Pass media data through pipeline

```python
def process_slot(self, slot_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process single slot with media preservation."""
    
    # Parse with media
    parser = DOCXParser(slot_data['input_file'])
    
    # Check for No School day
    if parser.is_no_school_day():
        logger.info(
            "no_school_day_detected",
            extra={"slot": slot_data['slot_number']}
        )
        # Copy input to output without processing
        import shutil
        output_path = self._generate_output_path(slot_data)
        shutil.copy2(slot_data['input_file'], output_path)
        
        return {
            'status': 'skipped',
            'reason': 'no_school_day',
            'output_file': output_path,
            'slot_number': slot_data['slot_number']
        }
    
    # Parse with media
    lesson_data = parser.parse_with_media()
    
    # Transform via LLM (media data passes through)
    transformed = self.llm_service.transform(lesson_data)
    
    # Render with media preservation
    output_path = self.renderer.render(
        transformed,
        slot_data['output_dir'],
        preserve_media=True
    )
    
    return {
        'status': 'completed',
        'output_file': output_path,
        'slot_number': slot_data['slot_number'],
        'has_images': len(lesson_data.get('images', [])) > 0,
        'has_hyperlinks': len(lesson_data.get('hyperlinks', [])) > 0
    }
```

---

### Step 5: Integration Testing (45 min)

**Create comprehensive test suite**:

```python
# tests/test_integration_media.py

def test_end_to_end_with_images():
    """Test complete workflow with images."""
    # 1. Create test input with image
    # 2. Process through batch processor
    # 3. Verify output has image
    # 4. Verify filename has timestamp
    pass

def test_end_to_end_with_hyperlinks():
    """Test complete workflow with hyperlinks."""
    pass

def test_no_school_day_workflow():
    """Test No School day is copied, not processed."""
    pass

def test_multiple_runs_unique_filenames():
    """Test multiple runs create unique files."""
    pass
```

---

## 📊 Success Criteria

- [ ] All tables in output have equal column widths
- [ ] Images from input appear in output
- [ ] Hyperlinks remain clickable in output
- [ ] Each run creates unique timestamped filename
- [ ] "No School" days are copied, not processed
- [ ] All existing tests still pass
- [ ] New tests pass
- [ ] Code follows DRY, SSOT, KISS, SOLID, YAGNI
- [ ] No duplicate code
- [ ] Logging comprehensive

---

## 📝 Post-Session Tasks

- [ ] Update documentation
- [ ] Create PR with changes
- [ ] Run full test suite
- [ ] Update CHANGELOG.md
- [ ] Prepare for Session 2

---

## 🐛 Known Issues / Edge Cases

1. **Image positioning**: Current implementation may not preserve exact positioning
2. **Hyperlink formatting**: May not preserve all original formatting
3. **Table width**: May need adjustment for merged cells
4. **Filename length**: Very long names may exceed OS limits

---

**Estimated Time**: 3-4 hours  
**Complexity**: Medium  
**Risk**: Low
