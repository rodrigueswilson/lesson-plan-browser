# WIDA Framework Files

WIDA (World-Class Instructional Design and Assessment) framework components and proficiency-level adaptations for bilingual teaching strategies.

## Files

### **wida_framework_reference.json**
WIDA 2020 Edition framework components and templates.

**Version:** 2020 Edition  
**Purpose:** Comprehensive WIDA framework reference for language objective development and proficiency-responsive instruction

**Key Components:**
- **ELD Standards:** SI (Social/Instructional), LA (Language Arts), MA (Mathematics), SC (Science), SS (Social Studies)
- **Proficiency Levels:** 1-6 (Entering through Reaching) with asset-based descriptions
- **Key Language Uses:** Narrate, Inform, Explain, Argue
- **Language Dimensions:** Discourse, Sentence, Word/Phrase
- **Grade Clusters:** K, 1, 2-3, 4-5, 6-8, 9-12
- **Language Objective Templates:** By Key Language Use and by Dimension
- **Student Objective Templates:** Student-friendly formats for board posting

**2020 Framework Updates:**
- Six proficiency levels (Level 6 is open-ended)
- Grade-cluster specific descriptors
- Asset-based approach emphasizing what multilingual learners CAN do
- Separation of Language Expectations from Proficiency Level Descriptors
- Intensified focus on discourse dimension of language use

### **wida_strategy_enhancements.json**
Proficiency-level adaptations for bilingual teaching strategies.

**Version:** 2.0  
**Last Updated:** 2025-09-20  
**Total Strategies:** 33

**Purpose:** Proficiency-responsive implementations, scaffolds, and language objectives for bilingual strategies aligned with WIDA 2020 framework

**Key Components:**
- **Strategy Adaptations:** Proficiency-specific implementations for all 33 strategies
- **WIDA Alignment:** Key Language Uses, dimensions, and assessment modes
- **Grade Cluster Focus:** Developmental considerations for K, 1, 2-3, 4-5, 6-8, 9-12
- **Proficiency Adaptations:** Three-tier scaffolding (Levels 1-2, 3-4, 5-6)
- **Implementation Guidance:** Specific supports, materials, and assessment methods
- **Language Objective Templates:** Strategy-specific WIDA-aligned objectives

**Proficiency Bands:**
- **Levels 1-2 (Entering/Emerging):** Heavy L1 use, visual supports, word/phrase outputs
- **Levels 3-4 (Developing/Expanding):** Sentence frames, structured supports, reduced language load
- **Levels 5-6 (Bridging/Reaching):** Discourse connectors, minimal scaffolds, gradual release

## Usage

### Integration with Prompt Engine
The prompt engine (`../prompt_v4.md`) loads these files to:
1. Generate WIDA-aligned bilingual language objectives
2. Apply proficiency-responsive strategy adaptations
3. Create level-banded assessment overlays
4. Ensure grade-cluster developmental appropriateness

### Strategy Selection Process
1. **Load WIDA Framework:** Access ELD standards, Key Language Uses, and templates
2. **Identify Proficiency Range:** Determine student proficiency levels (1-6)
3. **Select Key Language Use:** Match lesson type to Narrate/Inform/Explain/Argue
4. **Apply Adaptations:** Use proficiency-specific scaffolds from enhancements file
5. **Generate Objectives:** Create tri-objective structure with WIDA alignment

### Objective Generation Template
```
Students will use language to [Key Language Use] [content focus] 
(ELD-[standard].[grade-cluster].[function].[domain]) 
by [bilingual strategy] using [specific supports] 
appropriate for WIDA levels [target range], 
producing [product] that demonstrates [dimension focus].
```

## WIDA 2020 Framework Overview

### Proficiency Levels (Asset-Based)
1. **Entering:** Can use nonverbal communication, draw on L1 knowledge, recognize familiar words
2. **Emerging:** Can combine words meaningfully, use memorized chunks, participate in structured interactions
3. **Developing:** Can produce simple sentences, use learned language patterns, engage in basic academic discourse
4. **Expanding:** Can produce complex sentences, use varied language structures, engage in extended discourse
5. **Bridging:** Can produce grade-level discourse, use sophisticated language, approach native-like proficiency
6. **Reaching:** Can perform at or above grade-level expectations, demonstrate specialized language use

### Key Language Uses
- **Narrate:** Convey real or imaginary experiences through stories and histories
- **Inform:** Provide factual information, define, describe, compare, contrast
- **Explain:** Give account for how things work or why things happen
- **Argue:** Justify claims using evidence and reasoning

### Language Dimensions
- **Discourse:** Extended language use across sentences and paragraphs
- **Sentence:** Grammatical structures and syntax
- **Word/Phrase:** Vocabulary and formulaic expressions

## Cross-References

### Core System Files
- **Prompt Engine:** `../prompt_v4.md`
- **Strategy Pack Index:** `../strategies_pack_v2/_index.json`
- **Strategy Categories:** `../strategies_pack_v2/core/` and `../strategies_pack_v2/specialized/`

### Documentation
- **Architecture:** `../docs/architecture_001.md`
- **Strategy Dictionary:** `../docs/bilingual_strategies_dictionary.md`
- **Examples:** `../docs/examples/`

### Legacy WIDA Files
- `../deprecated/wida_framework_reference v2.json` - Earlier version
- `../deprecated/wida_strategy_enhancementsv2.json` - Earlier version

## Maintenance

### Updating WIDA Framework
When WIDA releases new framework updates:
1. Review official WIDA documentation for changes
2. Update `wida_framework_reference.json` with new components
3. Adjust proficiency level descriptors if needed
4. Update grade cluster specifications
5. Revise language objective templates
6. Test with sample lesson plans

### Updating Strategy Enhancements
When adding or modifying strategy adaptations:
1. Ensure alignment with current WIDA 2020 framework
2. Provide all three proficiency bands (1-2, 3-4, 5-6)
3. Include grade cluster considerations
4. Specify Key Language Uses supported
5. Add implementation guidance and materials
6. Update strategy count in metadata
7. Cross-reference with strategy pack files

## Resources

### Official WIDA Resources
- WIDA 2020 ELD Standards Framework
- WIDA Can Do Descriptors
- WIDA Performance Definitions
- WIDA Language Expectations

### Implementation Support
- Strategy-specific adaptations in this directory
- Comprehensive examples in `../docs/examples/`
- Prompt engine protocols in `../prompt_v4.md`

## Notes

These files are essential for:
- **WIDA compliance** in lesson plan transformations
- **Proficiency-responsive** instruction design
- **Asset-based** approach to multilingual learners
- **Research-backed** strategy implementations
- **Grade-appropriate** developmental considerations

All adaptations follow WIDA 2020 standards and emphasize what multilingual learners CAN do at each proficiency level.
