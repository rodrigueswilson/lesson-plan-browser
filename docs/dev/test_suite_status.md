# Test suite status

## Default local run (CI-parity scope)

Heavy or environment-specific tests are skipped via `pytest.mark.skip`, class-level `SkipTest`, or `-m` filters. For a **green** full collection (no live batch job, no `e2e` marker):

```bash
python -m pytest tests/ --ignore=tests/test_actual_processing.py -m "not e2e" -q
```

Documented optional gates: `RUN_ACTUAL_PROCESSING`, `RUN_STRUCTURED_OUTPUTS_API` (see [verification_and_llm_ops.md](verification_and_llm_ops.md)).

## Skipped / deferred tests (intentional)

| Area | Notes |
|------|--------|
| `tests/test_hyperlink_workflow_e2e.py` | Entire class skips unless the district template exists at `input/Lesson Plan Template SY'25-26.docx` **and** `HYPERLINK_E2E_INPUT` is set to an absolute path of a hyperlink-bearing lesson `.docx`. CI omits the env var; run locally when validating placement. Tests 05–07 run whenever the class is not skipped. |
| `tests/test_actual_processing.py` | Ignored in the command above; enable with `RUN_ACTUAL_PROCESSING=1`. |

## Fast unit slice (`pytest -m unit`)

Modules on the CI critical path are marked `unit` for a single-command run (see [.github/workflows/ci-integration-tests.yml](../../.github/workflows/ci-integration-tests.yml) and [verification_and_llm_ops.md](verification_and_llm_ops.md)):

```bash
python -m pytest tests/ -m unit -q
```

## LLM golden JSON (optional)

Frozen `ell_support` strategy ids and strings (no API calls):

```bash
set RUN_LLM_GOLDEN=1
python -m pytest tests/test_llm_golden.py -v
```

Fixtures under `tests/fixtures/llm_golden/` (see `tests/test_llm_golden.py` for the file list).

## Prometheus (LLM hot path)

Counters and histograms registered in `backend/metrics.py`:

- `llm_ell_support_strategy_id_invalid_total`
- `llm_transform_retry_total` (label `reason`: `json_parse`, `validation`)
- `llm_strategy_pack_injection_chars` (histogram: character length of injected strategy-pack context after build/truncation)

Wired in `backend/llm/transform_runner.py` and `backend/llm/strategy_pack_context.py` alongside existing log events (`ell_support_strategy_id_invalid`, `llm_retry_attempt`, etc.).
