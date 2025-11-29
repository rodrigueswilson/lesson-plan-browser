# MCP Server Evaluation for Lesson Plan Builder

## Executive Summary

**Recommendation: YES, implementing an MCP server would provide significant benefits**, particularly for context efficiency, progressive disclosure of strategies, and improved tooling. However, the implementation should be phased and complement (not replace) the existing prompt-based system initially.

## Current State Analysis

### Context Usage Patterns

1. **Large Prompt Template**: `prompt_v4.md` (~650 lines) is loaded entirely into every LLM call
2. **Schema Examples**: Full JSON schema examples are dynamically built and included in prompts (even with structured outputs)
3. **Strategy Files**: The prompt instructs the LLM to "load" JSON files, but these files are **NOT actually loaded into context** - this is a critical inefficiency
4. **Multiple Data Sources**: 
   - 33 strategies across 6 category files
   - WIDA framework files
   - Co-teaching models and phase patterns
   - Portuguese misconceptions database
   - **Additional sources needed** (not yet integrated):
     - Subject-specific curriculum documents (Math, ELA, Science, Social Studies standards)
     - Teacher assessment/evaluation framework: "The Framework for Effective Teaching"
     - District-specific instructional guidelines
     - State standards and benchmarks
     - Scope and sequence documents
     - Unit planning templates and rubrics
   - All referenced but not accessible to the LLM

### Token Consumption Estimate

Based on `llm_service.py` analysis:
- **Prompt template**: ~15,000-20,000 tokens (prompt_v4.md + schema examples)
- **Primary content**: Variable (teacher lesson plans)
- **Total per call**: ~20,000-30,000 input tokens typically
- **With all strategy files loaded**: Could add 50,000+ tokens if fully loaded

## Benefits of MCP Implementation

### 1. Progressive Disclosure (High Impact)

**Current Problem**: The prompt tells the LLM to "load" strategy files, but they're not actually accessible. The LLM must work from memory/instructions alone.

**MCP Solution**: 
- Present strategies as code APIs: `strategies.getByCategory()`, `strategies.search()`, `strategies.getById()`
- LLM can query only needed strategies based on lesson context
- Load 2-4 category files (~15-25 strategies) instead of all 33 upfront
- **Estimated savings**: 60-70% reduction in strategy-related tokens

**Implementation**:
```typescript
// MCP tools exposed as code APIs
import * as strategies from './mcp/strategies';
import * as wida from './mcp/wida';
import * as coTeaching from './mcp/co-teaching';

// LLM writes code to query only what's needed
const relevantStrategies = await strategies.search({
  grade: '6',
  subject: 'math',
  proficiencyLevels: [3, 4],
  primarySkill: 'reading'
});
```

### 2. Actual File Access (Critical Fix)

**Current Problem**: The prompt says "load the strategy index and category files" but the LLM cannot actually read them.

**MCP Solution**:
- MCP server provides actual file access via tools
- LLM can read JSON files on-demand
- Enables proper strategy selection based on actual data
- **Impact**: Fixes a fundamental limitation in current system

### 3. Context-Efficient Tool Results (High Impact)

**Current Problem**: Large schema examples and full prompt template sent every time.

**MCP Solution**:
- With code execution, filter and transform data before returning to model
- Example: Filter strategies by grade/proficiency before sending
- Only return relevant WIDA standards for the specific grade cluster
- **Estimated savings**: 30-40% reduction in prompt size

### 4. Better Tooling (Medium Impact)

**Proposed MCP Tools**:

```typescript
// Strategy tools
strategies.search({ grade, subject, proficiencyLevels, skill })
strategies.getById(strategyId)
strategies.getByCategory(category)
strategies.getCrossReferences(strategyId)

// WIDA tools
wida.getStandards(gradeCluster, subject)
wida.getProficiencyAdaptations(level, strategyId)
wida.getKeyLanguageUses(lessonType)

// Co-teaching tools
coTeaching.selectModel(proficiencyDistribution, constraints)
coTeaching.getPhasePattern(modelName, duration)
coTeaching.getPortugueseMisconceptions(keywords)

// Lesson plan tools
lessonPlan.validateSchema(json)
lessonPlan.mergeWeeklyPlans(plans)
lessonPlan.extractMetadata(docx)
```

### 5. Privacy-Preserving Operations (Low-Medium Impact)

**Benefit**: Intermediate results (strategy selections, filtered data) stay in execution environment
- Only final lesson plan JSON flows through model context
- Could tokenize sensitive student data if needed in future

### 6. State Persistence and Skills (Medium Impact)

**Benefit**: Agents can persist working code and build reusable functions
- Save successful strategy selection patterns
- Build library of grade-specific adaptations
- Track which strategies work best for different subjects

### 7. RAG Integration for Expanded Data Sources (High Impact - NEW)

**Current Limitation**: System only references internal strategy files. Cannot access curriculum documents, assessment frameworks, or other external educational resources.

**RAG Solution**: Integration with Retrieval-Augmented Generation enables:
- **Curriculum Alignment**: Access subject-specific curriculum documents, standards, and scope & sequence
- **Assessment Framework Integration**: Reference "The Framework for Effective Teaching" evaluation rubrics to ensure lesson plans meet professional standards
- **District Compliance**: Query district-specific guidelines and requirements
- **Standards Mapping**: Automatically align lessons with state standards and benchmarks
- **Dynamic Context**: Only retrieve relevant curriculum sections based on grade/subject/topic

**Impact**: Transforms lesson plans from strategy-focused to standards-aligned and curriculum-grounded

## Google Gemini File Search Tool Integration

### Overview

Google's File Search tool in the Gemini API provides **automated RAG capabilities** that complement MCP perfectly. It handles the RAG pipeline automatically:
- **Retrieval**: Automatically processes files, creates embeddings, stores them, and searches when prompted
- **Augmentation**: Relevant information from files is automatically added to the model's prompt
- **Generation**: Gemini uses the augmented prompt to generate grounded responses

### Key Features

1. **Automated RAG Pipeline**: No manual embedding management or vector database setup required
2. **Multiple File Formats**: Supports PDF, DOCX, TXT, JSON, and more
3. **Built-in Citations**: Responses include citations specifying which document sections were used
4. **Cost-Effective**: 
   - Initial indexing: $0.15 per 1 million tokens
   - Storage and query-time embeddings: Free
5. **Vector Search**: Semantic search capabilities - finds relevant content even if wording differs

### Integration with MCP

**Synergy**: MCP + Gemini File Search creates a powerful hybrid architecture:

```
┌─────────────────────────────────────────────────────────┐
│                    Lesson Plan Generation                │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                     │
   ┌────▼────┐                         ┌─────▼─────┐
   │   MCP   │                         │  Gemini  │
   │ Server  │                         │  File   │
   │         │                         │  Search  │
   └────┬────┘                         └─────┬─────┘
        │                                     │
   ┌────▼────────────────────────────────────▼────┐
   │  Structured Data Sources                     │
   │  • Strategy JSON files                        │
   │  • WIDA framework                            │
   │  • Co-teaching models                        │
   │  • Portuguese misconceptions                 │
   └──────────────────────────────────────────────┘
        │
   ┌────▼──────────────────────────────────────────┐
   │  Unstructured Document Sources (via File      │
   │  Search)                                      │
   │  • Curriculum documents (PDF/DOCX)           │
   │  • Assessment frameworks                      │
   │  • District guidelines                        │
   │  • State standards                           │
   │  • Scope & sequence documents                │
   └──────────────────────────────────────────────┘
```

### Benefits of Combined Approach

1. **Best of Both Worlds**:
   - **MCP**: Precise, structured data access (strategies, WIDA standards)
   - **File Search**: Flexible, semantic search across unstructured documents (curriculum, assessments)

2. **Progressive Disclosure**:
   - MCP loads only needed strategy categories (~15-25 strategies)
   - File Search retrieves only relevant curriculum sections
   - **Combined token savings**: 50-70% reduction vs. loading everything

3. **Quality Improvements**:
   - **Standards Alignment**: File Search ensures lessons align with curriculum documents
   - **Assessment Compliance**: References teacher evaluation frameworks automatically
   - **District Compliance**: Checks against district-specific requirements
   - **Verifiable Sources**: Built-in citations for all curriculum references

4. **Operational Efficiency**:
   - File Search handles document processing automatically
   - No need to maintain separate vector database
   - MCP provides structured query interface
   - Code execution enables filtering before context injection

### Implementation Strategy

**Hybrid Architecture**:

```typescript
// MCP tools for structured data
import * as strategies from './mcp/strategies';
import * as wida from './mcp/wida';

// Gemini File Search for unstructured documents
// (handled via Gemini API, not code execution)

// LLM workflow:
// 1. Query MCP for relevant strategies (structured)
const strategies = await strategies.search({ grade, subject });

// 2. Use Gemini File Search to retrieve curriculum context (unstructured)
// File Search automatically augments prompt with relevant curriculum sections

// 3. Generate lesson plan with both structured strategies and curriculum-aligned content
```

### Cost Analysis

**Current System**:
- ~20,000-30,000 input tokens per call
- No curriculum/assessment document access

**With MCP + File Search**:
- **MCP**: ~8,000-12,000 tokens (structured data, filtered)
- **File Search**: ~5,000-10,000 tokens (retrieved curriculum sections)
- **Total**: ~13,000-22,000 tokens
- **Savings**: 20-35% reduction + access to much larger knowledge base

**File Search Costs**:
- Initial indexing: $0.15 per 1M tokens (one-time per document)
- Query-time: Free (storage and embeddings included)
- **Example**: Index 100 curriculum documents (~10M tokens) = $1.50 one-time cost

### Recommended Data Sources for File Search

1. **Curriculum Documents**:
   - Subject-specific curriculum guides (Math, ELA, Science, Social Studies)
   - Grade-level scope and sequence documents
   - Unit planning templates

2. **Assessment Frameworks**:
   - "The Framework for Effective Teaching" evaluation rubrics
   - Lesson plan quality rubrics
   - Instructional effectiveness standards

3. **Standards Documents**:
   - State standards (Common Core, state-specific)
   - WIDA ELD standards (supplement MCP structured data)
   - Subject-specific standards (NCTM, NCTE, NGSS)

4. **District Resources**:
   - District curriculum maps
   - Instructional guidelines
   - Best practices documents

5. **Professional Development Materials**:
   - Co-teaching best practices
   - Bilingual education research summaries
   - Strategy implementation guides

## Slot-Based Processing Architecture

### Overview

The lesson plan system processes **slots** - each slot represents one (subject, grade) combination that repeats across the week:
- **Typical structure**: 5 slots per week (plus occasional Health slot)
- **Each slot**: Generates 5 days of lessons (except Science=4 days, Health=1 day)
- **Example slots**: 2nd Grade Math, 3rd Grade ELA, 2nd Grade Science, etc.

### Slot-Based Workflow

**Critical**: Each slot is processed **separately** to avoid context confusion between different grades/subjects:

```
For each slot (subject/grade combination):
  1. Extract slot metadata → grade, subject, available_days
  2. MCP queries → Filtered by THIS slot's grade/subject
     - Load relevant strategies for this specific grade/subject
     - Load WIDA standards for this grade cluster/subject
     - Load co-teaching models appropriate for this context
  3. File Search queries → Filtered by THIS slot's grade/subject
     - Retrieve curriculum documents for this specific grade/subject
     - Get "The Framework for Effective Teaching" requirements for this subject
     - Get standards alignment for this grade/subject
  4. Generate lesson plan → All days for THIS slot (5 days, or 4/1 as applicable)
  5. Store slot result

After all slots processed:
  6. Merge all slot results into final weekly plan JSON
```

### Benefits of Slot-Based Processing

1. **Context Isolation**: No confusion between 2nd grade Math and 3rd grade ELA
2. **Accurate Alignment**: Each slot gets curriculum/standards specific to its grade/subject
3. **Efficient Queries**: MCP/File Search queries are scoped to exactly what's needed
4. **Parallel Processing**: Slots can be processed concurrently for faster generation
5. **Aligns with Existing Architecture**: Matches current `batch_processor.py` slot processing

### Example: Multi-Grade/Multi-Subject Week

```
Slot 1: 2nd Grade Math
  → MCP(Math, Grade 2) + File Search(Math, Grade 2)
  → Generates 5 days of Math lessons for 2nd grade

Slot 2: 3rd Grade ELA  
  → MCP(ELA, Grade 3) + File Search(ELA, Grade 3)
  → Generates 5 days of ELA lessons for 3rd grade

Slot 3: 2nd Grade Science
  → MCP(Science, Grade 2) + File Search(Science, Grade 2)
  → Generates 4 days of Science lessons for 2nd grade

Slot 4: 3rd Grade Math
  → MCP(Math, Grade 3) + File Search(Math, Grade 3)
  → Generates 5 days of Math lessons for 3rd grade

Slot 5: 2nd Grade Health
  → MCP(Health, Grade 2) + File Search(Health, Grade 2)
  → Generates 1 day of Health lesson for 2nd grade

Final: Merge all 5 slots into weekly plan JSON
```

### Token Efficiency Per Slot

- **MCP queries**: ~2,000-3,000 tokens (filtered strategies, WIDA standards)
- **File Search**: ~3,000-5,000 tokens (retrieved curriculum sections)
- **Prompt + generation**: ~8,000-12,000 tokens
- **Total per slot**: ~13,000-20,000 tokens
- **5 slots**: ~65,000-100,000 tokens total (vs. ~100,000-150,000 if all mixed together)

## Implementation Approach

### Phase 1: Core MCP Server (MVP)

**Goal**: Fix the "file access" problem and enable progressive disclosure

**Components**:
1. **MCP Server** (`mcp_server/lesson_plan_mcp/`)
   - Strategy file access tools (filtered by grade/subject)
   - WIDA framework tools (filtered by grade cluster/subject)
   - Co-teaching model tools
   - Basic search/filter capabilities

2. **Code Execution Environment**
   - TypeScript/JavaScript runtime
   - File system access to `strategies_pack_v2/`, `wida/`, `co_teaching/`
   - Sandboxed execution

3. **Slot-Based Integration**
   - Update `batch_processor.py` to use MCP per slot
   - Each slot gets isolated MCP queries filtered by its grade/subject
   - Update `llm_service.py` to use MCP when available
   - Fallback to current prompt-based approach
   - A/B testing to measure improvements

**Estimated Effort**: 2-3 weeks

### Phase 2: Enhanced Tooling

**Goal**: Add advanced querying and filtering

**Components**:
- Advanced strategy search with multiple filters
- WIDA standard mapping tools
- Co-teaching model selection automation
- Schema validation tools

**Estimated Effort**: 1-2 weeks

### Phase 3: Code Execution Optimization

**Goal**: Leverage code execution for complex operations

**Components**:
- Strategy selection algorithm in code (not prompt)
- Multi-day plan merging/validation
- Template generation from code
- Performance optimization

**Estimated Effort**: 2-3 weeks

### Phase 4: Gemini File Search Integration (NEW)

**Goal**: Add RAG capabilities for curriculum and assessment document access

**Components**:
1. **File Search Setup**:
   - Create File Search stores for different document types
   - Index curriculum documents (PDF/DOCX) organized by subject/grade
   - Index "The Framework for Effective Teaching" assessment rubrics
   - Index district/state standards

2. **Slot-Based MCP-Gemini Integration**:
   - Process each slot separately with isolated context
   - MCP tools for structured data (strategies, WIDA) - filtered per slot
   - Gemini File Search API calls for unstructured documents - filtered per slot
   - Hybrid prompt construction combining both sources per slot

3. **Citation and Verification**:
   - Extract citations from File Search responses per slot
   - Include curriculum references in each slot's lesson plan
   - Verify standards alignment per slot

4. **Quality Assurance**:
   - Validate curriculum alignment per slot
   - Check "The Framework for Effective Teaching" compliance per slot
   - Ensure district guideline adherence per slot
   - Merge slot results into final weekly plan

**Estimated Effort**: 2-3 weeks

**Benefits**:
- Access to curriculum documents without manual processing
- Automatic standards alignment per slot (no context confusion)
- Built-in citations for verification
- Significant quality improvement in lesson plans
- Proper isolation between different grades/subjects

## Considerations and Challenges

### 1. Complexity vs. Benefit Trade-off

**Current System**: Simple, works, production-ready
**MCP System**: More complex, requires execution environment, security considerations

**Mitigation**: 
- Implement as optional enhancement initially
- Maintain backward compatibility
- Gradual migration path

### 2. Security Requirements

**Needs**:
- Sandboxed code execution
- Resource limits (memory, CPU, time)
- File system access controls
- API rate limiting

**Mitigation**: Use established MCP server frameworks with built-in security

### 3. Development Overhead

**Needs**:
- MCP server development
- Code execution environment setup
- Testing infrastructure
- Documentation

**Mitigation**: Leverage existing MCP SDKs and community patterns

### 4. Token Cost Analysis

**Current**: ~20,000-30,000 input tokens per call
**With MCP (optimized)**: ~8,000-15,000 input tokens per call
**With MCP + File Search**: ~13,000-22,000 input tokens per call
**Savings**: 
- MCP alone: 30-50% reduction
- MCP + File Search: 20-35% reduction + access to much larger knowledge base

**ROI**: 
- If processing 100 plans/week: ~500,000-1,000,000 tokens saved/week (MCP)
- At $0.01/1K tokens: $5-10/week savings
- Annual: ~$260-520 savings
- **Plus**: Better quality from actual file access + curriculum alignment

**File Search Costs**:
- Initial indexing: $0.15 per 1M tokens (one-time)
- Query-time: Free (storage and embeddings included)
- **Example**: Index 100 curriculum documents (~10M tokens) = $1.50 one-time cost
- **ROI**: Minimal cost for access to entire curriculum knowledge base

## Recommended Architecture

### MCP Server Structure

```
mcp_server/
├── lesson_plan_mcp/
│   ├── __init__.py
│   ├── server.py              # MCP server implementation
│   ├── tools/
│   │   ├── strategies.py      # Strategy access tools
│   │   ├── wida.py            # WIDA framework tools
│   │   ├── co_teaching.py     # Co-teaching model tools
│   │   └── lesson_plan.py    # Lesson plan utilities
│   └── resources/
│       └── file_system.py     # File system resource access
├── code_execution/
│   ├── runtime.py              # Code execution environment
│   └── sandbox.py              # Security sandbox
└── integration/
    └── llm_service_mcp.py     # MCP-aware LLM service wrapper
```

### Code Execution API Structure

```
mcp/
├── strategies/
│   ├── index.ts               # Strategy index access
│   ├── search.ts              # Search/filter strategies
│   └── get.ts                 # Get specific strategies
├── wida/
│   ├── standards.ts           # WIDA standards access
│   └── adaptations.ts         # Proficiency adaptations
├── co_teaching/
│   ├── models.ts              # Co-teaching model selection
│   └── phases.ts              # Phase pattern access
├── curriculum/                # NEW: Curriculum access via File Search
│   ├── search.ts              # Query curriculum documents
│   ├── getStandards.ts        # Retrieve relevant standards
│   └── validateAlignment.ts   # Check curriculum alignment
└── lesson_plan/
    ├── validate.ts            # Schema validation
    └── merge.ts               # Multi-day merging
```

### Gemini File Search Integration Structure

```
file_search_stores/
├── curriculum/
│   ├── math/                  # Math curriculum documents
│   ├── ela/                   # ELA curriculum documents
│   ├── science/              # Science curriculum documents
│   └── social_studies/       # Social studies curriculum documents
├── assessment/
│   ├── framework_effective_teaching/  # "The Framework for Effective Teaching" rubrics
│   └── lesson_plan_rubrics/           # Lesson plan quality rubrics
├── standards/
│   ├── state_standards/      # State-specific standards
│   ├── common_core/          # Common Core standards
│   └── wida_eld/            # WIDA ELD standards (supplement)
└── district/
    ├── curriculum_maps/      # District curriculum maps
    ├── guidelines/           # District instructional guidelines
    └── best_practices/       # District best practices
```

## Success Metrics

### Quantitative
- **Token reduction**: Target 30-50% reduction in input tokens
- **Response quality**: Maintain or improve lesson plan quality scores
- **Processing time**: No significant increase (target: <10% overhead)
- **Cost savings**: Track API cost reduction

### Qualitative
- **Strategy selection accuracy**: Better alignment with lesson context
- **WIDA integration**: More accurate standard mapping
- **Co-teaching model selection**: Better fit to proficiency distributions
- **Curriculum alignment**: Automatic alignment with curriculum documents and standards
- **Assessment compliance**: Lessons meet "The Framework for Effective Teaching" requirements
- **District compliance**: Adherence to district-specific guidelines
- **Developer experience**: Easier to add new strategies/tools
- **Verifiability**: Built-in citations for all curriculum and assessment references

## Conclusion

**Recommendation: Proceed with Phased Implementation (MCP + Gemini File Search)**

The current system has fundamental limitations:
1. It instructs the LLM to "load" files that aren't actually accessible
2. It cannot access curriculum documents, assessment frameworks, or district guidelines
3. Lesson plans lack curriculum alignment and standards verification

**Combined Solution (MCP + File Search)**:
- **MCP**: Fixes file access problem, provides structured data access, enables progressive disclosure
- **Gemini File Search**: Adds RAG capabilities for unstructured documents (curriculum, assessments, standards)
- **Together**: Comprehensive solution with both structured and unstructured data access

**Benefits**:
- Significant token savings (20-50% depending on phase)
- Better tooling and progressive disclosure
- **Curriculum alignment**: Automatic alignment with curriculum documents
- **Assessment compliance**: Meets "The Framework for Effective Teaching" requirements
- **Standards verification**: Built-in citations and verification
- Foundation for future enhancements
- Alignment with industry best practices

**Next Steps**:
1. **Phase 1**: Prototype MCP server with strategy file access
2. **Phase 1.5**: Integrate with existing `llm_service.py` as optional enhancement
3. **Phase 2**: Measure token usage and quality improvements
4. **Phase 3**: Add Gemini File Search integration for curriculum documents
5. **Phase 4**: Expand to assessment frameworks and district guidelines
6. Iterate based on results

**Risk Level**: Low-Medium (can maintain backward compatibility, phased rollout)
**Expected ROI**: Very High (fixes current limitations + token savings + curriculum alignment + assessment compliance)

**Key Insight**: MCP and Gemini File Search are **complementary, not competing** solutions:
- **MCP**: Best for structured, queryable data (strategies, WIDA standards)
- **File Search**: Best for unstructured documents (curriculum PDFs, assessment rubrics)
- **Combined**: Comprehensive knowledge access with optimal efficiency
- **Slot-Based Processing**: Ensures clean context isolation between different grades/subjects, preventing confusion and ensuring accurate curriculum alignment

