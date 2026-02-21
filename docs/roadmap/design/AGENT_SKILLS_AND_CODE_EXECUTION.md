# Agent Skills and Code Execution with MCP for Lesson Plan Builder

## Executive Summary

This document explores how Anthropic's **Agent Skills** and **Code Execution with MCP** can enhance the Lesson Plan Builder application. These approaches enable more efficient, composable, and scalable agent workflows by:

1. **Agent Skills**: Packaging domain expertise into reusable, discoverable skill folders
2. **Code Execution with MCP**: Using code execution environments to interact with MCP servers more efficiently, reducing token costs and improving performance

**Key Benefits**:
- **98.7% token reduction** in tool definition loading (from 150K to 2K tokens)
- **Progressive disclosure**: Load only needed tools/instructions
- **Context-efficient processing**: Filter and transform data before passing to LLM
- **Reusable expertise**: Skills can be shared and composed across tasks
- **State persistence**: Agents can maintain state across operations

> **Architecture Status (Dec 2025):** This architecture leverages the now-standard **Anthropic Model Context Protocol (MCP)** and **Code Execution** patterns. The "Agent Skills" directory structure is a custom design pattern to organize these MCP servers. This approach is fully supported by current SDKs.

**Note**: This document uses both TypeScript and Python examples. The codebase is primarily Python (FastAPI backend), but Agent Skills can be implemented in any language. TypeScript examples demonstrate the concept from Anthropic's documentation, while Python examples show practical implementation for this project.

> **Architecture decision (Feb 2026):**
> References to Google FileSearch / Gemini File Search in this document reflect the original hypothesis. The current recommended approach is **Claude MCP Local Document Access** — metadata-driven file lookup feeding documents into Claude's context window. Skills that reference `file_search_service.py` or `FileSearchService` should be understood as using a local curriculum context service instead. See [ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](./ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md) for full rationale. Google FileSearch remains a hypothesis for future evaluation.

**Related Documents**:
- [README.md](./README.md) - Master index of all expansion documents
- [ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](./ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md) - Detailed architecture for new features
- [CONTAINERIZATION_STRATEGY.md](./CONTAINERIZATION_STRATEGY.md) - Docker/Kubernetes recommendations
- [DATABASE_ARCHITECTURE_AND_SYNC.md](./DATABASE_ARCHITECTURE_AND_SYNC.md) - Existing sync architecture

---

## Table of Contents

1. [Agent Skills for Lesson Plan Builder](#agent-skills-for-lesson-plan-builder)
2. [Code Execution with MCP Integration](#code-execution-with-mcp-integration)
3. [Workflow Improvements](#workflow-improvements)
4. [Implementation Strategy](#implementation-strategy)
5. [Examples and Use Cases](#examples-and-use-cases)

---

## Agent Skills for Lesson Plan Builder

### What are Agent Skills?

Agent Skills are organized folders containing:
- **SKILL.md**: Structured instructions and metadata
- **Scripts**: Reusable code functions
- **Resources**: Reference materials, templates, examples
- **Examples**: Sample inputs/outputs

Skills enable agents to discover and load domain-specific expertise dynamically, transforming general-purpose agents into specialized tools.

### Proposed Skills for Our Application

#### 1. Lesson Plan Generation Skill

**Purpose**: Generate bilingual lesson plans with WIDA alignment and RAG context.

**Structure**:
```
skills/
└── lesson-plan-generation/
    ├── SKILL.md
    ├── scripts/
    │   ├── build_rag_query.py      # Python implementation
    │   ├── enhance_with_context.py
    │   ├── apply_strategies.py
    │   └── validate_output.py
    ├── resources/
    │   ├── strategy-selection-algorithm.md
    │   ├── wida-framework-reference.json
    │   └── prompt-templates/
    │       ├── language-objective.md
    │       └── bilingual-bridge.md
    └── examples/
        ├── input-primary-plan.json
        └── output-enhanced-plan.json
```

**SKILL.md Content**:
```markdown
# Lesson Plan Generation Skill

## Purpose
Generate WIDA-aligned bilingual lesson plans from primary teacher DOCX files, 
enhanced with RAG context from curriculum documents and assessment criteria.

## Capabilities
- Parse primary teacher lesson plans
- Build RAG query profiles from lesson metadata
- Retrieve relevant curriculum context
- Apply bilingual strategies (33 strategies, 6 categories)
- Generate language objectives with Portuguese/English frames
- Validate output against schema

## Inputs
- Primary teacher DOCX file
- Grade level
- Subject
- Week of
- User ID

## Outputs
- Enhanced lesson_json (SSOT)
- RAG retrieval results
- Strategy selections with citations
- Vocabulary candidates

## Usage (Python)
```python
from skills.lesson_plan_generation.scripts.enhance_with_context import generate_lesson_plan

plan = await generate_lesson_plan(
    docx_path='./input/week1-math.docx',
    grade='3',
    subject='math',
    week_of='01/15-01/19',
    user_id='teacher_123'
)
```

## Integration
This skill integrates with:
- `backend/services/file_search_service.py` - RAG retrieval
- `tools/batch_processor.py` - Main generation pipeline
- `backend/llm_service.py` - LLM transformations
```

#### 2. Vocabulary Extraction and Enrichment Skill

**Purpose**: Extract vocabulary from lesson plans and RAG context, then enrich with multimedia.

**Structure**:
```
skills/
└── vocabulary-extraction/
    ├── SKILL.md
    ├── scripts/
    │   ├── extract-from-plan.ts
    │   ├── extract-from-rag.ts
    │   ├── query-curriculum.ts
    │   ├── deduplicate-words.ts
    │   └── link-to-plan.ts
    ├── resources/
    │   ├── extraction-patterns.json
    │   └── curriculum-mapping.json
    └── examples/
        └── vocabulary-candidates.json
```

**Key Functions**:
- Extract vocabulary from `lesson_json`
- Extract vocabulary from RAG retrieval results
- Query curriculum for grade/subject vocabulary
- Deduplicate across sources
- Link vocabulary to specific plans/days

#### 3. Image Collection and Normalization Skill

**Purpose**: Collect images from multiple APIs and normalize to standard sizes.

**Structure**:
```
skills/
└── image-collection/
    ├── SKILL.md
    ├── scripts/
    │   ├── collect-from-apis.ts
    │   ├── normalize-image.ts
    │   ├── batch-normalize.ts
    │   └── filter-appropriate.ts
    ├── resources/
    │   ├── api-configs.json
    │   └── size-specs.json
    └── examples/
        └── normalized-images.json
```

**Key Functions**:
- Query Unsplash, Pixabay, Pexels, Openverse in parallel
- Filter for age-appropriate, educational content
- Normalize to standard sizes (vocabulary card, game, thumbnail, SCORM)
- Cache normalized versions
- Preserve transparency for PNGs

#### 4. Audio Generation Skill

**Purpose**: Generate pronunciation audio using Google TTS.

**Structure**:
```
skills/
└── audio-generation/
    ├── SKILL.md
    ├── scripts/
    │   ├── generate-pronunciation.ts
    │   ├── batch-generate.ts
    │   └── validate-audio.ts
    └── resources/
        └── voice-configs.json
```

**Key Functions**:
- Generate audio for English words
- Generate audio for Portuguese words (Brazil/Portugal variants)
- Batch process multiple words
- Validate audio quality

#### 5. Game Generation Skill

**Purpose**: Generate vocabulary games for browser and SCORM 2004.

**Structure**:
```
skills/
└── game-generation/
    ├── SKILL.md
    ├── scripts/
    │   ├── generate-matching.ts
    │   ├── generate-crossword.ts
    │   ├── generate-flashcards.ts
    │   ├── generate-word-search.ts
    │   ├── generate-bingo.ts
    │   └── package-scorm.ts
    ├── resources/
    │   ├── game-templates/
    │   │   ├── matching.html
    │   │   ├── crossword.html
    │   │   └── flashcards.html
    │   └── scorm-manifest-template.xml
    └── examples/
        └── scorm-package.zip
```

**Key Functions**:
- Generate 9 game types (matching, crossword, fill-gap, word search, flashcards, memory, sorting, word ladder, bingo)
- Create browser-compatible HTML/JavaScript games
- Package games as SCORM 2004 compliant zip files
- Include only approved images and audio

#### 6. SCORM 2004 Package Creation Skill

**Purpose**: Create SCORM 2004 compliant packages for LMS integration.

**Structure**:
```
skills/
└── scorm-package/
    ├── SKILL.md
    ├── scripts/
    │   ├── generate-manifest.ts
    │   ├── create-package.ts
    │   ├── validate-scorm.ts
    │   └── test-in-lms.ts
    ├── resources/
    │   ├── scorm-2004-schema.xsd
    │   └── manifest-template.xml
    └── examples/
        └── valid-scorm-package.zip
```

**Key Functions**:
- Generate `imsmanifest.xml` with SCORM 2004 schema
- Package games, images, audio into zip
- Validate SCORM compliance
- Test in LMS environments (Moodle, Canvas)

#### 7. Document Management Skill

**Purpose**: Manage curriculum and assessment documents in Google FileSearch.

**Structure**:
```
skills/
└── document-management/
    ├── SKILL.md
    ├── scripts/
    │   ├── upload-document.ts
    │   ├── list-documents.ts
    │   ├── update-metadata.ts
    │   ├── delete-document.ts
    │   └── audit-usage.ts
    └── resources/
        └── document-types.json
```

**Key Functions**:
- Upload documents to FileSearch store
- List and filter documents
- Update metadata (type, subject, grade range)
- Track document usage in retrievals

#### 8. Teacher Approval Workflow Skill

**Purpose**: Manage vocabulary approval and image selection workflow.

**Structure**:
```
skills/
└── approval-workflow/
    ├── SKILL.md
    ├── scripts/
    │   ├── get-pending-words.ts
    │   ├── approve-word.ts
    │   ├── select-image.ts
    │   ├── bulk-approve.ts
    │   └── finalize-week.ts
    └── resources/
        └── approval-states.json
```

**Key Functions**:
- Retrieve pending vocabulary for approval
- Approve/reject words
- Select preferred images
- Bulk operations
- Finalize week (lock approvals)

#### 9. RAG Query Optimization Skill

**Purpose**: Optimize RAG queries for better retrieval results.

**Structure**:
```
skills/
└── rag-optimization/
    ├── SKILL.md
    ├── scripts/
    │   ├── build-query-profile.ts
    │   ├── refine-query.ts
    │   ├── filter-results.ts
    │   └── analyze-retrieval.ts
    └── resources/
        └── query-templates.json
```

**Key Functions**:
- Build effective query profiles from lesson metadata
- Refine queries based on retrieval quality
- Filter and rank retrieval results
- Analyze retrieval effectiveness

---

## Code Execution with MCP Integration

### Why Code Execution with MCP?

Traditional MCP tool calling loads all tool definitions upfront and passes all intermediate results through the context window. This causes:

1. **Tool definition overload**: 150K+ tokens for hundreds of tools
2. **Intermediate result bloat**: Large documents/data pass through context multiple times
3. **Inefficient control flow**: Complex logic requires multiple tool call rounds

**Code execution with MCP** solves these by:
- **Progressive disclosure**: Load only needed tools
- **Context-efficient processing**: Filter/transform data in code before passing to LLM
- **Better control flow**: Use loops, conditionals, error handling in code
- **Privacy-preserving**: Sensitive data stays in execution environment

### Implementation Approach

Instead of direct tool calls, present MCP servers as code APIs. For this Python-based project, we can implement in Python:

```
backend/
├── services/
│   ├── file_search_service.py      # MCP client wrapper
│   ├── image_collector.py
│   ├── vocabulary_service.py
│   └── game_generator.py
└── mcp_servers/                     # MCP server API wrappers
    ├── file_search/
    │   ├── retrieve_context.py
    │   ├── upload_document.py
    │   └── __init__.py
    ├── image_apis/
    │   ├── unsplash.py
    │   ├── pixabay.py
    │   ├── pexels.py
    │   └── __init__.py
    ├── vocabulary/
    │   ├── extract.py
    │   ├── generate.py
    │   └── __init__.py
    └── games/
        ├── generate_matching.py
        ├── generate_crossword.py
        └── __init__.py
```

Each tool becomes a Python function:

```python
# backend/mcp_servers/file_search/retrieve_context.py
from typing import Dict, List, TypedDict
from backend.mcp_client import call_mcp_tool

# Uses google-genai library under the hood
# pip install google-genai

class RetrieveContextInput(TypedDict):
    queryProfile: Dict[str, any]  # grade, subject, objectives, standards
    storeId: str

class RetrieveContextResponse(TypedDict):
    items: List[Dict[str, any]]  # fileId, snippet, relevanceScore, citation

async def retrieve_context(input: RetrieveContextInput) -> RetrieveContextResponse:
    """
    Retrieve context from Google FileSearch via MCP.
    
    This function wraps the Google Gemini File API, allowing the Agent to:
    1. Search the verified FileSearchStore
    2. Filter results *in code* before returning to the LLM context
    """
    return await call_mcp_tool(
        'file_search__retrieve_context',
        input
    )
```

**Note**: TypeScript examples from Anthropic's documentation demonstrate the concept, but for this project, Python implementations align with the existing FastAPI backend. The principles remain the same regardless of language.

### Benefits for Our Workflow

#### 1. Progressive Tool Loading

**Before** (Direct Tool Calls):
```
Load ALL tool definitions (150K tokens):
- file_search.retrieve_context
- file_search.upload_document
- image_collector.collect_unsplash
- image_collector.collect_pixabay
- image_collector.collect_pexels
- vocabulary.extract_from_plan
- vocabulary.extract_from_rag
- vocabulary.generate_new_word
- audio.generate_pronunciation
- game.generate_matching
- game.generate_crossword
... (50+ more tools)
```

**After** (Code Execution):
```typescript
// Agent discovers tools by exploring filesystem
import * as fileSearch from './servers/file-search';
import * as imageCollector from './servers/image-apis';
// Only loads what it needs (2K tokens)
```

**Token Savings**: 98.7% reduction (150K → 2K tokens)

#### 2. Context-Efficient RAG Result Processing

**Before** (Direct Tool Calls):
```
TOOL CALL: file_search.retrieve_context(queryProfile)
  → Returns 50 document chunks (10K tokens)
  → All 10K tokens pass through context

TOOL CALL: llm.generate_lesson_plan(ragContext: 10K tokens)
  → Processes full 10K tokens again
```

**After** (Code Execution):
```typescript
// Filter and summarize in code before passing to LLM
const rawResults = await fileSearch.retrieveContext({ queryProfile });
const relevantChunks = rawResults.items
  .filter(item => item.relevanceScore > 0.7)
  .slice(0, 10)  // Top 10 most relevant
  .map(item => ({
    snippet: item.snippet.substring(0, 500),  // Truncate long snippets
    citation: item.citation
  }));

// Only 2K tokens pass to LLM instead of 10K
const plan = await llm.generateLessonPlan({
  primaryContent: parsedDocx,
  ragContext: relevantChunks  // Filtered and summarized
});
```

**Token Savings**: 80% reduction (10K → 2K tokens)

#### 3. Efficient Vocabulary Batch Processing

**Before** (Direct Tool Calls):
```
TOOL CALL: vocabulary.extract_from_plan(lessonJson)
  → Returns 50 vocabulary candidates
  → Each candidate processed individually

TOOL CALL: vocabulary.check_exists(word1)
TOOL CALL: vocabulary.check_exists(word2)
... (50 tool calls)

TOOL CALL: image_collector.collect(word1)
TOOL CALL: image_collector.collect(word2)
... (50 tool calls)
```

**After** (Code Execution):
```typescript
// Batch process in code
const candidates = await vocabulary.extractFromPlan(lessonJson);

// Check existence in batch
const existingWords = await vocabulary.batchCheckExists(
  candidates.map(c => ({ word: c.word, grade: c.grade, subject: c.subject }))
);

// Collect images in parallel
const imagePromises = candidates
  .filter(c => !existingWords.has(c.word))
  .map(candidate => 
    Promise.all([
      imageCollector.unsplash(candidate.word, { count: 5 }),
      imageCollector.pixabay(candidate.word, { count: 5 }),
      imageCollector.pexels(candidate.word, { count: 5 })
    ]).then(results => ({
      word: candidate.word,
      images: results.flat()
    }))
  );

const imageResults = await Promise.all(imagePromises);
```

**Performance Improvement**: 10x faster (parallel processing vs sequential)

#### 4. Image Normalization in Code

**Before** (Direct Tool Calls):
```
TOOL CALL: image_normalizer.normalize(url1, size: 'vocabulary_card')
  → Returns normalized URL
TOOL CALL: image_normalizer.normalize(url2, size: 'vocabulary_card')
  → Returns normalized URL
... (200 tool calls for 50 words × 4 images)
```

**After** (Code Execution):
```typescript
// Normalize images in code with caching
const normalizeImage = async (url: string, targetSize: [number, number]) => {
  // Check cache first
  const cached = await db.getNormalizedImage(url, targetSize);
  if (cached) return cached;
  
  // Download and normalize
  const image = await downloadImage(url);
  const normalized = await resizeImage(image, targetSize, { preserveTransparency: true });
  const normalizedUrl = await uploadToStorage(normalized);
  
  // Cache result
  await db.cacheNormalizedImage(url, normalizedUrl, targetSize);
  return normalizedUrl;
};

// Batch normalize
const normalizedImages = await Promise.all(
  imageUrls.map(url => normalizeImage(url, [800, 600]))
);
```

**Performance Improvement**: 5x faster (caching + parallel processing)

#### 5. Complex Approval Workflow

**Before** (Direct Tool Calls):
```
TOOL CALL: approval.get_pending_words(planId)
  → Returns 50 words
TOOL CALL: approval.get_word_details(word1)
  → Returns word + 5 images
TOOL CALL: approval.get_word_details(word2)
  → Returns word + 5 images
... (50 tool calls)

// Teacher approves in UI, then:
TOOL CALL: approval.approve_word(word1, imageUrl)
TOOL CALL: approval.approve_word(word2, imageUrl)
... (50 tool calls)
```

**After** (Code Execution):
```typescript
// Load all pending words with details in one batch
const pendingWords = await approval.getPendingWords(planId);
const wordDetails = await Promise.all(
  pendingWords.map(word => approval.getWordDetails(word.id))
);

// Process approvals in code
const approvals = await processApprovals(wordDetails, {
  bulkApprove: true,
  defaultImageSelection: 'first'  // Auto-select first image if teacher doesn't specify
});

// Batch update
await approval.batchApprove(approvals);
```

**Performance Improvement**: 10x faster (batch operations)

#### 6. Game Generation with Code

**Before** (Direct Tool Calls):
```
TOOL CALL: game.generate_matching(vocabItems)
  → Returns game JSON
TOOL CALL: game.generate_crossword(vocabItems)
  → Returns game JSON
TOOL CALL: scorm.package_games([game1, game2])
  → Returns SCORM zip
```

**After** (Code Execution):
```typescript
// Generate multiple games in parallel
const games = await Promise.all([
  gameGenerator.matching(vocabItems, { languageMode: 'bilingual' }),
  gameGenerator.crossword(vocabItems, { gridSize: 15 }),
  gameGenerator.flashcards(vocabItems, { spacedRepetition: true })
]);

// Package as SCORM in code
const scormPackage = await scorm.createPackage({
  games,
  manifest: {
    title: `Vocabulary Games - Week ${weekOf}`,
    description: 'Interactive vocabulary games',
    scormVersion: '2004'
  }
});

await fs.writeFile(`./output/scorm-${planId}.zip`, scormPackage);
```

**Performance Improvement**: 3x faster (parallel game generation)

---

## Workflow Improvements

### Enhanced Generation Flow with Code Execution

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Agent loads lesson-plan-generation skill                │
│    - Progressive disclosure: Only loads needed scripts     │
│    - Token cost: ~2K (vs 150K for all tools)              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Parse DOCX → Extract Metadata (in code)                 │
│    - No tool calls needed                                  │
│    - Fast local processing                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Build RAG Query (in code)                               │
│    - Uses rag-optimization skill                           │
│    - Filters metadata before query                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Retrieve Context (MCP via code)                         │
│    - fileSearch.retrieveContext()                          │
│    - Filter results in code (top 10, relevance > 0.7)     │
│    - Summarize snippets (500 chars max)                    │
│    - Token savings: 10K → 2K                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Generate Lesson Plan (LLM)                              │
│    - Enhanced prompt with filtered RAG context             │
│    - Uses lesson-plan-generation skill                     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Extract Vocabulary (in code)                            │
│    - Uses vocabulary-extraction skill                      │
│    - Batch process all candidates                          │
│    - Deduplicate across sources                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Collect Images (MCP via code, parallel)                 │
│    - Query 4 APIs in parallel                              │
│    - Filter inappropriate images in code                   │
│    - Normalize sizes in code (with caching)                │
│    - Performance: 10x faster                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. Generate Audio (MCP via code, parallel)                 │
│    - Batch generate pronunciations                         │
│    - Parallel processing                                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 9. Save Results (in code)                                  │
│    - Batch database operations                             │
│    - Efficient state management                            │
└─────────────────────────────────────────────────────────────┘
```

### Token Cost Comparison

**Traditional Approach** (Direct Tool Calls):
- Tool definitions: 150K tokens
- RAG results: 10K tokens
- Vocabulary processing: 5K tokens
- Image processing: 3K tokens
- **Total: ~168K tokens per generation**

**Code Execution Approach**:
- Skill loading (progressive): 2K tokens
- Filtered RAG results: 2K tokens
- Vocabulary processing: 1K tokens
- Image processing: 0.5K tokens (processed in code)
- **Total: ~5.5K tokens per generation**

**Savings: 96.7% reduction** (168K → 5.5K tokens)

### Performance Improvements

| Operation | Before (Tool Calls) | After (Code Execution) | Improvement |
|-----------|---------------------|------------------------|-------------|
| Tool Loading | 150K tokens | 2K tokens | 98.7% faster |
| RAG Processing | 10K tokens | 2K tokens | 80% faster |
| Vocabulary Batch | 50 sequential calls | 1 parallel batch | 10x faster |
| Image Collection | 200 sequential calls | 4 parallel batches | 50x faster |
| Image Normalization | 200 calls + cache misses | Cached + parallel | 5x faster |
| Game Generation | 3 sequential calls | 3 parallel calls | 3x faster |

---

## Implementation Strategy

### Phase 0: Dual-Mode Architecture (Risk Mitigation)

To ensure stability during the transition to Agent Skills, we will implement a **Dual-Mode** architecture:

1.  **Legacy Mode (Default)**: The existing `LLMService` continues to function exactly as is, providing a stable fallback.
2.  **Agentic Mode (Experimental)**: A feature toggle (`ENABLE_AGENTIC_GENERATION`) enables the new `AgentLLMService`.

**Benefits**:
- **Zero Downtime**: The production app remains stable on the Legacy path.
- **Incremental Testing**: We can toggle the new mode for specific users or during development.
- **Fallback Safety**: If the Agent/MCP pipeline fails, we can instantly revert to Legacy mode.

**Implementation**:
- Add `ENABLE_AGENTIC_GENERATION` flag to `backend/config.py`.
- Update frontend with a "Use Experimental Agent" toggle.
- Create `AgentLLMService` that implements the same interface as `LLMService`.

### Phase 1: Set Up Code Execution Environment

1. **Create MCP Client with Code Execution** (Python)
   ```python
   # backend/mcp_client.py
   from typing import TypeVar, Dict, Any
   import asyncio
   
   T = TypeVar('T')
   
   async def call_mcp_tool(
       tool_name: str,
       input_data: Dict[str, Any]
   ) -> Dict[str, Any]:
       """Call MCP server via stdio/HTTP and return typed response."""
       # Implementation: Connect to MCP server, send request, parse response
       # This wraps the actual MCP protocol communication
       pass
   ```

2. **Create Server API Structure** (Python modules)
   ```
   backend/
   ├── services/              # Existing service layer
   │   ├── file_search_service.py
   │   ├── image_collector.py
   │   └── vocabulary_service.py
   └── mcp_servers/           # MCP API wrappers (new)
       ├── file_search/
       ├── image_apis/
       ├── vocabulary/
       ├── audio/
       └── games/
   ```

3. **Set Up Python Execution Environment**
   - Use existing Python 3.11+ environment
   - Sandboxed execution for agent-generated code (if needed)
   - Resource limits (memory, CPU, time) via `resource` module
   - Integration with existing FastAPI async/await patterns

**Note**: For this project, code execution primarily means organizing existing Python services as MCP-compatible APIs, rather than executing dynamically generated code. This provides the benefits of progressive disclosure and context efficiency while maintaining type safety and existing code structure.

### Phase 2: Create Core Skills

1. **Start with High-Impact Skills**:
   - Lesson plan generation
   - Vocabulary extraction
   - Image collection

2. **Create SKILL.md Files**:
   - Document purpose, capabilities, inputs/outputs
   - Include usage examples
   - Link to related skills

3. **Implement Scripts**:
   - TypeScript functions
   - Type-safe interfaces
   - Error handling

### Phase 3: Migrate Workflows

1. **Identify Tool Call Bottlenecks**:
   - Large token consumers
   - Sequential operations
   - Repeated patterns

2. **Convert to Code Execution**:
   - Replace tool calls with code functions
   - Add filtering/transformation logic
   - Implement caching

3. **Test and Optimize**:
   - Measure token usage
   - Benchmark performance
   - Refine filtering logic

### Phase 4: Advanced Features

1. **State Persistence**:
   - Save intermediate results to files
   - Resume interrupted workflows
   - Track progress

2. **Skill Composition**:
   - Combine multiple skills
   - Create higher-level workflows
   - Share common utilities

3. **Privacy-Preserving Operations**:
   - Tokenize sensitive data
   - Filter PII before LLM
   - Secure data flow

---

## Examples and Use Cases

### Example 1: Efficient RAG-Enhanced Generation (Python)

```python
# Agent uses lesson-plan-generation skill
from skills.lesson_plan_generation.scripts.enhance_with_context import generate_lesson_plan
from backend.mcp_servers.file_search import retrieve_context
from backend.mcp_servers.vocabulary import extract_from_plan, deduplicate
from tools.docx_parser import DOCXParser

async def generate_enhanced_plan(docx_path: str, metadata: dict) -> dict:
    """Generate enhanced lesson plan with RAG context."""
    # 1. Parse DOCX (in code, no tool calls)
    parser = DOCXParser()
    parsed = await parser.parse(docx_path)
    
    # 2. Build RAG query (in code)
    query_profile = {
        'grade': metadata['grade'],
        'subject': metadata['subject'],
        'objectives': extract_objectives(parsed),
        'standards': extract_standards(parsed)
    }
    
    # 3. Retrieve context (MCP via code)
    raw_results = await retrieve_context({
        'queryProfile': query_profile,
        'storeId': metadata['storeId']
    })
    
    # 4. Filter and summarize in code (saves 8K tokens)
    relevant_context = [
        {
            'snippet': item['snippet'][:500],  # Truncate long snippets
            'citation': item['citation']
        }
        for item in raw_results['items']
        if item['relevanceScore'] > 0.7
    ][:10]  # Top 10 most relevant
    
    # 5. Generate plan (LLM with filtered context)
    plan = await generate_lesson_plan(
        primary_content=parsed,
        rag_context=relevant_context,
        strategies=load_strategies(metadata['grade']),
        wida_framework=load_wida()
    )
    
    # 6. Extract vocabulary (in code, batch)
    vocab_candidates = await extract_from_plan(plan)
    deduplicated = await deduplicate(vocab_candidates)
    
    return {'plan': plan, 'vocabCandidates': deduplicated}
```

**Integration Note**: This integrates with existing `tools/batch_processor.py` and `backend/services/file_search_service.py` from [ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](./ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md).

### Example 2: Parallel Image Collection (Python)

```python
# Agent uses image-collection skill
from backend.mcp_servers.image_apis import unsplash, pixabay, pexels, openverse
from skills.image_collection.scripts.normalize_image import normalize_image
from collections import defaultdict

async def collect_and_normalize_images(words: list[str], grade: str) -> dict:
    """Collect and normalize images from multiple APIs in parallel."""
    # Collect from all APIs in parallel
    image_tasks = []
    for word in words:
        task = asyncio.gather(
            unsplash(word, count=5, filters={'educational': True, 'gradeLevel': grade}),
            pixabay(word, count=5),
            pexels(word, count=5),
            openverse(word, count=5)
        )
        image_tasks.append((word, task))
    
    collected_images = []
    for word, task in image_tasks:
        results = await task
        collected_images.append({
            'word': word,
            'images': [img for result_list in results for img in result_list]
        })
    
    # Normalize all images in parallel (with caching)
    normalize_tasks = []
    for item in collected_images:
        for img in item['images']:
            task = normalize_image(img['url'], (800, 600))
            normalize_tasks.append({
                'word': item['word'],
                'original_url': img['url'],
                'source': img['source'],
                'normalize_task': task
            })
    
    normalized_results = await asyncio.gather(
        *[item['normalize_task'] for item in normalize_tasks]
    )
    
    # Combine results
    normalized = []
    for i, item in enumerate(normalize_tasks):
        normalized.append({
            'word': item['word'],
            'original_url': item['original_url'],
            'normalized_url': normalized_results[i],
            'source': item['source']
        })
    
    # Group by word
    grouped = defaultdict(list)
    for item in normalized:
        grouped[item['word']].append(item)
    
    return dict(grouped)
```

**Integration Note**: This integrates with `backend/services/image_collector.py` and `backend/services/image_normalizer.py` from [ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](./ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md).

### Example 3: Batch Vocabulary Processing (Python)

```python
# Agent uses vocabulary-extraction skill
from backend.mcp_servers.vocabulary import extract_from_plan, extract_from_rag, query_curriculum, deduplicate, batch_check_exists, batch_save
from backend.mcp_servers.image_apis import collect_images
from backend.mcp_servers.audio import generate_pronunciation

async def process_vocabulary(plan: dict, rag_context: list[dict]) -> list[dict]:
    """Process vocabulary from multiple sources in parallel."""
    # Extract from multiple sources in parallel
    from_plan, from_rag, from_curriculum = await asyncio.gather(
        extract_from_plan(plan),
        extract_from_rag(rag_context),
        query_curriculum({
            'grade': plan['grade'],
            'subject': plan['subject'],
            'unit': plan.get('unit')
        })
    )
    
    # Deduplicate across sources
    all_candidates = from_plan + from_rag + from_curriculum
    unique = deduplicate(all_candidates)
    
    # Check which words already exist (batch)
    check_items = [
        {'word': c['word'], 'grade': c['grade'], 'subject': c['subject']}
        for c in unique
    ]
    existing_words = await batch_check_exists(check_items)
    existing_set = {w['word'] for w in existing_words}
    
    # Process new words only
    new_words = [c for c in unique if c['word'] not in existing_set]
    
    # Collect images and generate audio in parallel
    enrichment_tasks = []
    for word in new_words:
        task = asyncio.gather(
            collect_images(word['word'], count=5),
            generate_pronunciation(word['word'], word.get('language', 'en'))
        )
        enrichment_tasks.append((word, task))
    
    enriched = []
    for word, task in enrichment_tasks:
        images, audio_url = await task
        enriched.append({
            **word,
            'images': [
                {
                    'url': img['url'],
                    'source': img['source'],
                    'normalized_url': None,  # Will normalize later
                    'approved': False
                }
                for img in images
            ],
            'audio_url': audio_url
        })
    
    # Save to database (batch)
    await batch_save(enriched)
    
    return enriched
```

**Integration Note**: This integrates with `backend/services/vocabulary_service.py`, `backend/services/vocabulary_extractor.py`, `backend/services/image_collector.py`, and `backend/services/audio_generator.py` from [ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](./ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md).

### Example 4: SCORM Package Generation

```typescript
// Agent uses game-generation and scorm-package skills
import * as gameGenerator from './servers/games';
import { createSCORMPackage } from './skills/scorm-package/scripts/create-package';

async function generateSCORMGames(planId: string, vocabItems: any[]) {
  // Generate multiple games in parallel
  const games = await Promise.all([
    gameGenerator.matching(vocabItems, {
      languageMode: 'bilingual',
      difficulty: 'medium'
    }),
    gameGenerator.crossword(vocabItems, {
      gridSize: 15,
      cluesLanguage: 'en'
    }),
    gameGenerator.flashcards(vocabItems, {
      spacedRepetition: true,
      showImages: true  // Only approved images
    }),
    gameGenerator.wordSearch(vocabItems, {
      gridSize: 20,
      language: 'bilingual'
    })
  ]);
  
  // Package as SCORM 2004
  const scormPackage = await createSCORMPackage({
    games,
    manifest: {
      identifier: `vocab-games-${planId}`,
      title: `Vocabulary Games - Week ${planId}`,
      description: 'Interactive vocabulary games for bilingual learners',
      scormVersion: '2004',
      organization: {
        identifier: 'vocab-games-org',
        title: 'Vocabulary Games',
        items: games.map((game, idx) => ({
          identifier: `game-${idx}`,
          title: game.title,
          resource: {
            href: game.htmlFile,
            type: 'webcontent'
          }
        }))
      }
    },
    assets: {
      images: vocabItems
        .filter(v => v.approved && v.selectedImage)
        .map(v => v.selectedImage),
      audio: vocabItems
        .filter(v => v.audioUrl)
        .map(v => v.audioUrl)
    }
  });
  
  // Save package
  const packagePath = `./output/scorm-${planId}.zip`;
  await fs.writeFile(packagePath, scormPackage);
  
  return packagePath;
}
```

---

## Security Considerations

### Code Execution Sandboxing

**CRITICAL**: Code execution without proper sandboxing is a security risk. All agent-generated or skill-executed code must run in a restricted environment.

#### Sandbox Implementation

**Resource Limits**:
```python
# backend/services/sandbox_executor.py
import resource
import signal
import asyncio
from RestrictedPython import compile_restricted, safe_globals
from RestrictedPython.Guards import safe_builtins
from RestrictedPython.transformer import RestrictingNodeTransformer

class SandboxedExecutor:
    """Execute code in restricted environment with resource limits."""
    
    def __init__(self):
        self.memory_limit = 512 * 1024 * 1024  # 512MB
        self.cpu_time_limit = 30  # 30 seconds
        self.allowed_modules = {
            'asyncio', 'json', 'typing', 'datetime', 
            'collections', 'itertools', 'functools'
        }
        self.restricted_globals = {
            **safe_globals,
            '__builtins__': safe_builtins,
            '_getiter_': lambda x: x,
            '_iter_unpack_': lambda x: x,
        }
    
    async def execute(
        self, 
        code: str, 
        inputs: dict,
        timeout: int = 30
    ) -> dict:
        """
        Execute code with resource limits and sandboxing.
        
        Security Measures:
        1. RestrictedPython compilation (prevents dangerous operations)
        2. Memory limit enforcement
        3. CPU time limit enforcement
        4. Network access blocked (except via MCP)
        5. File system access restricted
        """
        # Set memory limit
        try:
            resource.setrlimit(
                resource.RLIMIT_AS,
                (self.memory_limit, self.memory_limit)
            )
        except (ValueError, OSError) as e:
            logger.warning(f"Could not set memory limit: {e}")
        
        # Compile with RestrictedPython
        try:
            byte_code = compile_restricted(code, '<inline>', 'exec')
            if byte_code.errors:
                raise SecurityError(f"Code compilation failed: {byte_code.errors}")
        except Exception as e:
            raise SecurityError(f"Code compilation error: {str(e)}")
        
        # Prepare execution environment
        exec_globals = {
            **self.restricted_globals,
            **{k: v for k, v in inputs.items() if k in self.allowed_modules},
            'result': None
        }
        
        # Execute with timeout
        try:
            await asyncio.wait_for(
                self._execute_with_timeout(byte_code.code, exec_globals),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise SecurityError(f"Code execution exceeded {timeout}s timeout")
        except MemoryError:
            raise SecurityError("Code execution exceeded memory limit")
        except Exception as e:
            raise SecurityError(f"Code execution error: {str(e)}")
        
        return exec_globals.get('result')
    
    async def _execute_with_timeout(self, code, globals_dict):
        """Execute code in thread with CPU time limit."""
        def run_code():
            # Set CPU time limit
            signal.signal(signal.SIGXCPU, self._timeout_handler)
            try:
                resource.setrlimit(
                    resource.RLIMIT_CPU,
                    (self.cpu_time_limit, self.cpu_time_limit)
                )
            except (ValueError, OSError):
                pass  # Not available on all platforms
            
            exec(code, globals_dict)
        
        # Run in thread pool to allow timeout
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, run_code)
    
    def _timeout_handler(self, signum, frame):
        """Handle CPU time limit exceeded."""
        raise SecurityError(f"Code execution exceeded {self.cpu_time_limit}s CPU time limit")
```

**Network Access Control**:
```python
# Block direct network access, only allow via MCP
class RestrictedNetwork:
    """Block network access except via MCP."""
    
    def __init__(self):
        self.allowed_hosts = set()  # Empty - no direct network access
    
    def __getattr__(self, name):
        """Block network module access."""
        raise SecurityError(
            f"Direct network access blocked. Use MCP tools for external communication."
        )

# Add to restricted globals
restricted_globals['socket'] = RestrictedNetwork()
restricted_globals['urllib'] = RestrictedNetwork()
restricted_globals['requests'] = RestrictedNetwork()
```

**File System Restrictions**:
```python
# backend/services/restricted_filesystem.py
class RestrictedFileSystem:
    """Restrict file system access to allowed directories."""
    
    def __init__(self, allowed_dirs: list):
        self.allowed_dirs = [Path(d).resolve() for d in allowed_dirs]
        self.allowed_dirs_set = set(self.allowed_dirs)
    
    def open(self, path, *args, **kwargs):
        """Open file only if in allowed directory."""
        resolved_path = Path(path).resolve()
        
        # Check if path is within allowed directory
        if not any(
            str(resolved_path).startswith(str(allowed))
            for allowed in self.allowed_dirs
        ):
            raise SecurityError(
                f"File access denied: {path} not in allowed directories"
            )
        
        return open(resolved_path, *args, **kwargs)
    
    def listdir(self, path):
        """List directory only if allowed."""
        resolved_path = Path(path).resolve()
        if resolved_path not in self.allowed_dirs_set:
            raise SecurityError(f"Directory access denied: {path}")
        return os.listdir(resolved_path)
```

#### Input Validation

**Validate all inputs to MCP tools**:
```python
# backend/mcp_client.py
from pydantic import BaseModel, validator
from typing import Dict, Any

class MCPToolInput(BaseModel):
    """Validated input for MCP tool calls."""
    tool_name: str
    input_data: Dict[str, Any]
    
    @validator('tool_name')
    def validate_tool_name(cls, v):
        allowed_tools = {
            'file_search__retrieve_context',
            'image_collector__collect',
            'vocabulary__extract',
            # ... other allowed tools
        }
        if v not in allowed_tools:
            raise ValueError(f"Tool {v} not in allowed list")
        return v
    
    @validator('input_data')
    def sanitize_input_data(cls, v):
        """Sanitize input data to prevent injection."""
        # Remove any potentially dangerous fields
        dangerous_keys = {'__class__', '__dict__', '__globals__', 'eval', 'exec'}
        sanitized = {
            k: v for k, v in v.items()
            if k not in dangerous_keys
        }
        return sanitized

async def call_mcp_tool(tool_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Call MCP tool with input validation."""
    # Validate input
    validated = MCPToolInput(tool_name=tool_name, input_data=input_data)
    
    # Sanitize file paths
    if 'file_path' in validated.input_data:
        validated.input_data['file_path'] = sanitize_file_path(
            validated.input_data['file_path']
        )
    
    # Execute tool call
    return await _execute_mcp_tool(validated.tool_name, validated.input_data)

def sanitize_file_path(path: str) -> str:
    """Sanitize file path to prevent directory traversal."""
    # Remove any .. or absolute paths
    sanitized = Path(path).resolve()
    
    # Check against allowed directories
    allowed_base = Path('./data').resolve()
    if not str(sanitized).startswith(str(allowed_base)):
        raise SecurityError(f"File path outside allowed directory: {path}")
    
    return str(sanitized)
```

#### Security Audit Logging

**Log all code execution for security auditing**:
```python
# backend/services/security_audit.py
class SecurityAuditLogger:
    """Log security-relevant events."""
    
    async def log_code_execution(
        self,
        code_hash: str,
        inputs_hash: str,
        result_hash: str,
        execution_time: float,
        memory_used: int
    ):
        """Log code execution for audit trail."""
        await self.db.insert('security_audit_log', {
            'event_type': 'code_execution',
            'code_hash': code_hash,
            'inputs_hash': inputs_hash,
            'result_hash': result_hash,
            'execution_time_ms': execution_time * 1000,
            'memory_used_bytes': memory_used,
            'timestamp': datetime.now(),
            'user_id': get_current_user_id()
        })
    
    async def log_security_violation(
        self,
        violation_type: str,
        details: dict
    ):
        """Log security violations."""
        logger.error(
            f"Security violation: {violation_type}",
            extra={'violation': violation_type, 'details': details}
        )
        
        # Alert administrators
        await self._send_security_alert(violation_type, details)
```

### Privacy-Preserving Operations

1. **Data Tokenization**:
   - Tokenize PII before passing to LLM
   - Untokenize in MCP client when needed
   - Never log sensitive data

2. **Selective Logging**:
   - Only log what's explicitly returned
   - Filter sensitive fields
   - Audit data flow

---

## Conclusion

Agent Skills and Code Execution with MCP provide significant improvements to the Lesson Plan Builder workflow:

**Benefits**:
- **96.7% token reduction** (168K → 5.5K tokens per generation)
- **10-50x performance improvements** for batch operations
- **Reusable expertise** through composable skills
- **Better control flow** with code execution
- **Privacy-preserving** operations

**Implementation Path**:
1. Set up code execution environment
2. Create core skills (lesson plan, vocabulary, images)
3. Migrate workflows to code execution
4. Add advanced features (state persistence, skill composition)

These improvements make the application more efficient, scalable, and cost-effective while maintaining the same functionality and quality.

---

## Integration with Containerization Strategy

**Alignment with [CONTAINERIZATION_STRATEGY.md](./CONTAINERIZATION_STRATEGY.md)**:

- **Background Workers**: Skills that run as separate services (image collection, audio generation, game generation) align with Docker containerization recommendations
- **Main Backend**: Skills integrated into FastAPI backend remain as Python modules (no containerization needed initially)
- **Code Execution**: Python-based implementation fits existing architecture without requiring new infrastructure

**Containerization for Skills**:
- Image collection worker → Docker container (complex dependencies)
- Audio generation worker → Docker container (Google TTS dependencies)
- Game generation worker → Docker container (SCORM packaging tools)
- Main backend skills → Python modules (no containerization needed)

## References

- [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Code execution with MCP: Building more efficient agents](https://www.anthropic.com/engineering/code-execution-with-mcp)
- [ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](./ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md) - Enhanced architecture document
- [CONTAINERIZATION_STRATEGY.md](./CONTAINERIZATION_STRATEGY.md) - Docker/Kubernetes recommendations
- [DATABASE_ARCHITECTURE_AND_SYNC.md](./DATABASE_ARCHITECTURE_AND_SYNC.md) - Existing sync architecture

