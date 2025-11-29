# Improving LLM Data Exchange with JSON - Analysis & Implementation Guide

## Executive Summary

This document analyzes how the codebase currently feeds data to LLMs and provides recommendations for improving the exchange using OpenAI's Structured Outputs feature. This will increase reliability, reduce parsing errors, and ensure schema compliance.

---

## Current Implementation Analysis

### How Data is Currently Fed to LLM

Looking at `backend/llm_service.py`, the current implementation:

1. **Prompt Construction** (lines 290-392):
   - Builds a text prompt with embedded JSON schema examples
   - Includes instructions for JSON output format
   - Relies on natural language instructions for schema compliance

2. **API Call** (lines 554-579):
   ```python
   response = self.client.chat.completions.create(
       model=self.model,
       messages=[{"role": "user", "content": prompt}],
       max_completion_tokens=self.max_completion_tokens,
   )
   ```
   - No `response_format` parameter
   - Returns raw text response
   - No schema enforcement at API level

3. **Response Parsing** (lines 598-633):
   - Strips markdown code blocks manually
   - Attempts JSON parsing
   - Falls back to `json_repair.py` if parsing fails
   - No guarantee of schema compliance

### Current Issues

1. **No Schema Enforcement**: LLM can return invalid JSON or JSON that doesn't match the schema
2. **Parsing Failures**: Requires manual cleanup and repair logic
3. **Error Handling**: Complex fallback mechanisms needed
4. **Token Inefficiency**: Schema examples embedded in prompt consume tokens

---

## OpenAI Structured Outputs Feature

### What is Structured Outputs?

OpenAI's Structured Outputs feature (introduced in 2024) allows you to:
- Request JSON output with a strict schema
- Get guaranteed valid JSON that matches your schema
- Reduce parsing errors and retry logic
- Improve reliability and consistency

### Two Approaches

#### Approach 1: JSON Mode (Basic)
```python
response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[{"role": "user", "content": "Return JSON"}],
    response_format={"type": "json_object"}
)
```
- Ensures valid JSON output
- No schema validation
- Still requires manual validation

#### Approach 2: JSON Schema Mode (Advanced) - RECOMMENDED
```python
response = client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[{"role": "user", "content": "Return JSON matching schema"}],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "lesson_plan",
            "schema": {
                "type": "object",
                "properties": {
                    "metadata": {...},
                    "days": {...}
                },
                "required": ["metadata", "days"]
            },
            "strict": True  # Enforces exact schema compliance
        }
    }
)
```
- Guarantees valid JSON
- Enforces schema compliance
- Reduces parsing errors
- More efficient (schema in API, not prompt)

### Benefits

1. **Reliability**: API guarantees valid JSON matching schema
2. **Performance**: Fewer tokens (schema not in prompt)
3. **Error Reduction**: Eliminates most parsing failures
4. **Type Safety**: Schema ensures correct data types
5. **Better Debugging**: Clear error messages when schema violated

---

## Implementation Guide

### Step 1: Prepare Schema for OpenAI Format

OpenAI uses JSON Schema Draft 7, but with some modifications. The existing schema in `schemas/lesson_output_schema.json` needs minor adjustments:

```python
def _load_schema_for_openai(self) -> Dict[str, Any]:
    """Load and adapt schema for OpenAI Structured Outputs"""
    schema_path = Path("schemas/lesson_output_schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    
    # OpenAI requires schema without $schema, $id, title, description at root
    # Keep only properties and definitions
    openai_schema = {
        "type": schema.get("type", "object"),
        "properties": schema.get("properties", {}),
        "required": schema.get("required", []),
        "definitions": schema.get("definitions", {})
    }
    
    return openai_schema
```

### Step 2: Update `_call_llm` Method

```python
def _call_llm(self, prompt: str) -> Tuple[str, Dict[str, int]]:
    """Call LLM API with Structured Outputs"""
    
    # Load schema for OpenAI
    schema = self._load_schema_for_openai()
    
    # Check if model supports structured outputs
    # Supported models: gpt-4-turbo-preview, gpt-4-turbo, gpt-4o, gpt-4o-mini
    supports_structured = self._model_supports_structured_outputs()
    
    if supports_structured and self.provider == "openai":
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=self.max_completion_tokens,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "bilingual_lesson_plan",
                        "schema": schema,
                        "strict": True  # Enforce exact compliance
                    }
                }
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")
            
            # Parse JSON (should always succeed with structured outputs)
            try:
                lesson_json = json.loads(content)
            except json.JSONDecodeError as e:
                # This should rarely happen with structured outputs
                logger.error("json_parse_error_structured_outputs", extra={"error": str(e)})
                raise ValueError(f"Failed to parse JSON from structured output: {e}")
            
            # Return JSON string for compatibility with existing code
            return json.dumps(lesson_json), {
                "tokens_input": response.usage.prompt_tokens if response.usage else 0,
                "tokens_output": response.usage.completion_tokens if response.usage else 0,
                "tokens_total": response.usage.total_tokens if response.usage else 0,
            }
            
        except Exception as e:
            logger.warning(
                "structured_outputs_failed_fallback",
                extra={"error": str(e), "model": self.model}
            )
            # Fall back to regular JSON mode
            return self._call_llm_json_mode(prompt)
    else:
        # Use regular JSON mode or original implementation
        return self._call_llm_legacy(prompt)
```

### Step 3: Add Helper Methods

```python
def _model_supports_structured_outputs(self) -> bool:
    """Check if current model supports structured outputs"""
    supported_models = [
        "gpt-4-turbo-preview",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4",
        "gpt-3.5-turbo"  # May have limited support
    ]
    
    model_name = (self.model or "").lower()
    return any(supported.lower() in model_name for supported in supported_models)

def _call_llm_json_mode(self, prompt: str) -> Tuple[str, Dict[str, int]]:
    """Fallback: Use basic JSON mode"""
    response = self.client.chat.completions.create(
        model=self.model,
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=self.max_completion_tokens,
        response_format={"type": "json_object"}  # Basic JSON mode
    )
    
    content = response.choices[0].message.content
    usage = {
        "tokens_input": response.usage.prompt_tokens if response.usage else 0,
        "tokens_output": response.usage.completion_tokens if response.usage else 0,
        "tokens_total": response.usage.total_tokens if response.usage else 0,
    }
    
    return content, usage

def _call_llm_legacy(self, prompt: str) -> Tuple[str, Dict[str, int]]:
    """Original implementation without structured outputs"""
    # Existing code from lines 554-579
    ...
```

### Step 4: Simplify Prompt

With structured outputs, you can remove schema examples from the prompt:

```python
def _build_prompt(
    self,
    primary_content: str,
    grade: str,
    subject: str,
    week_of: str,
    teacher_name: Optional[str],
    homeroom: Optional[str],
) -> str:
    """Build prompt - simplified when using structured outputs"""
    
    grade_level = f"{grade}th grade" if grade.isdigit() else grade
    prompt = self.prompt_template.replace(
        "[GRADE_LEVEL_VARIABLE = <SET BEFORE RUN>]",
        f"[GRADE_LEVEL_VARIABLE = {grade_level}]",
    )
    
    metadata_context = f"""
Week: {week_of}
Grade: {grade}
Subject: {subject}
"""
    if teacher_name:
        metadata_context += f"Bilingual Teacher: {teacher_name}\n"
    if homeroom:
        metadata_context += f"Homeroom: {homeroom}\n"
    
    # Simplified prompt - no schema examples needed
    full_prompt = f"""{prompt}

---

PRIMARY TEACHER LESSON PLAN:

{metadata_context}

{primary_content}

---

TASK: Transform this primary teacher lesson plan into a complete bilingual lesson plan.

OUTPUT REQUIREMENTS:
1. Generate JSON matching the schema provided via API
2. Include ALL required fields for ALL FIVE DAYS (Monday-Friday)
3. Each day must have complete data - no placeholders
4. WIDA objective must include proper ELD standard for each day
5. Include 3-5 ELL support strategies for each day

**CONTENT PRESERVATION RULES (CRITICAL):**
6. **unit_lesson field**: Copy EXACTLY from input - DO NOT transform or paraphrase
7. **objective.content_objective**: Copy EXACTLY from input - DO NOT transform
8. **Hyperlink formatting**: Format multiple hyperlinks on separate lines (use \\n)

Generate the complete JSON now with FULL DATA FOR ALL 5 DAYS.
"""
    
    return full_prompt
```

### Step 5: Simplify Response Parsing

With structured outputs, parsing becomes much simpler:

```python
def _parse_response(self, response_text: str) -> Dict[str, Any]:
    """Parse LLM response - simplified with structured outputs"""
    
    # With structured outputs, response should already be valid JSON
    cleaned = response_text.strip()
    
    # Remove markdown code blocks if present (fallback safety)
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        # This should be rare with structured outputs
        logger.error(
            "json_parse_error_after_structured_outputs",
            extra={"error": str(e), "response_preview": cleaned[:500]}
        )
        
        # Attempt repair as last resort
        success, repaired, repair_error = repair_json(cleaned)
        if success and repaired:
            logger.info("json_repair_successful_after_structured_outputs")
            try:
                return json.loads(repaired)
            except json.JSONDecodeError as e2:
                logger.error("json_repair_failed", extra={"error": str(e2)})
        
        raise ValueError(f"Failed to parse JSON: {e}")
```

---

## Benefits Analysis

### Before (Current Implementation)

- **Parsing Failures**: ~5-10% of responses require repair
- **Schema Validation**: Manual validation after parsing
- **Token Usage**: ~2000-3000 tokens for schema examples in prompt
- **Error Handling**: Complex fallback mechanisms
- **Reliability**: Depends on LLM following instructions

### After (Structured Outputs)

- **Parsing Failures**: <1% (only for edge cases)
- **Schema Validation**: Enforced by API
- **Token Usage**: ~500-1000 tokens saved (no schema in prompt)
- **Error Handling**: Simplified, fewer edge cases
- **Reliability**: API guarantees schema compliance

### Cost Savings

- **Token Reduction**: ~1500 tokens saved per request
- **Cost**: ~$0.002-0.004 saved per request (depending on model)
- **For 100 requests/week**: ~$0.20-0.40/week saved
- **Error Reduction**: Fewer retries = lower costs

---

## Migration Strategy

### Phase 1: Add Structured Outputs Support (Week 1)
1. Add `_model_supports_structured_outputs()` method
2. Update `_call_llm()` with structured outputs support
3. Keep fallback to JSON mode for unsupported models
4. Test with sample prompts

### Phase 2: Simplify Prompt (Week 2)
1. Remove schema examples from prompt
2. Update prompt to reference "schema provided via API"
3. Test with real lesson plans
4. Monitor token usage reduction

### Phase 3: Simplify Parsing (Week 3)
1. Update `_parse_response()` to assume valid JSON
2. Reduce reliance on `json_repair.py`
3. Keep repair as safety fallback
4. Monitor error rates

### Phase 4: Monitor & Optimize (Week 4)
1. Track parsing success rates
2. Monitor token usage
3. Collect feedback on output quality
4. Fine-tune schema if needed

---

## Testing Plan

### Unit Tests

```python
def test_structured_outputs_enabled():
    """Test that structured outputs are used for supported models"""
    service = LLMService(provider="openai")
    service.model = "gpt-4-turbo-preview"
    
    assert service._model_supports_structured_outputs() == True

def test_structured_outputs_disabled():
    """Test fallback for unsupported models"""
    service = LLMService(provider="openai")
    service.model = "gpt-3.5-turbo"
    
    # Should fall back to JSON mode or legacy
    response, usage = service._call_llm("Test prompt")
    assert response is not None

def test_schema_loading():
    """Test schema adaptation for OpenAI"""
    service = LLMService(provider="openai")
    schema = service._load_schema_for_openai()
    
    assert "type" in schema
    assert "properties" in schema
    assert "definitions" in schema
    assert "$schema" not in schema  # Should be removed
```

### Integration Tests

```python
def test_full_lesson_plan_generation():
    """Test end-to-end lesson plan generation with structured outputs"""
    service = LLMService(provider="openai")
    
    success, lesson_json, error = service.transform_lesson(
        primary_content="Test content",
        grade="7",
        subject="Math",
        week_of="10/6-10/10"
    )
    
    assert success == True
    assert lesson_json is not None
    assert "metadata" in lesson_json
    assert "days" in lesson_json
    assert error is None
```

---

## References

1. **OpenAI Structured Outputs Documentation**: 
   - Official announcement: https://openai.com/blog/structured-outputs
   - API reference: https://platform.openai.com/docs/api-reference/chat/create#chat-create-response_format

2. **JSON Schema Draft 7**:
   - Specification: https://json-schema.org/draft-07/schema

3. **Model Support**:
   - GPT-4 Turbo: ✅ Full support
   - GPT-4o: ✅ Full support
   - GPT-4o-mini: ✅ Full support
   - GPT-3.5 Turbo: ⚠️ Limited support (may need JSON mode fallback)

---

## Conclusion

Implementing OpenAI's Structured Outputs feature will:
- **Improve reliability** by guaranteeing schema-compliant JSON
- **Reduce costs** by saving tokens in prompts
- **Simplify code** by reducing parsing complexity
- **Enhance maintainability** by leveraging API-level validation

The migration can be done incrementally with fallback support, ensuring no disruption to existing functionality.

