# Vocabulary and Sentence Frames Integration Audit

## Current State Analysis

### Problem Statement
Currently, vocabulary words and sentence frames are generated independently, with no explicit connection between them beyond sharing the same lesson content and objectives. This is pedagogically inefficient because students don't practice using vocabulary words in the sentence frames.

### Current Generation Process

#### Vocabulary Generation (`prompt_v4.md` lines 289-336)
- **Source**: Extracted from lesson objectives and content
- **Output**: Exactly 6 English-Portuguese word pairs
- **Structure**: Each pair includes:
  - `english`: English word
  - `portuguese`: Portuguese word
  - `is_cognate`: Boolean indicating if true cognate
  - `relevance_note`: Why the word is relevant to the lesson

#### Sentence Frame Generation (`prompt_v4.md` lines 337-390)
- **Source**: Based on target language functions and Key Language Use (Narrate, Inform, Explain, Argue)
- **Output**: Exactly 8 sentence frames/stems/questions
- **Distribution**:
  - 3 frames for Levels 1-2
  - 3 frames for Levels 3-4
  - 1 stem + 1 open question for Levels 5-6
- **Structure**: Each frame includes:
  - `proficiency_level`: WIDA level group
  - `english`: English sentence frame
  - `portuguese`: Portuguese sentence frame
  - `language_function`: Target function (explain, compare, describe, etc.)
  - `frame_type`: frame, stem, or open_question

### Current Disconnection

**No explicit instruction exists to:**
1. Use vocabulary words within sentence frames
2. Reference vocabulary pairs when generating frames
3. Ensure vocabulary appears in frame examples or placeholders
4. Create frames that naturally incorporate the lesson's vocabulary

**The only connection is:**
- Both are generated from the same lesson content/objectives
- Both are stored in the same daily plan structure
- Both may be referenced in ELL support strategies

### Pedagogical Impact

**Current Problem:**
- Students learn vocabulary words separately from sentence frames
- Sentence frames use generic language that doesn't reinforce vocabulary
- Missed opportunity for vocabulary practice in context
- Reduced vocabulary retention and application

**Desired Outcome:**
- Sentence frames should incorporate vocabulary words where appropriate
- Students practice vocabulary in authentic sentence structures
- Better vocabulary retention through contextualized practice
- More cohesive lesson design

## Proposed Solution

### Integration Strategy

1. **Modify Sentence Frame Generation Protocol** to require vocabulary integration:
   - After generating vocabulary pairs, use them when creating sentence frames
   - Incorporate vocabulary words into frames where semantically appropriate
   - Ensure at least 4-5 frames per day (ideally all 8) use vocabulary from the vocabulary_cognates list
   - Maintain natural language flow (don't force vocabulary if it doesn't fit)

2. **Update Prompt Instructions**:
   - Add explicit step: "Review the vocabulary_cognates list and incorporate appropriate vocabulary words into sentence frames"
   - Provide examples of vocabulary-integrated frames
   - Clarify that not ALL frames need vocabulary, but several should

3. **Validation Requirements**:
   - Check that vocabulary words appear in sentence frames where appropriate
   - Ensure vocabulary integration is natural and pedagogically sound

### Example Integration

**Before (Current):**
- Vocabulary: `law → lei`, `system → sistema`, `economy → economia`
- Sentence Frame: "This shows ___ because ___" (generic, no vocabulary)

**After (Proposed):**
- Vocabulary: `law → lei`, `system → sistema`, `economy → economia`
- Sentence Frame: "The legal **system** shows ___ because ___" (incorporates vocabulary word "system")

Or:
- Sentence Frame: "The **economy** demonstrates ___ when ___" (incorporates vocabulary word "economy")

### Implementation Notes

- **Natural Integration**: Vocabulary should fit naturally into frames, not be forced
- **Proficiency-Appropriate**: Lower levels (1-2) may use vocabulary more simply; higher levels (5-6) may use vocabulary in more complex structures
- **Language Function Alignment**: Vocabulary integration should still support the target language function
- **Portuguese Equivalents**: When vocabulary is used in English frames, ensure Portuguese frames use the corresponding Portuguese vocabulary word

## Files Requiring Changes

1. **`prompt_v4.md`**: Update Sentence Frame Generation Protocol section
2. **Validation**: May need to add checks to ensure vocabulary integration occurs
3. **Testing**: Verify that generated frames actually use vocabulary words

## Implementation Status

### ✅ Changes Made

1. **Updated `prompt_v4.md` Sentence Frame Generation Protocol:**
   - Added **Step 1.5: Integrate Vocabulary Words (CRITICAL)** with explicit requirements
   - Modified proficiency-level frame generation sections to include vocabulary integration examples
   - Added **Step 5: Vocabulary Integration Validation** to verify integration
   - Updated validation checklists to include vocabulary integration checks

2. **Key Requirements Added:**
   - At least 4-5 sentence frames per day (ideally all 8) must incorporate vocabulary from vocabulary_cognates
   - Vocabulary integration must be natural and contextually appropriate
   - Portuguese frames must use corresponding Portuguese vocabulary when English frames use English vocabulary
   - Examples provided for each proficiency level showing vocabulary integration

3. **Validation Added:**
   - Pre-execution checklist includes vocabulary integration validation
   - Quality assurance checklist includes vocabulary-pedagogy alignment checks

### Next Steps

1. ✅ ~~Review and approve this audit~~ - COMPLETED
2. ✅ ~~Update `prompt_v4.md` with vocabulary integration requirements~~ - COMPLETED
3. **Test with sample lesson plans to verify integration** - PENDING
4. **Monitor generated outputs to ensure quality** - ONGOING

### Testing Recommendations

1. Generate sample lesson plans and verify:
   - At least 4-5 frames per day (ideally all 8) use vocabulary words
   - Vocabulary integration is natural and appropriate
   - Portuguese frames correctly use Portuguese vocabulary equivalents
   - Vocabulary integration supports language functions

2. Monitor for:
   - Over-forced vocabulary (unnatural language)
   - Missing vocabulary integration (frames don't use vocabulary)
   - Portuguese-English vocabulary mismatches
   - Vocabulary integration that doesn't support language functions

