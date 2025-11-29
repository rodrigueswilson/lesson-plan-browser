# Bilingual Teaching Strategies Pack v2.0

Modular collection of 33 research-backed bilingual teaching strategies with intelligent category-based loading for optimized LLM processing.

## Overview

**Pack Version:** 2.0  
**Schema Version:** 1.7_enhanced  
**Total Strategies:** 33  
**Last Updated:** 2025-09-14  
**WIDA Aligned:** Yes

## Architecture

### Modular Design
The v2.0 pack uses intelligent category-based loading to optimize LLM token usage:
- Load only 2-4 relevant categories per lesson (vs. all 33 strategies)
- Reduces context from ~48KB to ~15-25KB per request
- Maintains full strategy depth and quality

### Master Index
**File:** `_index.json`

**Contains:**
- Pack metadata and version information
- Category mappings with strategy counts
- Selection rules by lesson type, grade cluster, proficiency range, and skill
- Loading algorithm with fallback rules
- Cross-references to WIDA files and prompt engine

## Category Structure

### Core Categories (4 files)

#### **language_skills.json** (9 strategies)
Core language development strategies focusing on vocabulary, comprehension, and skill-building.

**Strategies:**
- bilingual_dictionary
- bilingual_word_walls
- explicit_vocabulary
- cognate_awareness
- graphic_organizers
- interactive_read_alouds
- language_experience_approach
- sentence_frames
- total_physical_response

**Best For:** Reading, writing, speaking, listening skills | All grade clusters | All proficiency levels

#### **frameworks_models.json** (7 strategies)
Comprehensive pedagogical frameworks and instructional models.

**Strategies:**
- translanguaging
- siop
- dual_language_instruction
- clil
- scaffolded_instruction
- differentiated_instruction
- project_based_learning

**Best For:** Integrated skills | Grades 3-12 | Proficiency levels 2-6

#### **cross_linguistic.json** (8 strategies)
Strategies leveraging cross-linguistic connections and biliteracy development.

**Strategies:**
- contrastive_analysis
- the_bridge
- preview_review
- strategic_code_switching
- bilingual_books_texts
- cross_linguistic_transfer
- metalinguistic_awareness
- heritage_language_connections

**Best For:** Reading, writing, integrated | Grades 3-12 | Proficiency levels 3-6

#### **assessment_scaffolding.json** (5 strategies)
Assessment strategies and scaffolding techniques for multilingual learners.

**Strategies:**
- formative_assessment_ml
- portfolio_assessment
- peer_assessment_bilingual
- alternative_assessment
- language_objectives_assessment

**Best For:** Integrated skills | All grade clusters | All proficiency levels

### Specialized Categories (2 files)

#### **social_interactive.json** (2 strategies)
Collaborative learning and social interaction strategies.

**Strategies:**
- collaborative_learning
- peer_tutoring_bilingual

**Best For:** Speaking, listening | Grades K-8 | Proficiency levels 1-4

#### **cultural_identity.json** (2 strategies)
Culturally responsive and identity-affirming pedagogical approaches.

**Strategies:**
- culturally_responsive_pedagogy
- funds_of_knowledge

**Best For:** Integrated skills | Grades 3-12 | Proficiency levels 2-6

## Selection Rules

### By Lesson Type
- **Reading comprehension:** language_skills + cross_linguistic
- **Vocabulary development:** language_skills + assessment_scaffolding
- **Writing workshop:** language_skills + cross_linguistic + cultural_identity
- **Math problem solving:** language_skills + assessment_scaffolding
- **Science inquiry:** frameworks_models + social_interactive
- **Social studies discussion:** frameworks_models + cultural_identity + cross_linguistic
- **Literature analysis:** cross_linguistic + cultural_identity + frameworks_models
- **Research project:** frameworks_models + cross_linguistic + assessment_scaffolding

### By Grade Cluster
- **K-2:** language_skills + social_interactive
- **3-5:** language_skills + frameworks_models + assessment_scaffolding
- **6-8:** frameworks_models + cross_linguistic + cultural_identity
- **9-12:** cross_linguistic + cultural_identity + frameworks_models

### By Proficiency Range
- **Levels 1-2:** language_skills + assessment_scaffolding + social_interactive
- **Levels 3-4:** frameworks_models + cross_linguistic + language_skills
- **Levels 5-6:** cultural_identity + cross_linguistic + frameworks_models
- **Mixed levels:** language_skills + assessment_scaffolding + frameworks_models

### By Primary Skill
- **Speaking:** language_skills + social_interactive
- **Listening:** language_skills + social_interactive + frameworks_models
- **Reading:** language_skills + cross_linguistic
- **Writing:** language_skills + cross_linguistic + cultural_identity
- **Integrated:** frameworks_models + assessment_scaffolding + cultural_identity

## Loading Algorithm

1. **Analyze lesson context** (subject, grade, proficiency range)
2. **Apply selection rules** to identify 2-4 relevant categories
3. **Load identified category files** (~15-25 strategies total)
4. **Apply 8-step strategy selection** within loaded pool
5. **Generate lesson plan** with selected strategies

### Fallback Rules
- **If uncertain:** Load language_skills.json (core strategies)
- **If mixed proficiency:** Load language_skills.json + assessment_scaffolding.json
- **If complex lesson:** Load maximum 4 categories
- **If new teacher:** Load language_skills.json + frameworks_models.json

## Schema v1.7_enhanced

Each strategy includes:

### Core Fields
- `strategy_id` - Unique identifier
- `strategy_name` - Display name
- `core_principle` - Foundational concept

### WIDA Integration
- `high_level_categories` - Array of WIDA categories
- `skill_weights` - Quantified skill distribution (speaking, listening, reading, writing)

### Implementation
- `delivery_modes` - Array: push-in, pull-out, whole-group, small-group, individual
- `l1_modes` - Array: translanguaging, preview-review, strategic-code-switch, none
- `applicable_contexts` - When to use the strategy

### Pedagogical Definitions
- `short_en` - Brief description
- `long_en` - Comprehensive explanation
- `look_fors` - Observable indicators of effective implementation
- `non_examples` - What NOT to do

### Quality Assurance
- `research_foundation` - Researcher citations
- `cross_refs` - Related strategies
- `evidence_tier` - Research strength

## Usage with Prompt Engine

The prompt engine (`prompt_v4.md`) automatically:
1. Loads `_index.json` to access selection rules
2. Analyzes lesson context to determine relevant categories
4. Applies fine-selection within loaded strategies
5. Generates WIDA-enhanced lesson plans with selected strategies

## Cross-References

### Core System Files
- **Prompt Engine:** `../prompt_v4.md`
- **WIDA Files:** `../wida/`
- **Strategy Pack Index:** `_index.json` (this directory)
- **Strategy Categories:** `core/` and `specialized/` (this directory)

### Documentation
- **Architecture:** `../docs/architecture_001.md`
- **Strategy Dictionary:** `../docs/bilingual_strategies_dictionary.md`
- **Examples:** `../docs/examples/`

### Legacy Files
- `../deprecated/wida_framework_reference v2.json` - Earlier WIDA version
- `../deprecated/wida_strategy_enhancementsv2.json` - Earlier enhancements version

## Maintenance

When adding new strategies:
1. Add to appropriate category file (or create new category)
2. Update `_index.json` with strategy ID and count
3. Update selection rules if needed
4. Ensure schema v1.7_enhanced compliance
5. Add WIDA proficiency adaptations to `../wida/wida_strategy_enhancements.json`
6. Update strategy dictionary documentation
