# LLM Workflow Test - Manual Instructions

## Purpose
Test the complete transformation pipeline from primary teacher content to bilingual lesson plan.

---

## Step 1: Prepare Primary Teacher Content

**Sample Input:**
```
Week of: 10/6-10/10
Grade: 6
Subject: Science
Teacher: Ms. Johnson

MONDAY - Unit 3 Lesson 1: States of Matter

Objective: Students will identify the three states of matter and their properties.

Anticipatory Set: Show ice cube melting in a beaker. Ask: What is happening? Why? Record observations.

Instruction: 
- Present three states of matter with demonstrations
- Show solid (ice), liquid (water), gas (steam)
- Discuss molecular movement in each state
- Students complete comparison chart

Misconceptions: Students may think gases have no mass or that liquids always take the shape of their container from the bottom up.

Assessment: Students complete three-column chart comparing states of matter. Must include at least 3 properties for each state.

Homework: Find 5 examples of each state of matter at home. Draw or photograph them. Label in English.
```

---

## Step 2: Configure the Prompt

1. Open `prompt_v4.md`
2. Replace line 5: `[GRADE_LEVEL_VARIABLE = <SET BEFORE RUN>]` with `[GRADE_LEVEL_VARIABLE = 6th grade]`
3. Add at the top:
   ```
   ENABLE_JSON_OUTPUT=true
   ```

---

## Step 3: Build the Complete Prompt

**System Message:**
```
You are a Portuguese-English bilingual education specialist. Output only valid JSON matching the schema provided.
```

**User Message:**
```
[Full content of prompt_v4.md with grade level configured]

---

PRIMARY TEACHER LESSON PLAN:

[Paste the sample input above]

---

TASK: Transform this into a bilingual lesson plan following the framework.
Output ONLY valid JSON (no markdown code blocks).
```

---

## Step 4: Send to LLM

**Options:**

### Option A: OpenAI API (Requires API Key)
```bash
python test_llm_workflow.py
```

### Option B: Claude (Anthropic)
1. Go to https://claude.ai
2. Paste the complete prompt
3. Copy the JSON response

### Option C: ChatGPT Web Interface
1. Go to https://chat.openai.com
2. Paste the complete prompt
3. Copy the JSON response

---

## Step 5: Save the Response

Save the LLM's JSON output to: `output/llm_test_lesson.json`

---

## Step 6: Validate the JSON

```bash
python -c "import requests, json; data=json.load(open('output/llm_test_lesson.json','r',encoding='utf-8')); r=requests.post('http://localhost:8000/api/validate', json={'json_data':data}); print('Valid:', r.json()['valid']); print('Errors:', r.json().get('errors', 'None'))"
```

---

## Step 7: Render to DOCX

```bash
python -c "import requests, json; data=json.load(open('output/llm_test_lesson.json','r',encoding='utf-8')); r=requests.post('http://localhost:8000/api/render', json={'json_data':data, 'output_filename':'llm_test_lesson.docx'}); result=r.json(); print('Success:', result['success']); print('Output:', result.get('output_path'))"
```

---

## Expected Results

### ✅ Success Criteria

1. **LLM generates valid JSON** with:
   - WIDA-aligned objectives (with ELD standard)
   - Bilingual bridges (Portuguese cognates)
   - Co-teaching model selection
   - 3-5 ELL support strategies
   - Linguistic misconception notes
   - Bilingual assessment overlay
   - Family connection

2. **JSON validates** against schema

3. **DOCX renders** successfully

### ❌ Common Issues

**Issue 1: LLM wraps JSON in code blocks**
- **Fix:** Strip ```json and ``` from response

**Issue 2: Missing required fields**
- **Fix:** Update prompt to emphasize required fields

**Issue 3: Invalid ELD standard format**
- **Fix:** Provide more examples in prompt

**Issue 4: Array size violations**
- **Fix:** Specify "exactly 3-5 ELL strategies"

---

## What We're Testing

1. ✅ **Prompt effectiveness** - Does prompt_v4.md produce correct output?
2. ✅ **LLM capability** - Can the LLM follow complex instructions?
3. ✅ **Schema compliance** - Does output match lesson_output_schema.json?
4. ✅ **WIDA integration** - Are objectives properly formatted?
5. ✅ **Strategy selection** - Does it choose appropriate strategies?
6. ✅ **Bilingual quality** - Are Portuguese elements authentic?
7. ✅ **Rendering** - Does our DOCX generator handle LLM output?

---

## Next Steps After Success

1. **Automate the workflow** - Build the Python pipeline
2. **Add DOCX input parser** - Extract from primary teacher files
3. **Build multi-slot processor** - Handle 6 classes at once
4. **Add user profiles** - Save configurations
5. **Create UI** - Make it user-friendly

---

## Quick Test Commands

**Check system health:**
```bash
curl http://localhost:8000/api/health
```

**Validate JSON file:**
```bash
python -c "import requests, json; data=json.load(open('output/llm_test_lesson.json','r')); r=requests.post('http://localhost:8000/api/validate', json={'json_data':data}); print(r.json())"
```

**Render to DOCX:**
```bash
python -c "import requests, json; data=json.load(open('output/llm_test_lesson.json','r')); r=requests.post('http://localhost:8000/api/render', json={'json_data':data, 'output_filename':'test.docx'}); print(r.json())"
```

---

## Do You Have an OpenAI API Key?

**Yes:** Run `python test_llm_workflow.py`  
**No:** Follow manual steps above using ChatGPT web interface

---

**Ready to test!** 🚀
