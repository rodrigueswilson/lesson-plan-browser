# JSON Output Implementation Plan
## Structured Output with Deterministic Rendering

**Version:** 1.0  
**Date:** 2025-10-04  
**Purpose:** Implement JSON schema + Jinja2 renderer for consistent, validated lesson plan output  
**Status:** Planning - Awaiting Review

---

## Executive Summary

### Problem Statement

**Current State:**
- LLM generates markdown directly in `prompt_v4.md`
- Inconsistent formatting (spacing, `<br>` usage, structure)
- No validation of output structure
- Difficult to maintain consistent format across runs
- Hard to programmatically enforce layout
- Cannot easily render to multiple formats (Markdown, DOCX)

**Desired State:**
- Consistent output format every time
- Validated structure before rendering
- Separation of content generation (LLM) from presentation (templates)
- Easy to modify format without changing prompt
- Support for multiple output formats (Markdown, DOCX)
- Testable and maintainable

### Proposed Solution

**Architecture: JSON Schema + Jinja2 Renderer**

```
LLM (prompt_v4.md) → Generates JSON (structured data)
         ↓
JSON Schema Validation → Ensures structure correctness
         ↓
Jinja2 Template Engine → Renders to Markdown/DOCX
         ↓
Consistent Output → Same format every time
```

**Key Benefits:**
1. ✅ **Separation of Concerns:** Content generation vs. presentation
2. ✅ **Validation:** Catch malformed output immediately
3. ✅ **Consistency:** Exact same format every time
4. ✅ **Flexibility:** Change format without touching prompt
5. ✅ **Multi-format:** Render to Markdown, DOCX, HTML, etc.
6. ✅ **Testability:** Snapshot tests ensure no regressions

---

## Detailed Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     INPUT LAYER                              │
│  Primary Teacher Lesson Plan (DOCX) + Grade Level           │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                  LLM PROCESSING                              │
│  prompt_v4.md → LLM → JSON Output (structured data)         │
│  - 5-phase pipeline (strategies, co-teaching, assessment)   │
│  - Outputs pure JSON (no markdown formatting)               │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                 VALIDATION LAYER                             │
│  JSON Schema Validator (lesson_output_schema.json)          │
│  - Validates structure, required fields, data types         │
│  - Returns specific errors if validation fails              │
│  - Triggers retry with error feedback if needed             │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                 RENDERING LAYER                              │
│  Jinja2 Template Engine + Templates                         │
│  - lesson_plan.md.jinja2 (main template)                    │
│  - Cell-specific templates (objective, tailored, etc.)      │
│  - Deterministic rendering (same input → same output)       │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                   OUTPUT LAYER                               │
│  - Markdown table (Word-compatible)                         │
│  - DOCX (direct rendering via python-docx)                  │
│  - HTML (future: web preview)                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 0: Foundations & Observability (Week 0-1)

#### Objective
Establish guardrails so the JSON pipeline can be toggled, monitored, and rolled back without impacting current users.

#### Deliverables

- **Feature flag:** `ENABLE_JSON_OUTPUT` (backend + prompt toggle) to run legacy markdown and JSON side-by-side.
- **Telemetry hooks:** Structured logs for raw JSON responses, validation outcomes, render results, retry count, and token usage (e.g., `logs/json_pipeline.log`).
- **Error dashboard:** Lightweight Grafana panel/CSV export summarizing success %, top validation errors, average retries, render latency, token footprint.
- **Storage policy:** Retain last N validated payloads per user for debugging; redact PII before persistence.
- **Pre-commit checks:** Enforce schema lint (`check-jsonschema`) and template lint (`jinja-lint`) so malformed assets never land in main.
- **Runbook stub:** “JSON pipeline toggle & observability” doc describing how to flip the flag, inspect logs, and roll back.

#### Notes

- Keep the flag default `false` until Phase 4 validation passes.
- Logging must be asynchronous/non-blocking to avoid performance regressions.

---

### Phase 1: JSON Schema Definition (Week 1)

#### Objective
Define comprehensive JSON schema that captures all lesson plan components with strict validation rules.

#### Deliverables

**File:** `schemas/lesson_output_schema.json`

**Schema Structure:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Bilingual Lesson Plan Output",
  "type": "object",
  "required": ["metadata", "days"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["week_of", "grade", "subject", "homeroom"],
      "properties": {
        "week_of": { "type": "string", "pattern": "^\\d{1,2}/\\d{1,2}-\\d{1,2}/\\d{1,2}$" },
        "grade": { "type": "string" },
        "subject": { "type": "string" },
        "homeroom": { "type": "string" }
      }
    },
    "days": {
      "type": "object",
      "required": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "properties": {
        "monday": { "$ref": "#/definitions/day_plan" },
        "tuesday": { "$ref": "#/definitions/day_plan" },
        "wednesday": { "$ref": "#/definitions/day_plan" },
        "thursday": { "$ref": "#/definitions/day_plan" },
        "friday": { "$ref": "#/definitions/day_plan" }
      }
    }
  },
  "definitions": {
    "day_plan": { ... }
  }
}
```

**Key Definitions:**

1. **`day_plan`** - Complete structure for one day
   - `unit_lesson` (string)
   - `objective` (object with content_objective, student_goal, wida_objective)
   - `anticipatory_set` (object with original_content, bilingual_bridge)
   - `tailored_instruction` (object with co_teaching_model, ell_support, etc.)
   - `misconceptions` (object with original_content, linguistic_note)
   - `assessment` (object with primary_assessment, bilingual_overlay)
   - `homework` (object with original_content, family_connection)

2. **`co_teaching_model`** - Co-teaching structure
   - `model_name` (enum: Station, Parallel, Team, Alternative, etc.)
   - `rationale` (string)
   - `wida_context` (string)
   - `phase_plan` (array of phase objects with name, minutes, teacher roles)
   - `implementation_notes` (array of strings)
   - `warnings` (array of strings, optional)

3. **`linguistic_note`** - Misconception structure
   - `pattern_id` (enum: subject_pronoun_omission, adjective_placement, etc.)
   - `note` (string)
   - `prevention_tip` (string)

4. **`bilingual_overlay`** - Assessment overlay structure
   - `instrument` (string)
   - `wida_mapping` (string)
   - `supports_by_level` (object with levels_1_2, levels_3_4, levels_5_6)
   - `scoring_lens` (string)
   - `constraints_honored` (string)

**Validation Rules:**
- Required fields enforcement
- String length limits (e.g., student_goal max 80 chars)
- Enum validation (e.g., co-teaching model names)
- Array size constraints (e.g., ell_support: 3-5 items)
- Pattern matching (e.g., date formats)
- Numeric constraints (e.g., phase minutes: 1-45)

#### Testing
- Validate schema itself using JSON Schema meta-validator
- Create 5 sample valid JSON files (different grade levels, subjects)
- Create 5 sample invalid JSON files (missing fields, wrong types, etc.)
- Verify validation catches all errors

---

### Phase 2: Prompt Modification (Week 1-2)

#### Objective
Update `prompt_v4.md` to output pure JSON instead of markdown tables.

#### Changes to prompt_v4.md

**Add New Section: "JSON Output Format"**

Location: After "Required Output Structure" section

```markdown
## **CRITICAL: JSON Output Format**

### **Output Mode: JSON ONLY**

Your response MUST be valid JSON matching the schema below. 

**IMPORTANT RULES:**
1. Output ONLY the JSON object - no text before or after
2. Do NOT wrap in markdown code blocks (no ```json```)
3. Ensure all strings are properly escaped
4. Use double quotes for all keys and string values
5. Do not include comments in JSON
6. Validate structure matches schema exactly

### **JSON Structure Template**

```json
{
  "metadata": {
    "week_of": "10/6-10/10",
    "grade": "7",
    "subject": "Social Studies",
    "homeroom": "302"
  },
  "days": {
    "monday": {
      "unit_lesson": "Unit One Lesson Seven",
      "objective": {
        "content_objective": "Students will be able to explain how systems of law and banking enabled growth in trade, wealth, and peace",
        "student_goal": "I will explain Roman systems using evidence and a graphic organizer",
        "wida_objective": "Students will use language to explain how Roman law, banking, and Pax Romana enabled economic growth (ELD-SS.6-8.Explain.Reading/Writing) by using cognate awareness and graphic organizers with Portuguese-English vocabulary bridges appropriate for WIDA levels 2-5, producing a written explanation that demonstrates understanding of cause-effect relationships in historical systems."
      },
      "anticipatory_set": {
        "original_content": "Students will respond to an everybody writes.",
        "bilingual_bridge": "Preview key Portuguese-English cognates on board: lei/law, banco/bank, comércio/trade, paz/peace. Quick L1 connection: 'Como as leis ajudam o comércio?' (How do laws help trade?)"
      },
      "tailored_instruction": {
        "original_content": "Engage / Introduction: Briefly introduce the key systems that helped Rome grow: Roman law, banking, and the Pax Romana. Explain that these systems supported trade, created wealth, and maintained peace.",
        "co_teaching_model": {
          "model_name": "Station Teaching",
          "rationale": "Mixed range (4+ levels) needs differentiated stations or dual support",
          "wida_context": "Mixed range with typical 7th grade distribution (Levels 2-5), requiring differentiated small-group support for complex historical content",
          "phase_plan": [
            {
              "phase_name": "Warmup",
              "minutes": 5,
              "bilingual_teacher_role": "Introduce stations/rotation; Preview vocab (L1)",
              "primary_teacher_role": "Content objective",
              "details": ""
            },
            {
              "phase_name": "Practice",
              "minutes": 30,
              "bilingual_teacher_role": "Station 1: Intensive vocabulary/L1 cognate work with Levels 2-3",
              "primary_teacher_role": "Station 2: Content application with Levels 4-5",
              "details": "Station 3 (Independent): Bilingual materials practice (all levels rotate). Rotation: 10 minutes per station with visual timer"
            },
            {
              "phase_name": "Closure",
              "minutes": 10,
              "bilingual_teacher_role": "Whole-group debrief and exit ticket check",
              "primary_teacher_role": "Whole-group debrief and exit ticket check",
              "details": ""
            }
          ],
          "implementation_notes": [
            "Prepare 3 station signs, rotation chart, visual timer",
            "Station 1 materials: Cognate cards, bilingual vocabulary chart",
            "Station 2 materials: Cornell Notes templates, content handouts",
            "Station 3 materials: Bilingual reading passages, word banks, answer keys"
          ],
          "warnings": []
        },
        "ell_support": [
          {
            "strategy_id": "cognate_awareness",
            "strategy_name": "Cognate Awareness",
            "implementation": "Create bilingual vocabulary anchor chart with Portuguese-English cognates: lei/law, sistema/system, economia/economy, império/empire. Post visibly during slideshow.",
            "proficiency_levels": "Levels 2-5"
          },
          {
            "strategy_id": "graphic_organizers",
            "strategy_name": "Graphic Organizers",
            "implementation": "Provide Cornell Notes template with pre-filled headers in both languages. Left column: 'Conceitos Principais/Key Concepts.' Right: 'Detalhes/Details.'",
            "proficiency_levels": "Levels 2-4"
          },
          {
            "strategy_id": "sentence_frames",
            "strategy_name": "Sentence Frames",
            "implementation": "Exit ticket frames: 'Roman ___ helped Rome grow because ___.' / 'O sistema romano de ___ ajudou porque ___.'",
            "proficiency_levels": "Levels 2-3"
          }
        ],
        "special_needs_support": [
          "Visual timeline of Roman systems; color-code law (blue), banking (green), Pax Romana (gold)"
        ],
        "materials": [
          "Bilingual vocabulary chart (poster paper)",
          "Cornell Notes template (handout)",
          "Sentence frame strips"
        ]
      },
      "misconceptions": {
        "original_content": "Students may believe there is no correlation between trade and law",
        "linguistic_note": {
          "pattern_id": "subject_pronoun_omission",
          "note": "Portuguese speakers often drop subject pronouns ('Go to school' instead of 'I go to school') because verb conjugation shows the person",
          "prevention_tip": "Use sentence frames that explicitly include subject pronouns: 'I [verb]...', 'She [verb]...', 'They [verb]...'"
        }
      },
      "assessment": {
        "primary_assessment": "Exit Ticket",
        "bilingual_overlay": {
          "instrument": "Written exit ticket (1-2 sentences)",
          "wida_mapping": "Explain + ELD-SS.6-8.Writing + Levels 2-5",
          "supports_by_level": {
            "levels_1_2": "Sentence frame provided, word bank with cognates, allow L1 draft then translate",
            "levels_3_4": "Sentence starter provided, cognate chart reference, bilingual dictionary allowed",
            "levels_5_6": "Open response, optional sentence frames, focus on academic vocabulary"
          },
          "scoring_lens": "Accept responses showing understanding of cause-effect relationship; credit use of academic vocabulary (law/lei, banking/banco, peace/paz); allow code-switching if meaning is clear",
          "constraints_honored": "No new materials; uses existing exit ticket format"
        }
      },
      "homework": {
        "original_content": "",
        "family_connection": "Ask family: 'Como as leis ajudam nossa comunidade?' (How do laws help our community?) Discuss in Portuguese/English and share one example in class."
      }
    },
    "tuesday": { ... },
    "wednesday": { ... },
    "thursday": { ... },
    "friday": { ... }
  }
}
```

### **Validation and Error Handling**

If your JSON output fails validation, you will receive specific error messages. Common errors to avoid:

1. **Missing Required Fields:** Ensure all required properties are present
2. **Wrong Data Types:** Use strings for text, integers for numbers, arrays for lists
3. **Invalid Enum Values:** Co-teaching model names must match exactly (e.g., "Station Teaching" not "station")
4. **Array Size Violations:** ell_support must have 3-5 items
5. **String Length Violations:** student_goal must be ≤80 characters

### **Testing Your JSON**

Before submitting, verify:
- [ ] Valid JSON syntax (use jsonlint.com or similar)
- [ ] All required fields present
- [ ] Proper nesting and structure
- [ ] No trailing commas
- [ ] Proper string escaping
```

**Update Existing Sections:**

1. **Pre-Execution Validation Checklist** - Add:
   ```markdown
   * [ ] JSON output mode enabled
   * [ ] Schema validation configured
   * [ ] Error handling and retry logic ready
   ```

2. **Post-Output Requirements** - Replace with:
   ```markdown
   ## **Post-Output Requirements**

   **JSON Delivery:** Output valid JSON matching lesson_output_schema.json

   **No Additional Text:** Do not include explanations, summaries, or markdown formatting

   **Validation:** JSON will be validated before rendering to final format
   ```

#### Testing
- Test with 3 sample lesson plans (different grades/subjects)
- Verify LLM outputs valid JSON
- Test error handling with intentionally malformed JSON
- Measure token usage impact (JSON vs. markdown)

---

### Phase 3: Jinja2 Template Creation (Week 2)

#### Objective
Create modular Jinja2 templates for deterministic rendering of JSON to markdown tables.

#### Template Structure

**Directory:** `templates/`

```
templates/
├── lesson_plan.md.jinja2           # Main template (table structure)
├── cells/
│   ├── objective.jinja2             # Objective cell content
│   ├── anticipatory_set.jinja2      # Anticipatory Set cell content
│   ├── tailored_instruction.jinja2  # Tailored Instruction cell content
│   ├── misconceptions.jinja2        # Misconceptions cell content
│   ├── assessment.jinja2            # Assessment cell content
│   └── homework.jinja2              # Homework cell content
└── partials/
    ├── co_teaching_model.jinja2     # Co-teaching model section
    ├── ell_support.jinja2           # ELL support bullets
    └── bilingual_overlay.jinja2     # Assessment overlay section
```

#### Main Template: `lesson_plan.md.jinja2`

```jinja2
# Enhanced Bilingual Lesson Plan - {{ metadata.subject }}

**Week of:** {{ metadata.week_of }}
**Grade:** {{ metadata.grade }}
**Homeroom:** {{ metadata.homeroom }}

| | MONDAY | TUESDAY | WEDNESDAY | THURSDAY | FRIDAY |
|---|---|---|---|---|---|
| **Unit, Lesson #, Module:** | {{ days.monday.unit_lesson }} | {{ days.tuesday.unit_lesson }} | {{ days.wednesday.unit_lesson }} | {{ days.thursday.unit_lesson }} | {{ days.friday.unit_lesson }} |
| **Objective:** | {% include 'cells/objective.jinja2' with {'day': days.monday} %} | {% include 'cells/objective.jinja2' with {'day': days.tuesday} %} | {% include 'cells/objective.jinja2' with {'day': days.wednesday} %} | {% include 'cells/objective.jinja2' with {'day': days.thursday} %} | {% include 'cells/objective.jinja2' with {'day': days.friday} %} |
| **Anticipatory Set:** | {% include 'cells/anticipatory_set.jinja2' with {'day': days.monday} %} | {% include 'cells/anticipatory_set.jinja2' with {'day': days.tuesday} %} | {% include 'cells/anticipatory_set.jinja2' with {'day': days.wednesday} %} | {% include 'cells/anticipatory_set.jinja2' with {'day': days.thursday} %} | {% include 'cells/anticipatory_set.jinja2' with {'day': days.friday} %} |
| **Tailored Instruction:** | {% include 'cells/tailored_instruction.jinja2' with {'day': days.monday} %} | {% include 'cells/tailored_instruction.jinja2' with {'day': days.tuesday} %} | {% include 'cells/tailored_instruction.jinja2' with {'day': days.wednesday} %} | {% include 'cells/tailored_instruction.jinja2' with {'day': days.thursday} %} | {% include 'cells/tailored_instruction.jinja2' with {'day': days.friday} %} |
| **Misconceptions:** | {% include 'cells/misconceptions.jinja2' with {'day': days.monday} %} | {% include 'cells/misconceptions.jinja2' with {'day': days.tuesday} %} | {% include 'cells/misconceptions.jinja2' with {'day': days.wednesday} %} | {% include 'cells/misconceptions.jinja2' with {'day': days.thursday} %} | {% include 'cells/misconceptions.jinja2' with {'day': days.friday} %} |
| **Assessment:** | {% include 'cells/assessment.jinja2' with {'day': days.monday} %} | {% include 'cells/assessment.jinja2' with {'day': days.tuesday} %} | {% include 'cells/assessment.jinja2' with {'day': days.wednesday} %} | {% include 'cells/assessment.jinja2' with {'day': days.thursday} %} | {% include 'cells/assessment.jinja2' with {'day': days.friday} %} |
| **Homework:** | {% include 'cells/homework.jinja2' with {'day': days.monday} %} | {% include 'cells/homework.jinja2' with {'day': days.tuesday} %} | {% include 'cells/homework.jinja2' with {'day': days.wednesday} %} | {% include 'cells/homework.jinja2' with {'day': days.thursday} %} | {% include 'cells/homework.jinja2' with {'day': days.friday} %} |
```

#### Cell Templates

**`cells/objective.jinja2`:**
```jinja2
**Content Objective:** {{ day.objective.content_objective }}

**Student Goal (I will...):** {{ day.objective.student_goal }}

**WIDA Bilingual Language Objective:** {{ day.objective.wida_objective }}
```

**`cells/tailored_instruction.jinja2`:**
```jinja2
{{ day.tailored_instruction.original_content }}

---

{% include 'partials/co_teaching_model.jinja2' with {'model': day.tailored_instruction.co_teaching_model} %}

---

{% include 'partials/ell_support.jinja2' with {'support': day.tailored_instruction.ell_support} %}

**Special Needs Support:**
{% for item in day.tailored_instruction.special_needs_support %}
• {{ item }}
{% endfor %}

**Materials:** {{ day.tailored_instruction.materials | join(', ') }}
```

**`partials/co_teaching_model.jinja2`:**
```jinja2
**Co-Teaching Model:** {{ model.model_name }}

**Rationale:** {{ model.rationale }}

**WIDA Proficiency Context:** {{ model.wida_context }}

**45-Minute Structure:**
{% for phase in model.phase_plan %}
* **{{ phase.phase_name }} ({{ phase.minutes }} min):**
  * Bilingual Teacher: {{ phase.bilingual_teacher_role }}
  * Primary Teacher: {{ phase.primary_teacher_role }}
{% if phase.details %}  * {{ phase.details }}{% endif %}
{% endfor %}

**Implementation Notes:**
{% for note in model.implementation_notes %}
* {{ note }}
{% endfor %}

{% if model.warnings %}
**Warnings:**
{% for warning in model.warnings %}
* {{ warning }}
{% endfor %}
{% endif %}
```

**`cells/misconceptions.jinja2`:**
```jinja2
{{ day.misconceptions.original_content }}

**Linguistic Note (Portuguese→English):**
{{ day.misconceptions.linguistic_note.note }} {{ day.misconceptions.linguistic_note.prevention_tip }}
```

**`cells/assessment.jinja2`:**
```jinja2
{{ day.assessment.primary_assessment }}

{% include 'partials/bilingual_overlay.jinja2' with {'overlay': day.assessment.bilingual_overlay} %}
```

**`partials/bilingual_overlay.jinja2`:**
```jinja2
**Bilingual Assessment Overlay (Primary-Assessment-First):**
**Instrument:** {{ overlay.instrument }}
**WIDA Mapping:** {{ overlay.wida_mapping }}
**Supports by Level:**
• Levels 1-2: {{ overlay.supports_by_level.levels_1_2 }}
• Levels 3-4: {{ overlay.supports_by_level.levels_3_4 }}
• Levels 5-6: {{ overlay.supports_by_level.levels_5_6 }}
**Scoring Lens:** {{ overlay.scoring_lens }}
**Constraints Honored:** {{ overlay.constraints_honored }}
```

#### Template Features

**Consistent Spacing:**
- Exactly one blank line between sections (enforced by template)
- `<br>` usage controlled by template (not LLM)
- Consistent bullet formatting (• vs. - vs. *)

**Conditional Rendering:**
- Show warnings only if present
- Handle empty original_content gracefully
- Skip sections if data missing (with clear placeholder)

**Filters and Functions:**
- `| join(', ')` for material lists
- `| length` for validation
- Custom filters for text formatting if needed

#### Testing
- Render 5 sample JSON files
- Compare output byte-by-byte (should be identical for same input)
- Test with missing optional fields
- Test with empty arrays
- Verify Word-compatibility of markdown output

---

### Phase 4: Python Renderer Implementation (Week 2-3)

#### Objective
Build Python script to validate JSON and render templates with error handling and retry logic.

#### File Structure

```
tools/
├── render_lesson_plan.py          # Main renderer
├── validate_schema.py              # Schema validation
├── retry_logic.py                  # LLM retry with error feedback
└── tests/
    ├── test_validation.py          # Validation tests
    ├── test_rendering.py           # Rendering tests
    └── fixtures/
        ├── valid_lesson_1.json     # Test data
        ├── invalid_lesson_1.json   # Test data
        └── expected_output_1.md    # Expected output
```

#### Main Renderer: `render_lesson_plan.py`

```python
"""
Lesson Plan Renderer
Validates JSON against schema and renders to markdown using Jinja2 templates.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Tuple, List

import jsonschema
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class LessonPlanRenderer:
    """Validates and renders lesson plans from JSON to markdown."""
    
    def __init__(self, schema_path: Path, template_dir: Path):
        """
        Initialize renderer.
        
        Args:
            schema_path: Path to JSON schema file
            template_dir: Path to Jinja2 templates directory
        """
        self.schema_path = schema_path
        self.template_dir = template_dir
        
        # Load schema
        with open(schema_path) as f:
            self.schema = json.load(f)
        
        # Setup Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
    
    def validate(self, data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate lesson plan JSON against schema.
        
        Args:
            data: Lesson plan data as dictionary
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            jsonschema.validate(data, self.schema)
            return True, []
        except jsonschema.ValidationError as e:
            # Collect all validation errors
            errors = [str(e)]
            
            # Get additional context
            if e.path:
                path = '.'.join(str(p) for p in e.path)
                errors.append(f"Error at: {path}")
            
            if e.validator_value:
                errors.append(f"Expected: {e.validator_value}")
            
            return False, errors
        except jsonschema.SchemaError as e:
            return False, [f"Schema error: {str(e)}"]
    
    def render(self, data: Dict, output_path: Path) -> str:
        """
        Render lesson plan from JSON data to markdown.
        
        Args:
            data: Validated lesson plan data
            output_path: Path to write output file
            
        Returns:
            Rendered markdown string
        """
        try:
            template = self.env.get_template('lesson_plan.md.jinja2')
            output = template.render(**data)
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output)
            
            return output
            
        except TemplateNotFound as e:
            raise FileNotFoundError(f"Template not found: {e}")
        except Exception as e:
            raise RuntimeError(f"Rendering error: {str(e)}")
    
    def render_from_file(self, json_path: Path, output_path: Path) -> Tuple[bool, str]:
        """
        Load JSON file, validate, and render.
        
        Args:
            json_path: Path to JSON input file
            output_path: Path to markdown output file
            
        Returns:
            Tuple of (success, message)
        """
        # Load JSON
        try:
            with open(json_path, encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
        except FileNotFoundError:
            return False, f"File not found: {json_path}"
        
        # Validate
        valid, errors = self.validate(data)
        if not valid:
            error_msg = "Validation errors:\n" + "\n".join(f"  - {e}" for e in errors)
            return False, error_msg
        
        # Render
        try:
            self.render(data, output_path)
            return True, f"Successfully rendered to {output_path}"
        except Exception as e:
            return False, f"Rendering failed: {str(e)}"


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Render lesson plan from JSON')
    parser.add_argument('input', type=Path, help='Input JSON file')
    parser.add_argument('output', type=Path, help='Output markdown file')
    parser.add_argument('--schema', type=Path, 
                       default=Path('schemas/lesson_output_schema.json'),
                       help='JSON schema file')
    parser.add_argument('--templates', type=Path,
                       default=Path('templates'),
                       help='Templates directory')
    
    args = parser.parse_args()
    
    # Initialize renderer
    renderer = LessonPlanRenderer(args.schema, args.templates)
    
    # Render
    success, message = renderer.render_from_file(args.input, args.output)
    
    print(message)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
```

#### Retry Logic: `retry_logic.py`

```python
"""
LLM retry logic with validation error feedback.
"""

import json
from typing import Dict, Callable, Optional

from validate_schema import LessonPlanRenderer


def generate_with_retry(
    llm_generate: Callable[[str], str],
    initial_prompt: str,
    renderer: LessonPlanRenderer,
    max_retries: int = 3
) -> Optional[Dict]:
    """
    Generate lesson plan with automatic retry on validation errors.
    
    Args:
        llm_generate: Function that takes prompt and returns LLM response
        initial_prompt: Initial prompt to send to LLM
        renderer: LessonPlanRenderer instance for validation
        max_retries: Maximum number of retry attempts
        
    Returns:
        Validated lesson plan data or None if all retries failed
    """
    prompt = initial_prompt
    
    for attempt in range(max_retries):
        # Generate response
        response = llm_generate(prompt)
        
        # Try to parse JSON
        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            # JSON parsing failed - provide specific feedback
            error_prompt = f"""
Your previous response was not valid JSON. Error: {str(e)}

Please ensure:
1. Output is pure JSON (no markdown code blocks)
2. All strings use double quotes
3. No trailing commas
4. Proper escaping of special characters

Generate the lesson plan JSON again, ensuring valid JSON syntax.
"""
            prompt = error_prompt
            continue
        
        # Validate against schema
        valid, errors = renderer.validate(data)
        
        if valid:
            return data
        
        # Validation failed - provide specific feedback
        error_list = "\n".join(f"  {i+1}. {e}" for i, e in enumerate(errors))
        error_prompt = f"""
Your previous JSON output had validation errors:

{error_list}

Please correct these errors and generate the lesson plan JSON again.
Ensure all required fields are present and data types match the schema.
"""
        prompt = error_prompt
    
    # All retries exhausted
    return None


def format_validation_errors_for_llm(errors: list) -> str:
    """
    Format validation errors in a way that's helpful for LLM correction.
    
    Args:
        errors: List of validation error messages
        
    Returns:
        Formatted error message for LLM
    """
    formatted = []
    
    for error in errors:
        # Extract key information
        if "is a required property" in error:
            field = error.split("'")[1]
            formatted.append(f"Missing required field: '{field}'")
        elif "is not of type" in error:
            formatted.append(f"Wrong data type: {error}")
        elif "is not one of" in error:
            formatted.append(f"Invalid enum value: {error}")
        else:
            formatted.append(error)
    
    return "\n".join(formatted)
```

#### Testing Framework

**`tests/test_rendering.py`:**
```python
"""
Test rendering consistency and correctness.
"""

import json
from pathlib import Path
import pytest

from render_lesson_plan import LessonPlanRenderer


@pytest.fixture
def renderer():
    """Create renderer instance for testing."""
    schema_path = Path('schemas/lesson_output_schema.json')
    template_dir = Path('templates')
    return LessonPlanRenderer(schema_path, template_dir)


def test_render_consistency(renderer, tmp_path):
    """Test that rendering produces identical output for same input."""
    # Load test data
    with open('tests/fixtures/valid_lesson_1.json') as f:
        data = json.load(f)
    
    # Render twice
    output1 = tmp_path / 'out1.md'
    output2 = tmp_path / 'out2.md'
    
    renderer.render(data, output1)
    renderer.render(data, output2)
    
    # Compare byte-by-byte
    assert output1.read_bytes() == output2.read_bytes()


def test_render_matches_snapshot(renderer, tmp_path):
    """Test that rendering matches expected output."""
    # Load test data
    with open('tests/fixtures/valid_lesson_1.json') as f:
        data = json.load(f)
    
    # Render
    output = tmp_path / 'output.md'
    renderer.render(data, output)
    
    # Compare with expected
    expected = Path('tests/fixtures/expected_output_1.md').read_text()
    actual = output.read_text()
    
    assert actual == expected


def test_validation_catches_errors(renderer):
    """Test that validation catches common errors."""
    # Load invalid data
    with open('tests/fixtures/invalid_lesson_1.json') as f:
        data = json.load(f)
    
    # Validate
    valid, errors = renderer.validate(data)
    
    assert not valid
    assert len(errors) > 0
```

---

### Phase 5: DOCX Renderer (Week 3-4)

#### Objective
Add direct DOCX rendering using python-docx to maintain district template formatting.

#### Implementation

**File:** `tools/render_to_docx.py`

```python
"""
DOCX Renderer
Renders lesson plan JSON directly to DOCX using district template.
"""

from pathlib import Path
from typing import Dict

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


class DOCXRenderer:
    """Renders lesson plans to DOCX format."""
    
    def __init__(self, template_path: Path):
        """
        Initialize DOCX renderer.
        
        Args:
            template_path: Path to district DOCX template
        """
        self.template_path = template_path
    
    def render(self, data: Dict, output_path: Path):
        """
        Render lesson plan to DOCX.
        
        Args:
            data: Validated lesson plan data
            output_path: Path to output DOCX file
        """
        # Load template
        doc = Document(self.template_path)
        
        # Find lesson plan table (assume first table)
        table = doc.tables[0]
        
        # Populate metadata (header cells)
        self._populate_header(table, data['metadata'])
        
        # Populate each day
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        for col_idx, day in enumerate(days, start=1):
            self._populate_day_column(table, col_idx, data['days'][day])
        
        # Save
        doc.save(output_path)
    
    def _populate_header(self, table, metadata: Dict):
        """Populate header cells with metadata."""
        # Week of, Grade, Homeroom, Subject
        # Exact cell locations depend on template structure
        pass
    
    def _populate_day_column(self, table, col_idx: int, day_data: Dict):
        """Populate one day's column in the table."""
        # Row 0: Unit/Lesson
        self._set_cell_text(table, 0, col_idx, day_data['unit_lesson'])
        
        # Row 1: Objective
        objective_text = self._format_objective(day_data['objective'])
        self._set_cell_text(table, 1, col_idx, objective_text)
        
        # Row 2: Anticipatory Set
        anticipatory_text = self._format_anticipatory_set(day_data['anticipatory_set'])
        self._set_cell_text(table, 2, col_idx, anticipatory_text)
        
        # Row 3: Tailored Instruction
        tailored_text = self._format_tailored_instruction(day_data['tailored_instruction'])
        self._set_cell_text(table, 3, col_idx, tailored_text)
        
        # Row 4: Misconceptions
        misconceptions_text = self._format_misconceptions(day_data['misconceptions'])
        self._set_cell_text(table, 4, col_idx, misconceptions_text)
        
        # Row 5: Assessment
        assessment_text = self._format_assessment(day_data['assessment'])
        self._set_cell_text(table, 5, col_idx, assessment_text)
        
        # Row 6: Homework
        homework_text = self._format_homework(day_data['homework'])
        self._set_cell_text(table, 6, col_idx, homework_text)
    
    def _set_cell_text(self, table, row: int, col: int, text: str):
        """Set cell text with proper formatting."""
        cell = table.cell(row, col)
        cell.text = text
        
        # Apply formatting (font, size, etc.)
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.name = 'Calibri'
                run.font.size = Pt(11)
    
    def _format_objective(self, objective: Dict) -> str:
        """Format objective cell content."""
        return (
            f"Content Objective: {objective['content_objective']}\n\n"
            f"Student Goal (I will...): {objective['student_goal']}\n\n"
            f"WIDA Bilingual Language Objective: {objective['wida_objective']}"
        )
    
    def _format_tailored_instruction(self, tailored: Dict) -> str:
        """Format tailored instruction cell content."""
        parts = [tailored['original_content']]
        
        # Co-teaching model
        model = tailored['co_teaching_model']
        parts.append(f"\n---\n\nCo-Teaching Model: {model['model_name']}")
        parts.append(f"Rationale: {model['rationale']}")
        parts.append(f"WIDA Context: {model['wida_context']}")
        
        # Phase plan
        parts.append("\n45-Minute Structure:")
        for phase in model['phase_plan']:
            parts.append(f"• {phase['phase_name']} ({phase['minutes']} min):")
            parts.append(f"  - Bilingual Teacher: {phase['bilingual_teacher_role']}")
            parts.append(f"  - Primary Teacher: {phase['primary_teacher_role']}")
            if phase.get('details'):
                parts.append(f"  - {phase['details']}")
        
        # Implementation notes
        if model['implementation_notes']:
            parts.append("\nImplementation Notes:")
            for note in model['implementation_notes']:
                parts.append(f"• {note}")
        
        # ELL Support
        parts.append("\n---\n\nELL Support:")
        for strategy in tailored['ell_support']:
            parts.append(f"• {strategy['strategy_name']} ({strategy['proficiency_levels']}): {strategy['implementation']}")
        
        # Special Needs
        parts.append("\nSpecial Needs Support:")
        for support in tailored['special_needs_support']:
            parts.append(f"• {support}")
        
        # Materials
        materials = ', '.join(tailored['materials'])
        parts.append(f"\nMaterials: {materials}")
        
        return '\n'.join(parts)
    
    # ... other formatting methods
```

#### Integration with FastAPI

**Update backend to support both formats:**

```python
@app.post("/api/generate-lesson-plan")
async def generate_lesson_plan(
    request: LessonPlanRequest,
    output_format: str = "markdown"  # or "docx"
):
    """Generate lesson plan in requested format."""
    
    # Generate JSON from LLM
    json_data = await generate_json_from_llm(request)
    
    # Validate
    valid, errors = renderer.validate(json_data)
    if not valid:
        raise HTTPException(400, detail=errors)
    
    # Render to requested format
    if output_format == "markdown":
        output = renderer.render(json_data, output_path)
        return {"format": "markdown", "content": output}
    elif output_format == "docx":
        docx_renderer.render(json_data, output_path)
        return FileResponse(output_path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        raise HTTPException(400, detail="Invalid format")
```

---

## Integration with Existing System

### FastAPI Backend Integration

**Update:** `backend/api/lesson_plan.py`

```python
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from tools.render_lesson_plan import LessonPlanRenderer
from tools.render_to_docx import DOCXRenderer
from tools.retry_logic import generate_with_retry

router = APIRouter()

# Initialize renderers
markdown_renderer = LessonPlanRenderer(
    schema_path=Path('schemas/lesson_output_schema.json'),
    template_dir=Path('templates')
)

docx_renderer = DOCXRenderer(
    template_path=Path('input/Lesson Plan Template SY\'25-26.docx')
)


@router.post("/generate")
async def generate_lesson_plan(request: LessonPlanRequest):
    """
    Generate lesson plan with JSON validation and rendering.
    
    Returns JSON data for preview or download.
    """
    # Generate JSON from LLM with retry logic
    json_data = generate_with_retry(
        llm_generate=lambda p: call_llm(p, request),
        initial_prompt=build_prompt(request),
        renderer=markdown_renderer,
        max_retries=3
    )
    
    if json_data is None:
        raise HTTPException(500, detail="Failed to generate valid lesson plan after retries")
    
    return {"status": "success", "data": json_data}


@router.post("/render/markdown")
async def render_markdown(data: dict):
    """Render validated JSON to markdown."""
    output_path = Path(f"output/lesson_plan_{timestamp()}.md")
    
    try:
        markdown_renderer.render(data, output_path)
        return FileResponse(output_path, media_type="text/markdown")
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.post("/render/docx")
async def render_docx(data: dict):
    """Render validated JSON to DOCX."""
    output_path = Path(f"output/lesson_plan_{timestamp()}.docx")
    
    try:
        docx_renderer.render(data, output_path)
        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="lesson_plan.docx"
        )
    except Exception as e:
        raise HTTPException(500, detail=str(e))
```

### Tauri Frontend Integration

**Update:** `frontend/src/components/LessonPlanGenerator.tsx`

```typescript
async function generateLessonPlan() {
  setLoading(true);
  
  try {
    // Step 1: Generate JSON
    const response = await fetch('/api/generate', {
      method: 'POST',
      body: JSON.stringify(formData),
      headers: { 'Content-Type': 'application/json' }
    });
    
    const { data } = await response.json();
    setJsonData(data);
    
    // Step 2: Preview (optional)
    setShowPreview(true);
    
  } catch (error) {
    setError(error.message);
  } finally {
    setLoading(false);
  }
}

async function downloadMarkdown() {
  const response = await fetch('/api/render/markdown', {
    method: 'POST',
    body: JSON.stringify(jsonData),
    headers: { 'Content-Type': 'application/json' }
  });
  
  const blob = await response.blob();
  downloadFile(blob, 'lesson_plan.md');
}

async function downloadDOCX() {
  const response = await fetch('/api/render/docx', {
    method: 'POST',
    body: JSON.stringify(jsonData),
    headers: { 'Content-Type': 'application/json' }
  });
  
  const blob = await response.blob();
  downloadFile(blob, 'lesson_plan.docx');
}
```

---

## Testing Strategy

### Unit Tests

1. **Schema Validation Tests**
   - Valid JSON passes
   - Invalid JSON fails with specific errors
   - Edge cases (empty arrays, missing optional fields)

2. **Rendering Tests**
   - Consistency (same input → same output)
   - Snapshot testing (output matches expected)
   - Template error handling
   - Pre-commit integration to guard snapshots (`pytest --snapshot-update` disabled on CI)

3. **Retry Logic Tests**
   - Successful retry after validation error
   - Exhausted retries return None
    - Error message formatting
    - JSON syntax repair helper (e.g., `json_repair`) confirmed to auto-fix minor punctuation issues before re-prompting

### Integration Tests

1. **End-to-End Tests**
   - Full pipeline: prompt → JSON → validation → rendering
   - Multiple formats (markdown, DOCX)
   - Error recovery

2. **Performance Tests**
   - Rendering speed (target: <100ms)
   - Memory usage
    - Concurrent requests
    - Token footprint comparison: markdown vs. JSON payloads (monitor via Phase 0 telemetry)

### User Acceptance Tests

1. **Format Consistency**
   - Generate 10 lesson plans
   - Verify identical formatting
   - Check Word compatibility

2. **Error Handling**
   - Intentionally malformed JSON
   - Missing required fields
   - Invalid enum values

---

## Migration Strategy

### Phase 1: Parallel Operation (Week 4)

- Keep existing markdown generation in prompt
- Add JSON generation as optional mode
- Compare outputs side-by-side
- Validate consistency

### Phase 2: Gradual Rollout (Week 5)

- Enable JSON mode for new users
- Collect feedback on format consistency
- Monitor error rates
- Refine templates based on feedback

### Phase 3: Full Migration (Week 6)

- Switch all users to JSON mode
- Deprecate direct markdown generation
- Update documentation
- Archive old prompt version

---

## Success Metrics

### Technical Metrics

1. **Validation Success Rate:** >95% of LLM outputs pass validation on first try
2. **Rendering Consistency:** 100% identical output for same input
3. **Performance:** Rendering <100ms, validation <50ms
4. **Error Recovery:** >90% successful retry after validation error

### User Experience Metrics

1. **Format Consistency:** User reports of inconsistent formatting drop to zero
2. **Word Compatibility:** 100% of rendered markdown pastes correctly into Word
3. **User Satisfaction:** Positive feedback on output quality
4. **Time Savings:** Reduced manual formatting time

---

## Risks and Mitigation

### Risk 1: LLM Struggles with JSON Output

**Mitigation:**
- Provide clear JSON examples in prompt
- Implement retry logic with specific error feedback
- Add JSON syntax validation before schema validation
- Consider JSON repair libraries (e.g., `json-repair`)

### Risk 2: Template Maintenance Overhead

**Mitigation:**
- Modular template design (easy to update individual cells)
- Version control for templates
- Automated testing catches template breaks
- Documentation for template modification

### Risk 3: Performance Degradation

**Mitigation:**
- Cache rendered templates
- Optimize Jinja2 configuration
- Profile rendering pipeline
- Implement async rendering if needed

### Risk 4: Schema Evolution
### Risk 5: Token Budget & Latency Regression

**Concern:** JSON responses may increase token usage, latency, and cost relative to the current markdown output.

**Mitigation:**
- Track token count per response via Phase 0 telemetry; alert if median increases >20%.
- Trim redundant text (e.g., empty strings, repeated strategy metadata) before sending prompts.
- Enforce stricter max-length constraints in the schema for verbose fields.
- Consider ID references for frequently repeated values (strategy lookup) to shrink payload size.
- Evaluate gzip or streaming responses if/when API support is available.

---

**Mitigation:**
- Semantic versioning for schema
- Backward compatibility checks
- Migration scripts for schema updates
- Clear deprecation policy

---

## Open Questions for Review

### 1. Schema Design

**Question:** Should we use a single monolithic schema or multiple smaller schemas (one per day, one per section)?

**Options:**
- **A:** Single schema (current proposal) - Easier validation, single source of truth
- **B:** Modular schemas - More flexible, easier to evolve

**Recommendation:** Start with single schema, refactor to modular if complexity grows

### 2. Error Handling Strategy

**Question:** How many retries should we allow before giving up?

**Options:**
- **A:** 3 retries (current proposal) - Balance between success and speed
- **B:** 5 retries - Higher success rate but slower
- **C:** Adaptive retries - Based on error type

**Recommendation:** Start with 3, monitor success rates, adjust if needed

### 3. Output Format Priority

**Question:** Should we prioritize markdown or DOCX rendering?

**Options:**
- **A:** Markdown first (current proposal) - Easier to implement, human-readable
- **B:** DOCX first - Matches final output format
- **C:** Both simultaneously - More work but complete solution

**Recommendation:** Markdown first (Phase 3), DOCX second (Phase 5)

### 4. Template Complexity

**Question:** How much logic should live in templates vs. Python?

**Options:**
- **A:** Minimal logic in templates (current proposal) - Easier to maintain
- **B:** Rich logic in templates - More flexible, less Python code
- **C:** Hybrid - Complex logic in Python, simple formatting in templates

**Recommendation:** Minimal logic in templates, complex transformations in Python

### 5. Validation Strictness

**Question:** Should validation be strict (fail on any error) or lenient (allow optional fields missing)?

**Options:**
- **A:** Strict (current proposal) - Ensures complete data
- **B:** Lenient - More forgiving, fewer retries
- **C:** Configurable - User chooses strictness level

**Recommendation:** Strict for required fields, lenient for optional fields

### 6. Caching Strategy

**Question:** Should we cache rendered outputs?

**Options:**
- **A:** No caching (current proposal) - Simpler, always fresh
- **B:** Cache by JSON hash - Faster for repeated renders
- **C:** Cache with TTL - Balance freshness and speed

**Recommendation:** No caching initially, add if performance issues arise

### 7. Preview Functionality

**Question:** Should we provide a preview before final rendering?

**Options:**
- **A:** JSON preview only - Shows raw data
- **B:** Rendered preview - Shows final output
- **C:** Both - Complete visibility

**Recommendation:** Both - JSON for debugging, rendered for user review

### 8. Version Control

**Question:** How should we version schemas and templates?

**Options:**
- **A:** Git tags - Simple, standard
- **B:** Semantic versioning in files - Explicit, trackable
- **C:** Database versioning - Complex but powerful

**Recommendation:** Semantic versioning in files + Git tags

---

## Timeline Summary

| Phase | Duration | Deliverables | Dependencies |
|-------|----------|--------------|--------------|
| **Phase 1: Schema** | Week 1 | lesson_output_schema.json, test fixtures | None |
| **Phase 2: Prompt** | Week 1-2 | Updated prompt_v4.md, JSON examples | Phase 1 |
| **Phase 3: Templates** | Week 2 | Jinja2 templates, cell partials | Phase 1 |
| **Phase 4: Renderer** | Week 2-3 | Python renderer, validation, retry logic | Phase 1, 3 |
| **Phase 5: DOCX** | Week 3-4 | DOCX renderer, template integration | Phase 4 |
| **Phase 6: Integration** | Week 4 | FastAPI/Tauri integration | Phase 4, 5 |
| **Phase 7: Testing** | Week 4-5 | Unit tests, integration tests, UAT | All phases |
| **Phase 8: Migration** | Week 5-6 | Parallel operation, rollout, deprecation | Phase 7 |

**Total Duration:** 6 weeks

---

## Conclusion

This implementation plan provides a comprehensive approach to achieving consistent, validated lesson plan output through JSON schema + Jinja2 rendering. The architecture separates content generation from presentation, enabling:

1. ✅ **Guaranteed consistency** - Same format every time
2. ✅ **Validation** - Catch errors before rendering
3. ✅ **Flexibility** - Easy format changes without prompt updates
4. ✅ **Multi-format** - Render to markdown, DOCX, HTML
5. ✅ **Testability** - Snapshot tests ensure no regressions
6. ✅ **Maintainability** - Clear separation of concerns

The phased approach allows for incremental implementation, testing, and validation at each step, minimizing risk while delivering value early.

**Recommendation:** Proceed with implementation starting with Phase 1 (Schema Definition).

---

**Document Status:** Ready for Review  
**Author:** AI Assistant (Cascade)  
**Date:** 2025-10-04  
**Version:** 1.0  
**Review Required:** Yes - seeking validation before implementation
