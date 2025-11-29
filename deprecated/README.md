# Deprecated Files

Legacy files and previous versions superseded by current production system. These files are preserved for reference and historical context.

## Deprecation Policy

Files in this directory are:
- **No longer used** in production workflows
- **Superseded** by newer versions or modular architecture
- **Preserved** for reference and version history
- **Not maintained** - updates go to current production files

## Recently Deprecated

### **enhanced_prompt_v4.md** (15 KB)
Early v4 prompt draft with legacy monolithic strategy loading.

**Superseded by:** `../prompt_v4.md`

**Reason:** 
- Uses legacy monolithic strategy loading (all 33 strategies at once)
- Missing Primary-Assessment-First protocol
- Lacks explicit Word-compatible table formatting
- Simpler error handling without modular pack support

**Date Deprecated:** 2025-10-04

### **bilingual_strategies_references_annotated_ordered_by27.md** (37 KB)
Legacy strategy reference file with annotations.

**Superseded by:** `../docs/bilingual_strategies_dictionary.md` and modular `../strategies_pack_v2/`

**Reason:**
- Replaced by comprehensive strategy dictionary
- Superseded by modular v2.0 strategy pack
- Outdated schema (pre-v1.7_enhanced)

**Date Deprecated:** 2025-10-04

## Prompt Versions

### **Prompt_Lesson_Plan_V3_WIDA_Enhanced.md** (13 KB)
Version 3 prompt with WIDA enhancements.

**Superseded by:** `../prompt_v4.md`

**Key Differences:**
- No modular strategy pack integration
- Missing Primary-Assessment-First protocol
- Simpler assessment approach
- No `[GRADE_LEVEL_VARIABLE]` system

**Date Deprecated:** 2025-09-14

### **Prompt Lesson Plan V2.md** (12 KB)
Original version 2 prompt.

**Superseded by:** V3, then V4

**Key Differences:**
- Basic strategy selection
- No WIDA framework integration
- Limited proficiency differentiation

**Date Deprecated:** 2025-08-01 (estimated)

## Strategy Database Versions

### **bilingual_strategies_v2_full.json** (82 KB)
Attempted v2 with JSON syntax errors (orphaned content at line 498).

**Issues:**
- JSON structure error (premature closing brace)
- Orphaned strategy definitions
- Never reached production

**Superseded by:** Modular v2.0 pack

### **bilingual_strategies_v1_6_full.json** (48 KB)
Monolithic v1.6 collection with WIDA alignment fields.

**Superseded by:** Modular `../strategies_pack_v2/` (v2.0)

**Reason:**
- Monolithic file too large for efficient LLM processing
- No intelligent category loading
- Replaced by modular architecture

**Date Deprecated:** 2025-09-14

### **bilingual_strategies_v1_5_full.json** (45 KB)
Enhanced metadata version with skill weights and categories.

**Superseded by:** v1.6, then modular v2.0

### **bilingual_strategies_v1_4_full.json** (39 KB)
Expanded collection (33 strategies, source docs removed).

**Superseded by:** v1.5

### **bilingual_strategies_v1_3_full.json** (53 KB)
Basic strategy collection (27 strategies).

**Superseded by:** v1.4

### **bilingual_strategies_v1_3_full_with_refs_v2.json** (76 KB)
Research-annotated v1.3 collection.

**Superseded by:** v1.4+ (references moved to separate documentation)

### Chunked Files (v1.3)
- `bilingual_strategies_v1_3_chunk01.json` through `chunk05.json`
- Temporary files from v1.3 development
- Merged into full v1.3 file

### **bilingual_strategies_merged.json** / **temp_merged.json** (33 KB each)
Temporary merge files from development.

**Status:** Development artifacts, no longer needed

## WIDA Files

### **wida_framework_reference v2.json** (13 KB)
Earlier version of WIDA framework reference.

**Superseded by:** `../wida_framework_reference.json` (2020 Edition)

### **wida_strategy_enhancementsv2.json** (19 KB)
Earlier version of proficiency adaptations.

**Superseded by:** `../wida_strategy_enhancements.json` (v2.0)

## Sample Files

### **Lesson Plan Template SY'25-26.docx** (281 KB)
Duplicate of district template (also in `../input/`).

**Status:** Duplicate file, active version in `../input/`

### Sample Lesson Plans
- **Lesson Plan Sample.docx** (24 KB)
- **Lesson Plan Sample.pdf** (216 KB)
- **Sample lesson plan.txt** (9 KB)

**Status:** Older samples, superseded by current examples in `../docs/examples/`

### Sample Outputs
- **Sample_lesson_plan_WIDA_enhanced.doc** (15 KB)
- **Sample_lesson_plan_WIDA_enhanced.docx** (21 KB)
- **Sample_lesson_plan_WIDA_enhanced.txt** (15 KB)

**Status:** Older transformation outputs, superseded by `../docs/examples/Sample_Lesson_Transformation_WIDA.md`

## Version Timeline

```
2025-08 (est): Prompt V2
2025-08 (est): Strategy DB v1.3 → v1.4 → v1.5
2025-09-01:    Strategy DB v1.6 (WIDA alignment)
2025-09-14:    Prompt V3 (WIDA Enhanced)
2025-09-14:    Strategy Pack v2.0 (modular architecture)
2025-09-20:    WIDA Enhancements v2.0
2025-10-04:    Prompt V4 (Primary-Assessment-First)
```

## Reference Use Only

These files may be useful for:
- Understanding system evolution
- Comparing feature changes across versions
- Recovering specific implementations
- Historical documentation

**Do not use these files in production workflows.**

## Current Production Files

See main project README for current file locations:
- **Prompt:** `../prompt_v4.md`
- **Strategy Pack:** `../strategies_pack_v2/`
- **WIDA Framework:** `../wida_framework_reference.json`
- **WIDA Enhancements:** `../wida_strategy_enhancements.json`
- **Documentation:** `../docs/`
