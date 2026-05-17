# Instructor curriculum smoke (research only)

Bounded check for **Wave 1 backlog item (1)**: show that a **lesson-shaped Pydantic model** plus Instructor can extract fields from a short fixture resembling flattened curriculum text.

**Not production code.** Do not import from `tools/scraper` here; a future integration should go through [backend/llm](../../../backend/llm) patterns and preserve A4 SSOT per [CURRICULUM_EXTRACTION_ARCHITECTURE.md](../../scrapers/CURRICULUM_EXTRACTION_ARCHITECTURE.md).

## Setup

From repository root (optional venv):

```bash
pip install instructor openai pydantic
```

Keys: prefer `OPENAI_API_KEY_TESTS` (or `GPT5_API_KEY_TESTS` when `INSTRUCTOR_SMOKE_MODEL` is `gpt-5*`) so lesson generation keeps using `OPENAI_API_KEY` / `GPT5_API_KEY`. If unset, falls back to those production env vars (see `backend.llm.api_key.get_openai_api_key_for_tests`).

## Run

```bash
python docs/research/spikes/instructor_curriculum_smoke/smoke_lesson_extract.py
```

Without a key, the script exits **0** after printing a skip message (CI-friendly).

With a key, it calls a small model (default `gpt-4o-mini`) and prints JSON for `LessonExtractStub`.

## Next

If output quality is acceptable on real excerpts, open a sprint task to add an **optional second pass** behind a flag in the scraper/ingest path, reusing centralized LLM configuration.
