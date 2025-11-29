# LLM Workflow Test Plan

**Date:** 2025-10-05  
**Status:** Ready to Execute  
**Purpose:** Validate end-to-end LLM transformation pipeline

---

## What We're Testing

The complete workflow from primary teacher content → LLM transformation → bilingual lesson plan → DOCX output.

### Components Involved

1. **prompt_v4.md** - Comprehensive transformation framework
2. **LLM (GPT-4/Claude)** - AI transformation engine
3. **lesson_output_schema.json** - Output validation
4. **DOCX Renderer** - Final document generation

---

## Test Files Created

### 1. Automated Test Script
**File:** `test_llm_workflow.py`

**Features:**
- Loads prompt_v4.md framework
- Sends to OpenAI API
- Validates JSON response
- Renders to DOCX
- Full error handling

**Requirements:**
- OpenAI API key in environment variable `OPENAI_API_KEY`
- Python packages: `openai`, `requests`

**Usage:**
```bash
python test_llm_workflow.py
```

### 2. Manual Test Guide
**File:** `test_llm_workflow_manual.md`

**Features:**
- Step-by-step instructions
- No API key required
- Use ChatGPT web interface
- Validation commands
- Troubleshooting guide

**Usage:**
- Follow the guide to test manually

---

## Sample Test Case

### Input: Primary Teacher Lesson
```
Week: 10/6-10/10
Grade: 6
Subject: Science
Topic: States of Matter

Objective: Students will identify three states of matter
Instruction: Demonstrate solid, liquid, gas
Assessment: Comparison chart
```

### Expected Output: Bilingual Lesson Plan JSON

**Must include:**
- ✅ WIDA objective with ELD-SC.6-8.Explain.Reading/Writing
- ✅ Bilingual bridge with Portuguese cognates (sólido/solid, líquido/liquid, gás/gas)
- ✅ Co-teaching model (Station/Parallel/Team based on proficiency)
- ✅ 3-5 ELL strategies (cognate awareness, graphic organizers, etc.)
- ✅ Linguistic misconception note
- ✅ Bilingual assessment overlay
- ✅ Family connection in Portuguese

---

## Success Criteria

### Phase 1: LLM Generation ✅
- [ ] LLM produces valid JSON
- [ ] All required fields present
- [ ] WIDA objectives properly formatted
- [ ] ELD standards correct (ELD-XX.#-#.Function.Domain)
- [ ] Portuguese elements authentic
- [ ] Strategies appropriate for grade 6

### Phase 2: Validation ✅
- [ ] JSON passes schema validation
- [ ] No missing required fields
- [ ] Array sizes correct (3-5 ELL strategies)
- [ ] String lengths within limits
- [ ] Enum values match exactly

### Phase 3: Rendering ✅
- [ ] DOCX generates successfully
- [ ] All content renders properly
- [ ] Formatting preserved
- [ ] File size reasonable (~280KB)
- [ ] Opens in Microsoft Word

---

## How to Run the Test

### Option 1: Automated (Requires API Key)

```bash
# Set API key
set OPENAI_API_KEY=your-key-here

# Run test
python test_llm_workflow.py
```

### Option 2: Manual (No API Key)

1. Open `test_llm_workflow_manual.md`
2. Follow step-by-step instructions
3. Use ChatGPT web interface
4. Validate and render manually

---

## What This Validates

### ✅ Prompt Effectiveness
- Does prompt_v4.md produce correct output?
- Are instructions clear enough for LLM?
- Does it handle all required fields?

### ✅ LLM Capability
- Can GPT-4/Claude follow complex instructions?
- Does it generate authentic Portuguese?
- Are WIDA objectives properly formatted?

### ✅ Schema Compliance
- Does output match lesson_output_schema.json?
- Are all required fields present?
- Are data types correct?

### ✅ Integration
- Does LLM output work with our validator?
- Does it render to DOCX correctly?
- Is the end-to-end pipeline functional?

---

## Expected Timeline

**Total time:** ~30 minutes

1. **Setup** (5 min) - Get API key or prepare manual test
2. **Execution** (10 min) - Run LLM transformation
3. **Validation** (5 min) - Check JSON against schema
4. **Rendering** (5 min) - Generate DOCX
5. **Review** (5 min) - Examine output quality

---

## Next Steps After Success

### Immediate (If Test Passes)
1. ✅ LLM transformation works
2. ✅ Prompt is effective
3. ✅ Schema is correct
4. ✅ Rendering handles LLM output

### Phase 2: Build Automation
1. **DOCX Input Parser** - Extract from primary teacher files
2. **Subject Extraction** - User selects which subject
3. **Batch Processor** - Handle 6 classes at once
4. **User Profiles** - Save configurations

### Phase 3: Complete System
1. **Multi-user support**
2. **Combined DOCX output**
3. **Signature box with date**
4. **Proper filename format**

---

## Troubleshooting

### Issue: No API Key
**Solution:** Use manual test with ChatGPT web interface

### Issue: LLM wraps JSON in code blocks
**Solution:** Script automatically strips ```json and ```

### Issue: Validation fails
**Solution:** Check specific error messages, update prompt

### Issue: Missing required fields
**Solution:** Enhance prompt to emphasize required fields

### Issue: Invalid ELD standard format
**Solution:** Provide more examples in prompt

---

## Files Involved

### Input Files
- `prompt_v4.md` - Transformation framework
- `schemas/lesson_output_schema.json` - Output schema
- `strategies_pack_v2/` - Strategy database
- `wida_framework_reference.json` - WIDA standards
- `co_teaching/` - Co-teaching models

### Test Files
- `test_llm_workflow.py` - Automated test
- `test_llm_workflow_manual.md` - Manual guide

### Output Files
- `output/llm_test_lesson.json` - Generated JSON
- `output/llm_test_lesson.docx` - Rendered DOCX

---

## Questions to Answer

1. **Does the LLM understand the prompt?** ✓
2. **Is the output JSON valid?** ✓
3. **Does it match the schema?** ✓
4. **Are WIDA objectives correct?** ✓
5. **Is Portuguese authentic?** ✓
6. **Does rendering work?** ✓
7. **Is quality acceptable?** ✓

---

## Success Metrics

**Quality Indicators:**
- WIDA objectives include proper ELD standards
- Portuguese cognates are accurate
- Co-teaching model is appropriate
- ELL strategies are research-based
- Assessment overlay is practical
- Family connections are culturally appropriate

**Technical Indicators:**
- JSON validates without errors
- DOCX renders in <100ms
- File size is reasonable
- All content is present

---

**Ready to test the LLM workflow!** 🚀

**Next:** Run `python test_llm_workflow.py` or follow manual guide

---

**Status:** Awaiting execution  
**Blocker:** Need OpenAI API key (or use manual method)  
**ETA:** 30 minutes to complete test
