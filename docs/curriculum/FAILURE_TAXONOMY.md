# Failure taxonomy (ingest and adaptation)

**Purpose:** Single source of truth for machine-readable failure codes used in ingest reports, empirical profiling rows, and (optionally) adaptation alerts.

**Related:**

- `docs/curriculum/SAMPLE_MATRIX_AND_ADAPTATION_ALERTS.md` — wave execution and alert payload shape
- `docs/curriculum/QUALITY_GATES.md` — outcome labeling
- `tools/scraper/ingest_failure_codes.py` — code enum + `apply_ingest_failure_code` (keep in sync with this doc)
- `tools/scraper/table_extractor.py` — `_build_ingest_report` JSON under `ingest_reports/`
- `docs/curriculum/research-notes/2026-03-27-blind-spots-and-empirical-research-plan.md` — empirical methodology

---

## Rules

1. Every **Yellow** or **Red** unit should record **at least one** primary code when the failure is understood; use `UNKNOWN` only when triage is incomplete.
2. Optionally record **secondary** codes in `secondary_failure_codes` when multiple independent issues apply.
3. **Cap** the share of `UNKNOWN` over total classified failures; if it stays high, narrow the taxonomy or improve instrumentation—not silent overflow.
4. Prefer these codes in JSON fields:
   - `primary_failure_code` — string or `null` (no primary classification yet)
   - `secondary_failure_codes` — array of strings (empty when none)

Adaptation alert payloads may use `category` aligned with the same code strings below (instead of ad-hoc prose slugs).

---

## Codes (v0)

Edit this table only after an empirical pass; bump version note in git message when changing codes.

| Code | Meaning | Typical next action |
|------|---------|---------------------|
| `ANCHOR_MISS` | Expected `SubjectConfig` anchor not matched | Extend anchors or add archetype |
| `TABLE_GRID` | Non-rectangular table or merge/grid breaks parser assumptions | Table handler + tests |
| `BOUNDARY_LEAK` | Content routed wrong (e.g. procedure text in standards) | Guards in mapping / flush logic |
| `EXPORT_LOSS` | Structural mismatch between export (DOCX) and Docs JSON (or similar) | Export–parser protocol (research plan Part D) |
| `LINK_SKIP` | Linked resource not exportable or not ingested | Inventory / manual path |
| `SCHEMA_GATE` | Post-verifier or DB validation failure (`verify_curriculum_db`, schema checks) | Ingest mapping or DB rules |
| `EMPTY_FIELD` | Required lesson or unit field empty after ingest | Trace upstream to a row above |
| `UNKNOWN` | Not yet classified | Triage; do not leave as terminal state for waves |

### Reserved / future

Add new codes here after Wave profiling shows a repeated class not covered above (keep the set small: target roughly 8–12 active codes).

---

## Ingest report fragment (example)

```json
{
  "primary_failure_code": "BOUNDARY_LEAK",
  "secondary_failure_codes": ["ANCHOR_MISS"]
}
```

When ingest completes successfully with no classification step yet, reports use `primary_failure_code: null` and `secondary_failure_codes: []`.

---

## Automation (tooling)

- **`tools/scraper/table_extractor.py`:** Every ingest report includes `ingest_stats` (lessons started, paragraphs appended, section hit counts). If zero lessons were persisted and no lesson titles matched the subject pattern, the report is tagged `ANCHOR_MISS`. If the stream started lessons but none were persistable, it is tagged `EMPTY_FIELD`.
- **`tools/scraper/table_extractor.py`:** Ingest also flags likely equation-token loss in standards text (placeholder patterns where math symbols are missing) and adds `EXPORT_LOSS`.
- **`python tools/scraper/verify_curriculum_db.py --ingest-report PATH`:** If verification fails, the given report JSON is updated in place: each issue line is appended to `warnings` and mapped to a code via `failure_code_for_data_integrity_issue` (data checks) or `SCHEMA_GATE` (schema validation or second-template smoke failures).

Pass the **same** `ingest_reports/<run_id>.json` produced by the ingest you are validating so codes attach to the correct run.
