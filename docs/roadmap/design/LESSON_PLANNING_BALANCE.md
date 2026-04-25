# Lesson Planning Balance: Domains and Key Language Uses

**Status:** Planning  
**Goal:** Plan how the lesson planner achieves **balance** in the distribution of the four language domains (Listening, Reading, Speaking, Writing) and the four Key Language Uses (Narrate, Argue, Inform, Explain) across the week, unit, period, and school year—by subject. The planner will need **prediction and memory** to establish and maintain this balance.

**Related:** [reference_docs/WIDA_ELD/README.md](../../reference_docs/WIDA_ELD/README.md), [REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md](./REFERENCE_DOCS_AND_LESSON_PLAN_ACCESS.md), [WIDA_FRAMEWORK_INGESTION_AND_USE.md](./WIDA_FRAMEWORK_INGESTION_AND_USE.md), [ASSESSMENT_MODULE.md](./ASSESSMENT_MODULE.md) (assessment data informs balance; data must remain anonymized).

**WIDA and balance:** WIDA does not mandate a specific formula or balance of domains or Key Uses per week or unit; the framework "does not prescribe a specific curriculum, pedagogy, or teaching methodology." Instead, educators identify the **"most prominent Key Language Uses"** that align with the unit's content standards, essential questions, and main learning events. Our approach—flexible tagging, memory of what has been used, and prediction/targets for distribution—aligns with that: we support balance without imposing a rigid quota.

---

## 1. Why balance matters

We do **not** want every class to be about the same domain (e.g. Writing) or the same Key Language Use. We want to **distribute** instruction across:

- **Four domains:** Listening, Reading, Speaking, Writing (WIDA language modalities).
- **Four Key Language Uses:** Narrate, Argue, Inform, Explain (WIDA communicative purposes).

Balance supports equitable language development and aligns with WIDA’s expectation that learners engage in multiple modes and purposes over time. The lesson planner (LLM plus any agents/skills) must therefore consider not only “what fits this slot” but “how this slot fits into the larger distribution.”

---

## 2. Scope: by subject

Balance is applied **inside each subject**. For each subject (e.g. ELA, Math, Science, Social Studies), we aim to distribute the four domains and the four Key Language Uses across the relevant time windows. So we track and plan balance **per subject**, not only globally.

---

## 3. Four layers for balance

The planner must establish and maintain balance across **four time layers**:

| Layer | Scope | Role |
|-------|--------|------|
| **Weekly** | 5 days (the lesson plans we generate for one week) | Ensure the week does not overuse one domain or one key use; distribute across the five days. |
| **By unit** | One curriculum unit (e.g. Unit 3: Fractions) | Balance across the unit so that by the end of the unit, domains and key uses are distributed. |
| **By period** | Grading period, semester, or other defined period | Balance across the period so that over several units and weeks, distribution holds. |
| **By school year** | Full school year | Balance across the year so that over all periods and units, no single domain or key use dominates. |

Weekly planning (5 days) is the immediate output; the planner must have **memory** of what has already been used (in the unit, period, year) and **prediction** or targets for what should be used next so that balance is maintained across all four layers.

---

## 4. Memory and prediction

To achieve balance across these layers, the lesson planner will need:

- **Memory:** A way to know what domains and Key Language Uses have already been emphasized in (a) the current unit, (b) the current period, (c) the school year so far. That implies storing or querying **counts or proportions** (e.g. per subject: how many lessons focused on Writing vs. Listening vs. Reading vs. Speaking; how many on Narrate vs. Argue vs. Inform vs. Explain) at the unit, period, and year level.
- **Prediction / targets:** A way to decide what the *next* lesson(s) should emphasize so that the distribution moves toward balance (e.g. if Writing and Inform have been overused this unit, the planner may steer the next slot toward Listening and Narrate, or Reading and Argue). Targets can be simple (e.g. roughly equal counts per domain and per key use over the unit) or more nuanced (e.g. curriculum-driven priorities with a cap on overuse).

Implementation options (to be detailed later): store balance state in the database (e.g. per subject, per unit/period/year: domain and key-use counts or proportions); provide this state to the LLM or to an agent/skill as **context** when generating the next week’s plans; optionally use a small “balance advisor” that suggests or constrains the next slot’s domain and key use so the planner stays on track.

---

## 5. Balance guided by assessment data

Balance can also be **guided by the data we receive from assessment**. If assessment shows that students are **low in one domain** (e.g. Writing) and **advanced in another** (e.g. Reading), the planner should **insist more on the weaker domain** and less on the stronger one—so we emphasize Writing more and Reading less in the coming weeks or unit, rather than treating all four domains equally. The same idea applies to Key Language Uses: if students are strong in Inform but weak in Argue, the planner can tilt the distribution toward Argue.

- **Source of data:** The [Assessment module](./ASSESSMENT_MODULE.md) collects evidence (e.g. checklist, tally) by domain and can support inferences about proficiency or need by domain (and eventually by key use if we assess that). That data must remain **anonymized** when used for planning; the LLM receives only aggregated or coded signals (e.g. "class is low on Writing, high on Reading") never student-identifying information.
- **Use in balance:** Balance targets or the "balance advisor" can take **assessment-informed adjustments**: e.g. increase the target share for Writing and decrease for Reading when assessment indicates that need. Balance is then not only "spread evenly" but **differentiated** according to what students need most.

---

## 6. Summary

| Dimension | What to balance |
|-----------|------------------|
| **Domains** | Listening, Reading, Speaking, Writing (four) |
| **Key Language Uses** | Narrate, Argue, Inform, Explain (four) |
| **Scope** | Per subject; balance inside each subject. |
| **Layers** | Weekly (5 days), by unit, by period, by school year (four layers). |
| **Planner need** | Memory (what has been used) and prediction/targets (what to use next) to establish and maintain balance across the four layers. |
| **Assessment guidance** | Balance can be adjusted by assessment data: emphasize domains/key uses where students are low, ease off where they are advanced; data must stay anonymized (see Assessment module). |

---

## 7. Checklist (planning)

- [ ] Define how we store or compute “usage so far” for domain and Key Language Use per subject, per unit, per period, per school year.
- [ ] Define balance targets or rules (e.g. rough parity over a unit; maximum share for any single domain/key use).
- [ ] Design how the weekly lesson planner receives balance context (memory) and any targets or constraints (prediction) when generating the 5-day plan.
- [ ] Consider a “balance advisor” agent/skill or prompt section that orients the LLM toward the desired distribution for the coming week given the current unit/period/year state.
- [ ] Integrate with primary teacher’s lesson plan: balance should support, not override, what the teacher has chosen to teach and when; balance can influence *how* (which domain/key use to emphasize) within that scope.
- [ ] Define how assessment data (anonymized) feeds into balance: e.g. aggregate signals by domain/key use (e.g. "low on Writing, high on Reading") and use them to adjust targets so the planner emphasizes weaker areas and does not over-emphasize stronger ones.
