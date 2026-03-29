# Sample Matrix and Adaptation Alerts

**Purpose:** Define exactly which units to ingest first, in what order, and how the system reports when parser logic is insufficient for a file pattern.

**Related:**
- `docs/curriculum/PHASED_ROLLOUT_PLAN.md`
- `docs/curriculum/QUALITY_GATES.md`
- `docs/curriculum/TEST_PROTOCOL_UNIT_ACCEPTANCE.md`
- `docs/curriculum/FAILURE_TAXONOMY.md` (SSOT for ingest/adaptation failure codes)

---

## 1) Rollout matrix (what to extract first)

Use this matrix as execution SSOT for staged hardening.

| Wave | Priority | Grade | Subject | Unit label (registry) | Source doc id | Why selected | Target outcome |
|---|---:|---:|---|---|---|---|---|
| W1 | 1 | 3 | Math | `Unit 2_Area_and_Multiplication` | `1hBoK4uk0Z_GBEixY4wFHXtFi1gLOXarytFhKamftSOE` | Current anchor unit + known parser work | First Unit-Complete baseline |
| W1 | 2 | 3 | Math | `Unit 1_Introducing_Multiplication` | `13jAzcMR9KqRj3P9rvgySxPWysPAGBh9GsftzT3sw8fg` | Same grade/subject, different structure | Same-subject resilience |
| W1 | 3 | 3 | Math | `Unit 3_Extending_Operations_to_Fractions` | `1W1IBU71bwuGpP3M3NTdQXQSH8Jx8fRKF-l9I4Rdo2B4` | Fractions language + standards variance | Boundary and standards robustness |
| W1 | 4 | 3 | Math | `Unit 7_Two-Dimensional_Shapes_and_Perimeter` | `1W0aGPyiUTW7ASQd-x2eGjwW_--e9G_GYil_3SrXrC_8` | Geometry/perimeter heading variance | Topic variance in same subject |
| W2 | 5 | 2 | Math | `Unit 6_Geometry_Time_and_Money` | `1Sc97mZeXhUqDjDXsLcMW77JyCYiqHlTrAqjwvDSOcBA` | Vertical geometry link precursor (G2->G3) | Cross-grade math sanity |
| W2 | 6 | 1 | Math | `Unit 7_Geometry_and_Time` | `1tgtrwHXKAP-sgNOAdi5-3yu2hvbWRTg5mpck-L1I4OU` | Earlier-grade template variation | Lower-grade template validation |
| W3 | 7 | 3 | ELA | `Grade_3_Unit_10_-_Charlottes_Web` | `1Mn99HCsUm19VGyivXTmgJMu8u0WYclb4j9DRWRVdv2s` | First ELA unit contrast | Phase 4 ELA hardening start |
| W3 | 8 | 3 | ELA | Inventory-selected second full ELA unit | `TBD (from PHASE1 inventory)` | Confirm ELA variance not overfit to one unit | ELA pattern confidence |
| W4 | 9 | 4-5 | Math + ELA | One full unit each grade/subject | `TBD` | Mid-grade complexity expansion | Cluster validation (4-5) |
| W5 | 10 | 6-8 | Math + ELA | One full unit each grade/subject | `TBD` | Upper-grade complexity and terminology | Grade-8 readiness evidence |

Notes:
- `unknown` IDs in registry are excluded from primary matrix until linked to canonical source docs.
- `TBD` rows must be filled from `docs/roadmap/design/PHASE1_CURRICULUM_DOCUMENT_INVENTORY.md` before execution.

---

## 2) Wave execution policy

For each row in the matrix:
1. Ingest unit.
2. Run quality gates.
3. Archive evidence.
4. Classify adaptation status.
5. If gates pass, run scoped refactor cleanup.
6. Re-run the same tests.
7. Merge and push only after both test runs pass.

Do not start the next wave with unresolved **Critical** adaptation failures in the current wave.

### Branch policy for waves

- One branch per wave: `curriculum/wave-<n>-<scope>`
- Optionally one sub-branch per high-risk unit if needed.
- Merge wave branch only after all in-wave units satisfy wave exit criteria.
- Apply end-of-wave refactor protocol from `docs/refactor/*` before merge:
  - atomic refactor commits,
  - tests before each commit,
  - post-refactor full wave test rerun,
  - LOC snapshot refresh.

---

## 3) Adaptation status model (per unit)

Each unit gets exactly one status:

- **Green (Adaptive):** all critical gates pass; minor warnings only.
- **Yellow (Partial):** extracts core content but has non-critical misses (for example intro/table variant fallback).
- **Red (Insufficient):** parser cannot reliably map required structures; quality gates fail.

---

## 4) Insufficient adaptation detection and alerts

When parser behavior is not sufficient, report it explicitly with a machine-readable alert record.

### 4.1 Alert triggers

Create an alert when any of these are true:
- `standards_structured` missing or malformed for lessons that include standards.
- standards text contains procedure headings (`Activity`, `Warm-up`, etc.).
- required section coverage below threshold (for example missing procedure/narrative in expected templates).
- provenance metadata missing.
- parse crash, partial abort, or unit ingest count below expected minimum.

### 4.2 Alert severity

- **Critical:** correctness risk (wrong section routing, malformed structured standards, missing provenance).
- **Major:** incomplete extraction but recoverable manually.
- **Minor:** cosmetic or low-risk formatting deviations.

### 4.3 Alert payload (required fields)

Use `category` values from `docs/curriculum/FAILURE_TAXONOMY.md` so alerts match ingest reports and profiling.

```json
{
  "run_id": "2026-03-26T22-15-00Z_g3u3",
  "unit_id": "Math_3_U3_xxx",
  "grade": "3",
  "subject": "Math",
  "source_doc_id": "1W1IBU71bwuGpP3M3NTdQXQSH8Jx8fRKF-l9I4Rdo2B4",
  "severity": "Critical",
  "category": "BOUNDARY_LEAK",
  "signal": "heading leaked into standards description",
  "sample_lesson_id": "Math_3_U3_L4",
  "recommendation": "extend _is_non_standard_heading and rerun wave row",
  "created_at": "2026-03-26T22:18:12Z"
}
```

### 4.4 Alert destinations

- Append to run report: `ingest_reports/<run_id>.json`.
- Append one-line summary to `ingest_reports/<run_id>.md`.
- Optional future API feed: `/api/curriculum/ingest-alerts` (planned).

---

## 5) Wave exit criteria

A wave is complete only when:
- all rows are Green or explicitly accepted Yellow with remediation owner/date,
- no unresolved Critical alerts,
- evidence package exists for each unit.

---

## 6) Cross-grade semantic linkage preparation

This matrix also supports teacher vertical alignment:
- prioritize geometry/fractions/area units across neighboring grades,
- capture semantic tags per unit (`geometry`, `fractions`, `area`, `measurement`),
- later map `previous_grade_unit` and `next_grade_unit` links in UI.

Initial seed candidates from this matrix:
- Grade 1 `Unit 7_Geometry_and_Time`
- Grade 2 `Unit 6_Geometry_Time_and_Money`
- Grade 3 `Unit 7_Two-Dimensional_Shapes_and_Perimeter`

---

## 7) Ownership template

For each matrix row, fill:
- **Owner**
- **Scheduled date**
- **Branch**
- **Result status** (Green/Yellow/Red)
- **Open remediation ticket(s)**
- **Evidence path**
- **Test run #1**
- **Refactor summary**
- **Test run #2**

Use this file as the planning board until a dedicated DB-backed tracker is introduced.
