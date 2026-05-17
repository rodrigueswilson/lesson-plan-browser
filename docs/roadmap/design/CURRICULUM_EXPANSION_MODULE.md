# Curriculum Expansion (Teacher Improvements) Module

## 📋 Overview
The **Curriculum Expansion** module allows teachers to contribute to and improve the reference curriculum repository without overwritting the official Board of Education (BoE) "Source of Truth." It enables the addition of "Teacher Extensions"—such as better teaching videos, supplementary materials, or deeper conceptual explanations—that are layered on top of the base curriculum.

## 🎯 Key Objectives
1. **Layered Data Model**: Maintain a strict separation between "Official Curriculum" and "Teacher Extensions."
2. **Quality Enhancement**: Allow teachers to share and preserve high-quality materials (YouTube, PDFs, Web links) discovered during lesson delivery.
3. **Standards Compliance**: Ensure extensions are tagged with relevant NJ/Common Core Standards to maintain instructional alignment.
4. **Hybrid Retrieval**: Enable AI agents to prioritize "Teacher Extensions" for enrichment while sticking to "Official Objectives" for core compliance.

## 🛠️ Components

### A. Extension Registry (Backend)
- A separate database table/collection for `curriculum_extensions`.
- Each extension links to a specific `unit_id` or `lesson_id` from the official repository.
- Metadata includes: `contributor_id`, `resource_type` (Video, Document, Link), `standard_alignment`, and `pedagogical_note`.

### B. Inline Improvement UI (Frontend)
- **"Improve this Lesson" Button**: Located in the Curriculum Navigator.
- **Resource Uploader**: Drag-and-drop support for PDFs and Link embedding for YouTube/Web.
- **Extension Feed**: A sidebar showing supplementary materials suggested by the teacher (or peers in the future).

### C. Validation & Guardrails
- **Standard Lock**: The official "Student Goal" and "NJ Standard" fields remain read-only to ensure the lesson's legal/instructional core is never lost.
- **Agent Awareness**: When the LLM generates a lesson plan, the prompt will say: "Use the Official Objective [X], but enrich the explanation using the Teacher Extension [Y]."

## 📅 Phases

### Phase 1: Local Personalization
- Allow a teacher to add private notes and links to a lesson in the Curriculum Navigator.
- Store these in a local `user_curriculum_extensions.json`.
- Display extensions alongside official content.

### Phase 2: Metadata & Asset Linking
- Implement the structured registry for different resource types (Video vs. PDF).
- Index teacher extensions in the **Vector Database** so they appear in semantic searches.

### Phase 3: Collaborative Improvement (Future)
- Potentially share high-quality extensions across a department or school.
- "Rating" system for curriculum improvements (e.g., "This video really helped with Unit 4").
