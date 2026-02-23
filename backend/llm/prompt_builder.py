"""
Prompt building for LLM lesson plan transformation.
Loads template, builds main prompt, retry prompt, and schema example.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.llm.prompt_fragments import JSON_SYNTAX_RULES
from backend.llm.retry_prompt import build_retry_prompt as _build_retry_prompt
from backend.llm.schema_example import build_schema_example as _build_schema_example
from backend.telemetry import logger


def load_prompt_template() -> str:
    """Load prompt_v4.md from standard locations. Raises FileNotFoundError if not found."""
    project_root = Path(__file__).resolve().parent.parent.parent
    possible_paths = [
        Path("prompt_v4.md"),
        Path("docs/prompt_v4.md"),
        project_root / "prompt_v4.md",
        project_root / "docs" / "prompt_v4.md",
    ]

    prompt_path = None
    for path in possible_paths:
        if path.exists():
            prompt_path = path
            break

    if not prompt_path:
        searched_paths = [str(p) for p in possible_paths]
        error_msg = f"ERROR LLM Service: prompt_v4.md not found. Searched in: {', '.join(searched_paths)}"
        print(error_msg)
        raise FileNotFoundError(
            f"prompt_v4.md not found. Searched in: {', '.join(searched_paths)}"
        )

    try:
        print(f"OK LLM Service: Loaded prompt template from {prompt_path}")
    except UnicodeEncodeError:
        print(f"OK LLM Service: Loaded prompt template from {prompt_path}")
    logger.info(
        "prompt_template_loaded",
        extra={"path": str(prompt_path), "message": f"Loaded prompt template from {prompt_path}"},
    )

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def build_prompt(
    prompt_template: str,
    primary_content: str,
    grade: str,
    subject: str,
    week_of: str,
    teacher_name: Optional[str],
    homeroom: Optional[str],
    available_days: Optional[List[str]] = None,
    using_structured_outputs: bool = False,
    schema_example: Optional[str] = None,
) -> str:
    """Build complete prompt for LLM. When using_structured_outputs is False, schema_example must be provided."""
    grade_level = f"{grade}th grade" if grade.isdigit() else grade
    prompt = prompt_template.replace(
        "[GRADE_LEVEL_VARIABLE = <SET BEFORE RUN>]",
        f"[GRADE_LEVEL_VARIABLE = {grade_level}]",
    )

    metadata_context = f"""
Week: {week_of}
Grade: {grade}
Subject: {subject}
Teacher Name: {teacher_name or "Not specified"}
Homeroom: {homeroom or "Not specified"}
"""

    if available_days:
        available_days_normalized = [day.lower().strip() for day in available_days]
        days_to_generate = [
            d
            for d in ["monday", "tuesday", "wednesday", "thursday", "friday"]
            if d in available_days_normalized
        ]
        if not days_to_generate:
            days_to_generate = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        days_text = ", ".join([d.capitalize() for d in days_to_generate])
        days_instruction = (
            f"**CRITICAL: Include ALL required fields ONLY for {days_text}**"
        )
        days_count_text = f"{len(days_to_generate)} day{'s' if len(days_to_generate) != 1 else ''}"
    else:
        days_to_generate = ["monday", "tuesday", "wednesday", "thursday", "friday"]
        days_text = "Monday, Tuesday, Wednesday, Thursday, Friday"
        days_instruction = f"**CRITICAL: Include ALL required fields for ALL FIVE DAYS ({days_text})**"
        days_count_text = "ALL 5 DAYS"

    if using_structured_outputs:
        if available_days and days_to_generate and len(days_to_generate) < 5:
            all_days_requirement = f"""
**CRITICAL JSON STRUCTURE REQUIREMENT:**
Your JSON MUST include ONLY the following days: {", ".join(days_to_generate)}
- Generate FULL, DETAILED content for {days_text} with all required fields
- **DO NOT include keys for other days** (monday, tuesday, wednesday, thursday, friday that are NOT in the list above)
- **CRITICAL: USE THE SINGLE-SLOT STRUCTURE** (do not use a "slots" array inside each day; put unit_lesson, objective, etc. directly inside the day object)
- The backend will automatically add missing days - focus your token budget on high-quality content for the requested days
"""
        else:
            all_days_requirement = """
**CRITICAL JSON STRUCTURE REQUIREMENT:**
Your JSON MUST include ALL 5 days: monday, tuesday, wednesday, thursday, friday
- Generate FULL, DETAILED content for ALL days with all required fields
- **CRITICAL: USE THE SINGLE-SLOT STRUCTURE** (do not use a "slots" array inside each day; put unit_lesson, objective, etc. directly inside the day object)
"""

        no_school_instruction = (
            '5. **For days NOT in the list above: Use minimal "No School" placeholders** (see structure above)\n'
            '   **IMPORTANT**: Even for "No School" days, preserve ANY content that exists in the DOCX (especially tailored_instruction.original_content, co_teaching_model, etc.). Only use "No School" placeholders for fields that are TRULY missing from the DOCX.\n'
            '   **SCHEMA COMPLIANCE**: For "No School" days you MUST still satisfy the schema: tailored_instruction.co_teaching_model.wida_context at least 30 characters; phase_plan at least 2 phases with minutes >= 1 each (no zero minutes); assessment.bilingual_overlay.supports_by_level.levels_1_2, levels_3_4, levels_5_6 at least 20 characters each. Do not use "N/A" or "No School day." where the schema requires longer strings.'
        )
        focus_instruction = f"5. **Focus your response on generating high-quality content for {days_text} only** - you have limited tokens, use them efficiently"
        output_req_5 = (
            focus_instruction
            if available_days and days_to_generate and len(days_to_generate) < 5
            else no_school_instruction
        )
        output_req_1 = (
            f"1. **CRITICAL: Your JSON MUST include ONLY the following days: {', '.join(days_to_generate)}** - Do NOT include keys for other days (they will be added programmatically by the backend)"
            if available_days and days_to_generate and len(days_to_generate) < 5
            else "1. **MANDATORY: Your JSON MUST include ALL 5 days (monday, tuesday, wednesday, thursday, friday)** - This is a schema requirement that cannot be skipped"
        )

        full_prompt = f"""SYSTEM CONFIGURATION:
- ENABLE_JSON_OUTPUT=true
- Output ONLY valid JSON matching the schema provided via API
- NO markdown code blocks (no ```json```)
- NO text before or after the JSON
- ALL fields must match the schema exactly

{JSON_SYNTAX_RULES}

{all_days_requirement}

{prompt}

---

PRIMARY TEACHER LESSON PLAN:

{metadata_context}

{primary_content}

---

TASK: Transform this primary teacher lesson plan into a complete bilingual lesson plan.

## SELF-CHECK BEFORE RETURNING JSON:

Before returning your JSON response, verify:
1. [OK] All property names are in double quotes (scan for unquoted keys)
2. [OK] All string values are properly closed with double quotes
3. [OK] No trailing commas after last items in objects/arrays
4. [OK] All special characters in strings are properly escaped
5. [OK] No comments (// or /* */) in the JSON
6. [OK] The JSON structure matches the schema exactly

If ANY check fails, fix it before returning.

OUTPUT REQUIREMENTS:
{output_req_1}
2. Generate JSON matching the schema structure provided via API
3. {days_instruction}
4. **For {days_text}: Populate with FULL, DETAILED content - no placeholders, no "TBD", no minimal data**
{output_req_5}
6. **CRITICAL: vocabulary_cognates (exactly 6 items) and sentence_frames (exactly 8 items) are MANDATORY for ALL lesson days** - Never omit these fields

**CRITICAL: pattern_id ENUM VALUES (MUST USE EXACTLY ONE):**
The `misconceptions.linguistic_note.pattern_id` field MUST be one of these exact values:
- 'subject_pronoun_omission'
- 'adjective_placement'
- 'past_tense_ed_dropping'
- 'preposition_depend_on'
- 'false_cognate_actual'
- 'false_cognate_library'
- 'default'

**DO NOT** generate creative pattern names. Use ONLY the values listed above.

**CRITICAL: proficiency_level ENUM VALUES:**
The `sentence_frames[].proficiency_level` field MUST be one of:
- 'levels_1_2'
- 'levels_3_4'
- 'levels_5_6'

**CRITICAL: wida_mapping PATTERN REQUIREMENT:**
The `assessment.bilingual_overlay.wida_mapping` field MUST match this pattern:
Pattern: `.*(Explain|Narrate|Inform|Argue).*ELD.*Level`

**Required Format:**
- Must contain one of: Explain, Narrate, Inform, or Argue
- Must contain "ELD" followed by standard code
- Must contain the word "Level" (or "Levels")

**CORRECT Examples:**
- "Explain; ELD-SS.6-8.Explain.Writing; Levels 2-4"
- "Inform; ELD-MA.2-3.Inform.Reading; Level 3"
- "Narrate; ELD-LA.4-5.Narrate.Speaking; Levels 1-2"

**INCORRECT Examples (will fail validation):**
- "Inform; ELD-MA.2-3.Infor...ey Language Use: Inform" (missing "Level")
- "Explain the concept using ELD standards" (missing pattern structure)
"""
        return full_prompt

    if schema_example is None:
        schema_example = build_schema_example(
            week_of, grade, subject, teacher_name, homeroom
        )

    full_prompt = f"""SYSTEM CONFIGURATION:
- ENABLE_JSON_OUTPUT=true
- Output ONLY valid JSON matching the exact schema structure below
- NO markdown code blocks (no ```json```)
- NO text before or after the JSON
- ALL fields must match the schema exactly

{JSON_SYNTAX_RULES}

{prompt}

---

REQUIRED JSON SCHEMA STRUCTURE:

You MUST output JSON that matches this EXACT structure:

{schema_example}

CRITICAL REQUIREMENTS:
1. Root object has "metadata" and "days" keys
2. metadata.week_of format: "MM/DD-MM/DD" (e.g., "10/6-10/10")
3. days object must include: {days_text.lower()}
4. {days_instruction}
5. Each day has: unit_lesson, objective, anticipatory_set, tailored_instruction, misconceptions, assessment, homework
6. objective has: content_objective, student_goal, wida_objective
7. wida_objective MUST include ELD standard format: (ELD-XX.#-#.Function.Domain)
8. anticipatory_set has: original_content, bilingual_bridge
9. tailored_instruction has: original_content, co_teaching_model, ell_support (3-5 items), special_needs_support (1-2 items), materials
10. co_teaching_model has: model_name, rationale, wida_context, phase_plan (at least 2 phases, e.g. Warmup+Practice or Input+Closure), implementation_notes
11. Each ell_support item has: strategy_id, strategy_name, implementation, proficiency_levels
12. misconceptions has: original_content, linguistic_note
13. assessment has: primary_assessment, bilingual_overlay
14. homework has: original_content, family_connection

**CRITICAL: pattern_id ENUM VALUES (MUST USE EXACTLY ONE):**
The `misconceptions.linguistic_note.pattern_id` field MUST be one of these exact values:
- 'subject_pronoun_omission'
- 'adjective_placement'
- 'past_tense_ed_dropping'
- 'preposition_depend_on'
- 'false_cognate_actual'
- 'false_cognate_library'
- 'default'

**DO NOT** generate creative pattern names. Use ONLY the values listed above.

**CRITICAL: proficiency_level ENUM VALUES:**
The `sentence_frames[].proficiency_level` field MUST be one of:
- 'levels_1_2'
- 'levels_3_4'
- 'levels_5_6'

**CRITICAL: wida_mapping PATTERN REQUIREMENT:**
The `assessment.bilingual_overlay.wida_mapping` field MUST match this pattern:
Pattern: `.*(Explain|Narrate|Inform|Argue).*ELD.*Level`

**Required Format:**
- Must contain one of: Explain, Narrate, Inform, or Argue
- Must contain "ELD" followed by standard code
- Must contain the word "Level" (or "Levels")

**CORRECT Examples:**
- "Explain; ELD-SS.6-8.Explain.Writing; Levels 2-4"
- "Inform; ELD-MA.2-3.Inform.Reading; Level 3"
- "Narrate; ELD-LA.4-5.Narrate.Speaking; Levels 1-2"

**INCORRECT Examples (will fail validation):**
- "Inform; ELD-MA.2-3.Infor...ey Language Use: Inform" (missing "Level")
- "Explain the concept using ELD standards" (missing pattern structure)

---

PRIMARY TEACHER LESSON PLAN:

{metadata_context}

{primary_content}

---

TASK: Transform this primary teacher lesson plan into a complete bilingual lesson plan.

## SELF-CHECK BEFORE RETURNING JSON:

Before returning your JSON response, verify:
1. [OK] All property names are in double quotes (scan for unquoted keys)
2. [OK] All string values are properly closed with double quotes
3. [OK] No trailing commas after last items in objects/arrays
4. [OK] All special characters in strings are properly escaped
5. [OK] No comments (// or /* */) in the JSON
6. [OK] The JSON structure matches the schema exactly

If ANY check fails, fix it before returning.

OUTPUT REQUIREMENTS:
1. Generate JSON matching the EXACT schema structure above
2. {days_instruction}
3. **IMPORTANT: The schema requires all 5 days, but only populate {days_text} with FULL, DETAILED content**
4. **For days NOT in the list above, use minimal "No School" placeholders** (this is a single-lesson document)
   **IMPORTANT**: Even for "No School" days, preserve ANY content that exists in the DOCX (especially tailored_instruction.original_content, co_teaching_model, etc.). Only use "No School" placeholders for fields that are TRULY missing from the DOCX.
   **SCHEMA COMPLIANCE**: For "No School" days you MUST still satisfy the schema: tailored_instruction.co_teaching_model.wida_context at least 30 characters; phase_plan at least 2 phases with minutes >= 1 each (no zero minutes); assessment.bilingual_overlay.supports_by_level.levels_1_2, levels_3_4, levels_5_6 at least 20 characters each. Do not use "N/A" or "No School day." where the schema requires longer strings.
5. **Each requested day must have complete data - no placeholders, no "TBD", no minimal data**
6. WIDA objective must include proper ELD standard for each requested day
7. Include 3-5 ELL support strategies for each requested day
8. Add Portuguese cognates in bilingual_bridge for each requested day
9. Include co-teaching model with phase plan for each requested day
10. Add linguistic misconception notes for each requested day
11. Create bilingual assessment overlay for each requested day
12. Add family connection in Portuguese for each requested day

**WIDA LANGUAGE DOMAINS - FLEXIBLE SELECTION (CRITICAL):**

The four language domains (Listening, Reading, Speaking, Writing) are the structural backbone of WIDA's framework, but NOT every lesson must include all four. Select 1-4 domains based on:

1. **Lesson Activities Analysis**: 
   - Analyze the activities in `tailored_instruction.co_teaching_model.phase_plan`
   - Analyze the strategies in `tailored_instruction.ell_support`
   - Each strategy supports specific domains (e.g., Think-Pair-Share -> Listening + Speaking)
   
2. **Content Objectives**: 
   - What students need to do determines which domains are necessary
   - If students must read -> include Reading
   - If students must write -> include Writing  
   - If students must discuss -> include Speaking + Listening
   - If students must present -> include Speaking (possibly + Writing for notes)

3. **Activity-to-Domain Mapping**:
   - Think-Pair-Share -> Listening + Speaking
   - Reading comprehension -> Reading (possibly + Writing if responses)
   - Writing workshop -> Writing (possibly + Reading if mentor texts)
   - Direct instruction/lecture -> Listening (possibly + Writing if note-taking)
   - Literature circles -> Reading + Speaking + Listening
   - Research projects -> Reading + Writing (possibly + Speaking if presentations)
   - Jigsaw activities -> Reading + Speaking + Listening

**objective.student_goal REQUIREMENTS:**
- Format: "I will..." (first person, child-friendly language)
- Include ONLY the domains (1-4) that the lesson activities actually support
- Explicitly name each selected domain with child-friendly verbs (e.g., "listen to...", "read...", "speak...", "write...") so students immediately know which language skills they will practice; if multiple domains are targeted, mention each of them inside the sentence
- Append a domain tag at the end of the sentence using parentheses with comma-separated lowercase domains (e.g., `(listening, speaking)` or `(reading)`), followed immediately by a period; list only the domains actually practiced
- Use simple, age-appropriate language that a child can understand
- Keep to 1 sentence, maximum 12-15 words for clarity (not counting the domain tag)
- Structure: "I will [domain actions] about/to [content focus] (domain list)"
- Domain-specific child-friendly verbs:
  - Listening: "listen to", "hear", "pay attention to"
  - Reading: "read", "look at", "find in the text"
  - Speaking: "speak", "tell", "share", "talk about", "say"
  - Writing: "write", "put in writing", "write down"
- **Self-check:** Before returning the JSON, re-read every `objective.student_goal`. If any day is missing at least one of the verbs `listen`, `read`, `speak`, or `write` (or their -ing forms) **or** the sentence does not end with the parentheses domain tag plus trailing period described above, fix it before returning the response.

**Examples by domain count:**
- 1 domain (Writing only): "I will write a paragraph about the water cycle."
- 2 domains (Listening + Speaking): "I will listen to my partner and speak to share my ideas about fractions."
- 2 domains (Reading + Writing): "I will read the story and write about my favorite part."
- 3 domains (Reading + Speaking + Writing): "I will read the text, speak with my group, and write my answer."
- 4 domains (All): "I will listen to the explanation, read the text, speak with my partner, and write my response."

        **objective.wida_objective REQUIREMENTS:**
        - Include ONLY the domains (1-4) that the lesson activities actually support
        - Explicitly name each domain used in the objective text
        - Use appropriate ELD code format with domain notation:
          - Single domain: ELD-XX.#-#.Function.Domain (e.g., ELD-SS.6-8.Explain.Writing)
          - Multiple domains: ELD-XX.#-#.Function.Domain1/Domain2 (e.g., ELD-SS.6-8.Explain.Listening/Speaking)
          - All four: ELD-XX.#-#.Function.Listening/Reading/Speaking/Writing
        - Structure: "Students will [function] [content] through [domain actions], using [supports] appropriate for WIDA levels X-X (ELD-XX.#-#.Function.[Domains])."
        - **Pattern reminder:** The ELD code must include all four segments (`ELD-[Standard].[GradeCluster].[Function].[Domains]`). Example: `ELD-LA.2-3.Explain.Writing` (single domain) or `ELD-LA.2-3.Explain.Listening/Writing` (multiple domains). Formats like `ELD-LA.2-3.Explain/Writing` are invalid because the function segment is missing.
        - **Function-to-domain separator rule:** Always insert a period between the Function segment and the first domain (e.g., `.Explain.Listening`). Never insert a slash between the Function and the first domain; slashes are only used to separate multiple domains after the Function segment.
        - **Pattern reminder:** The ELD code must end with the domain suffix (e.g., `.Listening/Speaking`). Never return `ELD-LA.2-3.Explain` without the domain segment.
        - **Self-check:** Before returning JSON, confirm each `objective.wida_objective` includes an ELD code that matches `ELD-[Standard].[GradeCluster].[Function].[Domains]` with Domains drawn from Listening/Reading/Speaking/Writing. If a code fails this pattern, rewrite it until it passes.

**Examples by domain count:**
- 1 domain (Writing): "Students will explain the water cycle through writing a paragraph describing each stage, using sentence frames and vocabulary supports appropriate for WIDA levels 2-4 (ELD-SC.4-5.Explain.Writing)."
- 2 domains (Listening + Speaking): "Students will compare fractions through listening to explanations and speaking with partners using sentence frames, using visual supports appropriate for WIDA levels 2-3 (ELD-MA.3-5.Compare.Listening/Speaking)."
- 3 domains (Reading + Speaking + Writing): "Students will analyze characters through reading the text, speaking in literature circles, and writing character descriptions, using graphic organizers and sentence frames appropriate for WIDA levels 3-5 (ELD-LA.4-5.Analyze.Reading/Speaking/Writing)."
- 4 domains (All): "Students will explain historical events through listening to primary sources, reading documents, speaking in discussions, and writing summaries, using cognates and sentence frames appropriate for WIDA levels 2-4 (ELD-SS.6-8.Explain.Listening/Reading/Speaking/Writing)."

**CRITICAL**: Do NOT force all four domains if the lesson activities don't support them. Analyze the actual activities in phase_plan and ell_support, then select domains accordingly. The goal is authentic alignment between activities and language domains.

**CONTENT PRESERVATION RULES (CRITICAL):**
12. **unit_lesson field**: Copy EXACTLY from input - DO NOT transform, paraphrase, or translate. Preserve all hyperlink text verbatim.
13. **objective.content_objective**: Copy EXACTLY from input primary teacher's objective - DO NOT transform or paraphrase.
14. **Hyperlink formatting**: When multiple hyperlinks exist, format each on its own line (use \\n) for readability:
    Example:
    "LESSON 9: MEASURE TO FIND THE AREA\\nLESSON 10: SOLVE AREA PROBLEMS\\nLESSON 11: AREA AND THE MULTIPLICATION TABLE"
    NOT: "LESSON 9: MEASURE TO FIND THE AREA LESSON 10: SOLVE AREA PROBLEMS..."

Generate the complete JSON now with FULL DATA FOR {days_count_text.upper()}. Output ONLY the JSON, nothing else.
"""

    return full_prompt


def build_retry_prompt(
    original_prompt: str,
    validation_error: Optional[str],
    retry_count: int,
    available_days: Optional[List[str]] = None,
    error_analysis: Optional[Dict[str, Any]] = None,
) -> str:
    """Build a retry prompt with feedback about validation errors."""
    return _build_retry_prompt(
        original_prompt,
        validation_error,
        retry_count,
        available_days=available_days,
        error_analysis=error_analysis,
    )


def build_schema_example(
    week_of: str,
    grade: str,
    subject: str,
    teacher_name: Optional[str],
    homeroom: Optional[str],
) -> str:
    """Build schema example JSON string (single-slot structure only)."""
    return _build_schema_example(week_of, grade, subject, teacher_name, homeroom)
