# Instructor library vs LP `transform_runner` (Wave 2)

**Purpose:** Record how upstream **567-labs/instructor** relates to LP’s lesson transform loop, without duplicating Pass 1 bullets in [wave_1_pass1_notes.md](wave_1_pass1_notes.md).

## Where LP uses Instructor

- [backend/llm/providers.py](../../../backend/llm/providers.py) — `call_instructor_chat_completion` calls `instructor_client.chat.completions.create_with_completion` (OpenAI) with `response_model=BilingualLessonPlanOutputSchema` and passes **`max_retries`** into the Instructor client.
- [backend/llm/transform_runner.py](../../../backend/llm/transform_runner.py) — For OpenAI with `service.instructor_client`, the **first attempt** uses the Instructor path. If **domain validation** fails (`validate_structure`, ELL strategy IDs), LP sets `skip_instructor_path = True` and continues with the **legacy** `parse_llm_response` path and **`_build_retry_prompt`** feedback loop. Exceptions from Instructor fall through to the same legacy path.

## What Instructor provides (upstream pattern)

- **Pydantic `response_model`:** Parses model output into a typed object; **reask / retry** inside the patched client when the model returns content that does not validate against the schema (provider-specific handlers; see clone `instructor/providers/*/`, tests such as `test_retry_json_mode.py`).
- **Optional hooks:** Validators, multimodal paths, and provider adapters beyond what LP uses today.

## What LP adds on top

- **Lesson-specific validation** after Instructor returns: `validate_structure`, `validate_ell_support_strategy_ids`, truncation handling (`max_completion_tokens` bump), and **retry prompts** that embed validation errors for the non-Instructor completion path.
- **Operational split:** Rate-limit retries are configured via app settings and passed into Instructor’s `max_retries`; the outer `while retry_count <= max_retries` loop in `transform_runner` coordinates **parse errors**, **validation failures**, and **token limits** across both paths.

## Conclusion (Wave 2)

- **Not redundant:** LP already **depends on Instructor** for the primary OpenAI structured lesson output. The research spike ([instructor_curriculum_smoke](../spikes/instructor_curriculum_smoke/README.md)) validates the same **small Pydantic model** pattern for **curriculum-shaped** excerpts outside the main lesson schema.
- **Further dependency depth** (e.g. more `instructor` validators or hooks in scraper second-pass) should be justified per issue with field ownership and failure policy ([runbooks/05_research_to_product_backlog.md](../runbooks/05_research_to_product_backlog.md)).
