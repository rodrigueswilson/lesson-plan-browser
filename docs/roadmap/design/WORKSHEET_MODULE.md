## Worksheet Module – Class Worksheets from Lesson Plans

### Purpose and scope

Every generated lesson plan should have an associated **worksheet** that:

- Provides students with structured **practice on the lesson’s content and language goals** (content objectives + language objectives).
- **Per-Lesson Generation**: Every generated lesson plan results in a corresponding, custom-built worksheet.
- **Physical-to-Digital Loop (FastScan)**: Worksheets are designed for efficient batch-scanning (e.g., Epson FastScan) to automatically archive student work and extract assessment scores.
- **Unified ID QR Codes**: Each worksheet contains a unique, complex QR code identifying the **Student**, **Subject**, **Unit**, and **Lesson** for automated sorting and database linking.
- **ODPAR Reinforcement**: Directly supports the ODPAR system by aligning activities with the specific Objectives and Assessments of that lesson.
- Gives teachers **quick, WIDA-aligned opportunities to assess** both content understanding and language use during or after the class.
- Reuses as much as possible of the information already present in the system: **lesson plan steps**, **vocabulary items**, **sentence frames**, and (when available) **assessment focuses** from the ASSESSMENT_MODULE.

The worksheet module is a **generation and storage layer** that turns lesson plans into printable/PDF and digital worksheets; it is not a separate student portal (students access digital content primarily through Schoology via SCORM/cmi5).

---

### Inputs and outputs

**Inputs (from existing modules):**

- **Weekly / daily lesson plan data**
  - Subject, grade, WIDA level band, Key Language Use, content and language objectives.
  - Lesson steps, activities, and target outcomes.
- **Vocabulary module**
  - Selected vocabulary for the slot (everyday, cross-disciplinary, technical), with translations, images, and leveled definitions.
  - Sentence frames / stems aligned to the lesson’s WIDA level and Key Use.
- **Assessment module (when available)**
  - Recommended assessment focus for that lesson (e.g. “Recount in Speaking, WIDA 2–3”, “Explain in Writing, WIDA 3–4”).
  - Suggested assessment tool pattern (e.g. quick rubric, checklist, short constructed response).

**Outputs:**

- **Teacher-facing worksheet plan**
  - Metadata: lesson ID, date, subject, grade, WIDA band, Key Use.
  - List of generated exercise blocks with purpose and target language/content.
- **Student-facing worksheet artifacts**
  - **Printable/PDF worksheet** per lesson (one page if possible; more only when needed).
  - **Digital worksheet data** that can be reused inside:
    - cmi5/SCORM packages (as “Practice” tab items),
    - tablet activities (where supported).

---

### Worksheet structure (per lesson)

Each worksheet should be small and focused, typically **3–5 exercise blocks** per lesson, aligned with the plan and WIDA guidance:

1. **Warm-up / activation**
   - Simple task to activate prior knowledge and everyday language (e.g. short matching, quick draw-and-label, “what do you already know?” sentence frame).
2. **Content-focused practice**
   - Exercises tied to the lesson’s **content standard** (e.g. reading a short text/diagram and answering content questions).
   - Uses a mix of multiple choice, short answer, labeling, or sorting/categorization.
3. **Language-focused practice**
   - Tasks that use the lesson’s **target vocabulary and sentence frames** (e.g. cloze with frames, write 2–3 sentences using a frame, sort words into categories like everyday vs technical).
4. **Quick assessment / exit ticket**
   - One concise item that gives evidence for the lesson’s **language objective** (e.g. “Use this frame to explain…”, “Circle the best sentence that describes…”).
   - Designed so it can be quickly scored or documented in the ASSESSMENT_MODULE.
5. **Optional enrichment / homework**
   - Short extension task (e.g. “Ask a family member… and write one sentence using this frame”) when teachers opt in.

The generator should **prioritize staying within one double-sided sheet per lesson** (A4/Letter) unless the teacher explicitly requests more.

---

### Exercise types (worksheet-friendly)

The worksheet module reuses the same **canonical exercise types** as the vocabulary and games modules, but expressed in paper/PDF-friendly form:

- **Matching and multiple choice**
  - Match word ↔ definition, word ↔ picture, or statement ↔ diagram.
  - MCQs on vocabulary meaning or use, aligned to WIDA level.
- **Cloze and sentence frames**
  - Fill-in-the-gap items where students complete frames with target vocabulary or phrases.
  - Sentence stems where students complete the idea in writing (content + language).
- **Sorting and categorization**
  - Tables or graphic organizers where students group words (e.g. everyday / cross-disciplinary / technical; agree / disagree / ask for clarification).
- **Labeling and short constructed responses**
  - Label parts of a diagram, chart, or picture with target vocabulary.
  - 1–3 sentence written responses using specified frames.
- **Simple checklists / rubrics (teacher use)**
  - Small rubric or checklist strip printed at the bottom or side, to help the teacher **record evidence** while students work (aligned with the ASSESSMENT_MODULE patterns).

The module should avoid task types that do not translate well to paper (e.g. timing, complex drag-and-drop), unless they are clearly adapted to a static format.
 
---
 
### 📐 Formatting & Templates (US Standards)
 
To ensure professional-grade, classroom-ready materials, the generation engine will adhere to the following standards:
 
1. **Paper Size**: Fixed **US Letter (8.5" x 11")** with standard safety margins (0.5").
2. **Technology**: **HTML/CSS Templates** converted to PDF. This allows for dynamic layout adjustments and high-quality typography.
3. **Adaptive Unit Theming (School Book Style)**:
    - Templates will dynamically switch **Color Palettes** and **Iconography** based on the specific **Unit** and **Subject**.
    - For example: *Grade 2 Math Unit 4 (Number Lines)* may feature a "Blue/Secondary" theme, while *Unit 5 (Money)* may switch to a "Green/Primary" theme.
    - This visual consistency helps students associate colors with conceptual domains, mimicking high-quality textbook series.
4. **Dual Rendering (B&W vs. Color)**:
    - For each lesson, the system will generate **Two PDF Versions**:
        - **Full Color**: High-engagement, suitable for digital tablets or color printing.
        - **Printer-Friendly (B&W)**: High-contrast, zero-background-shading version optimized for economical black-and-white xeroxing.
5. **Grade-Adaptive Font Scaling**:
    - **Grade 1**: Primary font size (Body) should be **14pt - 16pt** with generous line spacing.
    - **Grade 2**: Primary font size (Body) should be **12pt - 14pt**.
    - **Grade 3 and above**: Primary font size (Body) should be **11pt - 12pt**.
6. **Visual Accessibility**: High-contrast, dyslexia-friendly fonts (e.g., Lexend or Open Sans) and clear visual section breaks to support diverse learners.
 
---
 
### 🖋️ Editorial & Graphic Standards
 
The worksheet generation agent MUST follow these professional publishing standards:
 
1. **Cognitive Load Management (Chunking)**:
    - Information MUST be broken into small, manageable "tasks" using numbered lists or distinct boxes.
    - Objectives for the worksheet (Student-friendly "I can..." statements) MUST be visible at the top.
2. **Visual Hierarchy (The CARP Framework)**:
    - **Contrast**: Use bold headers and high-contrast lines for clarity in B&W printing.
    - **Alignment**: Text and graphics MUST follow a consistent grid to reduce visual noise.
    - **Repetition**: Consistent iconography (e.g., a 👂 icon for "Listen" tasks, a ✏️ for "Write" tasks) across all units.
    - **Proximity**: Related items (e.g., a diagram and its corresponding questions) MUST be grouped in the same visual block.
3. **Meaningful Visuals**: Graphics MUST support the lesson's content (e.g., a science diagram or a math number line) and never be purely decorative.
4. **Interactive Bridges (Digital-to-Paper)**:
    - The bottom corner of the worksheet SHOULD feature a **QR Code** that links directly to the `cmi5` package's audio instructions or the unit's vocabulary game.
5. **Physical-to-Digital Identification (FastScan Optimization)**:
    - **Header QR Code**: A secondary, high-density QR code MUST be present in the top-right corner.
    - **Metadata Encoding**: This code encodes the `student_uuid`, `lesson_uuid`, and `assessment_id`.
    - **Batch Processing**: The system provides a "FastScan Importer" skill that listens for new PDFs from a local scanner directory (e.g., Epson FastScan output), parses the QR metadata, and automatically attaches the scanned image to the correct student record in the **ASSESSMENT_MODULE**.
6. **Universal Design (UDL)**:
    - Inclusion of "Sentence Frames" and "Word Banks" directly on the page to provide permanent scaffolding during independent practice.
 
---

### Alignment with WIDA and assessment

For each worksheet, the generator should:

- Make explicit in metadata which **WIDA ELD standard, Key Language Use, and domain/mode** the worksheet supports (e.g. “Std 3 Math – Inform – Expressive, Writing focus”).
- Ensure that at least one exercise directly supports the **language objective** using appropriate sentence frames and vocabulary category mix.
- Include **one clear assessment opportunity** that can be tied to an ASSESSMENT_MODULE tool (e.g. a short writing task scored with a simple rubric).

This keeps worksheets tightly coupled to the lesson’s WIDA alignment and makes them useful artifacts in the ODPAR (Observe–Document–Plan–Act–Review) cycle.

---

### Integration points

- **From lesson plan to worksheet**
  - When a new lesson plan is generated or edited, the system can:
    - Propose a default worksheet outline (3–5 exercises) using the plan’s vocabulary and steps.
    - Allow the teacher to accept, tweak, or regenerate the worksheet.
- **With vocabulary and games**
  - The same vocabulary set and frames used in the worksheet should be reused in:
    - In-app games for that lesson.
    - cmi5 “Practice” tab items for Schoology.
- **With ASSESSMENT_MODULE**
  - The assessment tools for the tablet app can mirror the worksheet’s **exit ticket** and key language task, so that teacher observations and worksheet products refer to the same learning target.

Implementation details (database tables, APIs, UI) can be added in a later phase; this document defines the **role and shape** of the worksheet module in the overall architecture.

---

### Future module extension: PDF localization with template fidelity (EN -> PT)

Planned future capability: generate a Portuguese worksheet PDF from an English source worksheet while preserving classroom-print fidelity.

#### Target behavior

- Input: original English worksheet PDF (+ optional existing Spanish counterpart when available).
- Output: Portuguese worksheet PDF with the same:
  - page size and margins,
  - image placements and dimensions,
  - table/box geometry,
  - visual hierarchy and template structure.
- Only language layer changes (English text replaced by Portuguese translation).

#### Technical research requirements (pre-implementation)

1. **Artifact characterization**
   - Determine whether text in source PDFs is selectable text, vector glyphs, equation objects, or rasterized images.
2. **Math/fraction preservation**
   - Verify formula and special-symbol fidelity in translated output (no silent loss of math semantics).
3. **Layout lock strategy**
   - Define safe text expansion rules (Portuguese tends to be longer than English) with overflow controls.
4. **Image/text layer handling**
   - Detect image-embedded text regions and define fallback OCR + overlay approach only where needed.

#### Acceptance criteria for this extension

- Portuguese PDF visually matches source template within agreed tolerance.
- Math symbols and formulas remain semantically intact.
- Side-by-side review (EN vs PT) passes for at least one full worksheet set before scale-up.

