# Agentic cmi5 Design Rules (Pedagogical Framework)

## 📋 Overview
This document defines the **Agentic Rules** that the AI Package Architect must follow when generating `cmi5` instructional modules. These rules ensure that all digital content adheres to the latest best practices for language acquisition, content development, and accessibility.

## 🤖 The "Agentic Architect" Role
The agent is not a simple file-maker; it is a **Pedagogical Designer**. When assembling a `cmi5` Assignable Unit (AU), the agent MUST apply the following rules autonomously.

## 📏 Core Design Rules

### 1. Multimodal Primacy (Accessibility)
- **Audio Overlays**: Every student-facing instruction, heading, and prompt MUST have a high-quality TTS audio counterpart (Google Cloud TTS).
- **Visual Clues**: For WIDA Levels 1-2, the agent MUST prioritize image-rich definitions over text.

### 2. Temporal Syllable Sync (Reading Support)
- **Syllabification**: For reading passages, the agent MUST use a syllabification engine to break down Tier 2 and Tier 3 words.
- **Sync Maps**: The agent MUST generate a JSON timestamp map (`syllable_sync.json`) that allows the UI to highlight each syllable in sync with the audio playback.

### 3. Contextual Diction (Differentiated Meaning)
- **Subject Filtering**: When retrieving data from the **Merriam-Webster API**, the agent MUST only select the definition matching the current **Subject** (e.g., *Table* as a data structure in Math, not furniture).
- **Instructional Focus**: The agent MUST prioritize the specific meaning found in the Board of Education curriculum for that Unit.

### 4. 6-Level Tiered Complexity (WIDA Alignment)
- **Parallel Content**: The agent MUST generate **six versions** of the lesson's vocabulary, definitions, and practice exercises.
- **Complexity Scale**:
    - **Levels 1-2**: Focus on "Identification" (Images + simple phrases).
    - **Levels 3-4**: Focus on "Description" (Simple sentences + sentence frames).
    - **Levels 5-6**: Focus on "Analysis" (Academic paragraphs + complex syntax).

### 5. Interactive Scaffolding (Real-time Support)
- **Vocabulary Overlays**: Key terms MUST be wrapped in interactive "Pop-overs" that present the level-appropriate definition, image, and L1 translation (Portuguese) on hover/tap.
- **Agentic Feedback**: The agent MUST embed "Hint Logs" that the cmi5 package can trigger if a student makes multiple mistakes on a specific task.

### 6. Universal Design for Learning (UDL)
- **Flexible Representation**: Content MUST be presented in multiple formats (Text, Audio, Diagram).
- **Engagement Toggles**: The package should allow the student (or teacher) to toggle between B&W and Color themes for visual comfort.
 
### 7. App-Style Engagement Mechanics
- **Micro-Learning Units**: The agent MUST structure cmi5 Assignable Units (AUs) into **5-15 minute "Sprint" modules** to maintain high student focus.
- **Spaced Repetition (SRS) Continuity**: If xAPI data indicates a student struggled with a word in Lesson A, the agent MUST prioritize that word for "Warm-up" review in the generated Lesson B.
- **Gamified Narrative**: Lessons should be framed as **"Curriculum Quests"** or "Scenarios" (e.g., "The Math Lab Mystery") rather than dry instructional lists.
- **Immediate Corrective Loops**: Every interactive challenge MUST provide immediate feedback using a **3-step scaffolding logic**:
    1. *Level 1*: Gentle hint (e.g., "Look at the picture again").
    2. *Level 2*: Structural clue (e.g., "The word starts with P").
    3. *Level 3*: Contextual explanation + Answer.
- **Native Contextual Links**: The agent MUST search for and embed **short native speaker clips** (YouTube/Internal) that demonstrate local or authentic uses of the lesson's key phrases.
 
## 🛠️ Implementation Strategy
- **Rule Injection**: These rules are part of the System Prompt for the `Interoperability Agent`.
- **Validation Step**: Before a `cmi5` package is finalized, a "Verifier Agent" checks the output against these rules to ensure 100% compliance.
