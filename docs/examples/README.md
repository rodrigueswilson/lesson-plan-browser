# Example Lesson Plans

This directory contains sample lesson plans demonstrating the transformation process from primary teacher input to WIDA-enhanced bilingual output.

## Files

### **Sample_lesson_plan.md**
Example primary teacher lesson plan used as input for transformation.

**Content:**
- Weekly lesson plan table format
- Original objectives and instructional activities
- Assessment methods
- Homework assignments

**Purpose:** Demonstrates the typical input format expected by the transformation system.

### **Sample_Lesson_Transformation_WIDA.md**
WIDA-enhanced bilingual lesson plan output from the transformation process.

**Enhancements Include:**
- **Tri-objective structure:** Content Objective, Student Goal (I will...), WIDA Bilingual Language Objective
- **Bilingual Bridge:** L1/culture connections in Anticipatory Set
- **ELL Support:** Research-backed strategy implementations with proficiency-responsive adaptations
- **Bilingual Assessment Overlay:** Primary-Assessment-First protocol with level-banded supports
- **Family Connection:** Portuguese-English home activities
- **Strategy Citations:** JSON references and research foundations

**Key Features Demonstrated:**
- WIDA Key Language Use alignment (Narrate, Inform, Explain, Argue)
- ELD standard generation (ELD-LA.grade-cluster.function.domain)
- Proficiency differentiation (Levels 1-2, 3-4, 5-6)
- Grade-cluster developmental appropriateness
- Asset-based multilingual learner approach

## Transformation Process

### Input Requirements
1. Primary teacher lesson plan (DOCX or markdown table format)
2. Grade level specification
3. Student proficiency range
4. Content area and vocabulary context

### Processing Steps
1. **Phase 1:** Smart category loading from `strategies_pack_v2/_index.json`
2. **Phase 2:** Strategy fine-selection within loaded categories
3. **Phase 3:** Primary-Assessment-First overlay integration
4. **Output:** Word-compatible markdown table with complete enhancements

### Output Format
- Maintains original table structure
- Adds bilingual enhancements to each section
- Includes strategy summary and assessment overlay snapshot
- Ready for copy-paste into Microsoft Word

## Usage

### For Educators
Review these examples to understand:
- What information to include in primary lesson plans
- How bilingual strategies enhance instruction
- What WIDA-aligned objectives look like
- How assessments are adapted for multilingual learners

### For Developers
Use these examples to:
- Test prompt modifications
- Validate output formatting
- Verify strategy selection logic
- Ensure WIDA alignment accuracy

## Related Documentation

- **[Prompt Engine](../../prompt_v4.md)** - Transformation prompt with all protocols
- **[Strategy Dictionary](../bilingual_strategies_dictionary.md)** - Complete strategy reference
- **[Architecture](../architecture_001.md)** - System design and data flow
- **[WIDA Files](../../wida/)** - WIDA 2020 framework and proficiency adaptations
- **[Strategy Pack](../../strategies_pack_v2/)** - Modular strategy files

## Notes

These examples represent typical use cases for elementary grade levels. The system supports K-12 with grade-appropriate adaptations through the `[GRADE_LEVEL_VARIABLE]` system in the prompt engine.
