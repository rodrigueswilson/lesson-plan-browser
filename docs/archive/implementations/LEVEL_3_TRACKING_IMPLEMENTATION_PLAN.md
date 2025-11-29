# Level 3 Detailed Tracking - Full Implementation Plan

**Scope**: Add 60+ granular operations across all phases  
**Estimated Time**: 4-6 hours  
**Status**: PLANNED - Ready for implementation

---

## 🎯 Overview

This document outlines the complete Level 3 tracking implementation, breaking down each of the 19 current operations into 3-5 sub-operations each.

**Current**: 19 operations  
**Target**: 60+ operations  
**Benefit**: Pinpoint exact bottlenecks within each operation

---

## 🔵 PARSE Phase - Detailed Implementation

### Current Operations (5)
1. parse_locate_file
2. parse_open_docx
3. parse_extract_text
4. parse_extract_metadata
5. parse_list_subjects

### Detailed Breakdown (15 operations)

#### 1. parse_locate_file → 3 sub-operations
```python
# In tools/docx_parser.py, parse_docx()

with tracker.track_operation(plan_id, "parse_validate_path"):
    file_path_obj = Path(file_path)

with tracker.track_operation(plan_id, "parse_check_exists"):
    if not file_path_obj.exists():
        raise FileNotFoundError(...)

with tracker.track_operation(plan_id, "parse_get_file_info"):
    file_size = file_path_obj.stat().st_size
    # Store file_size in metadata
```

#### 2. parse_open_docx → 4 sub-operations
```python
# In DOCXParser.__init__()

with tracker.track_operation(plan_id, "parse_load_docx_file"):
    self.doc = Document(str(self.file_path))

with tracker.track_operation(plan_id, "parse_read_paragraphs"):
    self.paragraphs = [p.text.strip() for p in self.doc.paragraphs if p.text.strip()]

with tracker.track_operation(plan_id, "parse_read_tables"):
    self.tables = self._extract_tables()

with tracker.track_operation(plan_id, "parse_count_elements"):
    para_count = len(self.paragraphs)
    table_count = len(self.tables)
```

#### 3. parse_extract_text → 3 sub-operations
```python
with tracker.track_operation(plan_id, "parse_get_paragraph_text"):
    para_text = '\n'.join(self.paragraphs)

with tracker.track_operation(plan_id, "parse_get_table_text"):
    table_text = self._extract_table_text()

with tracker.track_operation(plan_id, "parse_combine_text"):
    full_text = para_text + '\n' + table_text
```

#### 4. parse_extract_metadata → 3 sub-operations
```python
with tracker.track_operation(plan_id, "parse_get_core_properties"):
    core_props = self.doc.core_properties

with tracker.track_operation(plan_id, "parse_extract_week_info"):
    week_info = self.extract_week_info()

with tracker.track_operation(plan_id, "parse_build_metadata_dict"):
    metadata = {
        'title': core_props.title,
        'author': core_props.author,
        'week_info': week_info,
        ...
    }
```

#### 5. parse_list_subjects → 2 sub-operations
```python
with tracker.track_operation(plan_id, "parse_scan_for_subjects"):
    subjects = self._scan_content_for_subjects()

with tracker.track_operation(plan_id, "parse_validate_subjects"):
    valid_subjects = [s for s in subjects if self._is_valid_subject(s)]
```

**Total PARSE operations**: 5 → 15

---

## 🟠 PROCESS Phase - Detailed Implementation

### Current Operations (4)
1. llm_build_prompt
2. llm_api_call
3. llm_parse_response
4. llm_validate_structure

### Detailed Breakdown (20 operations)

#### 1. llm_build_prompt → 7 sub-operations
```python
# In backend/llm_service.py, _build_prompt()

with tracker.track_operation(plan_id, "llm_load_template"):
    prompt_template = self.prompt_template

with tracker.track_operation(plan_id, "llm_configure_grade"):
    grade_level = f"{grade}th grade" if grade.isdigit() else grade
    prompt = prompt_template.replace("[GRADE_LEVEL_VARIABLE = <SET BEFORE RUN>]", ...)

with tracker.track_operation(plan_id, "llm_build_metadata_context"):
    metadata_context = f"Week: {week_of}\nGrade: {grade}\n..."

with tracker.track_operation(plan_id, "llm_build_schema_example"):
    schema_example = self._build_schema_example(...)

with tracker.track_operation(plan_id, "llm_add_wida_context"):
    # Add WIDA framework context

with tracker.track_operation(plan_id, "llm_add_strategies"):
    # Add teaching strategies

with tracker.track_operation(plan_id, "llm_assemble_prompt"):
    full_prompt = prompt.replace("{{METADATA}}", metadata_context)
    # ... all replacements
```

#### 2. llm_api_call → 6 sub-operations
```python
# In backend/llm_service.py, _call_llm()

with tracker.track_operation(plan_id, "llm_count_prompt_tokens"):
    # Estimate or count tokens in prompt
    prompt_token_count = len(prompt.split()) * 1.3  # rough estimate

with tracker.track_operation(plan_id, "llm_prepare_request"):
    if self.provider == "openai":
        messages = [{"role": "user", "content": prompt}]

with tracker.track_operation(plan_id, "llm_network_call") as op:
    # THE ACTUAL API CALL
    response = self.client.chat.completions.create(
        model=self.model,
        messages=messages,
        max_completion_tokens=self.max_completion_tokens,
    )
    # This is where 90% of llm_api_call time is spent!

with tracker.track_operation(plan_id, "llm_extract_content"):
    content = response.choices[0].message.content

with tracker.track_operation(plan_id, "llm_extract_usage"):
    usage = {
        "tokens_input": response.usage.prompt_tokens,
        "tokens_output": response.usage.completion_tokens,
        "tokens_total": response.usage.total_tokens,
    }

with tracker.track_operation(plan_id, "llm_validate_response"):
    if not content:
        raise ValueError("Empty response")
```

#### 3. llm_parse_response → 4 sub-operations
```python
# In backend/llm_service.py, _parse_response()

with tracker.track_operation(plan_id, "llm_clean_response"):
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

with tracker.track_operation(plan_id, "llm_parse_json"):
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        needs_repair = True

with tracker.track_operation(plan_id, "llm_repair_json") if needs_repair:
    success, repaired, error = repair_json(cleaned)

with tracker.track_operation(plan_id, "llm_verify_parsed"):
    # Verify it's a dict with expected structure
```

#### 4. llm_validate_structure → 3 sub-operations
```python
# In backend/llm_service.py, _validate_structure()

with tracker.track_operation(plan_id, "llm_validate_root_keys"):
    required_keys = ["metadata", "days"]
    for key in required_keys:
        if key not in lesson_json:
            return False

with tracker.track_operation(plan_id, "llm_validate_days"):
    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    for day in days:
        if day not in lesson_json["days"]:
            return False

with tracker.track_operation(plan_id, "llm_validate_day_structure"):
    for day_name, day_data in lesson_json["days"].items():
        # Check each day has required fields
```

**Total PROCESS operations**: 4 → 20

---

## 🟢 RENDER Phase - Detailed Implementation

### Current Operations (7)
1. render_load_template
2. render_fill_metadata
3. render_fill_days
4. render_insert_images
5. render_restore_hyperlinks
6. render_normalize_tables
7. render_save_docx

### Detailed Breakdown (25 operations)

#### 1. render_load_template → 3 sub-operations
```python
# In tools/docx_renderer.py, render()

with tracker.track_operation(plan_id, "render_open_template_file"):
    doc = Document(self.template_path)

with tracker.track_operation(plan_id, "render_identify_tables"):
    metadata_table = doc.tables[self.METADATA_TABLE_IDX]
    daily_plans_table = doc.tables[self.DAILY_PLANS_TABLE_IDX]

with tracker.track_operation(plan_id, "render_cache_structure"):
    # Cache table references for faster access
```

#### 2. render_fill_metadata → 5 sub-operations
```python
with tracker.track_operation(plan_id, "render_fill_teacher_name"):
    if "teacher_name" in metadata:
        cell.text = f"Name: {metadata['teacher_name']}"

with tracker.track_operation(plan_id, "render_fill_grade"):
    cell.text = f"Grade: {metadata['grade']}"

with tracker.track_operation(plan_id, "render_fill_homeroom"):
    cell.text = f"Homeroom: {metadata['homeroom']}"

with tracker.track_operation(plan_id, "render_fill_subject"):
    cell.text = f"Subject: {metadata['subject']}"

with tracker.track_operation(plan_id, "render_fill_week"):
    cell.text = f"Week of: {metadata['week_of']}"
```

#### 3. render_fill_days → 5 sub-operations (one per day)
```python
for day_name in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
    with tracker.track_operation(plan_id, f"render_fill_{day_name}"):
        day_data = json_data["days"][day_name]
        self._fill_day(doc, day_name, day_data)
```

Or even more detailed (per field per day = 35 operations!):
```python
with tracker.track_operation(plan_id, "render_fill_monday_objective"):
    # Fill objective cell

with tracker.track_operation(plan_id, "render_fill_monday_instruction"):
    # Fill instruction cell

# ... etc for each field
```

#### 4. render_insert_images → 3 sub-operations
```python
if "_images" in json_data:
    with tracker.track_operation(plan_id, "render_decode_images"):
        decoded_images = [base64.b64decode(img["data"]) for img in json_data["_images"]]
    
    with tracker.track_operation(plan_id, "render_create_image_elements"):
        for img_data in decoded_images:
            # Create image element
    
    with tracker.track_operation(plan_id, "render_position_images"):
        # Add images to document
```

#### 5. render_restore_hyperlinks → 2 sub-operations
```python
if "_hyperlinks" in json_data:
    with tracker.track_operation(plan_id, "render_create_hyperlink_xml"):
        # Create XML elements for hyperlinks
    
    with tracker.track_operation(plan_id, "render_apply_hyperlink_styles"):
        # Apply blue, underlined styling
```

#### 6. render_normalize_tables → 3 sub-operations
```python
with tracker.track_operation(plan_id, "render_calculate_widths"):
    from tools.docx_utils import calculate_table_widths

with tracker.track_operation(plan_id, "render_apply_widths"):
    # Apply calculated widths to tables

with tracker.track_operation(plan_id, "render_verify_widths"):
    # Verify all tables have consistent widths
```

#### 7. render_save_docx → 4 sub-operations
```python
with tracker.track_operation(plan_id, "render_create_output_dir"):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

with tracker.track_operation(plan_id, "render_generate_filename"):
    # Ensure filename is valid

with tracker.track_operation(plan_id, "render_save_file"):
    doc.save(output_path)

with tracker.track_operation(plan_id, "render_verify_saved"):
    if not output_path.exists():
        raise IOError("File not saved")
```

**Total RENDER operations**: 7 → 25

---

## 📊 Summary

### Operation Count by Phase

| Phase | Current | Level 3 | Increase |
|-------|---------|---------|----------|
| PARSE | 5 | 15 | +10 (3x) |
| PROCESS | 4 | 20 | +16 (5x) |
| RENDER | 7 | 25 | +18 (3.6x) |
| **TOTAL** | **16** | **60** | **+44 (3.75x)** |

---

## 🚀 Implementation Order

### Phase 1: PROCESS Detail (Highest Priority)
**Why**: 60% of workflow time, biggest bottleneck  
**Operations**: 20  
**Time**: 2 hours  
**Impact**: HIGH - Will pinpoint LLM bottleneck

### Phase 2: RENDER Detail
**Why**: 27% of workflow time, second priority  
**Operations**: 25  
**Time**: 2 hours  
**Impact**: MEDIUM - Will identify table/formatting issues

### Phase 3: PARSE Detail
**Why**: 13% of workflow time, already fast  
**Operations**: 15  
**Time**: 1 hour  
**Impact**: LOW - Likely won't find major issues

### Phase 4: Dashboard Updates
**Why**: Need to handle 60+ operations in UI  
**Time**: 1 hour  
**Impact**: Required for visualization

---

## ⚠️ Considerations

### Performance Overhead
- 60 tracking points = ~60 database inserts per plan
- Estimated overhead: 50-100ms total (negligible)
- Context manager handles this efficiently

### Code Complexity
- ~500 lines of tracking code
- Increases maintenance burden
- Need to keep tracking updated as code changes

### Data Volume
- 60 operations × 30 plans = 1,800 database rows
- Still manageable, but consider cleanup strategy

---

## 💡 Recommended Approach

**Option A: Implement All Now** (4-6 hours)
- Complete visibility
- Maximum detail
- Significant time investment

**Option B: Implement PROCESS Only** (2 hours)
- Focus on the 60% bottleneck
- Highest ROI
- Can add more later if needed

**Option C: Implement Incrementally**
- Start with PROCESS (2 hours)
- Test and analyze
- Add RENDER if needed (2 hours)
- Add PARSE if needed (1 hour)

---

## 🎯 Next Steps

1. **Choose approach** (A, B, or C)
2. **Implement tracking code**
3. **Test with real workflow**
4. **Update dashboard** to handle new operations
5. **Analyze results**
6. **Optimize based on data**

---

**Status**: Ready for implementation  
**Estimated Total Time**: 4-6 hours for full implementation  
**Recommendation**: Start with PROCESS phase (Option B) for highest impact
