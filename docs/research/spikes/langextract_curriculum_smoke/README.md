# LangExtract curriculum smoke (research only)

Minimal **Lesson N** / **procedure** style extraction using `langextract` + **Gemini** (or key-compatible cloud model per upstream docs).

## Setup

```bash
pip install langextract
```

Set **`LANGEXTRACT_API_KEY`** (Gemini / AI Studio) in **repo-root** `.env` or the environment, per [upstream README](https://github.com/google/langextract#api-key-setup-for-cloud-models). The smoke script loads `.env` from the repository root automatically.

### One-time checklist: create and wire `LANGEXTRACT_API_KEY`

1. Open [Google AI Studio API keys](https://aistudio.google.com/apikey) and **Create API key** (pick or create a Cloud project if prompted). Copy the key once.
2. In **repo-root** `.env` (never commit), add:
   - `LANGEXTRACT_API_KEY=<your-key>`
   - Optional: `LANGEXTRACT_SMOKE_MODEL=gemini-2.5-flash` (this is already the script default).
3. `pip install langextract` in the environment you use for research spikes.
4. From repo root, run the smoke script (see below). Expect `extractions_total`, `grounded`, and `interval=` lines when the key is valid.
5. Optional: append stdout to `docs/research/repos/langextract_smoke_output.txt` and update Run H in [wave_2_evidence.md](../../repos/wave_2_evidence.md) after a successful live call.

Do not paste keys into issues, CI, or tracked markdown.

## Input sources

- **Default:** Built-in short paragraph (~90 characters) for quick checks.
- **Lesson-scale (recommended for Wave 2 follow-up):** Set **`LANGEXTRACT_SMOKE_INPUT_FILE`** to a UTF-8 text file. Paths are relative to the **repository root** unless absolute. Example:

```bash
set LANGEXTRACT_SMOKE_INPUT_FILE=docs/research/spikes/langextract_curriculum_smoke/fixtures/lesson_length_sample.txt
python docs/research/spikes/langextract_curriculum_smoke/smoke_extract.py
```

Keep spike inputs **bounded** (on the order of one lesson or a few thousand characters) unless you are explicitly testing upstream long-document behavior.

### Real lesson from `curriculum.db` (Wave 2 Run J)

Export **stripped** narrative + procedure text for one lesson row, then point `LANGEXTRACT_SMOKE_INPUT_FILE` at the file:

```bash
python docs/research/spikes/langextract_curriculum_smoke/export_lesson_text_from_db.py ^
  --unit-id Math_2_U1_15E1iQ_x --lesson-number 1 ^
  --out docs/research/spikes/langextract_curriculum_smoke/fixtures/g2_u1_lesson_01_from_db.txt
set LANGEXTRACT_SMOKE_INPUT_FILE=docs/research/spikes/langextract_curriculum_smoke/fixtures/g2_u1_lesson_01_from_db.txt
python docs/research/spikes/langextract_curriculum_smoke/smoke_extract.py
```

Uses `CURRICULUM_DB_PATH` if set (default `data/curriculum.db`). Evidence: [wave_2_evidence.md](../../repos/wave_2_evidence.md) Run J.

## Run

```bash
python docs/research/spikes/langextract_curriculum_smoke/smoke_extract.py
```

On success, stdout ends with **`char_interval_verify_ok`**. Checks follow **LangExtract’s** `WordAligner` semantics ([alignment_status](https://github.com/google/langextract/blob/main/langextract/core/data.py)): `match_exact` rows must have `input_text[start:end] == extraction_text`; `match_lesser` / `match_fuzzy` rows only need a valid, non-empty in-range span (the library already aligned them). Rows **without** `alignment_status` (e.g. unit tests) use **whitespace-collapsed** equality so layout spacing does not fail the run.

Set **`LANGEXTRACT_SMOKE_REQUIRE_EXACT_ALIGNMENT=1`** to require every grounded extraction to be `match_exact` (stricter gate if you are tuning prompts).

**Offline unit tests** (no API key, no `langextract` package):

```bash
pytest tests/test_langextract_char_interval_verify.py
```

Without `LANGEXTRACT_API_KEY`, the script still prints **`input=`** and **`chars=`** (so file paths are validated), then exits **0** after a skip message.

## Model

Default `model_id` is `gemini-2.5-flash` (override with env `LANGEXTRACT_SMOKE_MODEL`). Align model lifecycle with Google’s docs before production use.
