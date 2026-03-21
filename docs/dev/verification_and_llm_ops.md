# Strategy pack verification and LLM operations

## SSOT drift check

From the repository root:

```bash
python tools/verify_strategy_pack_ssot.py
```

This compares `strategies_pack_v2/_index.json` and `wida/wida_strategy_enhancements.json` to the authoritative `strategies[].id` values in the six category JSON files. The same check runs in CI (`.github/workflows/ci-integration-tests.yml`) and via `tests/test_strategy_pack_ssot.py`.

## Pytest: CI-parity vs full suite

GitHub Actions runs a **subset** of tests (see workflow `Run unit-marked critical path tests`). Critical-path modules carry `pytestmark = pytest.mark.unit`. Approximate CI locally:

```bash
python -m pytest tests/ -m unit -v --tb=short
```

The **Postgres** job runs `tests/test_integration_authorization.py` plus `tests/test_authorization.py` only; the **SQLite** job runs the same integration file and then `pytest tests/ -m unit` (see comments in `.github/workflows/ci-integration-tests.yml`).

A full `pytest tests/` run may include tests that expect a specific environment, optional backends, or stricter schema behavior. Use the full suite when you are ready to triage failures in your checkout.

**Green slice (no live processing, exclude `e2e` marker):**

```bash
python -m pytest tests/ --ignore=tests/test_actual_processing.py -m "not e2e" -q
```

Known skips and optional gates are summarized in [test_suite_status.md](test_suite_status.md).

### Optional live API tests (off by default)

| Variable | Effect |
|----------|--------|
| `RUN_ACTUAL_PROCESSING=1` | Enables `tests/test_actual_processing.py` (batch + live processing). |
| `RUN_STRUCTURED_OUTPUTS_API=1` | Enables `tests/test_structured_outputs.py::test_integration_with_real_api` (live OpenAI transform; slow, uses quota). Requires `OPENAI_API_KEY` or `LLM_API_KEY`. |
| `RUN_LLM_GOLDEN=1` | Enables `tests/test_llm_golden.py` (all `tests/fixtures/llm_golden/*.json`; `ell_support[].strategy_id` checks against the strategy pack; no API calls). |

## Legacy strategy id grep policy

For **living** sources, `peer_tutoring_bilingual` and `dual_language_instruction` should appear only where intentional:

- `backend/llm/domain_analysis.py` — `LEGACY_ALIASES`
- `tests/test_wida_domain_selection.py` — legacy alias coverage
- `wida/README.md`, `docs/archive/test-files/README.md` — documentation of retired ids
- `docs/archive/test-files/*.json` — frozen historical samples

## Smoke generation (manual)

After changing prompts or pack injection:

1. Run one transform with a real provider (desktop app or API) on a small DOCX or fixture-derived content.
2. Confirm `tailored_instruction.ell_support[].strategy_id` values match pack ids from `strategies_pack_v2/_index.json`.
3. Optionally force an invalid id in a dev-only harness and confirm logs show `ell_support_strategy_id_invalid` and a retry with validation feedback in `transform_runner`.

## Observability (log search)

Useful structured log / event names when debugging transforms:

- `strategy_pack_injection_built` — injected context size and category selection (`backend/llm/strategy_pack_context.py`)
- `ell_support_strategy_id_invalid` — unknown ids after alias resolution (`backend/llm/transform_runner.py`)
- `llm_validation_failed_retry` / `llm_retry_attempt` — schema or post-parse validation retries (includes structured `grade` / `subject` where applicable)
- `llm_response_near_limit` / `increasing_max_tokens_for_retry` — output length pressure

## Prometheus metrics (LLM)

Export includes `llm_ell_support_strategy_id_invalid_total`, `llm_transform_retry_total`, and histogram `llm_strategy_pack_injection_chars` (see `backend/metrics.py`). Counters are incremented from `transform_runner` on invalid strategy ids or parse/validation retries; injection length is observed from `strategy_pack_context.build_strategy_pack_injection_block`.

## Token budget tuning

Pack injection size is capped in `backend/llm/strategy_pack_context.py` (`_MAX_INJECTION_CHARS`) and by how many categories/strategies are selected. Adjust there if prompts are too large for the model context or if you need more grounding (tradeoff: latency and cost).
