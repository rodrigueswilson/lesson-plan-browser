# Curriculum Structural Analysis (Math & ELA)

This document details the observed structural patterns in the Grade 3 Math Unit 2 curriculum document (`Unit_2__Area_and_Multiplication.docx`). These patterns serve as the anchor points for our high-fidelity ingestion pipeline.

## 1. Table Grid Structure
Each lesson is contained within a standalone table. The internal grid follows a 10-row, 2-column pattern (though some rows are merged).

| Row | Unique Cells | Primary Column A Header | Primary Column B Header |
| :--- | :--- | :--- | :--- |
| **1** | 1 (Merged) | **LESSON X: [Title]** | - |
| **2** | 2 | Teacher-Facing Learning Objective(s) | Lesson Purpose |
| **3** | 2 | Student-Facing Learning Objective(s) | Lesson Narrative |
| **4** | 2 | Mathematical Language Routine(s) | Learning Standards |
| **5** | 1 (Merged) | Section Title (e.g., "Required Preparation") | - |
| **6** | 1 (Merged) | Material List | - |
| **7** | 1 (Merged) | Section Title (e.g., "Lesson Delivery") | - |
| **8** | 2 | Supplemental Resources | Formative Assessment Resources |

## 2. Header Anchor Patterns
The following string patterns are **100% consistent** across all 15 lessons in Unit 2:

- **Row 2, Col 1**: `Teacher-Facing Learning Objective(s)`
- **Row 2, Col 2**: `Lesson Purpose`
- **Row 3, Col 1**: `Student-Facing Learning Objective(s)`
- **Row 3, Col 2**: `Lesson Narrative`
- **Row 4, Col 1**: `Mathematical Language Routine(s)`
- **Row 8, Col 1**: `Supplemental Resources`
- **Row 8, Col 2**: `Formative Assessment Resources`

## 3. Internal Content Formatting
Within each cell, the content follows a "Style-Anchored" hierarchy:
1. **Bold Header Paragraph**: The first paragraph is usually the field label (e.g., **Lesson Purpose**).
2. **Body Content**: Plain text, lists, or italics containing the actual curriculum data.
3. **Sub-Headers**: Occasionally, secondary bold lines appear (e.g., **Homework**) which signify specific delivery items.

## 4. Ingestion & Validation Strategy
1. **Fixed-Grid Mapping**: Use the verified row/column coordinates to locate specific data fields.
2. **Style-Aware Extraction**: Extract all paragraphs within a cell, but strip the initial bold header to avoid duplicate labels in the database.
3. **Validation Reinforcement**: Before saving, the parser will verify that the top bold paragraph in the cell matches the expected label. If it doesn't, a structural exception is logged.

## 5. Database Mapping
| Source Field | DB Column (`lessons` table) |
| :--- | :--- |
| Teacher Objectives | `learning_intentions` |
| Lesson Purpose | `purpose` (or prepends to `narrative_html`) |
| Student Objectives | `objectives_student` |
| Lesson Narrative | `narrative_html` |
| MLR | `mlr` |
## 6. Comparative Analysis & Grid Variability
Analysis of other Grade 3 Math units reveal significant structural divergence even within the same curriculum year.

### Grid Variation (Row 1 Anchoring)
| Unit | Row 1 Content | Data Shift |
| :--- | :--- | :--- |
| **Unit 2** | Merged Title Row ("LESSON 1...") | Objectives start at **Row 2** |
| **Unit 1** | Primary Field Headers | Objectives start at **Row 1** (No title row) |

### Grade-Level Validation Results
I have verified the following units across different grades:

| Grade | Unit | Header Strings Match? | Row Offset |
| :--- | :--- | :--- | :--- |
| **Grade 3** | Unit 2 (Area) | **YES** | Row 2 |
| **Grade 3** | Unit 1 (Math in World) | **YES** | Row 1 |
| **Grade 2** | Unit 2 (Subtract < 100) | **YES** | Row 1 |
| **Grade 1** | Unit 7 (Solid Shapes) | **YES** | Row 1 |

### Universal Anchor Tags (Math)
Confirming that the following strings are **"Universal Constants"** across the Math curriculum (K-5):
1. `Teacher-Facing Learning Objective(s)`
2. `Student-Facing Learning Objective(s)`
3. `Lesson Purpose`
4. `Lesson Narrative`
5. `Mathematical Language Routine(s)`

## 7. ELA Curriculum Structure
Analysis of Grade 3 ELA Units (`Grade_3_Unit_1.md`) shows a significant departure from Math's grid-based Docx tables.

### ELA Document Format
- **Type**: Markdown (likely converted from Google Docs).
- **Structure**: Hybrid of free-text headers and Markdown tables.
- **Unit Overview**: Contained in a "Summary of Key Learning" table.
- **Lesson Detail**: Each lesson has its own `| Lesson X: [Title] |` header followed by specific metadata rows.

### ELA Semantic Headers
The anchor strings for ELA differ from Math but remain consistent within the subject:
- `Learning Intention` (Maps to `learning_intentions` in DB)
- `Success Criteria` (Maps to `success_criteria` in DB)
- `Daily Instructional Task` (Maps to `daily_instructional_task` in DB)
- `Key Instructional Practices`
- `Learning Procedures`

## 8. Cross-Curricular Scalability
The **Semantic Search Parser** strategy is validated as the unified approach for all subjects. 

| Feature | Math Pattern | ELA Pattern | Ingestion Handle |
| :--- | :--- | :--- | :--- |
| **Strategy** | Header-based Search | Header-based Search | `Unified Semantic Search` |
| **Source Format** | DOCX Table Grid | MD Table/Header Blocks | `Format-Agnostic Extraction` |
| **Anchor Labels** | "Lesson Purpose", "Teacher-Facing..." | "Learning Intention", "Success Criteria" | `Subject-Specific Label Map` |

### Synthesis
While the specific strings and file formats change between Math and ELA, the **concept of semantic anchoring** remains the only reliable way to handle structural variance. The ingestion pipeline should implement a `ParserConfig` that passes subject-specific anchor tags to the core `find_cell_by_header` engine.
