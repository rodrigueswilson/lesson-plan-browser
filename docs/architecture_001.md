# **Bilingual Lesson Plan Transformation System Architecture**

## **System Overview**

This architecture outlines the file structure and data flow for transforming primary teacher lesson plans into WIDA-enhanced bilingual lesson plans using research-backed strategies and proficiency-responsive adaptations.

## **Core Architecture Components**

### **1. Data Layer (JSON Files)**

#### **Modular Strategy Pack (v2.0)**
- **Master Index:** `strategies_pack_v2/_index.json`
- **Purpose:** Intelligent category management and loading system for 33 bilingual strategies
- **Architecture:** Modular distribution across 6 category files
- **Key Components:**
  - Category mappings with strategy counts and descriptions
  - Intelligent selection rules based on lesson context, grade cluster, proficiency range
  - Loading algorithm for optimal LLM processing (2-4 categories, ~15-25 strategies)
  - Cross-references to WIDA framework and enhancement files

#### **Core Strategy Categories**
- **language_skills.json:** 9 core vocabulary and skill-building strategies
- **frameworks_models.json:** 7 comprehensive pedagogical frameworks
- **cross_linguistic.json:** 8 biliteracy and transfer strategies
- **assessment_scaffolding.json:** 5 evaluation and support techniques

#### **Specialized Strategy Categories**
- **social_interactive.json:** 2 collaborative learning approaches
- **cultural_identity.json:** 2 asset-based, culturally responsive strategies

#### **Enhanced Schema v1.7_enhanced**
- **Core Fields:** `strategy_id`, `strategy_name`, `core_principle`
- **WIDA Integration:** `high_level_categories` (array), `skill_weights` (quantified)
- **Implementation:** `delivery_modes`, `l1_modes`, `applicable_contexts`
- **Pedagogical Definitions:** `short_en`, `long_en`, `look_fors`, `non_examples`
- **Quality Assurance:** `research_foundation`, `cross_refs`, `evidence_tier`

#### **WIDA Framework Reference**
- **File:** `wida_framework_reference.json`
- **Purpose:** WIDA 2020 standards components and templates
- **Key Components:**
  - ELD Standards (SI, LA, MA, SC, SS)
  - Proficiency Levels 1-6 with asset-based descriptions
  - Key Language Uses (Narrate, Inform, Explain, Argue)
  - Language Dimensions (Discourse, Sentence, Word/Phrase)
  - Grade Clusters (K, 1, 2-3, 4-5, 6-8, 9-12)
  - Language objective templates and sentence frames
  - Student objective templates (by Key Language Use and by Dimension)

#### **WIDA Strategy Enhancements**
- **File:** `wida/wida_strategy_enhancements.json`
- **Purpose:** Proficiency-level adaptations for bilingual strategies
- **Key Components:**
  - Strategy-specific WIDA alignments
  - Proficiency adaptations (Levels 1-2, 3-4, 5-6)
  - Grade-cluster developmental considerations
  - Implementation scaffolds and assessment modes
  - Global defaults: WIDA language objective template; student objective templates; common pitfalls and success indicators by dimension

#### **Co-Teaching Model Selection**
- **Files:** `co_teaching/wida_model_rules.json`, `co_teaching/phase_patterns_45min.json`
- **Purpose:** WIDA-driven co-teaching model recommendation for 45-minute sessions
- **Key Components:**
  - 6 Friend & Cook co-teaching models adapted for bilingual education
  - WIDA band priorities (Levels 1-2, 3-4, 5-6, mixed range)
  - Special conditions (newcomer %, space, planning time)
  - Equity rules (avoid One Teach One Assist/Observe as primary)
  - 45-minute phase templates with teacher role specifications

#### **Linguistic Misconception Prediction (MVP)**
- **File:** `co_teaching/portuguese_misconceptions.json`
- **Purpose:** High-frequency Portuguese→English interference pattern prediction
- **Key Components:**
  - 6 high-frequency patterns (subject pronouns, adjective placement, past tense -ed, prepositions, false cognates)
  - Trigger keywords for simple pattern matching
  - Linguistic notes explaining L1→L2 interference
  - Prevention tips aligned with bilingual strategies
  - Default reminder for lessons without specific matches

### **2. Documentation Layer (Markdown Files)**

#### **Human-Readable Strategy Reference**
- **File:** `bilingual_strategies_dictionary.md`
- **Purpose:** Comprehensive educator reference for all 33 strategies
- **Content:** Detailed descriptions with skill weights, delivery modes, implementation steps
- **Audience:** Teachers, administrators, curriculum designers

#### **Transformation Prompt Engine**
- **File:** `prompt_v4.md`
- **Purpose:** AI prompt for lesson plan transformation with modular v2.0 strategy pack integration
- **Features:**
  - Two-phase strategy selection: intelligent category loading (2-4 categories) → fine-selection within loaded strategies
  - Tri-objective output: Content Objective; Student Goal (I will…); WIDA Bilingual Language Objective
  - Student Goal generation protocol (first-person, max 12 words, WIDA templates)
  - Primary-Assessment-First protocol: preserves teacher's assessment with WIDA overlay
  - Proficiency-differentiated language objectives (WIDA-aligned with level-banded supports)
  - Grade-cluster developmental considerations with `[GRADE_LEVEL_VARIABLE]` system
  - Asset-based multilingual learner approach
  - Microsoft Word-compatible markdown table output format

#### **Sample Implementation**
- **File:** `Sample_Lesson_Transformation_WIDA.md`
- **Purpose:** Concrete example of transformation output
- **Content:** Before/after lesson comparison with WIDA enhancements

## **Data Flow Architecture**

```
INPUT: Primary Teacher Lesson Plan (DOCX)
    ↓
PROCESSING ENGINE: prompt_v4.md
    ↓
PHASE 1: SMART CATEGORY LOADING
    ├── strategies_pack_v2/_index.json (master registry)
    ├── Lesson context analysis (subject, grade, objectives)
    ├── Category pre-selection (2-4 relevant categories)
    └── Load targeted strategy files (~15-25 strategies)
    ↓
PHASE 2: STRATEGY FINE-SELECTION
    ├── Content analysis within loaded categories
    ├── Proficiency range identification
    ├── Key Language Use alignment
    ├── Strategy compatibility analysis
    └── WIDA enhancement mapping
    ↓
PHASE 3: CO-TEACHING MODEL SELECTION (NEW)
    ├── Identify dominant WIDA band from class proficiency
    ├── Load priority models from wida_model_rules.json
    ├── Apply special conditions (newcomer, space, planning time)
    ├── Filter equity violations (avoid one_assist/one_observe)
    ├── Select top model and load 45-minute phase pattern
    └── Integrate model into Tailored Instruction with teacher roles
    ↓
PHASE 4: PRIMARY-ASSESSMENT-FIRST INTEGRATION
    ├── Capture primary teacher's assessment verbatim
    ├── Map to WIDA Key Language Use and ELD domains
    ├── Design level-banded overlay (no new materials)
    └── Add language-focused scoring lens
    ↓
PHASE 5: LINGUISTIC MISCONCEPTION PREDICTION (NEW)
    ├── Scan lesson objectives/vocabulary for trigger keywords
    ├── Match patterns in portuguese_misconceptions.json
    ├── Output specific linguistic note + prevention tip
    └── Add to Misconceptions row (if no match: default reminder)
    ↓
SUPPORTING DATA SOURCES:
    ├── wida/wida_framework_reference.json
    ├── wida/wida_strategy_enhancements.json
    ├── co_teaching/wida_model_rules.json
    ├── co_teaching/phase_patterns_45min.json
    └── co_teaching/portuguese_misconceptions.json
    ↓
OUTPUT GENERATION:
    ├── Markdown table (Word-compatible format)
    ├── Tri-objective structure per lesson
    ├── Strategy implementation details
    └── Assessment overlay documentation
    ↓
OUTPUT: WIDA-Enhanced Bilingual Lesson Plan (Markdown Table)
```

## **File Relationships and Dependencies**

### **Core Dependencies**
1. **Prompt Engine** requires all three JSON files for complete functionality
2. **Strategy Database** (v1.6) provides base strategy metadata
3. **WIDA Reference** supplies framework components and templates
4. **WIDA Enhancements** delivers proficiency-specific adaptations

### **Cross-References**
- Strategy IDs link across all JSON files
- WIDA proficiency levels consistent across reference and enhancement files
- Grade clusters align between WIDA components and strategy adaptations
- Language objectives templates integrate framework and enhancement data

## **Version Control and Evolution**

### **Strategy Database Versions**
- **v1.3:** Basic strategy collection (27 strategies)
- **v1.4:** Comprehensive collection (33 strategies, source docs removed)
- **v1.5:** Enhanced metadata (skill weights, categories)
- **v1.6:** WIDA alignment fields (monolithic file)
- **v2.0:** Modular architecture with intelligent category loading (current production version)

### **Enhancement Tracking**
- **WIDA Reference:** Updated to 2020 framework standards
- **Strategy Enhancements:** Proficiency-responsive implementations (v2.0)
- **Prompt Engine:** v4 with modular strategy pack, Primary-Assessment-First protocol, and Word-compatible output
- **Schema Evolution:** v1.7_enhanced with comprehensive pedagogical definitions

## **System Integration Points**

### **Input Requirements**
- Primary teacher lesson plan (any format)
- Grade level specification
- Student proficiency range identification
- Content area and vocabulary context

### **Processing Components**
1. **Five-Phase Processing Pipeline:**
   - Phase 1: Smart category pre-selection using _index.json rules
   - Phase 2: 8-step WIDA-enhanced filtering within loaded categories
   - Phase 3: Co-teaching model selection based on WIDA proficiency distribution (NEW)
   - Phase 4: Primary-Assessment-First integration with level-banded overlay
   - Phase 5: Linguistic misconception prediction via keyword matching (NEW)
2. **Language Objective Generation:** WIDA-aligned tri-objective system (Content → Student Goal → WIDA Bilingual)
3. **Proficiency Differentiation:** Three-tier adaptation (1-2, 3-4, 5-6) with specific scaffolds
4. **Co-Teaching Integration:** WIDA-driven model selection with 45-minute phase plans and teacher role specifications (NEW)
5. **Linguistic Misconception Prevention:** Portuguese→English interference pattern prediction with prevention strategies (NEW)
6. **Assessment Overlay Protocol:** 5-step methodology preserving primary assessment while adding WIDA supports
7. **Pedagogical Quality Assurance:** Enhanced definitions with look_fors and non_examples
8. **Output Formatting:** Microsoft Word-compatible markdown tables with `|` separators and `<br>` line breaks

### **Output Specifications**
- Enhanced lesson plan in markdown table format (Word-compatible)
- Tri-objective structure: Content Objective, Student Goal (I will...), WIDA Bilingual Language Objective
- Co-teaching model recommendation with 45-minute phase plan integrated into Tailored Instruction (NEW)
- Proficiency-differentiated instructional supports with level-banded scaffolds
- Research-backed strategy implementations with JSON citations
- Linguistic misconception notes with prevention tips in Misconceptions row (NEW)
- Primary-Assessment-First overlay with scoring lens
- Family connection activities (Portuguese-English)
- Strategy summary with WIDA mapping and research foundation

## **Quality Assurance Framework**

### **Data Integrity**
- JSON schema validation across all files
- Cross-reference consistency checks
- WIDA alignment verification
- Research foundation citations

### **Implementation Fidelity**
- Grade-cluster developmental appropriateness
- Proficiency-level accuracy
- Asset-based language consistency
- Cultural responsiveness validation

## **Scalability Considerations**

### **Horizontal Scaling**
- Additional strategy integration pathway
- New language pair support structure
- Extended grade range accommodation
- Multiple content area expansion

### **Vertical Enhancement**
- Advanced WIDA component integration
- Sophisticated assessment alignment
- Enhanced family engagement features
- Professional development integration

## **Usage Patterns**

### **Primary Workflow**
1. Load master index (_index.json) and supporting WIDA/co-teaching files
2. Set `[GRADE_LEVEL_VARIABLE]` in prompt_v4.md for target grade
3. Execute enhanced prompt with primary lesson plan input (DOCX)
4. Apply five-phase processing pipeline:
   - Phase 1: Smart category loading based on lesson context
   - Phase 2: Strategy fine-selection within loaded categories
   - Phase 3: Co-teaching model selection based on WIDA proficiency (NEW)
   - Phase 4: Primary-Assessment-First overlay integration
   - Phase 5: Linguistic misconception prediction via keyword matching (NEW)
5. Generate proficiency-differentiated adaptations using enhanced definitions
6. Format output as Word-compatible markdown table with co-teaching integration
7. Append strategy summary, co-teaching rationale, and assessment overlay snapshot

### **Maintenance Workflow**
1. Update strategy database with new research
2. Enhance WIDA reference with framework updates
3. Expand proficiency adaptations based on field testing
4. Refine prompt engine based on user feedback

## **File Manifest**

### **Production Files (Current v2.0 + Co-Teaching/Linguistic MVP)**
- `../strategies_pack_v2/_index.json` - Master registry and intelligent loading system (pack_version 2.0, schema v1.7_enhanced)
- `../strategies_pack_v2/core/language_skills.json` - 9 core strategies
- `../strategies_pack_v2/core/frameworks_models.json` - 7 pedagogical frameworks
- `../strategies_pack_v2/core/cross_linguistic.json` - 8 biliteracy strategies
- `../strategies_pack_v2/core/assessment_scaffolding.json` - 5 assessment strategies
- `../strategies_pack_v2/specialized/social_interactive.json` - 2 collaborative strategies
- `../strategies_pack_v2/specialized/cultural_identity.json` - 2 culturally responsive strategies
- `../wida/wida_framework_reference.json` - WIDA 2020 framework components
- `../wida/wida_strategy_enhancements.json` - Proficiency adaptations (v2.0)
- `../co_teaching/wida_model_rules.json` - WIDA-driven co-teaching model selection rules (NEW)
- `../co_teaching/phase_patterns_45min.json` - 45-minute phase templates for co-teaching models (NEW)
- `../co_teaching/portuguese_misconceptions.json` - High-frequency Portuguese→English interference patterns (NEW - MVP)
- `../co_teaching/co_teaching_models.csv` - Friend & Cook co-teaching models reference
- `../co_teaching/co_teaching_strategies.pdf` - Visual co-teaching guide (757KB)
- `../prompt_v4.md` - Transformation engine with modular v2.0 integration, co-teaching, and linguistic misconceptions
- `bilingual_strategies_dictionary.md` - Human reference guide (this directory)
- `../input/Lesson Plan Template SY'25-26.docx` - District template for DOCX generation

### **Documentation Files**
- `architecture_001.md` - This architecture document (this directory)
- `examples/Sample_lesson_plan.md` - Example primary teacher lesson plan
- `examples/Sample_Lesson_Transformation_WIDA.md` - WIDA-enhanced transformation output
- `co_teaching_integration_plan.md` - Comprehensive co-teaching integration research and planning (this directory)
- `linguistic_misconceptions_mvp.md` - Lightweight MVP for Portuguese→English interference prediction (this directory)
- `linguistic_misconceptions_integration_plan_v2_future.md` - Comprehensive linguistic plan (archived for future) (this directory)
- `ai_consultation_request.md` - Template for consulting other AI LLMs (this directory)
- `app_overview.md` - Application architecture (Tauri + FastAPI)
- `decisions/ADR-001-tech-stack.md` - Technology stack decisions

### **Legacy Files (Reference Only)**
- `../deprecated/bilingual_strategies_v1_3_full_with_refs_v2.json` - Research-annotated collection
- `../deprecated/bilingual_strategies_v1_6_full.json` - Monolithic v1.6 collection (superseded by modular v2.0)
- `../deprecated/bilingual_strategies_v1_5_full.json` - Enhanced metadata
- `../deprecated/bilingual_strategies_v1_4_full.json` - Expanded collection
- `../deprecated/Prompt Lesson Plan V2.md` - Original prompt version
- `../deprecated/Prompt_Lesson_Plan_V3_WIDA_Enhanced.md` - V3 prompt (superseded by prompt_v4.md)
- `../deprecated/enhanced_prompt_v4.md` - Early v4 draft with legacy monolithic strategy loading (superseded by prompt_v4.md)
- `../deprecated/bilingual_strategies_references_annotated_ordered_by27.md` - Legacy reference file

## **Integration Notes**

This architecture supports seamless integration with MCP (Model Context Protocol) environments for automated lesson plan transformation while maintaining human oversight and customization capabilities. The modular design allows for independent updates to strategies, WIDA components, or enhancement algorithms without system-wide disruption.
