# Enhanced Lesson Plan Generation and Vocabulary Modules

## Executive Summary

This document describes the architectural enhancements to the Lesson Plan Builder application, introducing:

1. **Enhanced Lesson Plan Generation** with Claude MCP Local Document Access (metadata-driven retrieval)
2. **Vocabulary Module** with shared vocabulary bank, multimedia support, and teacher approval workflow
3. **Game Generation Modules** for in-app browser games and SCORM 2004 packages for LMS integration
4. **Document Management UI** for managing local curriculum and assessment documents

These enhancements maintain compatibility with the existing local-first, P2P sync architecture described in `DATABASE_ARCHITECTURE_AND_SYNC.md`.

> **Reality check (Nov 2025):**  
> - `tools/batch_processor.py` still invokes the legacy LLM flow; there is no `FileSearchService`, no query profile builder, and no retrieval logging.  
> - The backend has zero vocabulary tables/endpoints. `backend/database.py` only knows about `WeeklyPlan`, `ClassSlot`, `ScheduleEntry`, `LessonStep`, and metrics.  
> - No worker containers or services exist for image collection, normalization, audio generation, or game/SCORM output.  
> - The frontend contains no vocabulary approval UI. Everything in this document remains **design-only** unless otherwise noted.

> **Architecture decision (Feb 2026):**
> - Google FileSearch RAG is retained below as a **hypothesis for future evaluation** — it may be revisited if the document corpus grows significantly or semantic search becomes a clear need.
> - The **current recommended approach** is **Claude MCP Local Document Access**: a metadata-driven file lookup that feeds documents directly into Claude's context window via MCP tools. See the new section below.
> - For 2 teachers with a bounded, well-structured curriculum, this simpler approach achieves equivalent results with fewer dependencies and lower cost.

**Key Principle**: Images are **never used** until teacher-approved. Words can be used without images if approval is pending.

**Related Documents**:
- [README.md](./README.md) - Master index of all expansion documents
- [AGENT_SKILLS_AND_CODE_EXECUTION.md](./AGENT_SKILLS_AND_CODE_EXECUTION.md) - How Agent Skills and code execution can optimize these workflows
- [CONTAINERIZATION_STRATEGY.md](./CONTAINERIZATION_STRATEGY.md) - Docker/Kubernetes recommendations for new services
- [DATABASE_ARCHITECTURE_AND_SYNC.md](./DATABASE_ARCHITECTURE_AND_SYNC.md) - Existing sync architecture

---

## Table of Contents

1. [Enhanced Generation Flow — Claude MCP Local Document Access (Current)](#enhanced-generation-flow--claude-mcp-local-document-access-current)
2. [Enhanced Generation Flow — Google FileSearch RAG (Hypothesis)](#enhanced-generation-flow--google-filesearch-rag-hypothesis)
3. [Vocabulary Module Architecture](#vocabulary-module-architecture)
4. [Image and Audio Collection System](#image-and-audio-collection-system)
5. [Teacher Approval Workflow](#teacher-approval-workflow)
6. [Game Generation Modules](#game-generation-modules)
7. [Document Management System](#document-management-system)
8. [Database Schema Changes](#database-schema-changes)
9. [Service Layer Architecture](#service-layer-architecture)
10. [Integration with Existing Architecture](#integration-with-existing-architecture)
11. [Implementation Phases](#implementation-phases)

---

## Enhanced Generation Flow — Claude MCP Local Document Access (Current)

### Overview

The lesson plan generation process is enhanced with **local curriculum document access via Claude MCP tools**. Instead of an external vector database or managed RAG service, the system uses metadata-driven file lookup to select the right documents, then feeds their content directly into Claude's context window for reasoning.

### Technology Choice: Claude MCP Local Document Access

**Selected**: Metadata-driven local file access via MCP tools (Claude API)

**Rationale — Why this approach fits our scale**:

The application serves **2 teachers** with a **bounded, well-structured** curriculum document corpus. The existing documents are already organized by clear metadata dimensions (grade cluster, subject, proficiency level, strategy category, lesson type, delivery mode). This structure makes metadata-based lookup highly effective without needing semantic vector search.

| Factor | Our situation | Implication |
|--------|--------------|-------------|
| Corpus size | ~40 JSON files across `strategies_pack_v2/`, `wida/`, `co_teaching/` | Entire corpus fits in Claude's context window if needed |
| Document structure | Well-organized by grade, subject, proficiency, category | Metadata lookup is precise — no fuzzy matching needed |
| User count | 2 teachers | No multi-tenant indexing or scaling concerns |
| Query patterns | Grade + subject + proficiency level + lesson type | Deterministic file selection, not open-ended search |
| Architecture | Local-first (SQLite, Tauri) | External API dependency contradicts design philosophy |

**Advantages over managed RAG (Google FileSearch)**:
- **No third-party dependency** — no Google Cloud project, no Gemini API key, no external service to fail
- **No vector database** — no embedding pipeline, no chunking strategy, no index maintenance
- **Zero additional cost** — documents are read locally and passed to the same Claude API call
- **Lower latency** — no extra network round-trip; local file reads are instant
- **Simpler fallback** — the system already works without document context (existing strategies are loaded locally)
- **Local-first alignment** — stays consistent with the SQLite/Tauri architecture
- **Full document context** — Claude reasons over complete documents, not fragments/chunks

**When to reconsider** (triggers for revisiting Google FileSearch hypothesis):
- Corpus grows beyond ~200 documents or ~2MB of text
- Teachers start uploading arbitrary curriculum PDFs that lack structured metadata
- Semantic search becomes a clear need (queries that metadata can't resolve)
- Multi-school deployment where document management at scale matters

### How It Works

The approach has three layers:

#### Layer 1: Document Registry (metadata index)

A lightweight `curriculum_documents` table tracks what documents exist and their metadata. This is the **lookup index** — it tells the system which files to load for a given lesson context.

```sql
CREATE TABLE curriculum_documents (
    id TEXT PRIMARY KEY,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,          -- relative path from project root
    document_type TEXT NOT NULL,       -- 'strategy', 'wida', 'co_teaching', 'curriculum', 'assessment'
    subject TEXT,                      -- 'math', 'ela', 'science', etc. (NULL = all subjects)
    grade_range TEXT,                  -- 'K', '1', '2-3', '4-5', '6-8', '9-12' (NULL = all grades)
    category TEXT,                     -- strategy category, co-teaching model, etc.
    tags TEXT,                         -- comma-separated custom tags
    description TEXT,
    file_format TEXT DEFAULT 'json',   -- 'json', 'md', 'txt'
    file_size_bytes INTEGER,
    content_hash TEXT,                 -- SHA-256 for change detection
    last_indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_curriculum_docs_lookup ON curriculum_documents(document_type, subject, grade_range);
CREATE INDEX idx_curriculum_docs_category ON curriculum_documents(category);
```

#### Layer 2: MCP Tool — `retrieve_curriculum_context`

An MCP tool that the Claude agent calls during lesson plan generation. It queries the registry, reads the matching files, and returns their content.

```python
# backend/services/curriculum_context_service.py

class CurriculumContextService:
    """
    Metadata-driven document lookup for lesson plan generation.

    Instead of semantic search, this service uses structured metadata
    (grade, subject, proficiency level, lesson type) to select the
    right documents and return their full content for Claude to reason over.
    """

    def __init__(self, db: DatabaseInterface):
        self.db = db
        self.project_root = Path(__file__).parent.parent.parent  # D:\LP

    async def retrieve_context(self, query_profile: dict) -> dict:
        """
        Given a lesson context (grade, subject, etc.), find and return
        relevant curriculum documents.

        Args:
            query_profile: {
                "grade": "3",
                "subject": "math",
                "proficiency_levels": [2, 3],  # WIDA levels of students
                "lesson_type": "math",          # maps to strategy selection
                "delivery_mode": "push-in",
                "unit_topic": "Measurement and Data"  # optional
            }

        Returns:
            {
                "documents": [...],         # list of document contents
                "document_count": int,
                "total_tokens_estimate": int,
                "selection_reasoning": str  # why these documents were chosen
            }
        """
        grade = query_profile.get("grade", "")
        subject = query_profile.get("subject", "")
        proficiency_levels = query_profile.get("proficiency_levels", [])
        lesson_type = query_profile.get("lesson_type", "")

        documents = []

        # 1. Load matching strategies from strategies_pack_v2
        strategies = await self._load_strategies(grade, subject, lesson_type, proficiency_levels)
        documents.extend(strategies)

        # 2. Load WIDA framework context for the proficiency levels
        wida_context = await self._load_wida_context(proficiency_levels)
        documents.extend(wida_context)

        # 3. Load relevant co-teaching models
        co_teaching = await self._load_co_teaching_context(query_profile.get("delivery_mode"))
        documents.extend(co_teaching)

        # 4. Load any user-uploaded curriculum documents matching grade+subject
        curriculum = await self._load_curriculum_documents(grade, subject)
        documents.extend(curriculum)

        return {
            "documents": documents,
            "document_count": len(documents),
            "total_tokens_estimate": sum(d.get("token_estimate", 0) for d in documents),
            "selection_reasoning": self._build_reasoning(query_profile, documents)
        }

    async def _load_strategies(self, grade, subject, lesson_type, proficiency_levels) -> list:
        """
        Use the _index.json selection rules to pick relevant strategy categories,
        then load those category files and filter strategies by grade cluster
        and proficiency level.
        """
        index_path = self.project_root / "strategies_pack_v2" / "_index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))

        grade_cluster = self._grade_to_cluster(grade)
        relevant_categories = self._select_categories_for_lesson_type(
            index.get("selection_rules", {}), lesson_type
        )

        documents = []
        for category in relevant_categories:
            # Determine if core or specialized
            core_path = self.project_root / "strategies_pack_v2" / "core" / f"{category}.json"
            spec_path = self.project_root / "strategies_pack_v2" / "specialized" / f"{category}.json"
            file_path = core_path if core_path.exists() else spec_path

            if file_path.exists():
                content = json.loads(file_path.read_text(encoding="utf-8"))
                # Filter strategies to those matching grade cluster + proficiency
                filtered = self._filter_strategies(
                    content.get("strategies", []),
                    grade_cluster,
                    proficiency_levels
                )
                if filtered:
                    documents.append({
                        "source": f"strategies_pack_v2/{file_path.parent.name}/{file_path.name}",
                        "document_type": "strategy",
                        "category": category,
                        "content": filtered,
                        "token_estimate": len(json.dumps(filtered)) // 4
                    })

        return documents

    async def _load_wida_context(self, proficiency_levels) -> list:
        """Load WIDA framework reference and strategy enhancements for the given levels."""
        documents = []

        # Load WIDA framework reference (always relevant)
        framework_path = self.project_root / "wida" / "wida_framework_reference.json"
        if framework_path.exists():
            content = json.loads(framework_path.read_text(encoding="utf-8"))
            documents.append({
                "source": "wida/wida_framework_reference.json",
                "document_type": "wida",
                "content": content,
                "token_estimate": len(json.dumps(content)) // 4
            })

        # Load proficiency-level enhancements (filtered to relevant levels)
        enhancements_path = self.project_root / "wida" / "wida_strategy_enhancements.json"
        if enhancements_path.exists():
            content = json.loads(enhancements_path.read_text(encoding="utf-8"))
            # Could filter to relevant proficiency bands here
            documents.append({
                "source": "wida/wida_strategy_enhancements.json",
                "document_type": "wida_enhancements",
                "content": content,
                "token_estimate": len(json.dumps(content)) // 4
            })

        return documents

    async def _load_co_teaching_context(self, delivery_mode) -> list:
        """Load co-teaching models relevant to the delivery mode."""
        documents = []
        co_teaching_path = self.project_root / "co_teaching" / "co_teaching_models.json"

        if co_teaching_path.exists():
            content = json.loads(co_teaching_path.read_text(encoding="utf-8"))
            documents.append({
                "source": "co_teaching/co_teaching_models.json",
                "document_type": "co_teaching",
                "content": content,
                "token_estimate": len(json.dumps(content)) // 4
            })

        # Always load Portuguese misconceptions (relevant for bilingual context)
        misconceptions_path = self.project_root / "co_teaching" / "portuguese_misconceptions.json"
        if misconceptions_path.exists():
            content = json.loads(misconceptions_path.read_text(encoding="utf-8"))
            documents.append({
                "source": "co_teaching/portuguese_misconceptions.json",
                "document_type": "linguistic_misconceptions",
                "content": content,
                "token_estimate": len(json.dumps(content)) // 4
            })

        return documents

    async def _load_curriculum_documents(self, grade, subject) -> list:
        """Load any user-uploaded curriculum documents from the registry."""
        grade_cluster = self._grade_to_cluster(grade)
        rows = await self.db.execute(
            """SELECT file_path, document_type, description
               FROM curriculum_documents
               WHERE document_type IN ('curriculum', 'assessment')
               AND (grade_range = ? OR grade_range IS NULL)
               AND (subject = ? OR subject IS NULL)""",
            (grade_cluster, subject)
        )

        documents = []
        for row in rows:
            file_path = self.project_root / row["file_path"]
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                documents.append({
                    "source": row["file_path"],
                    "document_type": row["document_type"],
                    "description": row.get("description", ""),
                    "content": content,
                    "token_estimate": len(content) // 4
                })

        return documents

    @staticmethod
    def _grade_to_cluster(grade: str) -> str:
        """Map a grade to its cluster (matches strategies_pack_v2 _index.json)."""
        grade_map = {
            "K": "K", "1": "1",
            "2": "2-3", "3": "2-3",
            "4": "4-5", "5": "4-5",
            "6": "6-8", "7": "6-8", "8": "6-8",
            "9": "9-12", "10": "9-12", "11": "9-12", "12": "9-12"
        }
        return grade_map.get(str(grade), "2-3")  # default to 2-3

    def _build_reasoning(self, query_profile, documents) -> str:
        """Explain why these documents were selected (for auditing)."""
        sources = [d["source"] for d in documents]
        return (
            f"Selected {len(documents)} documents for "
            f"grade={query_profile.get('grade')}, "
            f"subject={query_profile.get('subject')}, "
            f"proficiency={query_profile.get('proficiency_levels')}: "
            f"{', '.join(sources)}"
        )
```

#### Layer 3: Integration into the Generation Flow

The `CurriculumContextService` is called as an MCP tool during lesson plan generation. Claude receives the document contents as part of its context and reasons over them to produce the enhanced lesson plan.

```
┌─────────────────────────────────────────────────────────────┐
│ 1. DOCX Input → Parse → Extract Metadata                    │
│    (grade, subject, objectives, standards)                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Build Query Profile                                       │
│    - Grade cluster, subject, proficiency levels              │
│    - Lesson type, delivery mode                              │
│    - Unit topic (optional)                                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. CurriculumContextService.retrieve_context()               │
│    - Query curriculum_documents registry (metadata lookup)   │
│    - Read matching local files                               │
│    - Return full document content + selection reasoning       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Log Retrieval Results                                     │
│    - Save to context_retrievals table                        │
│    - Track which documents influenced the plan               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Claude LLM Generation                                     │
│    - Primary plan content                                    │
│    + Curriculum context (full document text in context)      │
│    + Bilingual strategies (filtered by metadata)             │
│    + WIDA framework (existing)                               │
│    Claude reasons over the complete content — no chunking    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Vocabulary Extraction                                     │
│    - Extract from lesson_json                                │
│    - Extract from curriculum context documents               │
│    - Query curriculum for grade/subject vocabulary            │
└─────────────────────────────────────────────────────────────┘
                          ↓
        (continues with Image/Audio, Approval, Games as before)
```

### Query Profile Structure

```json
{
  "grade": "3",
  "subject": "math",
  "proficiency_levels": [2, 3],
  "lesson_type": "math",
  "delivery_mode": "push-in",
  "unit_topic": "Measurement and Data",
  "user_id": "teacher_123"
}
```

### Retrieval Logging

Retrieval results are stored for:
- **Auditing**: Track which documents influenced each lesson plan
- **Debugging**: Understand why certain strategies were selected
- **Improvement**: Identify gaps in document coverage (e.g., no curriculum docs for a subject)

### Existing Document Corpus

The system already has well-organized documents ready for this approach:

| Location | Files | Organization | Content |
|----------|-------|-------------|---------|
| `strategies_pack_v2/core/` | 4 JSON files | By strategy category | 29 strategies with grade/proficiency metadata |
| `strategies_pack_v2/specialized/` | 2 JSON files | By strategy category | 4 strategies |
| `strategies_pack_v2/_index.json` | 1 file | Master index | Selection rules by lesson type, loading algorithm |
| `wida/` | 2 JSON files | By purpose | Framework reference + strategy enhancements |
| `co_teaching/` | 5 JSON files | By purpose | 6 co-teaching models, misconceptions, selection rules |

Total: ~14 files, all JSON, all with structured metadata. Additional user-uploaded curriculum documents (PDF, DOCX, TXT) can be registered in the `curriculum_documents` table.

---

## Enhanced Generation Flow — Google FileSearch RAG (Hypothesis)

> **Status: HYPOTHESIS — not currently planned for implementation.**
> This section documents Google FileSearch as a potential future approach. It may be revisited if the document corpus grows significantly, arbitrary document uploads become common, or semantic search proves necessary. See the triggers listed in the section above.

### Overview

The lesson plan generation process could alternatively be enhanced with Google FileSearch RAG to provide semantically relevant information from curated curriculum documents and assessment criteria.

### Technology Choice: Google FileSearch

**Hypothesis**: Google FileSearch (via Gemini API)

**Rationale**:
- Fully managed RAG system (handles storage, chunking, embeddings automatically)
- Supports PDF, DOCX, TXT, JSON formats
- Semantic search (finds relevant content even without exact matches)
- Built-in citations (tracks which documents were used)
- Cost-effective: Free storage and query-time embeddings; $0.15 per 1M tokens for initial indexing
- API-based (enables custom UI for document management)

### Enhanced Generation Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. DOCX Input → Parse → Extract Metadata                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Build RAG Query Profile                                  │
│    - Grade, subject, objectives, standards                  │
│    - Week context, unit topic                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. FileSearchService.retrieve_context()                     │
│    - Query Google FileSearch store                          │
│    - Get relevant document chunks with citations            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Store Retrieval Results                                  │
│    - Save to rag_retrievals table                           │
│    - Enable auditing and teacher editing                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. LLM Generation                                           │
│    - Primary plan content                                   │
│    + RAG context (curriculum, assessment criteria)          │
│    + Bilingual strategies (existing)                        │
│    + WIDA framework (existing)                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Vocabulary Extraction                                    │
│    - Extract from lesson_json                               │
│    - Extract from RAG context                               │
│    - Query curriculum for grade/subject vocabulary          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Image/Audio Generation (Background)                      │
│    - Collect 4-5 images per word from multiple APIs         │
│    - Generate audio pronunciation (Google TTS)              │
│    - Normalize image sizes                                  │
│    - Status: 'pending' (NOT approved yet)                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. lesson_json (SSOT) Saved                                 │
│    - Complete lesson plan                                   │
│    - Vocabulary items linked (without images until approved)│
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 9. Vocabulary Approval UI                                   │
│    - Teacher reviews vocabulary words                       │
│    - Selects preferred images                               │
│    - Approves/rejects words                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 10. Finalize Week                                           │
│     - Approved vocabulary ready for games                   │
│     - Images available for approved words only              │
└─────────────────────────────────────────────────────────────┘
```

### RAG Query Profile Structure

```json
{
  "grade": "3",
  "subject": "math",
  "objectives": ["Students will calculate area of rectangles"],
  "standards": ["CCSS.MATH.3.MD.C.7"],
  "week_of": "01/15-01/19",
  "unit_topic": "Measurement and Data",
  "user_id": "teacher_123"
}
```

### Retrieval Storage

Retrieval results are stored for:
- **Auditing**: Track which documents influenced each lesson plan
- **Teacher Editing**: Allow teachers to modify query profiles and re-run retrieval
- **Continuous Improvement**: Identify retrieval errors and improve query strategies

---

## Vocabulary Module Architecture

### Design Principles

1. **Shared Vocabulary Bank**: All teachers share the same vocabulary database (reduces API costs)
2. **Curriculum-Driven**: Vocabulary extracted from curriculum queries (grade + subject)
3. **Auto-Generation**: Images and audio generated automatically, but require teacher approval
4. **Per-Teacher Preferences**: Each teacher selects preferred images (Option A: per-teacher preferences)
5. **No Images Until Approved**: Words can be used without images; images only appear after teacher approval

### Vocabulary Ownership Model

- **Global Vocabulary Items**: One shared vocabulary bank for all teachers
- **Per-Teacher Approvals**: Each teacher approves words and selects preferred images
- **Usage Tracking**: Links vocabulary to specific lesson plans, weeks, and days

### Vocabulary Lifecycle

```
1. Curriculum Query → Identify essential vocabulary for grade/subject
2. Lesson Plan Generation → Extract vocabulary from plan + RAG context
3. Check Database → Does word exist?
   - If NO: Generate new word entry (images, audio, definitions)
   - If YES: Use existing entry
4. Link to Plan → Create vocabulary_usages record
5. Teacher Approval → Teacher reviews and approves words
6. Image Selection → Teacher selects preferred image (if approved)
7. Available for Games → Approved vocabulary ready for game generation
```

### Vocabulary Data Model

See [Database Schema Changes](#database-schema-changes) for complete schema.

**Key Tables**:
- `vocabulary_items`: Shared vocabulary bank (SSOT for words)
- `vocabulary_teacher_approvals`: Per-teacher approval and image preferences
- `vocabulary_usages`: Links words to specific lesson plans
- `image_normalization_cache`: Caches normalized image versions

---

## Image and Audio Collection System

### Image Collection Strategy

**Multi-API Approach**: Query multiple image APIs in parallel to collect 4-5 images per word.

**APIs Selected**:
1. **Unsplash API** (Free: 50 req/hour)
   - High-quality educational images
   - Transparent backgrounds available
   
2. **Pixabay API** (Free: 5,000 req/day)
   - Large educational collection
   - Transparent PNGs available
   
3. **Pexels API** (Free: 200 req/hour)
   - Educational and lifestyle images
   
4. **Openverse** (Free, no API key)
   - Creative Commons licensed
   - Educational focus

**Image Requirements**:
- Pedagogically appropriate for grade level
- Transparent backgrounds (PNG) preferred
- Age-appropriate content
- Clear, simple illustrations for concepts

### Image Normalization System

All images are normalized to standard sizes:

- **Vocabulary Card**: 800x600px
- **Game Image**: 400x300px
- **Thumbnail**: 200x200px
- **SCORM Image**: 600x450px

**Process**:
1. Download original image from API
2. Resize to target dimensions (preserve aspect ratio, add padding if needed)
3. Preserve transparency (if PNG)
4. Save normalized version to storage (local or Supabase Storage)
5. Cache in `image_normalization_cache` table
6. Generate thumbnail version

### Audio Generation

**Selected**: Google Cloud Text-to-Speech API

**Rationale**:
- Free tier: 0-4 million characters/month
- Supports Portuguese (Brazil/Portugal) and English
- Natural-sounding voices
- Educational use cases supported

**Process**:
1. Generate pronunciation for word in target language
2. Save audio file (MP3 format)
3. Store URL in `vocabulary_items.audio_url`
4. Audio is generated automatically (no approval needed, but can be regenerated)

### Image Approval Constraint

**CRITICAL RULE**: Images are **never displayed or used** until teacher-approved.

**Implementation**:
- Images collected and normalized during generation
- Status set to `'pending'` in `vocabulary_items.images[].approved_by_teacher_id`
- Words can be used in lesson plans **without images** if approval is pending
- Only after teacher approval: `approved_by_teacher_id` is set, image becomes available
- Games and SCORM packages only include approved images

**Fallback Behavior**:
- If word is not approved: Use word text only (no image)
- If word is approved but no image selected: Use word text only (teacher can select later)
- If word is approved with image: Use word + selected image

---

## Teacher Approval Workflow

### Vocabulary Approval UI

**Timing**: After lesson plan generation completes, before week finalization.

**UI Components**:

1. **Vocabulary List View**
   - Shows all vocabulary words for the week
   - Grouped by day/slot
   - Status indicators: Pending, Approved, Rejected

2. **Word Detail View** (for each word)
   - Word text (EN/PT)
   - Definitions (EN/PT)
   - Audio playback button
   - Image gallery (4-5 options in grid)
   - Approve/Reject toggle
   - Image selection (radio buttons)
   - Notes field (optional)

3. **Bulk Actions**
   - **Select All / Deselect All** - Toggle all words for batch operations
   - **Approve Selected** - Approve multiple words at once
   - **Reject Selected** - Reject multiple words at once
   - **Auto-Select First Image** - Bulk approve with default image selection (first image for each word)
   - **Filter by Status** - Show only pending/approved/rejected words
   - **Batch Image Selection** - Select same image for multiple words

4. **Finalize Button**
   - Locks all selections
   - Completes week finalization
   - Makes approved vocabulary available for games
   - Validates that all required words are approved (optional validation)

### Approval States

- **Pending**: Word generated, images collected, awaiting teacher review
- **Approved**: Teacher approved word, selected preferred image
- **Rejected**: Teacher rejected word (will not appear in games, but usage record preserved)

### Image Selection Workflow

1. Teacher views word with 4-5 image options
2. Teacher can:
   - Play audio to hear pronunciation
   - View images in full size
   - Select preferred image (radio button)
   - Reject inappropriate images (marks as rejected in database)
3. Teacher approves word → Selected image becomes active
4. If no image selected but word approved → Word used without image

---

## Game Generation Modules

### Overview

Two game generation modules create vocabulary games from approved vocabulary:

1. **Lesson Plan Browser Games**: In-app interactive games for use during lessons
2. **SCORM 2004 Package Generator**: Standalone SCORM packages for LMS integration

### Game Types Supported

1. **Matching Games**: Pair words with translations/definitions (cards or digital)
2. **Crossword Puzzles**: Clues matched with vocabulary words
3. **Fill-in-the-Gap (Cloze)**: Complete sentences with vocabulary
4. **Word Search**: Find vocabulary words in letter grid
5. **Flashcards**: Word/meaning cards with spaced repetition
6. **Memory/Concentration**: Find pairs by remembering locations
7. **Sorting/Categorization**: Group vocabulary by semantic/grammatical categories
8. **Word Ladders/Chains**: Change one letter at a time to form new words
9. **Bingo**: Mark words as definitions/translations are heard/seen

### Game Data Sources

Games use approved vocabulary items:
- **Word text** (EN/PT)
- **Definitions** (EN/PT)
- **Approved images only** (if teacher-approved)
- **Audio pronunciations**
- **Part of speech**
- **WIDA level**

### Lesson Plan Browser Games

**Purpose**: Interactive games for use during lessons on tablet/PC.

**Technology**: JavaScript/HTML5 games (can use Phaser.js or custom engine).

**Features**:
- Real-time gameplay
- Score tracking
- Progress saving
- Multiplayer support (optional)

**Integration**:
- Games linked to lesson plans via `plan_vocabulary_games` table
- Accessible from lesson plan browser module
- Can be launched during lesson delivery

### SCORM 2004 Package Generator

**Purpose**: Generate SCORM 2004 compliant packages for LMS platforms (Moodle, Canvas, Blackboard, etc.).

**SCORM 2004 Features**:
- Sequencing and navigation
- Objectives and assessments
- Progress tracking
- Score reporting
- Completion status

**Package Structure**:
```
scorm_package.zip
├── imsmanifest.xml (SCORM manifest)
├── vocabulary_game.html (Main game file)
├── assets/
│   ├── images/ (Approved images only)
│   ├── audio/ (Pronunciation audio)
│   ├── css/
│   └── js/
└── data/
    └── vocabulary.json (Game data)
```

**Generation Process**:
1. Select vocabulary items (from approved vocabulary)
2. Select game type(s)
3. Configure game parameters (difficulty, language mode, etc.)
4. Generate game HTML/JavaScript
5. Package as SCORM 2004 zip file
6. Store in `vocabulary_games.scorm_package_path`

**Image Handling in SCORM**:
- Only approved images included in package
- Images normalized to SCORM size (600x450px)
- Audio files included for pronunciation

---

## Document Management System

### Overview

UI for managing curriculum and assessment documents in Google FileSearch store.

### Features

1. **Upload Documents**
   - Drag & drop or file picker
   - Supported formats: PDF, DOCX, TXT, JSON
   - Automatic upload to FileSearch store
   - Progress tracking

2. **Document List**
   - View all documents with status (processing/active/failed)
   - Filter by type, subject, grade
   - Search by name/metadata

3. **Document Details**
   - View metadata (type, subject, grade range)
   - See when last queried
   - View custom tags/descriptions
   - Edit metadata

4. **Document Management**
   - Delete documents (removes from FileSearch store)
   - Update metadata
   - Re-upload updated versions

5. **Audit Log**
   - Track which documents were used in which retrievals
   - View retrieval history per document

### Document Types

- **Curriculum**: Grade/subject curriculum documents
- **Assessment Criteria**: Teacher evaluation criteria
- **Strategy Guides**: Bilingual teaching strategies
- **Standards**: Educational standards (CCSS, WIDA, etc.)

### Document Metadata

Each document can have:
- **Type**: Curriculum, assessment_criteria, etc.
- **Subject**: Math, Science, ELA, etc.
- **Grade Range**: K-2, 3-5, 6-8, etc.
- **Custom Tags**: User-defined tags
- **Description**: Free-text description

---

## Database Schema Changes

### New Tables

#### 1. `rag_retrievals`

Stores FileSearch retrieval results per plan generation.

```sql
CREATE TABLE rag_retrievals (
    id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    week_of TEXT NOT NULL,
    slot_number INTEGER,
    
    -- Query profile sent to FileSearch
    query_profile JSONB NOT NULL,
    
    -- Retrieved results
    retrieved_items JSONB NOT NULL,
    
    -- Metadata
    retrieval_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    retrieval_version INTEGER DEFAULT 1,
    
    -- Teacher edits
    teacher_modified BOOLEAN DEFAULT FALSE,
    modified_items JSONB,
    
    -- Sync tracking
    sync_status TEXT DEFAULT 'pending',
    last_synced_at TIMESTAMP,
    sync_device_id TEXT,
    
    FOREIGN KEY (plan_id) REFERENCES weekly_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_rag_retrievals_plan ON rag_retrievals(plan_id, retrieval_version);
```

#### 2. `file_search_documents`

Tracks documents uploaded to Google FileSearch.

```sql
CREATE TABLE file_search_documents (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    
    -- Document metadata
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size_bytes INTEGER,
    upload_path TEXT,
    
    -- Google FileSearch metadata
    file_search_store_id TEXT NOT NULL,
    file_search_file_id TEXT,
    file_search_status TEXT DEFAULT 'pending',
    
    -- Categorization
    document_type TEXT,
    subject TEXT,
    grade_range TEXT,
    custom_metadata JSONB,
    
    -- Lifecycle
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    last_queried_at TIMESTAMP,
    
    -- Sync tracking
    sync_status TEXT DEFAULT 'pending',
    last_synced_at TIMESTAMP,
    sync_device_id TEXT,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_file_search_docs_user ON file_search_documents(user_id, file_search_status);
CREATE INDEX idx_file_search_docs_type ON file_search_documents(document_type, subject, grade_range);
```

#### 3. `vocabulary_items`

Shared vocabulary bank (SSOT for words).

```sql
CREATE TABLE vocabulary_items (
    id TEXT PRIMARY KEY,
    
    -- Core word/phrase data
    word_text TEXT NOT NULL,
    word_type TEXT,
    language TEXT DEFAULT 'en',
    part_of_speech TEXT,
    grade TEXT NOT NULL,
    subject TEXT NOT NULL,
    unit_topic TEXT,
    wida_level_min INTEGER,
    wida_level_max INTEGER,
    
    -- Multimedia (multi-API images)
    images JSONB,  -- Array of {
                   --   url: string,
                   --   source_api: string,
                   --   source_id: string,
                   --   original_width: integer,
                   --   original_height: integer,
                   --   normalized_url: string,
                   --   thumbnail_url: string,
                   --   approved_by_teacher_id: string | null,
                   --   rejected: boolean
                   -- }
    audio_url TEXT,
    audio_source TEXT DEFAULT 'google_tts',
    definition_en TEXT,
    definition_pt TEXT,
    
    -- Generation metadata
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generated_by_plan_id TEXT,
    generation_method TEXT,
    
    -- Approval workflow
    approval_status TEXT DEFAULT 'pending',
    approved_by_user_id TEXT,
    approved_at TIMESTAMP,
    
    -- Usage statistics
    usage_count INTEGER DEFAULT 0,
    
    -- Sync tracking
    sync_status TEXT DEFAULT 'pending',
    last_synced_at TIMESTAMP,
    sync_device_id TEXT,
    
    UNIQUE(word_text, grade, subject)
);

CREATE INDEX idx_vocab_grade_subject ON vocabulary_items(grade, subject, approval_status);
CREATE INDEX idx_vocab_word_text ON vocabulary_items(word_text);
CREATE INDEX idx_vocab_wida_level ON vocabulary_items(wida_level_min, wida_level_max);
```

#### 4. `vocabulary_teacher_approvals`

Per-teacher approval and image preferences.

```sql
CREATE TABLE vocabulary_teacher_approvals (
    id TEXT PRIMARY KEY,
    vocab_item_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    approved BOOLEAN DEFAULT FALSE,
    selected_image_url TEXT,
    rejected_image_urls JSONB,
    notes TEXT,
    approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (vocab_item_id) REFERENCES vocabulary_items(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    UNIQUE(vocab_item_id, user_id)
);
```

#### 5. `vocabulary_usages`

Links vocabulary to specific lesson plans.

```sql
CREATE TABLE vocabulary_usages (
    id TEXT PRIMARY KEY,
    vocab_item_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    week_of TEXT NOT NULL,
    slot_number INTEGER,
    day TEXT,
    activity_context TEXT,
    
    -- Teacher preferences for this usage
    selected_image_url TEXT,
    teacher_notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (vocab_item_id) REFERENCES vocabulary_items(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES weekly_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_vocab_usages_plan ON vocabulary_usages(plan_id);
CREATE INDEX idx_vocab_usages_user ON vocabulary_usages(user_id, week_of);
```

#### 6. `image_normalization_cache`

Caches normalized image versions.

```sql
CREATE TABLE image_normalization_cache (
    id TEXT PRIMARY KEY,
    original_url TEXT NOT NULL UNIQUE,
    source_api TEXT NOT NULL,
    
    -- Normalized versions
    normalized_url TEXT NOT NULL,
    thumbnail_url TEXT NOT NULL,
    
    -- Normalization metadata
    original_width INTEGER,
    original_height INTEGER,
    normalized_width INTEGER DEFAULT 800,
    normalized_height INTEGER DEFAULT 600,
    format TEXT DEFAULT 'png',
    has_transparency BOOLEAN,
    
    -- Storage location
    storage_path TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(original_url)
);
```

#### 7. `vocabulary_games`

Stores game configurations.

```sql
CREATE TABLE vocabulary_games (
    id TEXT PRIMARY KEY,
    game_type TEXT NOT NULL,
    
    -- Vocabulary selection
    vocab_item_ids JSONB NOT NULL,
    
    -- Game configuration
    difficulty_level TEXT,
    language_mode TEXT,
    game_config JSONB,
    
    -- Generation metadata
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generated_by_user_id TEXT,
    generated_for_plan_id TEXT,
    
    -- Output formats
    browser_game_data JSONB,
    scorm_package_path TEXT,
    
    FOREIGN KEY (generated_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (generated_for_plan_id) REFERENCES weekly_plans(id) ON DELETE SET NULL
);
```

#### 8. `plan_vocabulary_games`

Links games to lesson plans.

```sql
CREATE TABLE plan_vocabulary_games (
    id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    display_order INTEGER,
    
    FOREIGN KEY (plan_id) REFERENCES weekly_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (game_id) REFERENCES vocabulary_games(id) ON DELETE CASCADE
);
```

### Modified Tables

#### `weekly_plans`

Add optional reference to retrieval:

```sql
-- Already has lesson_json JSONB column (from DATABASE_ARCHITECTURE_AND_SYNC.md)
-- No additional changes needed (retrieval linked via rag_retrievals.plan_id)
```

---

## Service Layer Architecture

### New Services

**Note**: These services can be organized as Agent Skills (see [AGENT_SKILLS_AND_CODE_EXECUTION.md](./AGENT_SKILLS_AND_CODE_EXECUTION.md)) for better code organization and progressive loading. They can also be containerized as background workers (see [CONTAINERIZATION_STRATEGY.md](./CONTAINERIZATION_STRATEGY.md)).

#### 1. `FileSearchService`

Manages Google FileSearch integration.

```python
# backend/services/file_search_service.py
class FileSearchService:
    async def create_store(self, store_name: str) -> str
    async def upload_document(self, file_path: str, metadata: Dict) -> str
    async def list_documents(self, store_id: str) -> List[Dict]
    async def delete_document(self, file_search_file_id: str) -> bool
    async def retrieve_context(self, query_profile: Dict, store_id: str) -> Dict
    async def get_retrieval_status(self, file_id: str) -> str
```

**Containerization**: Not needed initially - simple API client, can run in main backend.

**CRITICAL: API Fallback Strategy**

The FileSearch service must implement graceful degradation. If Google FileSearch is unavailable, the system must continue functioning by falling back to local strategy files.

**Fallback Implementation**:
```python
# backend/services/file_search_service.py
from backend.telemetry import logger
from pathlib import Path
import json

class FileSearchService:
    def __init__(self):
        self.fallback_enabled = True
        self.retry_attempts = 3
        self.retry_delay = 2  # seconds
    
    async def retrieve_context_with_fallback(
        self, 
        query_profile: Dict, 
        store_id: str
    ) -> Dict:
        """
        Retrieve context with automatic fallback to local strategies.
        
        Fallback Strategy:
        1. Try Google FileSearch (with retries)
        2. If fails, use cached recent retrievals
        3. If no cache, fallback to local strategy files
        4. Log fallback for monitoring
        """
        # Try primary FileSearch with retries
        for attempt in range(self.retry_attempts):
            try:
                result = await self.retrieve_context(query_profile, store_id)
                
                # Cache successful retrieval
                await self._cache_retrieval(query_profile, result)
                
                return result
                
            except FileSearchError as e:
                if attempt < self.retry_attempts - 1:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        f"FileSearch attempt {attempt + 1} failed, retrying in {delay}s",
                        extra={"error": str(e), "query_profile": query_profile}
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    # All retries failed, use fallback
                    logger.error(
                        f"FileSearch failed after {self.retry_attempts} attempts, using fallback",
                        extra={"error": str(e), "query_profile": query_profile}
                    )
                    break
        
        # Fallback: Try cached retrieval
        cached = await self._get_cached_retrieval(query_profile)
        if cached:
            logger.info("Using cached FileSearch retrieval", extra={"query_profile": query_profile})
            return cached
        
        # Fallback: Use local strategy files
        if self.fallback_enabled:
            logger.info("Falling back to local strategy files", extra={"query_profile": query_profile})
            return await self._fallback_to_local_strategies(query_profile)
        else:
            # No fallback - raise error
            raise FileSearchUnavailableError(
                "FileSearch unavailable and fallback disabled",
                query_profile
            )
    
    async def _fallback_to_local_strategies(self, query_profile: Dict) -> Dict:
        """Fallback to local strategy files when FileSearch is unavailable."""
        grade = query_profile.get('grade')
        subject = query_profile.get('subject')
        
        # Load relevant strategy categories based on query
        strategy_categories = self._select_strategy_categories(grade, subject)
        
        # Load strategy files
        strategies = []
        for category in strategy_categories:
            strategy_file = Path(f"strategies_pack_v2/core/{category}.json")
            if strategy_file.exists():
                with open(strategy_file) as f:
                    category_strategies = json.load(f)
                    strategies.extend(category_strategies.get('strategies', []))
        
        # Format as retrieval result
        return {
            "items": [
                {
                    "fileId": f"local_strategy_{s['id']}",
                    "snippet": f"{s.get('strategy_name', '')}: {s.get('core_principle', '')}",
                    "relevanceScore": 0.8,  # High relevance for local strategies
                    "citation": f"Local Strategy: {s.get('id', 'unknown')}",
                    "source": "local_fallback"
                }
                for s in strategies[:10]  # Limit to top 10
            ],
            "fallback_used": True,
            "fallback_reason": "FileSearch unavailable"
        }
    
    async def _cache_retrieval(self, query_profile: Dict, result: Dict):
        """Cache retrieval result for offline use."""
        cache_key = self._generate_cache_key(query_profile)
        cache_data = {
            "query_profile": query_profile,
            "result": result,
            "cached_at": datetime.now().isoformat(),
            "ttl": 86400  # 24 hours
        }
        # Store in Redis or local cache
        await self.cache.set(cache_key, cache_data, ttl=86400)
    
    async def _get_cached_retrieval(self, query_profile: Dict) -> Optional[Dict]:
        """Get cached retrieval if available and fresh."""
        cache_key = self._generate_cache_key(query_profile)
        cached = await self.cache.get(cache_key)
        
        if cached and not self._is_cache_expired(cached):
            return cached["result"]
        
        return None
```

**Graceful Degradation Behavior**:
- **With RAG**: Enhanced lesson plans with curriculum context
- **Without RAG (fallback)**: Standard lesson plans using local strategies only
- **User Notification**: Inform user when fallback is used (optional, non-blocking)
- **Monitoring**: Track fallback usage rate for service health monitoring

#### 2. `ImageCollector`

Collects images from multiple APIs.

```python
# backend/services/image_collector.py
class ImageCollector:
    async def collect_images(
        self,
        query: str,
        count: int = 5,
        grade_level: str = None,
        subject: str = None
    ) -> List[Dict]:
        """Query Unsplash, Pixabay, Pexels, Openverse in parallel."""
```

**Containerization**: ✅ Recommended - Can run as background worker container with image processing dependencies (PIL/Pillow, etc.). See [CONTAINERIZATION_STRATEGY.md](./CONTAINERIZATION_STRATEGY.md).

#### 3. `AudioGenerator`

Generates audio using Google TTS.

```python
# backend/services/audio_generator.py
class AudioGenerator:
    async def generate_pronunciation(
        self,
        word: str,
        language: str = 'en'  # 'en', 'pt-BR', 'pt-PT'
    ) -> str:
        """Generate audio URL for word pronunciation."""
```

**Containerization**: ✅ Recommended - Can run as background worker container with Google TTS dependencies. See [CONTAINERIZATION_STRATEGY.md](./CONTAINERIZATION_STRATEGY.md).

#### 4. `ImageNormalizer`

Normalizes images to standard sizes.

```python
# backend/services/image_normalizer.py
class ImageNormalizer:
    STANDARD_SIZES = {
        'vocabulary_card': (800, 600),
        'game_image': (400, 300),
        'thumbnail': (200, 200),
        'scorm_image': (600, 450)
    }
    
    async def normalize_image(
        self,
        original_url: str,
        source_api: str,
        target_size: Tuple[int, int] = (800, 600),
        preserve_transparency: bool = True
    ) -> Dict:
        """Download, resize, and cache normalized image."""
```

**Containerization**: ✅ Recommended - Part of image collection worker, requires PIL/Pillow and image processing libraries. See [CONTAINERIZATION_STRATEGY.md](./CONTAINERIZATION_STRATEGY.md).

#### 5. `VocabularyExtractor`

Extracts vocabulary from plans and RAG context.

```python
# backend/services/vocabulary_extractor.py
class VocabularyExtractor:
    def extract_from_plan(self, lesson_json: Dict) -> List[Dict]
    def extract_from_rag_context(self, rag_items: List[Dict]) -> List[Dict]
    def extract_from_curriculum_query(self, grade: str, subject: str, unit: str) -> List[Dict]
```

#### 6. `VocabularyService`

Manages vocabulary generation, storage, and approval.

```python
# backend/services/vocabulary_service.py
class VocabularyService:
    async def find_by_text_grade_subject(self, word_text: str, grade: str, subject: str) -> Optional[Dict]
    async def generate_new_word(self, word_text: str, ...) -> str
    async def get_teacher_approval(self, vocab_item_id: str, user_id: str) -> Optional[Dict]
    async def approve_word(self, vocab_item_id: str, user_id: str, selected_image_url: str) -> Dict
    async def create_usage(self, vocab_item_id: str, plan_id: str, ...) -> str
```

#### 7. `VocabularyGameGenerator`

Generates vocabulary games for browser and SCORM.

```python
# backend/services/game_generator.py
class VocabularyGameGenerator:
    async def generate_matching_game(self, vocab_items: List[Dict], language_mode: str) -> Dict
    async def generate_crossword(self, vocab_items: List[Dict], grid_size: int) -> Dict
    async def generate_flashcards(self, vocab_items: List[Dict], spaced_repetition: bool) -> Dict
    async def generate_scorm_package(self, game_id: str, games: List[Dict]) -> str
    # ... other game types
```

**Containerization**: ✅ Recommended (when implemented) - SCORM package generation may have dependencies (zip tools, XML processing). Can run as background worker. See [CONTAINERIZATION_STRATEGY.md](./CONTAINERIZATION_STRATEGY.md).

**Code Execution Optimization**: These services benefit from code execution patterns (see [AGENT_SKILLS_AND_CODE_EXECUTION.md](./AGENT_SKILLS_AND_CODE_EXECUTION.md)) for batch processing and parallel game generation.

---

## Integration with Existing Architecture

### Compatibility with DATABASE_ARCHITECTURE_AND_SYNC.md

**Preserved Principles**:
- ✅ `lesson_json` remains SSOT for lesson plans
- ✅ Local-first architecture (vocab/retrieval tables exist locally and in Supabase)
- ✅ P2P sync pattern (vocab/retrieval sync alongside plans)
- ✅ Sync tracking (same `sync_status`, `last_synced_at`, `sync_device_id` pattern)

**New Considerations**:
- Vocabulary is shared (all teachers), so sync must handle multi-teacher approvals
- Retrieval edits are per-plan, so conflicts are less likely
- Images stored locally and in Supabase Storage (sync via same mechanism)

### Data Flow Integration

```
Existing Flow:
DOCX → Parse → LLM → lesson_json → Render DOCX

Enhanced Flow:
DOCX → Parse → RAG Query → FileSearch → LLM (enhanced) → lesson_json
                                                              ↓
                                                    Vocabulary Extraction
                                                              ↓
                                                    Image/Audio Generation
                                                              ↓
                                                    Teacher Approval
                                                              ↓
                                                    Game Generation (optional)
```

### Storage Considerations

**Free Tier Sufficiency**:
- Vocabulary items: ~1-5KB per word (text + metadata)
- RAG retrievals: ~5-20KB per retrieval
- Vocabulary usages: ~500 bytes per usage link
- Image normalization cache: ~1KB per image (metadata only; images in storage)

**Estimates**:
- 1000 vocabulary items: ~5MB
- 200 retrievals/year: ~4MB
- 10,000 usage links: ~5MB
- **Total: ~14MB/year** (well within 500MB free tier)

**Image Storage**:
- Images stored in Supabase Storage (separate from database)
- Free tier: 1GB storage
- Estimated: ~50KB per normalized image
- 1000 words × 1 approved image = ~50MB (well within limit)

---

## Implementation Phases

### Phase 1: FileSearch RAG Integration (Weeks 1-2)

- [ ] Set up Google Cloud project and enable Gemini API + FileSearch
- [ ] Create FileSearch store
- [ ] Implement `FileSearchService`
- [ ] Integrate RAG retrieval into batch processor
- [ ] Create `rag_retrievals` table
- [ ] Test retrieval and storage

### Phase 2: Document Management UI (Week 3)

- [ ] Create `file_search_documents` table
- [ ] Build document upload UI
- [ ] Build document list/view UI
- [ ] Implement document deletion
- [ ] Add metadata editing
- [ ] Test document lifecycle

### Phase 3: Vocabulary Module Core (Weeks 4-5)

- [ ] Create vocabulary tables (`vocabulary_items`, `vocabulary_teacher_approvals`, `vocabulary_usages`)
- [ ] Implement `VocabularyExtractor`
- [ ] Implement `VocabularyService`
- [ ] Integrate vocabulary extraction into generation flow
- [ ] Test vocabulary extraction and storage

### Phase 4: Image/Audio Collection (Weeks 6-7)

- [ ] Set up API keys (Unsplash, Pixabay, Pexels, Openverse)
- [ ] Implement `ImageCollector`
- [ ] Set up Google Cloud TTS
- [ ] Implement `AudioGenerator`
- [ ] Implement `ImageNormalizer`
- [ ] Create `image_normalization_cache` table
- [ ] Test image/audio generation pipeline

### Phase 5: Teacher Approval Workflow (Week 8)

- [ ] Build Vocabulary Approval UI
- [ ] Implement approval API endpoints
- [ ] Test approval workflow
- [ ] Verify image constraint (no images until approved)

### Phase 6: Game Generation - Browser (Weeks 9-10)

- [ ] Create `vocabulary_games` and `plan_vocabulary_games` tables
- [ ] Implement `VocabularyGameGenerator` (browser games)
- [ ] Build game UI components
- [ ] Integrate games into lesson plan browser
- [ ] Test game generation and playback

### Phase 7: Game Generation - SCORM 2004 (Weeks 11-12)

- [ ] Research SCORM 2004 specification
- [ ] Implement SCORM manifest generator
- [ ] Implement SCORM package builder
- [ ] Test SCORM packages in LMS (Moodle, Canvas)
- [ ] Verify image handling (approved images only)

### Phase 8: Testing & Optimization (Weeks 13-14)

- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Error handling
- [ ] Documentation
- [ ] User acceptance testing

**Performance Testing Strategy**:

Define and implement SLAs for all operations:

- **Vocabulary Extraction**: < 100ms for 50 words
- **Image Collection**: < 5s for 50 words (parallel API calls)
- **Image Normalization**: < 500ms per image (with caching)
- **Audio Generation**: < 2s per word (batch processing)
- **Full Lesson Plan Generation**: < 10 minutes for 5 slots (including RAG, vocabulary, images)
- **P2P Sync**: < 5s for 1MB plan
- **RAG Retrieval**: < 2s per query (with fallback < 500ms)

**Load Testing Scenarios**:
- 10 concurrent lesson plan generations
- 100 vocabulary items processed in parallel
- 5 simultaneous P2P syncs
- 50 concurrent image collection requests

**Conflict Simulation Tests**:
- Simulate concurrent edits on same plan
- Test field-level conflict detection
- Verify vector clock comparison
- Test merge strategies with various conflict patterns

---

## Key Constraints and Rules

### Image Approval Constraint

**RULE**: Images are **never used** until teacher-approved.

**Implementation**:
- Images collected during generation, status: `'pending'`
- Words can be used **without images** if approval pending
- Only approved images appear in:
  - Lesson plan browser
  - Vocabulary games
  - SCORM packages
- Fallback: Word text only if no approved image

### Vocabulary Sharing

**RULE**: Vocabulary is shared across all teachers.

**Implementation**:
- `vocabulary_items` has no `user_id` (global)
- Per-teacher preferences in `vocabulary_teacher_approvals`
- Each teacher sees their selected image (Option A)

### SCORM 2004 Compliance

**RULE**: SCORM packages must be SCORM 2004 compliant.

**Implementation**:
- Generate `imsmanifest.xml` with SCORM 2004 schema
- Include sequencing and navigation
- Support objectives and assessments
- Track progress and completion

---

## API Dependencies

### External APIs

1. **Google Gemini API** (FileSearch)
   - Cost: $0.15 per 1M tokens (indexing only)
   - Free: Storage and query-time embeddings
   - **Rate Limits**: Not publicly documented, implement exponential backoff
   - **Fallback**: Local strategy files (see FileSearchService fallback)

2. **Unsplash API**
   - Free: 50 requests/hour
   - Requires API key
   - **Rate Limit Handling**: Queue requests, respect 50/hour limit

3. **Pixabay API**
   - Free: 5,000 requests/day
   - Requires API key
   - **Rate Limit Handling**: Most generous, use as primary source

4. **Pexels API**
   - Free: 200 requests/hour
   - Requires API key
   - **Rate Limit Handling**: Queue requests, respect 200/hour limit

5. **Openverse API**
   - Free, no API key required
   - Creative Commons licensed
   - **Rate Limit Handling**: No documented limits, use as fallback

6. **Google Cloud Text-to-Speech**
   - Free: 0-4 million characters/month
   - Requires Google Cloud project
   - **Rate Limit Handling**: Well within free tier for expected usage

### Cost Monitoring and Rate Limit Management

**CRITICAL**: Implement cost monitoring and rate limit tracking to prevent unexpected charges and API failures.

**Cost Tracking Implementation**:
```python
# backend/services/api_cost_tracker.py
from datetime import datetime, timedelta
from collections import defaultdict

class APICostTracker:
    """Track API usage and costs."""
    
    def __init__(self):
        self.usage = defaultdict(lambda: {
            'requests': 0,
            'tokens': 0,
            'cost': 0.0,
            'rate_limit_resets_at': None
        })
    
    async def track_file_search_indexing(self, tokens: int):
        """Track FileSearch indexing costs."""
        cost = (tokens / 1_000_000) * 0.15
        self.usage['file_search']['tokens'] += tokens
        self.usage['file_search']['cost'] += cost
        
        # Alert if approaching budget
        if self.usage['file_search']['cost'] > 1.0:  # $1 threshold
            await self._send_cost_alert('file_search', self.usage['file_search']['cost'])
    
    async def track_image_api_request(self, api_name: str, requests: int = 1):
        """Track image API requests and rate limits."""
        self.usage[api_name]['requests'] += requests
        
        # Check rate limits
        rate_limits = {
            'unsplash': {'limit': 50, 'window': 3600},  # 50/hour
            'pixabay': {'limit': 5000, 'window': 86400},  # 5000/day
            'pexels': {'limit': 200, 'window': 3600},  # 200/hour
        }
        
        if api_name in rate_limits:
            limit = rate_limits[api_name]
            if self.usage[api_name]['requests'] >= limit['limit']:
                # Rate limit reached, schedule reset
                reset_time = datetime.now() + timedelta(seconds=limit['window'])
                self.usage[api_name]['rate_limit_resets_at'] = reset_time
                raise RateLimitExceededError(
                    f"{api_name} rate limit reached. Resets at {reset_time}"
                )
    
    async def track_tts_usage(self, characters: int):
        """Track TTS character usage."""
        self.usage['tts']['tokens'] += characters  # Using 'tokens' field for characters
        
        # Check free tier limit (4M chars/month)
        if self.usage['tts']['tokens'] > 3_500_000:  # 3.5M warning threshold
            await self._send_usage_alert('tts', self.usage['tts']['tokens'])
    
    async def get_monthly_cost_summary(self) -> dict:
        """Get cost summary for current month."""
        return {
            api: {
                'requests': data['requests'],
                'cost': data['cost'],
                'rate_limit_status': self._get_rate_limit_status(api, data)
            }
            for api, data in self.usage.items()
        }
    
    def _get_rate_limit_status(self, api: str, data: dict) -> dict:
        """Get current rate limit status."""
        if data.get('rate_limit_resets_at'):
            if datetime.now() < data['rate_limit_resets_at']:
                return {
                    'limited': True,
                    'resets_at': data['rate_limit_resets_at'].isoformat()
                }
            else:
                # Reset window passed
                data['requests'] = 0
                data['rate_limit_resets_at'] = None
        
        return {'limited': False}
```

**Cost Dashboard Endpoint**:
```python
# backend/api.py
@app.get("/api/admin/cost-summary")
async def get_cost_summary(user_id: str):
    """Get API cost summary for user."""
    tracker = APICostTracker()
    summary = await tracker.get_monthly_cost_summary()
    
    return {
        "user_id": user_id,
        "month": datetime.now().strftime("%Y-%m"),
        "summary": summary,
        "total_cost": sum(s['cost'] for s in summary.values()),
        "alerts": await tracker.get_active_alerts()
    }
```

**Rate Limit Queue Implementation**:
```python
# backend/services/rate_limit_queue.py
class RateLimitQueue:
    """Queue API requests to respect rate limits."""
    
    def __init__(self):
        self.queues = {
            'unsplash': asyncio.Queue(),
            'pexels': asyncio.Queue(),
        }
        self.rate_limiters = {
            'unsplash': RateLimiter(max_calls=50, period=3600),
            'pexels': RateLimiter(max_calls=200, period=3600),
        }
    
    async def enqueue_request(self, api_name: str, request_func, *args, **kwargs):
        """Enqueue API request with rate limiting."""
        if api_name in self.rate_limiters:
            # Wait for rate limit window
            await self.rate_limiters[api_name].acquire()
        
        # Execute request
        return await request_func(*args, **kwargs)
```

---

## Security Considerations

### API Key Management

- Store API keys in environment variables or secure keychain
- Never commit keys to version control
- Rotate keys periodically

### Image Content Safety

- Filter inappropriate images (content moderation)
- Age-appropriate content for grade levels
- Teacher review required before approval

### Data Privacy

- Vocabulary items are shared (no PII)
- Teacher approvals are per-user (private)
- Document uploads are per-user (private)

### PII Scrubbing

**CRITICAL**: Remove PII before sending data to external APIs.

**Implementation**:
```python
# backend/services/pii_scrubber.py
import re
from typing import List

class PIIScrubber:
    """Remove PII from content before external API calls."""
    
    def scrub(self, content: str) -> str:
        """Remove PII from content."""
        # Remove email addresses
        content = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[EMAIL]',
            content
        )
        
        # Remove phone numbers
        content = re.sub(
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            '[PHONE]',
            content
        )
        
        # Remove potential student names (heuristic - would need ML model for production)
        # For now, rely on teacher to avoid including student names in lesson plans
        
        return content
    
    def scrub_query_profile(self, query_profile: dict) -> dict:
        """Scrub PII from RAG query profile."""
        scrubbed = query_profile.copy()
        
        # Scrub objectives (may contain student names)
        if 'objectives' in scrubbed:
            scrubbed['objectives'] = [
                self.scrub(obj) for obj in scrubbed['objectives']
            ]
        
        return scrubbed
```

**Usage**:
```python
# Before sending to FileSearch
scrubber = PIIScrubber()
clean_query = scrubber.scrub_query_profile(query_profile)
result = await file_search.retrieve_context(clean_query)
```

### Image Storage Cleanup

**Automated Cleanup Strategy**:
```python
# backend/services/image_cleanup.py
from datetime import datetime, timedelta

class ImageCleanupService:
    """Clean up unapproved and unused images."""
    
    async def cleanup_unapproved_images(self, days_old: int = 30):
        """Remove unapproved images older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Find unapproved images
        unapproved = await self.db.query("""
            SELECT id, normalized_url, original_url
            FROM image_normalization_cache
            WHERE created_at < ?
            AND NOT EXISTS (
                SELECT 1 FROM vocabulary_items
                WHERE images::jsonb @> jsonb_build_object('normalized_url', normalized_url)
                AND approval_status = 'approved'
            )
        """, (cutoff_date,))
        
        # Delete from storage and cache
        for img in unapproved:
            try:
                await self.storage.delete(img['normalized_url'])
                await self.storage.delete(img.get('thumbnail_url'))
                await self.db.delete('image_normalization_cache', img['id'])
                logger.info(f"Cleaned up unapproved image: {img['id']}")
            except Exception as e:
                logger.error(f"Failed to cleanup image {img['id']}: {e}")
    
    async def archive_rejected_images(self, days_old: int = 90):
        """Archive rejected images (don't delete immediately)."""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Move to archive storage
        rejected = await self.db.query("""
            SELECT id, normalized_url
            FROM image_normalization_cache
            WHERE created_at < ?
            AND EXISTS (
                SELECT 1 FROM vocabulary_items
                WHERE images::jsonb @> jsonb_build_object('normalized_url', normalized_url)
                AND images::jsonb @> jsonb_build_object('rejected', true)
            )
        """, (cutoff_date,))
        
        for img in rejected:
            await self.storage.archive(img['normalized_url'])
            logger.info(f"Archived rejected image: {img['id']}")
    
    async def monitor_storage_usage(self) -> dict:
        """Monitor storage usage and alert if approaching limits."""
        usage = await self.storage.get_usage()
        
        # Check Supabase Storage limit (1GB free tier)
        if usage['total_bytes'] > 900 * 1024 * 1024:  # 900MB warning
            await self._send_storage_alert(usage)
        
        return usage
```

---

## Future Enhancements

### Potential Additions

1. **Advanced RAG**: Fine-tune retrieval queries based on teacher feedback
2. **Image Quality Scoring**: Automatically rank images by quality
3. **Multi-Language Audio**: Support additional languages beyond EN/PT
4. **Game Analytics**: Track student performance in games
5. **SCORM Analytics**: Integrate SCORM reporting with LMS
6. **Vocabulary Spaced Repetition**: Implement SRS algorithm for flashcards

---

## Conclusion

This document outlines the architectural enhancements for enhanced lesson plan generation with FileSearch RAG, vocabulary module, and game generation. All enhancements maintain compatibility with the existing local-first, P2P sync architecture while adding powerful new capabilities for vocabulary learning and game-based instruction.

**Key Takeaways**:
- Images require teacher approval before use
- Vocabulary is shared across teachers (cost-effective)
- SCORM 2004 packages enable LMS integration
- All new features respect existing SSOT and sync patterns

---

## References

- [DATABASE_ARCHITECTURE_AND_SYNC.md](./DATABASE_ARCHITECTURE_AND_SYNC.md) - Existing sync architecture
- [AGENT_SKILLS_AND_CODE_EXECUTION.md](./AGENT_SKILLS_AND_CODE_EXECUTION.md) - How to optimize these workflows with Agent Skills and code execution
- [CONTAINERIZATION_STRATEGY.md](./CONTAINERIZATION_STRATEGY.md) - Docker/Kubernetes recommendations for new services
- [Google FileSearch Documentation](https://ai.google.dev/gemini-api/docs/file-search)
- [SCORM 2004 Specification](https://www.adlnet.gov/scorm/scorm-2004-4th-edition/)
- [Google Cloud TTS Documentation](https://cloud.google.com/text-to-speech/docs)

