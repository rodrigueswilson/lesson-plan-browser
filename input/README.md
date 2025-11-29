# Input Files

Sample primary teacher lesson plans used for testing and demonstration of the WIDA-enhanced bilingual transformation system.

## Files

### **Lesson Plan Template SY'25-26.docx**
District-approved lesson plan template for the 2025-26 school year.

**Purpose:**
- Authoritative source for DOCX generation
- Template structure for output formatting
- District formatting standards reference

**Usage:**
- Used by document processing pipeline (python-docx + docxcompose)
- Preserves headers, footers, and district branding
- Ensures output compliance with district requirements

### Sample Lesson Plans

#### **9_15-9_19 Davies Lesson Plans.docx** (30 KB)
Weekly lesson plans from Davies classroom, September 15-19.

#### **Lang Lesson Plans 9_15_25-9_19_25.docx** (3.7 MB)
Comprehensive language arts lesson plans for September 15-19, 2025.

#### **Ms. Savoca- 9_15_24-9_19_24 Lesson plans.docx** (3.8 MB)
Weekly lesson plans from Ms. Savoca's classroom, September 15-19, 2024.

#### **Piret Lesson Plans 9_22_25-9_26_25.docx** (302 KB)
Weekly lesson plans from Piret classroom, September 22-26, 2025.

## Input Format Requirements

### Expected Structure
Primary teacher lesson plans should include:
- **Weekly table format** with columns for each day (Monday-Friday)
- **Row sections:** Unit/Lesson, Objective, Anticipatory Set, Tailored Instruction, Misconceptions, Assessment, Homework
- **Content area identification** (Language Arts, Math, Science, Social Studies)
- **Grade level** (specified or inferred)

### Minimum Required Information
- **Objectives:** Clear learning goals for each lesson
- **Instructional activities:** Core teaching activities and materials
- **Assessment methods:** How student learning will be measured
- **Grade level context:** Either explicit or inferable from content

### Optional but Helpful
- Vocabulary lists
- Specific materials referenced
- Student proficiency information
- Testing schedules (e.g., MAP testing)
- Special accommodations already in place

## Processing Pipeline

### Input Parsing
1. Extract lesson plan table structure
2. Identify content areas and grade levels
3. Parse objectives and vocabulary
4. Capture assessment methods

### Transformation
1. Load relevant strategy categories based on lesson context
2. Apply two-phase strategy selection
3. Generate tri-objective structure
4. Create Primary-Assessment-First overlay
5. Add bilingual enhancements

### Output Generation
1. Format as Word-compatible markdown table
2. Maintain original structure and content
3. Add WIDA-aligned enhancements
4. Include strategy citations and research foundations

## File Format Support

### Current (v1)
- **DOCX only** for inputs and outputs
- No PDF support in initial version

### Document Processing
- **Library:** python-docx + docxcompose
- **Template-driven:** Uses district .dotx template
- **Formatting preservation:** Headers, footers, styles maintained
- **Multi-strategy approach:** Fields → bookmarks → text replacement

## Usage Notes

### For Testing
- Use these sample files to validate transformation logic
- Test different grade levels and content areas
- Verify output formatting and WIDA alignment

### For Development
- Reference these files for input parsing logic
- Test edge cases (missing sections, varied formats)
- Validate template capacity detection

### For Demonstration
- Show before/after transformation examples
- Demonstrate WIDA enhancement process
- Illustrate strategy selection logic

## Related Documentation

- **[Prompt Engine](../prompt_v4.md)** - Transformation prompt
- **[Architecture](../docs/architecture_001.md)** - System design
- **[Examples](../docs/examples/)** - Sample outputs
- **[App Overview](../docs/app_overview.md)** - Document processing pipeline

## Privacy Note

Sample lesson plans contain educational content only. Any personally identifiable information (PII) should be scrubbed before processing through external LLM services. The system includes PII scrubbing capabilities for privacy-first operation.
