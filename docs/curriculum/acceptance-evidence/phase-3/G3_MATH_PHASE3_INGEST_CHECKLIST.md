# Phase 3 — Grade 3 Math full corpus ingest checklist

**Registry SSOT:** [reference_docs/scraped_registry.json](../../../reference_docs/scraped_registry.json) → `Grade 3` → `Math`.

**Machine-readable corpus (unit ids, doc ids, titles):** [tools/db/g3_math_phase3_corpus.py](../../../tools/db/g3_math_phase3_corpus.py) — `G3_MATH_PHASE3_UNITS` and `G3_MATH_PHASE3_REGISTRY_EXCLUSIONS`.

**Batch driver (export + ingest + optional verify after each unit):**

```text
python tools/db/ingest_g3_math_phase3_corpus.py
```

Single unit:

```text
python tools/db/ingest_g3_math_phase3_corpus.py --unit-id Math_3_U6_1VozISaY
```

Per-unit manual equivalent (same as batch): [tools/db/ingest_wave_unit.py](../../../tools/db/ingest_wave_unit.py).

## In scope — multi-lesson teacher guides

| Registry key | Google Doc id (file id) | Stable `units.id` | Unit # | Ingest report (fill on pass) | Verify gate |
|--------------|-------------------------|-------------------|--------|------------------------------|-------------|
| `Unit 1_Introducing_Multiplication` | `13jAzcMR9KqRj3P9rvgySxPWysPAGBh9GsftzT3sw8fg` | `Math_3_U1_13jAzcMR` | 1 | `ingest_reports/2026-03-27T00-42-36Z_1f8e40bf.json` (historical) | pass (session 2026-03-27) |
| `Unit 2_Area_and_Multiplication` | `1hBoK4uk0Z_GBEixY4wFHXtFi1gLOXarytFhKamftSOE` | `Math_3_U2_1hBoK4uk` | 2 | `ingest_reports/2026-03-27T00-36-54Z_593534ca.json` (historical) | pass (session 2026-03-27) |
| `Unit 3_Extending_Operations_to_Fractions` | `1W1IBU71bwuGpP3M3NTdQXQSH8Jx8fRKF-l9I4Rdo2B4` | `Math_3_U3_1W1IBU71` | 3 | `ingest_reports/2026-03-27T01-37-45Z_fa7edaef.json` | pass (session 2026-03-27) |
| `Unit 4_Relating_Multiplication_to_Division` | `1VUoecGCd8fLAarsUTOgOMktXUFhZjJm_97wuAdH6QMs` | `Math_3_U4_1VUoecGC` | 4 | `ingest_reports/2026-03-28T02-43-49Z_aecdb755.json` | pass |
| `Unit 5_Fractions_as_Number` | `1LEDv2I_UuMnUiEH44IxLSXOVb846UD1uqlMwnD-B1mg` | `Math_3_U5_1LEDv2I_` | 5 | `ingest_reports/2026-03-28T03-02-35Z_5af67cf1.json` | pass |
| `Unit 6_Measuring_Length_Time_Liquid_Volume_and_Weight` | `1VozISaYFa5MWb5AqDLYVQ0ynWpFJHc4HDZK3k2tYbHE` | `Math_3_U6_1VozISaY` | 6 | `ingest_reports/2026-03-28T02-35-30Z_6f11c05b.json` | pass |
| `Unit 7_Two-Dimensional_Shapes_and_Perimeter` | `1W0aGPyiUTW7ASQd-x2eGjwW_--e9G_GYil_3SrXrC_8` | `Math_3_U7_1W0aGPyi` | 7 | `ingest_reports/2026-03-28T02-37-20Z_71146a94.json` | pass |
| `Unit 8_Putting_It_All_Together` | `1gFC5KEGeuEw3QxQVQWgf6zKS3DnFrhMZVK5QtB_HFto` | `Math_3_U8_1gFC5KEG` | 8 | `ingest_reports/2026-03-28T02-40-10Z_c35638b9.json` | pass |

**Note:** Registry rows with `unknown` placeholder ids are superseded by the real Doc id in the same object; the corpus module uses the real id only.

**SSOT for these eight IM units:** Each teacher guide appears only under `Grade 3` → `Math` in the registry. Duplicate keys that had appeared under `Uncategorized_Grade` → `Math` or `Uncategorized_Grade` → `Uncategorized_Subject` for the same Doc ids were removed so there is a single authoritative path and no drift between copies.

## Explicit exclusions (documented; not Phase 3 full-ingest targets)

| Registry key | Rationale |
|--------------|-----------|
| `Grade_3_Benchmark_2_Blueprint` | Benchmark blueprint, not a lesson guide corpus row. |
| `Grade_3_Benchmark_3_Blueprint` | Same. |
| `Grade_3_Benchmark_4_Blueprint` | Same. |
| `Grade_3_Mathematics_Curriculum_Guide` | Program guide, not a per-unit `ingest_to_curriculum` tab. |

## Quality gate (after each ingest)

From repo root:

```text
python tools/scraper/verify_curriculum_db.py --ingest-report ingest_reports/<run_id>.json
```

Use the path printed at end of ingest (`Ingest report written: ...`) or the newest file under `ingest_reports/` after a run.

## Regression sampling (Phase 3 policy)

After shared parser / `SubjectConfig` changes affecting Math:

1. **Non–Grade-3 Math:** ingest one Grade 2 Math unit (example from registry: `Grade 2` → `Math` → `Unit 1_Adding_Subtracting_and_Working_With_Data`, Doc id `15E1iQ_xlIaAes5NPDAdkNRm4-0eYV7PwQ6nOlOnjSnU`, suggested `units.id` `Math_2_U1_15E1iQ_x`).

**Grade 2 Math — full registry-backed corpus (units 1–9):** [tools/db/g2_math_corpus.py](../../../tools/db/g2_math_corpus.py) (`G2_MATH_UNITS`). Doc ids match the district hub **Grade 2 Mathematics Curriculum Guide** (`1Wb_ty4UKX6uWOuSP71yFxkuC5XOyCp6l1pKdEN5HQfw`) in `scraped_registry.json` → `Grade 2` → `Math`.

**Do not confuse with ELA:** `1Du6ukeZavMKEZt0nCzamwd7OfH4Jr-Liygqdwo2gjak` (*Copy of 02 - Second Grade Unit Description…*) is **Grade 2 ELA** (registry: `Grade 2` → `Uncategorized_Subject`). It is **not** an Illustrative Mathematics teacher guide. Grade 2 Math units use separate Doc ids under `Grade 2` → `Math` (e.g. Unit 1 → `15E1iQ_xlIaAes5NPDAdkNRm4-0eYV7PwQ6nOlOnjSnU`).

- Batch ingest (Drive export + DB, verify after each unit): `python tools/db/ingest_g2_math_corpus.py`
- Scrape all unit trees then ingest + verify: `powershell -File tools/scraper/grade2_math_scrape_and_ingest.ps1`

**Full reference scrape + DB ingest (refresh):** Re-downloads the unit tree (HTML/DOCX/JSON, linked resources) then re-runs `ingest_wave_unit` against a fresh Drive DOCX export.

- OAuth lives under `tools/scraper/credentials/`. If `token.json` refresh fails (`invalid_grant`), delete `token.json` and run the scrape step again to complete the browser consent flow.
- Unit 1 only (PowerShell): `powershell -File tools/scraper/grade2_math_unit1_scrape_and_ingest.ps1`
- All corpus units (PowerShell): `powershell -File tools/scraper/grade2_math_scrape_and_ingest.ps1`
- Manual scrape (repo root):

```text
python -m tools.scraper.main 15E1iQ_xlIaAes5NPDAdkNRm4-0eYV7PwQ6nOlOnjSnU --depth 4 --out reference_docs/scraped --force
```

- Ingest only (same as below), or after manual **File → Download → DOCX** from Google Docs: add `--docx path\to\unit.docx` to skip Drive export.

```text
python tools/db/ingest_wave_unit.py --unit-id Math_2_U1_15E1iQ_x --grade 2 --subject Math --unit-number 1 --title "Grade 2 Unit 1: Adding, Subtracting and Working With Data" --doc-id 15E1iQ_xlIaAes5NPDAdkNRm4-0eYV7PwQ6nOlOnjSnU
python tools/scraper/verify_curriculum_db.py
```

Optional: `verify_curriculum_db.py --ingest-report ingest_reports/<run_id>.json` when a batch run produced a report (`ingest_wave_unit.py` does not write one).

2. **ELA:** `verify_curriculum_db.py` data checks already probe a Grade 3 ELA unit when present; optional re-ingest: [tools/db/reingest_grade3_ela_sample.py](../../../tools/db/reingest_grade3_ela_sample.py) with operator-supplied DOCX.

## Session log (2026-03-27)

- Added corpus module (`tools/db/g3_math_phase3_corpus.py`), batch driver (`tools/db/ingest_g3_math_phase3_corpus.py`), and this checklist.
- Units 1–3 were already in `curriculum.db` (21 / 15 / 20 lessons).
- **Unit 4** added to `Grade 3` → `Math` in `scraped_registry.json`, corpus, and this table; ingested (`ingest_reports/2026-03-28T02-43-49Z_aecdb755.json`, 22 lessons) with verify pass.
- Units 5–8 ingested with `ingest_wave_unit.py` + verify; lesson counts: U5=18, U6=16, U7=15, U8=15.
- **Unit 5** restored to `G3_MATH_PHASE3_UNITS` and this checklist (batch driver includes it again).
- **Regression:** Grade 2 Math `Math_2_U1_15E1iQ_x` (`ingest_reports/2026-03-28T02-40-23Z_30d51100.json`) + verify pass; ELA `tests/test_grade3_ela_ingest_smoke.py` pass against `data/curriculum.db`.
- **Parser gaps:** none required for these runs (no code changes).
