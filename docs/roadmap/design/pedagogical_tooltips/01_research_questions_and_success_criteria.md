# Research questions and success criteria

**Status:** Living document  
**Companion:** [README.md](./README.md)

---

## 1. Product questions

| ID | Question | Owner / notes |
|----|----------|----------------|
| Q1 | Should strategy help appear on **structured** fields only (`ell_support[].strategy_id` / `strategy_name`) first, with prose matching as a later phase? | Reduces false positives; aligns with SSOT. |
| Q2 | For **WIDA**, is v1 limited to regex-friendly fragments (ELD codes, "WIDA levels X–Y", domain names) vs full Key Language Use sentences from PDFs? | Ties to [WIDA_FRAMEWORK_INGESTION_AND_USE.md](../WIDA_FRAMEWORK_INGESTION_AND_USE.md). |
| Q3 | **Hover vs click:** Should rich content (e.g. `long_en`) open only on click/focus to avoid accidental activation during scroll? | Classroom + trackpad use. |
| Q4 | Should teachers be able to **disable** inline tooltips (setting) if they find them distracting? | Optional v2. |
| Q5 | Do we show **aliases** (e.g. strategy pack `aliases[]`) as alternate surface forms for the same tooltip? | Matching policy. |

---

## 2. Technical / matching questions

| ID | Question | Notes |
|----|----------|-------|
| T1 | How do we handle **markdown** in the same string as annotated spans (`parseMarkdown` today)? | See [04_technical_spikes_checklist.md](./04_technical_spikes_checklist.md) spike M1. |
| T2 | What is the policy when the LLM **paraphrases** a strategy name (not in `strategy_name` or `aliases`)? | No tooltip vs fuzzy match vs "did you mean". |
| T3 | **Overlap:** Two strategies with similar substrings in prose—which wins? | Longest match, priority list, or first only. |
| T4 | **Offline:** Must the strategy pack and WIDA JSON ship **inside** the Tauri app bundle? | SSOT copy vs network fetch. |

---

## 3. Success criteria (measurable)

Criteria should be validated with a small **teacher review** (even informal) before calling the feature done.

| Criterion | Target | How to check |
|-----------|--------|--------------|
| S1 | Teachers can identify what a **strategy** means without leaving the lesson view | Task: "What is sentence frames?" answered using tooltip only |
| S2 | **WIDA level** bands (e.g. "Levels 2–5") map to correct Entering–Reaching gloss | Spot-check 5 lessons |
| S3 | No **blocking** UI: primary reading flow remains scroll/read | No modal for default path |
| S4 | **Keyboard:** Focusable triggers; Escape dismisses popover | Manual + axe/DevTools |
| S5 | **Touch:** Tap opens rich content; no hover-only critical info | Tablet smoke test |

---

## 4. Open decisions (move to [05_decision_log.md](./05_decision_log.md) when resolved)

| Topic | Options | Status |
|-------|---------|--------|
| Tooltip vs popover default | Short text in tooltip; long in popover | Open |
| Library stack | Radix / Floating UI / native `title` only | Open |
| Prose strategy matching | Off / conservative / aggressive | Open |

---

## 5. Research synthesis (online, 2025-03-20)

External references and detailed rationale for **Q1–Q5** and **T1–T4** are recorded in **[06_online_research_notes.md](./06_online_research_notes.md)** (library matrix, WCAG 1.4.13 / APG tooltip pattern, touch considerations).

**Short answers:**

- **Q1:** Favor structured `ell_support` + `strategy_id` for v1; add prose matching later with alias-aware matching.
- **Q2:** v1 WIDA: regex-friendly snippets + `wida_framework_reference.json`; defer PDF-sourced blocks to ingestion work.
- **Q3:** Use hover/focus for short gloss only; use click/focus + popover (or disclosure) for `long_en`-class content so hover is not the only path (see WCAG 1.4.13).
- **Q4:** Any “disable tooltips” switch is an **app-level** preference, not a library feature.
- **Q5:** Include `aliases[]` in lookup keys when matching strategy names in text.
- **T1–T4:** See sections 3–4 in `06_online_research_notes.md`.

**Bundle proof:** Library choice still requires a **measured** production build delta—see `06` section 1.3 and [04](./04_technical_spikes_checklist.md) S1 follow-up.
